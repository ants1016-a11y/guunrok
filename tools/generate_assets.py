# tools/generate_assets.py
"""
Guunrok assets auto generator (one-shot).

What it does:
- Reads card specs (id + display name) from content.registry.CARD_REGISTRY (if available)
- Uses a small enemy name list + tries to include MaCheonGwang boss
- Calls OpenAI Images API to generate consistent-style PNG assets
- Saves them to:
  assets/bg/battle.png
  assets/portraits/enemy/<enemy_name>.png
  assets/portraits/player/default.png
  assets/cards/<card_name>.png

Usage:
  python tools/generate_assets.py --all --force
  python tools/generate_assets.py --cards --force
  python tools/generate_assets.py --enemies --force
  python tools/generate_assets.py --bg --force

Prereqs:
  python3 -m pip install openai pillow
  export OPENAI_API_KEY="..."
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

# --- Optional imports (we fail gracefully) ---
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

try:
    from PIL import Image
except Exception:
    Image = None  # type: ignore


# -----------------------------
# Style guide (keep consistent)
# -----------------------------
STYLE_GUIDE = """
동양 무협 일러스트 스타일. 수묵 느낌(먹번짐, 붓결) 기반.
전체 톤은 절제되고 차분하게. 과도한 디테일/복잡한 배경 금지.
텍스트/워터마크/로고/글자 절대 금지. 얼굴 왜곡 금지.
"""

BG_STYLE = (
    STYLE_GUIDE
    + """
배경 목표: 카드/UI에 집중될 수 있도록 '단색 수묵화(먹빛/회청)' 느낌의 여백 많은 배경.
거친 붓터치와 잔잔한 먹번짐만, 형태는 최소화(실루엣 수준).
대비가 강하지 않게, 밝기 변화는 부드럽게.
중앙은 매우 단순한 여백, 좌우/하단에만 은은한 붓결.
"""
)

PORTRAIT_STYLE = (
    STYLE_GUIDE
    + """
프레이밍: 가슴 위(흉상) 초상화, 정면 또는 3/4 시선.
배경은 단색 수묵 그라데이션(아주 단순). 인물은 선명.
"""
)

CARD_STYLE = (
    STYLE_GUIDE
    + """
카드 일러스트 목표: 심플한 '상징 아이콘' 하나만 중앙에 크게.
배경은 단색 또는 아주 약한 수묵 텍스처(거의 없음).
검/도/권/기운/문양 같은 상징을 또렷하게.
"""
)


# -----------------------------
# Helpers
# -----------------------------
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_dirs(root: Path) -> dict:
    assets = root / "assets"
    paths = {
        "assets": assets,
        "bg": assets / "bg",
        "portraits_enemy": assets / "portraits" / "enemy",
        "portraits_player": assets / "portraits" / "player",
        "cards": assets / "cards",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def safe_filename(name: str) -> str:
    bad = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    out = name
    for ch in bad:
        out = out.replace(ch, "_")
    out = out.strip()
    return out or "unknown"


def load_card_specs(root: Path) -> List[tuple[str, str]]:
    """
    Returns list of (card_id, display_name).
    - Ensures content is loaded so CARD_REGISTRY is populated.
    """
    sys.path.insert(0, str(root))

    try:
        from infra.loader import load_content  # type: ignore

        load_content("content")
    except Exception:
        pass

    try:
        from content.registry import CARD_REGISTRY  # type: ignore

        specs: List[tuple[str, str]] = []
        for cid, template in CARD_REGISTRY.items():
            disp = getattr(template, "name", None) or str(cid)
            specs.append((str(cid), str(disp)))

        specs.sort(key=lambda x: x[0])
        if specs:
            return specs
    except Exception:
        pass

    return [
        ("basic_attack", "기본 공격"),
        ("basic_defense", "기본 방어"),
        ("unge_josik", "운기조식"),
        ("samjaegong", "삼재공"),
        ("yukhapgwon", "육합권"),
        ("pocheonsam", "포천삼"),
        ("bokho", "복호"),
    ]


def load_enemy_names(root: Path) -> List[str]:
    names = [
        "산적",
        "산적 행동대장",
        "산적 부두목",
        "산채 졸개",
        "녹림 행동대장",
        "녹림왕 마천광",
    ]

    sys.path.insert(0, str(root))
    try:
        from content.enemies_nokrim import MaCheonGwang  # type: ignore

        boss = MaCheonGwang()
        if getattr(boss, "name", None) and boss.name not in names:
            names.append(boss.name)
    except Exception:
        pass

    out: List[str] = []
    for n in names:
        if n not in out:
            out.append(n)
    return out


@dataclass
class GenSpec:
    kind: str
    name: str
    prompt: str
    out_path: Path
    size: str
    alpha_png: bool = True


def make_specs(
    root: Path, do_bg: bool, do_cards: bool, do_enemies: bool
) -> List[GenSpec]:
    paths = ensure_dirs(root)
    specs: List[GenSpec] = []

    if do_bg:
        specs.append(
            GenSpec(
                kind="bg",
                name="battle",
                prompt=(
                    f"{BG_STYLE}\n"
                    "고해상도 게임 배경. 단색 수묵화. 여백 많고 절제된 붓결.\n"
                    "카드 UI를 돋보이게 하는 배경.\n"
                    "추가 요구: 강한 채도/강한 대비/화려한 요소 금지."
                ),
                out_path=paths["bg"] / "battle.png",
                size="1536x1024",
                alpha_png=False,
            )
        )

    if do_enemies:
        for en in load_enemy_names(root):
            specs.append(
                GenSpec(
                    kind="portrait_enemy",
                    name=en,
                    prompt=(
                        f"{PORTRAIT_STYLE}\n"
                        f"대상: {en} 무협 악당 초상.\n"
                        "표정: 위압적, 거칠고 냉혹.\n"
                        "의상/소품은 과하지 않게, 실루엣이 또렷하게."
                    ),
                    out_path=paths["portraits_enemy"] / f"{safe_filename(en)}.png",
                    size="1024x1024",
                    alpha_png=True,
                )
            )

        specs.append(
            GenSpec(
                kind="portrait_player",
                name="default",
                prompt=(
                    f"{PORTRAIT_STYLE}\n"
                    "대상: 무협 주인공(무인) 기본 초상.\n"
                    "표정: 침착, 결연.\n"
                    "배경 단색 수묵."
                ),
                out_path=paths["portraits_player"] / "default.png",
                size="1024x1024",
                alpha_png=True,
            )
        )

    # ✅ 핵심 수정: do_cards는 반드시 make_specs 내부에 있어야 함
    if do_cards:
        for cid, disp_name in load_card_specs(root):
            hint = ""
            if "검" in disp_name:
                hint = "상징: 검(칼날), 검기."
            elif "도" in disp_name:
                hint = "상징: 도(큰 칼), 참격."
            elif "권" in disp_name or "장" in disp_name:
                hint = "상징: 주먹/장풍, 충격파."
            elif "방어" in disp_name or "호신" in disp_name:
                hint = "상징: 방패/호신강기, 결계."
            elif "운기" in disp_name or "조식" in disp_name or "회복" in disp_name:
                hint = "상징: 기운의 순환, 숨결, 맥."
            else:
                hint = "상징: 무공 문양/기운."

            prompt = (
                f"{CARD_STYLE}\n"
                f"카드 이름: {disp_name}. {hint}\n"
                "구도: 정사각형 캔버스 중앙에 아이콘 1개를 크게.\n"
                "상하 여백 넉넉히.\n"
                "배경: 거의 단색. 복잡한 배경 금지.\n"
                "색감: 절제된 2~3색 이내."
            )

            # ✅ (1) 한글 표시명 파일을 무조건 생성 (게임 card.name 매칭의 근본)
            specs.append(
                GenSpec(
                    kind="card",
                    name=disp_name,
                    prompt=prompt,
                    out_path=paths["cards"] / f"{safe_filename(disp_name)}.png",
                    size="1024x1024",
                    alpha_png=True,
                )
            )

            # ✅ (2) 영문 id도 함께 생성 (혹시 다른 로직에서 id로 찾는 경우 대비)
            cid_fn = safe_filename(cid)
            disp_fn = safe_filename(disp_name)
            if cid_fn and cid_fn != disp_fn:
                specs.append(
                    GenSpec(
                        kind="card",
                        name=cid,
                        prompt=prompt,
                        out_path=paths["cards"] / f"{cid_fn}.png",
                        size="1024x1024",
                        alpha_png=True,
                    )
                )

    return specs


def require_openai():
    if OpenAI is None:
        raise RuntimeError(
            "openai 패키지가 없습니다. `python3 -m pip install openai` 를 먼저 실행하세요."
        )
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 없습니다. export OPENAI_API_KEY=... 로 설정하세요."
        )


def decode_and_save_png(b64_json: str, out_path: Path) -> None:
    img_bytes = base64.b64decode(b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_bytes)


def resize_to_expected(out_path: Path, target_px: Tuple[int, int]) -> None:
    if Image is None:
        return
    try:
        img = Image.open(out_path).convert("RGBA")
        img = img.resize(target_px, Image.LANCZOS)
        img.save(out_path, format="PNG")
    except Exception:
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="bg+enemies+cards 모두 생성")
    parser.add_argument("--bg", action="store_true", help="배경 생성")
    parser.add_argument("--enemies", action="store_true", help="적/플레이어 초상 생성")
    parser.add_argument("--cards", action="store_true", help="카드 이미지 생성")
    parser.add_argument("--model", default="gpt-image-1.5", help="이미지 모델")
    parser.add_argument("--sleep", type=float, default=0.2, help="요청 사이 sleep")
    parser.add_argument(
        "--force", action="store_true", help="이미 존재하는 파일도 덮어쓰기"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="생성 개수 제한(테스트용). 0이면 무제한"
    )
    args = parser.parse_args()

    do_bg = args.all or args.bg
    do_enemies = args.all or args.enemies
    do_cards = args.all or args.cards
    if not (do_bg or do_enemies or do_cards):
        print(
            "아무 옵션도 선택되지 않았습니다. --all 또는 --bg/--enemies/--cards 중 하나를 사용하세요."
        )
        return

    root = project_root()
    specs = make_specs(root, do_bg=do_bg, do_cards=do_cards, do_enemies=do_enemies)

    if args.limit and args.limit > 0:
        specs = specs[: args.limit]

    require_openai()
    client = OpenAI()

    print(f"Project root: {root}")
    print(f"Generating {len(specs)} assets...")
    print(f"Model: {args.model}")

    generated = 0
    skipped = 0

    for i, spec in enumerate(specs, start=1):
        if spec.out_path.exists() and not args.force:
            skipped += 1
            print(f"[{i}/{len(specs)}] SKIP exists: {spec.out_path}")
            continue

        print(
            f"[{i}/{len(specs)}] GEN {spec.kind}: {spec.name} -> {spec.out_path.name}"
        )

        try:
            resp = client.images.generate(
                model=args.model,
                prompt=spec.prompt,
                n=1,
                size=spec.size,
                output_format="png",
            )
            b64_json = resp.data[0].b64_json
            decode_and_save_png(b64_json, spec.out_path)

            if spec.kind == "bg":
                resize_to_expected(spec.out_path, (1280, 720))
            elif spec.kind.startswith("portrait"):
                resize_to_expected(spec.out_path, (256, 256))
            elif spec.kind == "card":
                resize_to_expected(spec.out_path, (512, 256))

            generated += 1
        except Exception as e:
            print(f"  !! FAIL: {e}")

        time.sleep(max(0.0, args.sleep))

    print("\nDone.")
    print(f"Generated: {generated}, Skipped: {skipped}")
    print("Assets folder:", root / "assets")


if __name__ == "__main__":
    main()
