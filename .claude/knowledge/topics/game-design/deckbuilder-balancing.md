# 덱빌딩 로그라이크 카드 밸런싱 디자인 패턴

- **최종 갱신**: 2026-08-27 (시드 노트)
- **출처**:
  - [How Slay the Spire's devs use data to balance their roguelike deck-builder — Game Developer](https://www.gamedeveloper.com/design/how-i-slay-the-spire-i-s-devs-use-data-to-balance-their-roguelike-deck-builder)
  - [How to Make a Deckbuilder Like Slay the Spire — Summer Engine](https://www.summerengine.com/blog/make-a-deckbuilder-like-slay-the-spire)
  - [Slay the Spire II — Wikipedia](https://en.wikipedia.org/wiki/Slay_the_Spire_II)
- **신뢰도**: 1차 리서치 (검색 요약 기반). 심화 필요 시 원문 재확인 권장.

## 핵심 원칙

1. **싱글플레이어는 완벽한 밸런스가 목표가 아니다.** 플레이어끼리 경쟁하지 않으므로
   카드들이 서로 동등할 필요가 없다. "재미"를 위해 일부러 강한 카드를 남겨도 된다.
   밸런싱의 목표는 공정함이 아니라 **다양한 덱이 모두 즐겁게 플레이되는 것**.
2. **데이터 기반 밸런싱.** Slay the Spire 팀은 플레이 데이터(카드 픽률, 승률)를 수집해
   빠르게 조정했다. 인디 규모에서도 간단한 지표 수집이 큰 효과.
3. **명확성이 깊이의 토대.** 카드 한 장의 기능은 항상 즉시 이해돼야 한다.
   깊이는 카드 자체의 복잡함이 아니라 **카드 × 유물 × 적 패턴 × 강화 × 경로 선택의
   상호작용**에서 나온다.
4. **자기완결적 확장.** 에너지(행동력)-드로우 코어 루프가 견고하면, 새 카드·유물·적은
   각각 독립적인 작은 추가물이 되어 예상 밖의 조합(창발)을 만든다.
5. **운 요소는 리플레이성의 엔진.** 랜덤 이벤트·랜덤 보상이 플레이 스타일 전환을
   강제해 회차마다 다른 경험을 만든다.
6. (2026-03 출시) **Slay the Spire II의 방향**: 캐릭터별로 승리 조건 자체가 다른
   4개 캐릭터, 룬(Rune) 기반 진행 메커니즘, UI 폴리시 강화.

## 구운록 적용 아이디어

- **행동력-패 루프 먼저 굳히기**: 현재 Energy 5 / 카드 비용 1~2 구조를 코어 루프로
  확정하고, 이후 무공 추가는 이 루프를 건드리지 않는 자기완결적 추가로 설계.
- **무공 픽률 로그**: `src/state/game.tsx`에 카드 사용 횟수/승패 카운트만 localStorage로
  쌓아도 데이터 기반 밸런싱 시작 가능 (서버 불필요).
- **명확성 규칙**: 무공 설명은 "8-12 데미지"처럼 숫자를 그대로 노출 (이미 그 방향).
  복잡한 무공은 키워드(예: 내공, 출혈)로 감싸되 키워드 수를 엄격히 제한.
- **회귀(되풀이) 시스템 = 운 요소 재활용**: 회차마다 무공 등장 풀이나 이벤트를 섞어
  리플레이성 확보. 회귀 메타 진행은 큐의 별도 주제로 심화 예정.
- **강함의 비대칭 허용**: 문파/계열별 "사기 무공" 한둘은 의도적으로 남겨 재미 요소로.
