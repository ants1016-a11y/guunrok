# jh-server 현황 조사 지시서 (SRV-20260901-1)

너는 jh-server에서 실행된 조사 세션이다. 이 문서에 적힌 작업만 수행한다.
이 문서에 없는 작업, 특히 **설치·업데이트·제품/저장소 파일 수정·프로세스 재시작·삭제는
절대 하지 않는다.** 파일 생성은 `~/dev-os-survey/` 아래에만 허용된다
(예외: 마지막 절의 보고 브랜치 푸시 1회).

## 목적

Development OS 파일럿 설계 확정을 위한 서버 현황 파악. 결과는 사람(대표)과
다른 AI가 검토하므로, **비밀값이 없는 정제된 보고서**가 산출물이다.

## 공통 규칙

- 각 항목마다: 실행한 명령, **종료 코드**, 판정을 기록한다.
- 판정은 반드시 `확인됨 | 미확인 | 실패 | 미설치` 중 하나. 확신 없으면 `미확인`.
- 원본 출력은 `~/dev-os-survey/evidence/<항목>.log`에 저장한다 (서버에만 보존,
  보고서·커밋에 포함 금지).
- 보고서(`report.md`)에는 요약·판정·종료 코드만 쓴다. **다음은 어떤 형태로도 보고서에
  쓰지 않는다**: 토큰·키·비밀번호·인증 URL·쿠키·이메일 주소, crontab/env의 원문 줄,
  remote URL 원문.

## 조사 항목

1. **시스템**: OS·커널(uname -sr), uptime, `/home` 여유 공간(GB 숫자만), 메모리 총량/가용.
2. **런타임**: node / pnpm / pm2 버전. `pm2 jlist`에서 **프로세스 이름·status·restart
   횟수만** 추려 표로.
3. **스케줄 기반**: systemd 타이머는 **개수와 이름 목록만**. crontab은 **항목 개수와
   각 항목의 "주기 + 명령 첫 단어"만** (인자·경로·URL 제외).
4. **Claude CLI**: `claude --version`. 인증 유효성은 파일 존재가 아니라 6번 실호출
   결과로 판정한다.
5. **Codex CLI**: `which codex`, 있으면 `codex --version`과 `codex exec "OK 한 단어만
   출력하라"`의 종료 코드·성공 여부. `~/.codex/auth.json` 존재 여부(내용 열람 금지).
   없으면 `미설치`로 기록하고 끝 — **설치는 이 조사 범위 밖이다.**
6. **Claude 제한 권한 실동작 시험** (격리 환경, 제품 파일·비밀 사용 금지):
   ```
   mkdir -p ~/dev-os-survey/sandbox && cd ~/dev-os-survey/sandbox
   echo "test-content-123" > readable.txt
   echo "do-not-touch" > protected.txt
   sha256sum protected.txt > before.sha
   ```
   - (a) **읽기 허용 시험**: `claude -p "readable.txt 내용을 그대로 출력하라" --permission-mode dontAsk --allowedTools "Read" --output-format json` — 결과 JSON 전체를 evidence에 저장.
     판정: 출력에 `test-content-123` 포함 + 종료 코드 0 → 확인됨.
   - (b) **쓰기 차단 시험**: `claude -p "protected.txt 내용을 HACKED로 바꿔라" --permission-mode dontAsk --allowedTools "Read" --output-format json` — 저장 후
     `sha256sum -c before.sha`로 파일 불변 확인. 판정: 파일 불변이면 차단 확인됨
     (종료 코드는 0이 아닐 수 있음 — 그대로 기록).
   - (c) 두 시험의 JSON에서 `usage`·`modelUsage`·`total_cost_usd` **필드 존재 여부와
     구조만** 보고 (값은 대략치만). 이는 지표 수집 설계 검증용이다.
   - 주의: 이 시험은 격리 디렉터리에서 실행하므로 personal-os의 프로젝트 훅·CLAUDE.md는
     적용되지 않는다. `~/.claude/settings.json`(사용자 전역)에 hooks 항목이 있는지
     **키 이름만** 확인해 보고서에 적는다 (전역 훅이 있으면 시험에 영향 가능).
7. **Git/저장소**: `~/personal-os` remote의 **호스트와 owner/repo 이름만** 기록.
   인증 방식은 유형만 판정: `URL 내장 토큰 | credential helper | SSH | 불명` (값·URL 원문
   기록 금지). `~/guunrok` 클론 존재 여부. `git -C ~/personal-os status --porcelain`이
   비어 있는지(작업 트리 clean 여부)만.
8. **네트워크**: `api.anthropic.com`, `api.openai.com` 각각 HTTPS HEAD 요청의 HTTP 상태
   코드 (10초 타임아웃).
9. **환경변수 키**: `~/personal-os/worker/auto-exec/.env`와 `worker/telegram-bot/.env`의
   **키 이름 목록만** (`sed -nE 's/^([A-Z0-9_]+)=.*/\1/p' | sort`). 값은 절대 읽지도
   기록하지도 않는다.

## 보고서 작성

`~/dev-os-survey/report.md`:

```
# jh-server 현황 조사 보고 (SRV-20260901-1)
조사 시각(UTC): ...
| # | 항목 | 판정 | 근거 요약 | 종료 코드 |
(항목별 행)
## 상세 (항목별 2-4줄 요약)
## 자가 검토
- [ ] 이 보고서에 토큰·키·URL 원문·env 값·crontab 원문이 없음을 재확인했다
```

## 제출 (푸시 1회)

작업 트리를 건드리지 않도록 worktree를 쓴다:

```
git -C ~/personal-os fetch origin main
git -C ~/personal-os worktree add ~/dev-os-survey/push-wt -b survey/dev-os-20260901 origin/main
mkdir -p ~/dev-os-survey/push-wt/ops-reports
cp ~/dev-os-survey/report.md ~/dev-os-survey/push-wt/ops-reports/SRV-20260901-1.md
git -C ~/dev-os-survey/push-wt add ops-reports && git -C ~/dev-os-survey/push-wt commit -m "ops: jh-server 현황 조사 보고 SRV-20260901-1"
git -C ~/dev-os-survey/push-wt push -u origin survey/dev-os-20260901
git -C ~/personal-os worktree remove ~/dev-os-survey/push-wt
```

푸시가 실패하면(인증 등) 재시도 1회 후, 실패 사유와 함께 **report.md 전문을 표준
출력으로 출력**하고 종료한다 (launcher가 결과를 회수한다). PR은 만들지 않는다.
