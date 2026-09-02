# jh-server 작업 지시서 (OPS-20260901-1): 텔레그램 봇 단독 복구

대표 승인 범위의 작업이다. 이 문서에 적힌 작업만 수행한다.
선행 보고: SRV-20260901-1 / SRV-20260901-2 (survey/dev-os-20260901 브랜치).

## 금지 (승인 범위 밖 — 위반 금지)

- auto-exec·영상 워커 기동 금지. `AUTO_EXEC_MODE` 변경 금지 (live→shadow 포함).
- `pm2 resurrect` 금지 (6월 저장본 전체 복원 금지). 서버 재부팅 금지.
- 제품 코드·설정 파일 수정 금지. 안전 확보에 코드 변경·권한 확대가 필요하다고
  판단되면 **수행하지 말고** 필요한 변경만 보고서에 적어 별도 승인을 요청한다.
- Telegram 메시지·업데이트 삭제 금지 (drop_pending 류 포함).
- 토큰·키·env 값·사용자 대화 내용을 출력·보고에 절대 싣지 않는다.

## 절차 (순서대로. 각 단계 종료 코드·판정 기록, 원본은 ~/dev-os-survey/evidence/에)

### 1. 오류 로그 요약 (기동 가능 판단)
`worker/telegram-bot/bot-error.log`(및 bot-out.log)를 읽되, 보고에는
**오류 유형별 집계·발생 기간·마지막 오류 시각·재발 위험 판단만** 쓴다.
사용자 대화 텍스트·토큰·ID 값은 인용 금지. 오류가 "기동하면 즉시 재실패" 성격
(예: 토큰 무효, 모듈 손상)이면 **기동하지 말고** 여기서 중단·보고.

### 2. 기동 전 안전 확인
- (a) **대기 업데이트**: `worker/telegram-bot/.env`의 토큰을 셸 변수로만 로드해
  (echo 금지) Telegram `getWebhookInfo`를 호출, `pending_update_count` 값만 기록.
  **0이 아니면 기동하지 말고** 건수만 보고 후 중단 (삭제 금지 — 처리 방침은 대표 결정).
- (b) **auto_exec_jobs 재확인**: SRV-2의 queue-count.mjs 재실행, pending=0 유지 확인.
- (c) **자동 개발 경로 명시**: 현재 코드에서 어떤 입력이 Claude 에이전트 실행
  (runAgent)으로 이어지는지 2줄로 보고에 명시 (코드 변경은 하지 말 것).
  이 경로 때문에 아래 5단계의 수신 검증은 반드시 `/status` 명령으로 한다.

### 3. 봇 단독 기동
`worker/telegram-bot/ecosystem.config.cjs`가 봇 1개만 정의하는지 확인 후:
`cd ~/personal-os/worker/telegram-bot && pm2 start ecosystem.config.cjs`
→ `pm2 ls`로 status online 확인 → 30초 대기 → restart 카운트 증가 여부와
bot-error.log 신규 라인 유무(내용은 유형만) 확인. crash-loop이면 `pm2 stop`으로
내리고 원인 요약만 보고 (재시도 반복 금지).

### 4. 송신 검증
토큰을 셸 변수로만 사용해 Telegram sendMessage로 `TELEGRAM_ALLOWED_USER_ID` 채팅에
다음 문구를 발송: "[관제 테스트] 봇 복구 완료. 수신 검증을 위해 이 채팅에 /status 라고
보내주세요. (일반 문장으로 답하면 개발 에이전트가 실행되므로 반드시 /status)"
→ API 응답 ok=true 확인.

### 5. 수신 검증 (비동기 — 대기하지 말 것)
대표의 `/status` 수신 여부는 이 세션이 기다리지 않는다. 대신 검증 방법만 보고에
명시한다: 수신되면 `telegram_commands` 감사 테이블에 기록이 남는다
(다음 관제 확인 때 조회). 이 단계는 `미검증 — 대표 응답 대기`로 표기.

### 6. 자동시작 등록 (봇 안정 확인 후에만)
- 기존 저장본 보존: `cp ~/.pm2/dump.pm2 ~/.pm2/dump.pm2.bak-20260901` (백업 확인).
- `pm2 save` — 현재 실행 목록(봇 1개)만 저장됨을 `dump.pm2` 내 이름으로 확인.
- `pm2 startup systemd -u ants1016 --hp /home/ants1016` 실행. **sudo 비밀번호가
  필요한 명령이 안내되면 sudo를 시도하지 말고**, 안내된 명령 원문(토큰 없음)을
  보고서에 "대표 실행 필요"로 기록만 한다. 재부팅 테스트는 하지 않는다.

### 7. 완료 보고
`~/dev-os-survey/report-ops1.md` 작성 — 형식: ① 봇 상태(online/실패)
② 송신 검증 결과 ③ 수신 검증(미검증 — 대기) ④ 오류 로그 요약과 재발 위험
⑤ 자동시작 등록 결과(백업 경로·저장 대상·대표 실행 필요 항목)
⑥ 미검증·중단 항목과 필요한 결정 ⑦ 각 단계 종료 코드.
worktree 절차(SRV-2와 동일)로 `survey/dev-os-20260901` 브랜치에
`ops-reports/OPS-20260901-1.md`로 커밋·푸시하고, 마지막 응답에 요약을 남긴다.

실패 시: 같은 단계를 2회 이상 반복하지 말고, 실패 지점·원인·필요한 결정을
보고서로 푸시 후 종료한다.
