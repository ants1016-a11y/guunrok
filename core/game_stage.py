"""
core/game_stage.py
챕터 구분, 스테이지 정보, 배경 서사 메시지를 관리합니다.
"""

CHAPTER_INFO = {
    1: {
        "name": "제1장: 산중 표창",
        "range": (1, 5),
        "desc": "첩첩산중을 헤치며 처음 강호에 발을 딛다.",
        "enemies": ["산적", "산적 행동대장", "산적 부두목"],
    },
    2: {
        "name": "제2장: 녹림의 그늘",
        "range": (6, 20),
        "desc": "녹림왕 마천광의 영역. 산채 졸개들이 길을 막는다.",
        "enemies": ["산채 졸개", "녹림 행동대장", "녹림왕 마천광"],
    },
    3: {
        "name": "제3장: 혈교의 음모",
        "range": (21, 999),
        "desc": "혈교가 강호를 잠식하기 시작했다. 자객의 독이 어둠 속에 도사린다.",
        "enemies": ["혈교 자객", "혈교 고수", "혈교 장로 혈마도"],
    },
}


def get_chapter(encounter: int) -> dict:
    """현재 조우 번호로 챕터 정보를 반환합니다."""
    for ch, info in CHAPTER_INFO.items():
        lo, hi = info["range"]
        if lo <= encounter <= hi:
            return {"chapter": ch, **info}
    return {"chapter": 3, **CHAPTER_INFO[3]}


def get_chapter_number(encounter: int) -> int:
    return get_chapter(encounter)["chapter"]


def is_chapter_transition(encounter: int) -> bool:
    """이전 조우가 다른 챕터였는지 확인합니다 (챕터 전환 연출용)."""
    if encounter <= 1:
        return False
    return get_chapter_number(encounter) != get_chapter_number(encounter - 1)


def get_boss_encounters(chapter: int) -> list:
    """해당 챕터에서 보스가 등장하는 조우 배수를 반환합니다."""
    return [n for n in range(CHAPTER_INFO[chapter]["range"][0],
                             CHAPTER_INFO[chapter]["range"][1] + 1)
            if n % 5 == 0]
