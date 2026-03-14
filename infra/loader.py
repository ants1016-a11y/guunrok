# infra/loader.py
import importlib
import pkgutil


def load_content(package_name):
    """지정한 폴더(package_name) 내의 모든 파이썬 파일을 찾아 실행합니다."""
    try:
        package = importlib.import_module(package_name)
        # 하위 폴더를 모두 탐색하며 모듈을 로드합니다.
        for loader, module_name, is_pkg in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            try:
                importlib.import_module(module_name)
                # 주인님의 컨셉에 맞춘 로그 출력
                print(f"📜 [기연] {module_name}의 비급을 발견하여 등록했습니다.")
            except Exception as module_err:
                # 개별 모듈 오류는 건너뛰고 계속 로드합니다.
                print(f"⚠️ [경고] {module_name} 로딩 실패, 건너뜁니다: {module_err}")
    except Exception as e:
        # 혈맥이 막혔을 때(에러 발생 시) 출력
        print(f"❌ [로더 에러] 컨텐츠를 읽어오는 중 혈맥이 막혔습니다: {e}")
