# 구운록 (Guunrok) - 무협 카드 배틀 게임

회귀한 둔재가 되어 녹림 도적들과 전투를 벌이는 턴제 카드 배틀 게임입니다.

## 설치 방법

### 1. 가상환경 활성화 (이미 활성화되어 있다면 생략)
```bash
# 가상환경이 있다면
source .venv/bin/activate  # 또는 사용 중인 가상환경 활성화
```

### 2. Pygame 설치
```bash
# 방법 1: requirements.txt 사용
pip install -r requirements.txt

# 방법 2: 직접 설치
pip install pygame

# 방법 3: python3 -m pip 사용 (가상환경이 아닌 경우)
python3 -m pip install pygame
```

## 실행 방법

```bash
python main.py
# 또는
python3 main.py
```

## 게임 조작법

- **마우스 클릭**: 카드를 클릭하여 선택하고, 같은 카드를 다시 클릭하면 사용
- **스페이스바**: 턴 종료
- **엔터**: 선택된 카드 사용
- **창 닫기**: 게임 종료

## 게임 특징

- **플레이어**: 회귀한 둔재 (탱커 스타일)
- **적**: 녹림 도적단 (졸개, 행동대장, 녹림왕)
- **카드 시스템**: 5종의 무공 카드
- **동적 스토리**: 전투 결과에 따라 생성되는 내레이션
- **턴제 전투**: 전략적인 카드 배틀

## 문제 해결

### ModuleNotFoundError: No module named 'pygame'
가상환경에 pygame이 설치되지 않았습니다. 위의 설치 방법을 따라 pygame을 설치하세요.

### 한글이 깨지는 경우
macOS에서는 자동으로 한글 폰트를 감지합니다. 만약 한글이 깨지면 시스템에 한글 폰트가 설치되어 있는지 확인하세요.

# guunrok
