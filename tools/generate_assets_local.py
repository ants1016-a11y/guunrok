# tools/generate_assets_local.py
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_dirs(root: Path) -> dict:
    assets = root / "assets"
    paths = {
        "assets": assets,
        "cards": assets / "cards",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def safe_filename(name: str) -> str:
    bad = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    out = name.strip()
    for ch in bad:
        out = out.replace(ch, "_")
    out = out.replace(" ", "_")
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "unknown"


def load_card_display_names(root: Path) -> List[Tuple[str, str, str]]:
    """
    Returns list of (card_id, display_name, type_value)
    - type_value: "공격"/"방어"/"기세" 같은 값 (없으면 "기세")
    """
    sys.path.insert(0, str(root))
    try:
        from infra.loader import load_content  # type: ignore

        load_content("content")
    except Exception:
        pass

    out: List[Tuple[str, str, str]] = []
    try:
        from content.registry import CARD_REGISTRY  # type: ignore

        for cid, template in CARD_REGISTRY.items():
            disp = getattr(template, "name", None) or str(cid)
            t = getattr(getattr(template, "type", None), "value", None) or "기세"
            out.append((str(cid), str(disp), str(t)))
        out.sort(key=lambda x: x[1])  # 한글명 기준 정렬
        return out
    except Exception:
        # fallback
        return [
            ("samjaegong", "삼재공", "기세"),
            ("yukhapgwon", "육합권", "공격"),
            ("pocheonsam", "포천삼", "방어"),
            ("bokhojang", "복호장", "공격"),
            ("yoonji", "유운지", "기세"),
        ]


def pick_font(size: int) -> ImageFont.ImageFont:
    # macOS 기본 폰트 우선
    candidates = [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/AppleGothic.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def ink_paper_bg(w: int, h: int, seed: int) -> Image.Image:
    rnd = random.Random(seed)
    # 밝은 수묵지
    base = Image.new("RGBA", (w, h), (245, 245, 242, 255))
    draw = ImageDraw.Draw(base)

    # 잔잔한 종이 결 (점/선)
    for _ in range(1200):
        x = rnd.randrange(0, w)
        y = rnd.randrange(0, h)
        a = rnd.randrange(6, 18)
        c = rnd.randrange(200, 235)
        draw.point((x, y), fill=(c, c, c, a))

    # 먹 번짐(연한 구름)
    cloud = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud)
    for _ in range(10):
        cx = rnd.randrange(int(w * 0.15), int(w * 0.85))
        cy = rnd.randrange(int(h * 0.20), int(h * 0.80))
        r = rnd.randrange(40, 120)
        a = rnd.randrange(18, 45)
        cd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(40, 40, 40, a))
    cloud = cloud.filter(ImageFilter.GaussianBlur(radius=10))
    base = Image.alpha_composite(base, cloud)
    return base


def classify_icon(name: str, type_value: str) -> str:
    n = name
    if "검" in n:
        return "sword"
    if "도" in n:
        return "blade"
    if "권" in n or "장" in n:
        return "fist"
    if "방어" in n or "호신" in n or type_value == "방어":
        return "shield"
    if "운기" in n or "조식" in n or "기" in n or type_value == "기세":
        return "qi"
    return "sigil"


def draw_ink_icon(canvas: Image.Image, kind: str, seed: int) -> None:
    rnd = random.Random(seed)
    d = ImageDraw.Draw(canvas)
    w, h = canvas.size
    cx, cy = w // 2, h // 2

    ink = (25, 25, 28, 230)
    ink2 = (25, 25, 28, 160)

    def brush_line(xy, width):
        # 붓 느낌: 여러 번 살짝 흔들어 그리기
        for i in range(4):
            jitter = rnd.randrange(-2, 3)
            d.line(
                [(xy[0][0] + jitter, xy[0][1]), (xy[1][0] - jitter, xy[1][1])],
                fill=ink2,
                width=max(1, width - 2),
            )
        d.line(xy, fill=ink, width=width)

    if kind == "sword":
        brush_line([(cx - 40, cy + 30), (cx + 35, cy - 35)], 8)
        brush_line([(cx + 12, cy - 18), (cx + 44, cy - 45)], 4)
        d.ellipse((cx - 10, cy + 22, cx + 10, cy + 42), outline=ink, width=5)
    elif kind == "blade":
        brush_line([(cx - 50, cy - 35), (cx + 50, cy + 35)], 12)
        d.arc(
            (cx - 55, cy - 55, cx + 55, cy + 55), start=200, end=330, fill=ink, width=6
        )
    elif kind == "fist":
        d.ellipse((cx - 42, cy - 42, cx + 42, cy + 42), outline=ink, width=8)
        for _ in range(4):
            ang = rnd.random() * 3.14
            r = rnd.randrange(8, 18)
            x = cx + int(r * (1 if rnd.random() > 0.5 else -1))
            y = cy + rnd.randrange(-10, 12)
            d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=ink2)
    elif kind == "shield":
        poly = [
            (cx, cy - 50),
            (cx + 40, cy - 20),
            (cx + 26, cy + 52),
            (cx - 26, cy + 52),
            (cx - 40, cy - 20),
        ]
        d.polygon(poly, outline=ink, fill=(0, 0, 0, 0))
        d.line([poly[0], poly[2]], fill=ink2, width=4)
    elif kind == "qi":
        d.ellipse((cx - 42, cy - 42, cx + 42, cy + 42), outline=ink, width=6)
        d.arc(
            (cx - 55, cy - 55, cx + 55, cy + 55), start=30, end=210, fill=ink2, width=8
        )
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=ink2)
    else:  # sigil
        for r in [48, 30, 14]:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink2, width=4)
        brush_line([(cx - 60, cy), (cx + 60, cy)], 6)
        brush_line([(cx, cy - 60), (cx, cy + 60)], 6)

    # 번짐 효과(살짝)
    blur = canvas.filter(ImageFilter.GaussianBlur(radius=1.6))
    canvas.alpha_composite(blur, (0, 0))


def render_card_image(name: str, type_value: str, out_path: Path, seed: int) -> None:
    # generate_assets.py가 최종적으로 512x256으로 리사이즈하니까
    # 여기서도 512x256으로 바로 맞춘다.
    W, H = 512, 256
    bg = ink_paper_bg(W, H, seed=seed)

    # 중앙 아이콘 캔버스(투명)
    icon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kind = classify_icon(name, type_value)
    draw_ink_icon(icon, kind, seed=seed + 7)

    # 합성
    img = Image.alpha_composite(bg, icon)

    # 아주 약한 금빛 포인트(테두리 느낌)
    d = ImageDraw.Draw(img)
    gold = (190, 155, 70, 80)
    d.rounded_rectangle((6, 6, W - 6, H - 6), radius=18, outline=gold, width=3)

    # 파일 저장
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", action="store_true", help="카드 이미지(로컬) 생성")
    parser.add_argument(
        "--force", action="store_true", help="이미 존재하는 파일도 덮어쓰기"
    )
    parser.add_argument("--limit", type=int, default=0, help="생성 개수 제한(테스트용)")
    parser.add_argument("--variant", type=int, default=0, help="버전 저장 (예: __v2)")
    parser.add_argument("--seed", type=int, default=0, help="고정 시드(0이면 랜덤)")
    args = parser.parse_args()

    if not args.cards:
        print("옵션이 없습니다. --cards 를 사용하세요.")
        return

    root = project_root()
    paths = ensure_dirs(root)

    cards = load_card_display_names(root)
    if args.limit and args.limit > 0:
        cards = cards[: args.limit]

    made = 0
    skipped = 0

    for cid, disp, type_value in cards:
        base_name = safe_filename(disp)  # ✅ 한글 파일명 유지
        if args.variant and args.variant > 0:
            fname = f"{base_name}__v{args.variant}.png"
        else:
            fname = f"{base_name}.png"

        out_path = paths["cards"] / fname

        if out_path.exists() and not args.force:
            skipped += 1
            continue

        seed = args.seed if args.seed else (hash(disp) & 0xFFFFFFFF)
        # 같은 카드라도 variant에 따라 그림 달라지게
        seed = (seed + args.variant * 10007) & 0xFFFFFFFF

        render_card_image(disp, type_value, out_path, seed=seed)
        made += 1

    print(f"Done. Made={made}, Skipped={skipped}")
    print("Cards folder:", paths["cards"])


if __name__ == "__main__":
    main()
