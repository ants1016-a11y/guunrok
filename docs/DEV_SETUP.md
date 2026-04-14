# 개발 환경 설정 가이드

이 문서는 Guunrok 프로젝트의 개발 환경을 설정하는 방법을 안내합니다.

## 필수 요구사항

- Python 3.11 이상
- pip (Python 패키지 관리자)

## 1. 프로젝트 클론 및 이동

```bash
cd /path/to/Guunrok
```

## 2. 가상 환경 설정 (권장)

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate  # Windows
```

## 3. 개발 도구 설치

### 필수 도구

```bash
# black (코드 포맷터)
python3 -m pip install black

# ruff (린터)
python3 -m pip install ruff
```

### 한 번에 설치

```bash
python3 -m pip install black ruff
```

## 4. 에디터 설정

### VS Code

1. VS Code 확장 프로그램 설치:
   - Python (Microsoft)
   - Black Formatter (Microsoft)
   - Ruff (Astral Software)

2. 프로젝트 루트의 `.vscode/settings.json`이 자동으로 적용됩니다.
   - 들여쓰기: 스페이스 4칸 고정
   - 저장 시 자동 포맷팅 활성화
   - 들여쓰기 자동 감지 비활성화

### 다른 에디터

`.editorconfig` 파일이 지원되는 에디터에서는 자동으로 설정이 적용됩니다.

## 5. Pre-commit 훅 설정

Git 커밋 전에 자동으로 코드 검사를 수행하도록 설정합니다.

```bash
# pre-commit 훅에 실행 권한 부여
chmod +x .git/hooks/pre-commit
```

이제 커밋 시 자동으로 다음 검사가 수행됩니다:
1. `python3 -m py_compile main.py` - 문법 검사
2. `python3 -m black --check main.py` - 포맷 검사
3. `python3 -m ruff check main.py` - 린팅 검사

## 6. 코드 포맷팅 및 린팅

### 수동 실행

```bash
# black으로 포맷팅
python3 -m black main.py

# ruff로 린팅 (자동 수정 포함)
python3 -m ruff check --fix main.py
```

### 자동 실행

VS Code에서 파일 저장 시 자동으로 포맷팅됩니다.

## 7. 게임 실행

```bash
# 개발 스크립트 실행 (자동 검사 포함)
./dev/run.sh
```

또는

```bash
python3 main.py
```

## 문제 해결

### 들여쓰기 오류가 계속 발생하는 경우

1. VS Code 설정 확인:
   - `editor.detectIndentation`이 `false`로 설정되어 있는지 확인
   - `editor.insertSpaces`가 `true`로 설정되어 있는지 확인
   - `editor.tabSize`가 `4`로 설정되어 있는지 확인

2. 파일 전체 재포맷팅:
   ```bash
   python3 -m black main.py
   ```

3. 들여쓰기 수동 확인:
   ```bash
   python3 -m py_compile main.py
   ```

### Pre-commit 훅이 작동하지 않는 경우

```bash
# 권한 확인
ls -l .git/hooks/pre-commit

# 권한 부여
chmod +x .git/hooks/pre-commit

# 테스트 실행
.git/hooks/pre-commit
```

## 추가 정보

- 프로젝트 설정 파일:
  - `.editorconfig` - 에디터 설정
  - `.vscode/settings.json` - VS Code 설정
  - `pyproject.toml` - black/ruff 설정
  - `.git/hooks/pre-commit` - Git 훅 설정

- 코드 스타일:
  - 들여쓰기: 스페이스 4칸 (탭 사용 금지)
  - 최대 줄 길이: 88자 (black 기본값)
  - 줄 끝: LF (Unix 스타일)
