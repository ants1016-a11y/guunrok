# 구현 지시서 (PILOT-20260902-1 r2): 봇 안전화 + 승인함 P1

> **범위 명칭: "봇 안전화 + 승인함 P1"** — Development OS 전체가 아니다.
> 일일 조사·제안 오케스트레이터·Codex 자동 검토는 이 범위에 **없으며**, P2로 분리된다.
> **승인 상태: 구현·단위 테스트·PR 작성까지 승인됨 (격리 브랜치).
> 운영 DB 적용·봇 교체·배포는 별도 승인.**
> r2 변경: 대표·Codex 검토 4항목 반영 (Codex 게이트 강제화 / 읽기 전용의 실차단
> 구성·검증 / 롤백의 무승인 경로 부활 금지 / 알림 재시도·중복 방지).

## 0. 불변 조건

- auto-exec·영상 워커 기동 금지. `AUTO_EXEC_MODE` 변경 금지.
- **main 직접 푸시 금지** — 브랜치 `pilot/approval-adapter`에서만 작업, PR은 머지하지 않음.
- 지정 변경 파일 외 수정 금지. 비밀값 커밋·출력 금지. 운영 봇(`nexus-tg-bot`, 현재
  main 코드로 가동 중)은 건드리지 않는다. 마이그레이션 SQL은 파일만 작성, **적용 금지**.
- 승인·감사 기록(`dev_approvals`, `dev_events`, `telegram_commands`)은 어떤 단계에서도
  삭제·수정하지 않는다 (스키마 롤백도 drop이 아니라 rename/archive).

## 1. 봇 안전 구조 (일반 문장 = 상담·조회·제안)

`worker/telegram-bot/lib/agent.ts`의 `query()` 옵션 변경:

- `permissionMode: "dontAsk"`
- `allowedTools: ["Read","Glob","Grep","WebFetch","WebSearch"]` (허용 목록)
- `disallowedTools: ["Write","Edit","MultiEdit","NotebookEdit","Bash","KillBash","Task","Tmux"]`
  (이중 봉인 — 허용 목록 밖 도구가 다른 경로로 살아나도 명시 차단)
- **설정 상속 차단**: `settingSources`를 명시적으로 비워 프로젝트 `.claude/settings.json`
  (훅·허용 규칙)이 로드되지 않게 한다. `mcpServers` 미구성 확인.
- **비밀 파일 읽기 차단**: `canUseTool` 콜백을 구현해 Read/Glob/Grep의 대상 경로가
  다음 패턴이면 거부: `**/.env*`, `**/credentials*`, `~/.claude/**`, `~/.pm2/**`,
  `**/auth.json`. 거부 시 사유를 결과에 남긴다.
- 응답 말미 고정 문구: "이 대화는 상담·조회용입니다. 실행이 필요하면 제안으로 올려
  승인을 받으세요."

**표현 규칙**: 위 구성은 "차단되도록 구성"까지이며, **"차단된다"는 판정은 5절의
실차단 시험 통과 후에만 기록**한다. 기능 변화(자유발화 개발 중단)는 대표 인지 완료.

## 2. DB 스키마 (파일 작성만 — 적용은 별도 승인)

`supabase/migrations/068_dev_proposals.sql` (신규). RLS는 034 패턴(service_role 전용).

```sql
create table dev_proposals (
  task_id text not null,
  version int not null default 1,
  content_hash text not null,
  title text not null,
  body text not null,
  proposal_type text not null check (proposal_type in ('process','project','test')),
  is_test boolean not null default false,   -- test 유형은 true 강제(트리거/체크)
  status text not null default 'draft' check (status in
    ('draft','sent','approved','rejected','revision_requested','superseded')),
  codex_review_status text not null default 'not_performed' check
    (codex_review_status in ('not_performed','pending','passed','failed')),
  codex_unmet_conditions text,
  created_at timestamptz default now(),
  primary key (task_id, version),
  check (proposal_type <> 'test' or is_test = true),
  check (is_test = false or proposal_type = 'test')
);
create table dev_approvals (
  id bigint generated always as identity primary key,
  task_id text not null, version int not null, content_hash text not null,
  decision text not null check (decision in
    ('approved','rejected','revision_requested','hold','blocked_codex','blocked_stale')),
  decision_note text,
  approver_tg_id text not null,
  raw_command text not null,
  decided_at timestamptz default now()
);
create table dev_events (
  id bigint generated always as identity primary key,
  event_type text not null check (event_type in
    ('approval_request','completed','failed','action_needed','receipt')),
  ref_task_id text,
  message_summary text not null,
  dedup_key text not null unique,           -- event_type+ref+본문해시 → 중복 발송 방지
  report_written boolean not null default false,
  tg_status text not null default 'pending' check
    (tg_status in ('pending','sent','retrying','failed_gave_up')),
  tg_message_id text,
  tg_sent_at timestamptz,
  retry_count int not null default 0,
  last_error text,
  created_at timestamptz default now()
);
```

스키마 롤백(적용됐을 경우): `alter table ... rename to zz_archived_...` 3건 —
**drop 금지** (감사 기록 보존).

## 3. 승인 어댑터 (변경 파일)

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `worker/telegram-bot/lib/proposals.ts` | 신규 | CRUD·정규화 sha256 해시·상태 전이·`notifyOwner()` |
| `worker/telegram-bot/commands/approval.ts` | 신규 | `승인\|거절\|수정\|보류 <ID>` 처리 (아래 규칙) |
| `worker/telegram-bot/index.ts` | 수정 | 120행 부근에 `bot.hears(/^(승인\|거절\|수정\|보류)\s+\S+/, handleApproval)` + `/help` 1줄 |
| `worker/telegram-bot/lib/agent.ts` | 수정 | 1절 전체 |
| `worker/telegram-bot/lib/proposals.test.ts` | 신규 | 단위 테스트 (5절) |
| `worker/telegram-bot/scripts/seed-tests.mjs` | 신규 | TEST-001~003 시드 (전부 `proposal_type='test'`, `is_test=true`) |

**승인 처리 규칙**:
1. 발신자 `from.id` = `TELEGRAM_ALLOWED_USER_ID` 일치 시에만 유효. 불일치는 무시+감사.
2. **Codex 게이트 (강제)**: `is_test=false`인 실제 제안은 `codex_review_status='passed'`가
   아니면 `승인` 명령을 **접수하되 승인 처리하지 않는다** — `dev_approvals`에
   `blocked_codex`로 기록하고 "Codex 검토 미통과로 승인 불가. 미충족: <codex_unmet_conditions>"
   회신. **TEST(is_test=true) 제안만 게이트를 우회**하며, 시험용임이 발송 문구에 명시되고
   실행 경로가 없는 데이터로만 존재한다.
3. 최신 version·해시에만 승인 유효. 구버전/해시 불일치 → `blocked_stale` 기록 + 재승인
   안내 회신. 중복 승인 → 상태 불변 + "이미 승인됨(최초 시각)" 회신.
4. `수정 <ID> <메모>` → revision_requested, 구버전 superseded (기존 승인 무효).
   `거절` → rejected. `보류` → hold 기록.
5. 모든 접수 회신은 `dev_events('receipt')` 경유.

**알림 규칙** (`notifyOwner`):
- 대상 이벤트: 승인 요청 / 완료 / 실패 / 조치 필요 / 접수 회신.
- 발송 전 `dedup_key`(event_type + ref_task_id + message 해시) 중복 검사 — 중복이면
  발송하지 않고 기존 행 참조.
- 발송 성공: `tg_status='sent'`, `tg_sent_at`, `tg_message_id` 기록.
- 실패: 지수 백오프(5s/15s/45s)로 **최대 3회** 재시도(`retrying`, `retry_count` 증가,
  `last_error` 기록). 최종 실패 시 `failed_gave_up` — 이 상태의 행이 존재하면 다음
  보고서에 반드시 "TG 발송 실패 N건" 명시.
- `report_written`(저장소/세션 보고 존재)과 `tg_status`는 **항상 별도로** 기록·대조.

## 4. 롤백 (무승인 개발 경로 부활 금지)

| 상황 | 복구 | 금지 |
|---|---|---|
| 구현 단계 이상 | 브랜치 폐기만 — 운영 무영향 | - |
| 시험 배포 중 이상 | 임시 봇 종료 → **기본값: 봇 정지 유지 + 대표에게 보고·결정 요청** | 자동으로 main(=bypassPermissions 경로 포함)을 재기동하지 않는다. 운영 복귀는 대표 지시로만 |
| 정식 배포 후 이상 | `pm2 stop nexus-tg-bot`(정지) 또는 **검증된 안전 커밋**(1절 변경이 포함된 마지막 정상 커밋)으로 복귀 | 1절 안전 변경을 제거하는 revert 금지 — 어떤 복귀 지점에도 `bypassPermissions` 경로가 없어야 함 |
| DB | rename/archive만 | drop·기록 수정 금지 |
| 자동시작 | `dump.pm2.bak-20260901` 복사 | - |

## 5. 검증

**구현 단계 (이번 승인 범위)** — 운영 무영향:
1. `npx tsc --noEmit` 통과 + `npm test`(vitest) 통과. 단위 테스트 최소 10케이스:
   해시 일치/불일치(2), 상태 전이(3), 중복·구버전 승인(2), **Codex 게이트 — 실제 제안
   승인 차단 + TEST 우회(2)**, 알림 dedup(1).
2. 브랜치 푸시. PR은 생성 시도하되 서버에서 불가하면 compare URL로 대체 보고
   (관제 세션이 PR 생성을 이어받음).
3. 보고서 푸시 + 텔레그램 알림("구현 완료 — 시험 배포 승인 대기").

**시험 배포 단계 (별도 승인)** — 마이그레이션 적용(관리자), 운영 봇 일시 중지 후:
- **실차단 시험 (1절 검증 — 이것 통과 전에는 "차단된다"고 기록 금지)**:
  ① 일반 문장으로 파일 수정 요청 → 파일 해시 불변 + `permission_denials` 기록
  ② Bash 실행 요청 → 거부 확인 ③ `.env` 내용 요청 → canUseTool 거부 확인
  ④ 프로젝트 훅 미로드 확인 (훅 부작용 파일 미생성).
- TEST-001(승인→기록→접수→개발 미실행→중복 승인), TEST-002(거절),
  TEST-003(수정→v2→구버전 승인 blocked_stale→v2 승인), **실제 제안 모형 1건으로
  Codex 게이트 차단(blocked_codex) 실동작 확인**.
- dev_events의 report_written vs tg_status 대조, 재시도·dedup 동작 확인.
- 종료 시 4절 롤백 규칙 적용 (자동 main 재기동 금지).

**정식 배포 단계 (별도 승인)**: PR 머지(대표) → pull → restart → `/status` → `pm2 save`.

## 6. 권한·관리자 단계

- 구현 세션 수정 허용: 3절 표 + `supabase/migrations/068_*.sql` 만. 새 비밀·sudo 불필요.
- 관리자(대표) 단계 — **미완 상태 명시 유지**: ① 마이그레이션 적용(시험 배포 승인 시)
  ② pm2 startup sudo 1줄(기존 미완, 봇 자동시작의 마지막 조각).

## 7. 이 지시서에 없는 것 (P2 — 별도 승인)

development-os 저장소 / 일일 조사·제안 오케스트레이터 / Codex 설치·인증·자동 검토 /
dev_task_metrics / 구운록 파일 이동. **현재 시스템에는 일일 자동 제안이 존재하지
않는다** — 이 사실은 보고서마다 명시한다.
