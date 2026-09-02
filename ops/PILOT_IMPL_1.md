# 파일럿 구현 지시서 (PILOT-20260902-1): 승인 서브시스템 + 봇 안전 구조

> **상태: 검토용 초안 — 대표 구현 승인 전. 이 문서만으로는 아무것도 실행하지 않는다.**
> 구현은 승인 후 jh-server CLI가 수행한다. 이 지시서의 범위는 personal-os(Nexus)의
> 승인 어댑터와 안전 구조까지이며(P1), development-os 저장소·일일 제안 오케스트레이터·
> Codex 연결은 다음 지시서(P2)로 분리한다.

## 0. 불변 조건 (전 단계 공통)

- auto-exec·영상 워커 기동 금지. `AUTO_EXEC_MODE` 변경 금지 (`live` 그대로).
- main 직접 푸시 금지 — 모든 변경은 브랜치 `pilot/approval-adapter` + PR. 병합은 대표만.
- 지정된 변경 파일 외 수정 금지. 비밀값 커밋·출력 금지. 서버 재부팅 금지.
- 승인해도 실제 개발은 실행되지 않는다 — 이 지시서의 코드에는 승인→실행 연결 자체가 없다.
- 봇 자동시작: 기존 승인 범위대로 `pm2 save`(봇 단독)까지 완료됨. **systemd 유닛 등록은
  관리자(sudo) 단계로 미완** — 대표 실행 필요 상태를 그대로 표시·유지한다.

## 1. 봇 안전 구조 변경 (대표 지시 1번)

**원칙: 일반 문장 = 상담·조회·제안. 저장소 수정·명령 실행의 승인이 아니다.
개발 실행은 명시적으로 승인된 작업 ID에만 연결한다 (파일럿에서는 연결 없음).**

변경: `worker/telegram-bot/lib/agent.ts`의 에이전트 옵션을
`permissionMode: "bypassPermissions"` → `permissionMode: "dontAsk"` +
`allowedTools: ["Read", "Glob", "Grep", "WebFetch", "WebSearch"]` 로 교체.

- 효과: 자유발화·음성은 코드를 **읽고 분석·상담·제안**할 수 있으나 쓰기·셸 실행이
  구조적으로 거부된다 (OPS-1에서 확인된 도구 목록 봉인 방식).
- **명시적 기능 변화 (대표 인지 필요)**: 기존 "바로 고쳐줘" 자유발화 개발 기능이
  중단된다. 이는 대표 지시 1번의 의도된 결과다. 향후 개발 실행은 승인된 작업 ID를
  통해서만 재개된다(P2 이후, 별도 승인).
- 에이전트 응답 말미에 고정 문구 1줄 추가: "이 대화는 상담·조회용입니다. 실행이
  필요하면 제안으로 올려 승인을 받으세요."

## 2. DB 변경 (신규 마이그레이션 1건)

`supabase/migrations/068_dev_proposals.sql` (신규). RLS는 034_telegram_commands.sql과
동일하게 service_role 전용. **적용은 관리자 단계** — 대표가 Supabase 대시보드에서
실행하거나, 시험 배포 승인 시 승인된 명령으로 1회 적용.

```sql
-- dev_proposals: 제안 원장
create table dev_proposals (
  task_id text not null,            -- 예: TEST-001, DEV-20260903-1
  version int not null default 1,
  content_hash text not null,       -- 본문 sha256 (정규화 후)
  title text not null,
  body text not null,
  proposal_type text not null check (proposal_type in ('process','project')),
  status text not null default 'draft' check (status in
    ('draft','sent','approved','rejected','revision_requested','superseded')),
  codex_review_status text not null default 'not_performed' check
    (codex_review_status in ('not_performed','pending','passed','failed')),
  codex_unmet_conditions text,      -- 미수행 사유 (예: 'Codex CLI 미설치·미인증')
  created_at timestamptz default now(),
  primary key (task_id, version)
);
-- dev_approvals: 결정 기록 (감사 — 갱신·삭제하지 않음)
create table dev_approvals (
  id bigint generated always as identity primary key,
  task_id text not null, version int not null, content_hash text not null,
  decision text not null check (decision in ('approved','rejected','revision_requested','hold')),
  decision_note text,
  approver_tg_id text not null,     -- TELEGRAM_ALLOWED_USER_ID와 일치 검증 후 기록
  raw_command text not null,        -- 대표가 보낸 명령 원문
  decided_at timestamptz default now()
);
-- dev_events: 보고·알림 이력 (지시 3번 — 보고서 작성과 TG 발송을 별도 기록)
create table dev_events (
  id bigint generated always as identity primary key,
  event_type text not null check (event_type in
    ('approval_request','completed','failed','action_needed','receipt')),
  ref_task_id text, message_summary text not null,
  report_written boolean not null default false,  -- 저장소/세션 보고 존재 여부
  tg_sent boolean not null,                       -- sendMessage ok=true 여부
  tg_message_id text,
  created_at timestamptz default now()
);
```

롤백 SQL: `drop table dev_events; drop table dev_approvals; drop table dev_proposals;`

## 3. 봇 승인 어댑터 (변경 파일 목록)

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `worker/telegram-bot/lib/proposals.ts` | 신규 | dev_proposals CRUD, 본문 정규화+sha256 해시, `notifyOwner()`(sendMessage 후 `dev_events`에 tg_sent·message_id 기록), 상태 전이 함수 |
| `worker/telegram-bot/commands/approval.ts` | 신규 | `승인|거절|수정|보류 <작업ID>` 파싱·처리 (아래 규칙), `telegram_commands` 감사는 기존 beginHandler/finishHandler 재사용 |
| `worker/telegram-bot/index.ts` | 수정 | **120행 부근**(에이전트 제어 뒤, `message:voice`/`message:text` 앞)에 `bot.hears(/^(승인|거절|수정|보류)\s+\S+/, handleApproval)` 1행 등록 + `/help`에 안내 1줄 |
| `worker/telegram-bot/lib/agent.ts` | 수정 | 1절의 권한 교체 + 고정 문구 |
| `worker/telegram-bot/lib/proposals.test.ts` | 신규 | vitest 단위 테스트: 해시 일치/불일치, 전 상태 전이, 중복 승인, 잘못된 ID |
| `worker/telegram-bot/scripts/seed-tests.mjs` | 신규 | TEST-001~003 시드 및 승인 요청 발송 (4절) |

**승인 처리 규칙** (AUTONOMY_RULES 준수):
- 발신자 `from.id`가 `TELEGRAM_ALLOWED_USER_ID`와 일치할 때만 유효. 불일치 시 무시+감사 기록.
- `승인 <ID>` → 해당 task_id의 **최신 version·해시**에 대해서만 approved 기록 + 접수
  회신("승인 접수: <ID> v<n> / 승인자 / 시각. 파일럿에서는 개발을 실행하지 않습니다").
- **중복 승인**: 이미 approved인 동일 버전 → 상태 변화 없이 "이미 승인됨(최초 승인 시각)" 회신.
- **구버전 승인**: 제안이 개정돼 해시가 다르면 거부 회신("제안이 v<n>으로 개정되어 기존
  승인 대상이 아닙니다. 최신 본문 확인 후 재승인 필요") — 기록은 dev_approvals에 남김.
- `수정 <ID> <내용>` → revision_requested + 사유 기록, 기존 승인 무효(구버전 superseded).
- `거절 <ID>` → rejected. `보류 <ID>` → hold 기록(상태 유지).
- 모든 접수 회신은 `dev_events(event_type='receipt')`로 기록.

**Codex 게이트** (지시 4번): 승인 요청 발송 문구에 `Codex 검토: <상태>`를 반드시 포함.
현재 서버는 Codex 미설치·미인증이므로 모든 제안은 `not_performed` +
`codex_unmet_conditions='Codex CLI 미설치·미인증(jh-server), 인증 방식·예산 미결정'`으로
생성된다. `passed`는 실제 `codex exec` 실행 증거(exit 0 + 출력 보존)가 있을 때만 기록
가능하며, 코드에 기본값으로 넣지 않는다. **검토 미수행 상태로 '검토 완료' 표기가
생성될 수 있는 경로가 없어야 한다** (단위 테스트 항목에 포함).

**알림 범위** (지시 3번): `notifyOwner()`는 승인 요청 외에 `completed`/`failed`/
`action_needed` 이벤트에도 사용한다. 발송 실패(ok≠true) 시 `tg_sent=false`로 기록하고
보고서에 "TG 발송 실패" 명시 — 조용한 실패 금지.

## 4. 검증 방법 (단계 분리)

**구현 단계 (이번 승인 범위 후보)** — 운영 무영향:
1. `npx tsc --noEmit` + `npm test`(vitest) 통과. 신규 테스트 최소 8케이스
   (해시 검증 2, 상태 전이 3, 중복·구버전 승인 2, Codex 게이트 1).
2. 브랜치 `pilot/approval-adapter` 푸시 + PR 생성 (머지하지 않음).
3. 보고서 푸시 + 텔레그램으로 "구현 완료, 시험 배포 승인 대기" 알림.

**시험 배포 단계 (별도 승인 필요)** — 운영 봇 일시 중단 수반(TG는 이중 폴링 시 409 충돌):
1. 마이그레이션 068 적용 (관리자 단계).
2. `pm2 stop nexus-tg-bot` → 브랜치 worktree에서 봇 임시 기동.
3. **TEST 왕복 시험**: `seed-tests.mjs`로 발송, 대표가 텔레그램에서 응답.
   - TEST-001: 승인 요청 → 대표 `승인 TEST-001` → 기록(ID·버전·해시·승인자·시각) →
     접수 회신 → **개발 미실행 확인** → 이어서 같은 명령 재전송으로 **중복 승인** 검증.
   - TEST-002: → 대표 `거절 TEST-002` → rejected 기록·회신 검증.
   - TEST-003: → 대표 `수정 TEST-003 <메모>` → v2 개정 발송 → 구버전에 대한
     `승인 TEST-003`이 거부되는지 → 최신 v2 승인 정상 처리 검증.
   - 일반 문장 1회 전송 → 에이전트가 조회 전용으로 응답하고 쓰기 거부되는지
     (`permission_denials` 확인) + 고정 문구 표시 검증.
4. 각 시험의 dev_events에 report_written/tg_sent가 별도 기록됐는지 대조.
5. 임시 봇 종료 → `pm2 start nexus-tg-bot`(운영 복귀, main 기준) → 복귀 확인.
6. 결과 보고 푸시 + TG 알림.

**정식 배포 단계 (별도 승인 필요)**: PR 머지(대표) → 서버 `git pull` →
`pm2 restart nexus-tg-bot` → `/status` 재확인 → `pm2 save` 갱신.

## 5. 권한

- 구현 세션의 수정 허용 경로: 3절 표의 파일 + `supabase/migrations/068_*.sql` **만**.
- 새 비밀·env 불필요 (기존 `SUPABASE_SERVICE_ROLE_KEY`·봇 토큰 재사용). sudo 불필요.
- 관리자(대표) 단계 2건: ① 마이그레이션 적용 ② (기존 미완) pm2 startup sudo 1줄.

## 6. 복구 방법

| 상황 | 복구 |
|---|---|
| 시험 배포 중 이상 | 임시 봇 종료 → `pm2 start nexus-tg-bot` (main 코드로 즉시 복귀) |
| 정식 배포 후 이상 | `git checkout <이전 커밋> -- worker/telegram-bot` 대신 **revert PR** + `pm2 restart` |
| DB 롤백 | 2절의 drop 3줄 (감사 기록 보존이 필요하면 drop 대신 rename) |
| 자동시작 원복 | `cp ~/.pm2/dump.pm2.bak-20260901 ~/.pm2/dump.pm2` |

## 7. 이 지시서가 하지 않는 것 (P2로 이월)

development-os 저장소 생성 / 일일 제안 오케스트레이터(pm2 워커) / Codex 설치·인증·
검토 자동화 / dev_task_metrics 지표 테이블 / 구운록 파일 이동. — 각각 별도 승인.
