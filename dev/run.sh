#!/bin/bash
# Guunrok 게임 실행 스크립트
# 이 스크립트는 실행 전 자동 검사를 수행합니다.

set -e  # 오류 발생 시 즉시 종료

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Guunrok 게임 실행 스크립트"
echo "=========================================="
echo ""

# 1. Python 컴파일 검사 (black보다 먼저 실행 - 문법 오류를 먼저 탐지)
# 중요: python3 -m py_compile main.py 통과 전에는 black 실행 금지
# 커서 작업 끝나면 무조건:
#   1) python3 -m py_compile main.py
#   2) (통과하면) black main.py
echo "[1/4] Python 문법 검사 중..."
if python3 -m py_compile main.py; then
    echo "  → 문법 검사 통과"
else
    echo "  ✗ 문법 오류 발견! 실행을 중단합니다."
    echo "  ✗ black 실행이 차단되었습니다. (py_compile 통과 후에만 실행 가능)"
    exit 1
fi
echo ""

# 2. black 설치 확인 및 설치
echo "[2/4] black 포맷터 확인 중..."
if ! python3 -m pip show black > /dev/null 2>&1; then
    echo "  → black이 설치되어 있지 않습니다. 설치 중..."
    python3 -m pip install -q black
    echo "  → black 설치 완료"
else
    echo "  → black이 이미 설치되어 있습니다."
fi
echo ""

# 3. black으로 코드 포맷팅 (py_compile 통과 후에만 실행)
echo "[3/4] 코드 포맷팅 중 (black)..."
python3 -m black main.py
echo "  → 포맷팅 완료"
echo ""

# 4. 게임 실행
echo "[4/4] 게임 실행 중..."
echo ""
python3 main.py
