# 디버깅 시스템 검증 절차

## 구현된 기능 요약

### 1. DebugLogger (파일 저장)
- `logs/run_YYYYMMDD_HHMMSS.log` 파일로 모든 로그 저장
- JSON Lines 형식 (한 줄에 하나의 JSON 객체)
- 레벨: DEBUG, INFO, WARN, ERROR, CRITICAL
- 태그: PHASE_TRANSITION, UI_CLICK, STATE_CHANGE, ERROR 등

### 2. State Snapshot 저장
- `snapshot_state()` 함수: 현재 게임 상태를 딕셔너리로 반환
- `dump_snapshot(tag)`: 파일로 저장 (`debug/snapshots/snap_*.json`)
- F9 키: 수동 스냅샷 저장
- 에러 발생 시 자동 스냅샷 저장

### 3. Phase Transition 단일 함수 강제
- `set_phase(new_phase, reason="")`만 phase 변경 가능
- prev_phase 자동 저장
- state_enter_id 자동 증가
- transition 로그 자동 기록
- CAMP/TRAINING 진입 시 enemy None 체크 및 강제 clear

### 4. "한 번만 실행" 가드
- `_handled_enter_ids` 딕셔너리로 각 이벤트별 마지막 처리된 enter_id 추적
- `on_victory()`, `on_defeat()` 등에 가드 적용

### 5. Error Boundary
- 메인 루프 try/except로 감싸기
- 프레임 단위 에러 처리
- 에러 발생 시:
  - 스냅샷 자동 저장
  - 최근 로그 200줄과 함께 에러 파일 저장 (`logs/error_*.txt`)
  - 화면에 에러 표시

### 6. UI 클릭 라우팅 가시화
- `button_registry`: {button_id: {"rect": pygame.Rect, "layer": str, "enabled": bool}}
- 클릭 시 `last_ui_click`에 기록
- F3 키: UI 클릭 영역 표시 (버튼 외곽선)
- 레이어 순서: modal -> panel -> hud

### 7. 재현 커맨드
- `--seed 1234` 옵션으로 랜덤 시드 고정
- 예: `python main.py --seed 1234`

## 검증 절차

### 1. F9 스냅샷 저장 검증

**절차:**
1. 게임 실행: `python main.py`
2. 전투 중 아무 phase에서든 F9 키 누르기
3. `debug/snapshots/` 폴더 확인
4. `snap_YYYYMMDD_HHMMSS_f9_manual.json` 파일 생성 확인

**검증 항목:**
- 파일이 생성되었는지
- JSON 형식이 올바른지
- `phase`, `prev_phase`, `player`, `enemy`, `last_ui_click`, `last_transition` 필드가 있는지

**예상 결과:**
```json
{
  "timestamp_ms": 1234567890,
  "phase": "PLAYER_TURN",
  "prev_phase": "ENEMY_TURN",
  "player": {
    "hp": 100,
    "max_hp": 100,
    "energy": 5,
    ...
  },
  "enemy": {
    "exists": true,
    "name": "녹림 졸개",
    "hp": 30,
    ...
  },
  "last_ui_click": {...},
  "last_transition": {...}
}
```

### 2. 에러 발생 시 자동 스냅샷/로그 저장 검증

**절차:**
1. 게임 실행 중 의도적으로 에러 발생시키기
   - 예: `main.py`에서 `raise Exception("테스트 에러")` 추가
2. 에러 발생 확인
3. 다음 파일들 확인:
   - `logs/error_YYYYMMDD_HHMMSS.txt` (에러 리포트)
   - `debug/snapshots/snap_*_error_*.json` (에러 시 스냅샷)
   - `logs/run_*.log` (최근 로그 200줄 포함)

**검증 항목:**
- 에러 파일에 stacktrace가 있는지
- 스냅샷이 저장되었는지
- 최근 로그 200줄이 포함되었는지
- 화면에 에러 메시지가 표시되었는지

**예상 결과:**
```
=== ERROR REPORT ===
Type: frame_error
Time: 2024-01-01T12:00:00
Phase: PLAYER_TURN
State: BATTLE
Chapter: 1, Encounter: 0
Turn: 5

=== STACKTRACE ===
Traceback (most recent call last):
  ...

=== SNAPSHOT ===
{...}

=== RECENT LOGS (200 lines) ===
{...}
```

### 3. Phase Transition 로그 검증

**절차:**
1. 게임 실행: `python main.py`
2. 전투 진행 (카드 사용, 턴 종료 등)
3. `logs/run_*.log` 파일 확인

**검증 항목:**
- 모든 phase 전환이 로그에 기록되었는지
- `PHASE_TRANSITION` 태그로 기록되었는지
- `from`, `to`, `reason`, `enter_id`가 포함되었는지

**예상 로그:**
```json
{"timestamp_ms": 1234567890, "level": "INFO", "tag": "PHASE_TRANSITION", "message": "PLAYER_TURN -> ENEMY_TURN", "data": {"reason": "플레이어 턴 종료", "enter_id": 5, ...}}
```

### 4. UI 클릭 라우팅 검증

**절차:**
1. 게임 실행: `python main.py`
2. F3 키 눌러서 UI 클릭 영역 표시
3. 버튼 클릭 (수련하기, 계속 걷기 등)
4. `logs/run_*.log` 파일 확인

**검증 항목:**
- 클릭된 버튼이 `UI_CLICK` 태그로 기록되었는지
- `button_id`, `layer`, `pos` 정보가 포함되었는지
- 스냅샷의 `last_ui_click`에 기록되었는지

**예상 로그:**
```json
{"timestamp_ms": 1234567890, "level": "INFO", "tag": "UI_CLICK", "message": "버튼 클릭: camp_train", "data": {"button_id": "camp_train", "layer": "hud", "pos": {"x": 400, "y": 300}, ...}}
```

### 5. "한 번만 실행" 가드 검증

**절차:**
1. 게임 실행: `python main.py`
2. 적을 물리쳐서 승리 상태 진입
3. `logs/run_*.log` 파일 확인
4. `on_victory`가 여러 번 호출되지 않았는지 확인

**검증 항목:**
- `on_victory` 로그가 한 번만 기록되었는지
- `_handled_enter_ids["on_victory"]`가 올바르게 설정되었는지

### 6. Seed 고정 재현 검증

**절차:**
1. 첫 번째 실행: `python main.py --seed 1234`
2. 카드 사용, 턴 종료 등 행동 기록
3. 두 번째 실행: `python main.py --seed 1234`
4. 동일한 행동 수행
5. 결과 비교 (적 HP, 카드 순서 등)

**검증 항목:**
- 두 실행의 결과가 동일한지
- 랜덤 요소가 시드에 따라 고정되었는지

### 7. CAMP/TRAINING 진입 시 enemy None 체크 검증

**절차:**
1. 게임 실행: `python main.py`
2. 전투 승리 후 CAMP 화면 진입
3. `logs/run_*.log` 파일 확인

**검증 항목:**
- `set_phase(PHASE_CAMP)` 호출 시 enemy가 None인지
- enemy가 None이 아니면 WARN 로그가 기록되었는지

**예상 로그:**
```json
{"timestamp_ms": 1234567890, "level": "WARN", "tag": "PHASE_TRANSITION", "message": "CAMP/TRAINING 진입 시 enemy가 None이 아님 (강제 clear)", ...}
```

## 디버깅 팁

### 버그 발생 시 확인 순서

1. **F9로 스냅샷 저장**
   - 현재 상태를 즉시 저장
   - `debug/snapshots/snap_*_f9_manual.json` 확인

2. **로그 파일 확인**
   - `logs/run_*.log`에서 최근 이벤트 확인
   - `PHASE_TRANSITION`, `UI_CLICK`, `ERROR` 태그 검색

3. **에러 파일 확인**
   - `logs/error_*.txt` 확인
   - stacktrace와 스냅샷 포함 여부 확인

4. **스냅샷 분석**
   - `phase`, `prev_phase` 확인
   - `last_ui_click`, `last_transition` 확인
   - `player`, `enemy` 상태 확인

### 자주 발생하는 버그 패턴

1. **Phase와 화면 불일치**
   - 증상: 화면은 CAMP인데 phase는 PLAYER_TURN
   - 확인: `last_transition` 로그 확인
   - 해결: `set_phase()` 호출 누락 확인

2. **버튼 클릭 무시**
   - 증상: 버튼 클릭해도 반응 없음
   - 확인: `UI_CLICK` 로그 확인, `button_registry` 확인
   - 해결: F3로 클릭 영역 확인, 레이어 순서 확인

3. **승리/패배 중복 처리**
   - 증상: 승리 메시지가 여러 번 표시됨
   - 확인: `_handled_enter_ids` 확인
   - 해결: "한 번만 실행" 가드 확인

## 파일 구조

```
Guunrok/
├── main.py
├── logs/
│   ├── run_20240101_120000.log  # 실행 로그
│   └── error_20240101_120500.txt  # 에러 리포트
└── debug/
    └── snapshots/
        ├── snap_20240101_120000_f9_manual.json
        └── snap_20240101_120500_error_frame_error.json
```

## 단축키

- **F1**: 수동 스냅샷 저장 (기존)
- **F9**: 수동 스냅샷 저장 (새로 추가)
- **F2**: 디버그 오버레이 토글
- **F3**: UI 클릭 영역 표시

