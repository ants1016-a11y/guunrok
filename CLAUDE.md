# 구운록 (Guunrok)

무협/회귀물 세계관의 턴제 카드 배틀 웹 게임. Next.js 16 (App Router) + React 19 +
Tailwind CSS 4 + TypeScript.

## 명령어

- `npm run dev` — 개발 서버
- `npm run build` — 프로덕션 빌드
- `npm run lint` — ESLint

## 구조

- `src/app/` — 페이지 (battle, inn, reward, training, world, worldmap)
- `src/lib/` — 게임 로직 (cards, enemies, formulas, player, types, worldmap)
- `src/state/game.tsx` — 전역 게임 상태
- `src/ui/` — 공용 UI 컴포넌트
- `docs/` — 게임 디자인(DESIGN.md), 세계관(LORE*.md), 개발 환경(DEV_SETUP.md)

## 거버넌스 (모든 세션 필독)

이 프로젝트는 "AI가 제안하고 대표가 승인하는" 구조로 운영됩니다. 루트의 거버넌스
문서 6종이 공식 기준입니다:

- `PROJECT_CHARTER.md` — 제품 방향·톤·하지 않는 것
- `AUTONOMY_RULES.md` — **자동 실행·승인 규칙 (반드시 준수)**. 현재 Stage 0:
  대표 승인 전에는 위험도와 관계없이 어떤 개발도 시작하지 않음
- `ROADMAP.md` — 현재 최우선 목표(P0)
- `DECISIONS.md` — 승인된 결정 기록 (감사 기록, 과거 항목 수정 금지)
- `STATUS.md` — 현재 상태·다음 후보 (작업 후 갱신 의무)
- `QUALITY_GATES.md` — 테스트·완료 기준

승인은 GitHub 제안 이슈에 저장소 소유자가 작업 ID를 포함해 단 댓글만 유효합니다.
자세한 형식은 AUTONOMY_RULES.md 참고.

## 자동 학습 지식 베이스 (중요)

이 프로젝트에는 자동 학습 시스템이 있습니다. 예약 루틴이 평상시에 스스로 리서치를
돌려 `.claude/knowledge/`에 최신 지식을 쌓습니다. 시스템 설명은
`.claude/knowledge/README.md`, 루틴 사양은 `.claude/knowledge/ROUTINE.md` 참고.

**개발 세션은 기능 개발·설계 작업을 시작하기 전에 반드시:**

1. `git fetch origin claude/knowledge-base` 실행 (최신 학습 결과는 이 브랜치에 쌓임).
2. 현재 브랜치에 없다면 그 브랜치의 지식을 읽기:
   `git show origin/claude/knowledge-base:.claude/knowledge/INDEX.md`
3. 작업과 관련된 노트가 있으면 같은 방식(`git show origin/claude/knowledge-base:<경로>`)으로
   읽고, 그 최신 지식을 반영해서 개발할 것.
4. 개발 중 알게 된 유용한 사실이나 다음에 학습하면 좋을 주제가 있으면
   `.claude/knowledge/research-queue.md`에 추가해 둘 것.

지식 베이스가 fetch 안 되거나 비어 있으면 그냥 진행하되, 사용자에게 한 줄로 알릴 것.
