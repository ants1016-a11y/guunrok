# jh-server 서비스 실태 진단 지시서 (SRV-20260901-2)

너는 jh-server에서 실행된 진단 세션이다. 이 문서에 적힌 작업만 수행한다.
**읽기 전용이다. 프로세스 시작·중지·재시작, 설치, 커밋, reset, stash, 파일 수정은
절대 하지 않는다.** 파일 생성은 `~/dev-os-survey/` 아래에만 허용 (보고 푸시 1회 제외).
SRV-20260901-1과 동일한 공통 규칙 적용: 항목별 종료 코드,
판정(`확인됨|미확인|실패|해당없음`), 원본은 `~/dev-os-survey/evidence/`에만,
보고서에 토큰·키·URL 원문·env 값·로그 본문 금지.

## 목적

pm2 목록이 비어 있는 것이 "전부 다운"인지 확인하고, 미커밋 변경과 대기 작업의
위험을 평가해 **안전한 복구 대상과 순서를 제안**한다. 복구 실행은 이번 범위 밖이다.

## 조사 항목

1. **실제 프로세스 실태** (pm2 목록만 믿지 말 것):
   - `ps -eo user,pid,etime,cmd`에서 node / tsx / pm2 / PM2 관련 행만 추려,
     **실행 계정·경과시간·명령 첫 두 토큰만** 보고 (전체 인자 금지).
   - 다른 PM2 인스턴스: `ls -d /home/*/.pm2 /root/.pm2 2>/dev/null` — 존재하는 경로 목록만.
     루트 권한 없으면 그 사실만 기록.
   - systemd: `systemctl list-units --type=service --state=running | grep -iE 'pm2|nexus|bot|node'`
     및 `systemctl --user list-units --type=service` 동일 필터 — 유닛 이름만.
   - Docker: `which docker`가 있으면 `docker ps --format '{{.Names}} {{.Status}}'` — 이름·상태만.
     권한 거부면 그 사실만 기록.
   - **판정**: 텔레그램 봇·auto-exec·영상 워커 각각에 대해 `실행 중(어디서) | 미실행 | 미확인`.

2. **pm2 중단 원인 단서** (원인은 단정하지 말고 증거만):
   - `~/.pm2/dump.pm2` 존재 여부·수정 시각 (있으면 안에 등록된 **프로세스 이름만** —
     `grep -o '"name":"[^"]*"' | sort -u` 수준).
   - `~/.pm2/pm2.log`의 **마지막 10줄의 타임스탬프와 로그 레벨만** (본문 금지).
   - `last reboot | head -3` — 최근 재부팅 시각.
   - `systemctl list-unit-files | grep -i pm2` — pm2 startup 등록 여부.
   - **판정**: "재부팅 후 미복구" 가설에 대해 `뒷받침됨 | 반박됨 | 불충분`.

3. **봇 최근 동작 흔적**: `worker/telegram-bot/`의 `bot-out.log`·`bot-error.log` 존재 여부와
   **수정 시각만** (내용 열람 금지 — 사용자 대화가 담길 수 있음). 수정 시각으로
   "마지막 동작 추정 시점"만 기록.

4. **미커밋 변경 21건 위험 평가**:
   - `git -C ~/personal-os status --porcelain` 전체를 evidence에 저장하고, 보고서에는
     **디렉터리별 개수 집계표**(예: worker/telegram-bot N건, worker/auto-exec N건, src/ N건 …)와
     **worker/ 하위 변경 파일의 경로 목록**만.
   - worker/ 하위 변경 파일 각각: `git diff --stat -- <파일>`의 증감 수치만 보고,
     그 변경이 봇/auto-exec 런타임 동작에 영향을 주는 파일인지 `영향 가능 | 영향 없음(문서 등) | 미확인`으로 판정.
     diff 본문은 보고서에 넣지 않는다.
   - 변경은 **절대 건드리지 않는다** (커밋·리셋·stash 금지).

5. **auto-exec 대기 큐** (읽기 전용 DB 조회):
   - `worker/auto-exec/` 안에서 dotenv로 env를 로드하는 **임시 Node 스크립트를
     ~/dev-os-survey/에 만들어** `auto_exec_jobs`를 status별 `select count`만 조회한다.
     env 값은 절대 stdout·보고서에 출력하지 않는다. node_modules가 없어서 실행 불가면
     `미확인`으로 기록 (설치 금지).
   - 보고: status별 건수 표 (pending 몇 건인지가 핵심).
   - `AUTO_EXEC_MODE`의 **값**은 예외적으로 보고 허용 (shadow/live 구분은 비밀이 아니고
     복구 위험 판단에 필수).

6. **복구 제안** (실행 금지, 제안만):
   위 결과를 근거로 다음 형식의 제안을 보고서 마지막에 쓴다.
   - 파일럿에 필요한 최소 복구 대상 (예: 봇만 / 봇+X)
   - 각 대상의 복구 전 선행 조건 (예: worker 변경 파일 검토, pending 잡 처리 방침)
   - 복구를 보류해야 할 대상과 이유 (예: auto-exec — pending N건 + MODE=live라면 위험)
   - pm2 startup 등록 권고 여부
   - 각 항목에 근거(조사 번호) 표기. 확신 없으면 "미확인 — 대표 확인 필요"로.

## 보고서·제출

`~/dev-os-survey/report2.md` 작성 (1차와 같은 표+상세+자가 검토 형식).
제출은 기존 브랜치에 파일 추가:

```
git -C ~/personal-os fetch origin survey/dev-os-20260901
git -C ~/personal-os worktree add ~/dev-os-survey/push-wt2 survey/dev-os-20260901
cp ~/dev-os-survey/report2.md ~/dev-os-survey/push-wt2/ops-reports/SRV-20260901-2.md
git -C ~/dev-os-survey/push-wt2 add ops-reports && git -C ~/dev-os-survey/push-wt2 commit -m "ops: jh-server 서비스 실태 진단 SRV-20260901-2"
git -C ~/dev-os-survey/push-wt2 push origin survey/dev-os-20260901
git -C ~/personal-os worktree remove ~/dev-os-survey/push-wt2
```

푸시 실패 시 재시도 1회 후 report2.md 전문을 표준 출력으로 내고 종료. PR 금지.
