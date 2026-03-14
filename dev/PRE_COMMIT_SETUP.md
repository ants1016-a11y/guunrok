# Pre-commit Hook 설정 가이드

이 프로젝트는 커밋 전 자동으로 코드 품질 검사를 수행하는 pre-commit hook을 사용합니다.

## 설치 방법

### 1. 자동 설치 (권장)

```bash
cd /Users/jaeheekim/Desktop/aicode/Guunrok
chmod +x .git/hooks/pre-commit
```

### 2. 수동 설치

`.git/hooks/pre-commit` 파일이 이미 생성되어 있습니다. 실행 권한만 부여하면 됩니다:

```bash
chmod +x .git/hooks/pre-commit
```

## 검사 항목

Pre-commit hook은 다음을 검사합니다:

1. **py_compile**: Python 문법/들여쓰기 오류 검사
2. **black**: 코드 포맷팅 검사

## 동작 방식

- 커밋 시 자동으로 실행됩니다
- 검사 실패 시 커밋이 중단됩니다
- 검사 통과 시 정상적으로 커밋이 진행됩니다

## 검사 실패 시 해결 방법

### py_compile 실패
```bash
python3 -m py_compile main.py
# 오류 메시지를 확인하고 수정
```

### black 검사 실패
```bash
python3 -m black main.py
# 포맷팅 후 다시 커밋
```

## 비활성화 (임시)

필요한 경우 `--no-verify` 플래그로 hook을 우회할 수 있습니다:

```bash
git commit --no-verify -m "메시지"
```

**주의**: 이 방법은 권장되지 않습니다. 코드 품질 검사를 우회하면 문제가 발생할 수 있습니다.
