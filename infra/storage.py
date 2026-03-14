import os
import json

SAVE_DIR = "saves"


def ensure_save_dir():
    """저장 폴더가 없으면 생성합니다."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def get_save_path(user_id):
    """사용자 ID에 해당하는 저장 파일 경로를 반환합니다."""
    return os.path.join(SAVE_DIR, f"{user_id}.json")


def save_game_data(user_id, data):
    """딕셔너리 데이터를 JSON 파일로 저장합니다."""
    ensure_save_dir()
    path = get_save_path(user_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[Storage] {user_id} 데이터 저장 완료.")
        return True
    except Exception as e:
        print(f"[Storage] 저장 실패: {e}")
        return False


def load_game_data(user_id):
    """JSON 파일을 읽어 딕셔너리로 반환합니다."""
    path = get_save_path(user_id)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[Storage] {user_id} 데이터 불러오기 성공.")
        return data
    except Exception as e:
        print(f"[Storage] 불러오기 실패: {e}")
        return None


def get_existing_users():
    """저장된 파일 목록에서 사용자 ID들을 추출합니다."""
    ensure_save_dir()
    files = os.listdir(SAVE_DIR)
    users = []
    for f in files:
        if f.endswith(".json"):
            users.append(f.replace(".json", ""))
    return users
