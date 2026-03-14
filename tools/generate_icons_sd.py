#!/usr/bin/env python3
"""
tools/generate_icons_sd.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stable Diffusion(로컬/무료) 기반 수묵 무공 아이콘 대량 생성 파이프라인.

사용 예:
  # 문법 검사
  python3 -m py_compile tools/generate_icons_sd.py

  # 5개만 테스트
  python3 tools/generate_icons_sd.py --limit 5 --force

  # 특정 카드만
  python3 tools/generate_icons_sd.py --only "육합권" --force

  # 전체 생성 (SD 2.1 권장 — SD 1.5는 runwayml 레포가 비공개됨)
  python3 tools/generate_icons_sd.py --force --model stabilityai/stable-diffusion-2-1

  # SDXL (품질 최상, 메모리 6GB+)
  python3 tools/generate_icons_sd.py --force --model stabilityai/stable-diffusion-xl-base-1.0

라이브러리 설치:
  python3 -m pip install -U diffusers transformers accelerate safetensors pillow torch
  (Mac: torch는 https://pytorch.org/ 에서 Metal/MPS 지원 버전 설치 권장)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# ── 프로젝트 루트 설정 ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ── 필수 라이브러리 확인 ──────────────────────────────────────────────────────
_INSTALL_HINT = (
    "python3 -m pip install -U diffusers transformers accelerate safetensors pillow"
)


def _check_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print(f"[ERROR] Pillow 미설치.\n  {_INSTALL_HINT}")
        sys.exit(1)


def _check_diffusers():
    try:
        import diffusers  # noqa: F401
    except ImportError:
        print(f"[ERROR] diffusers 미설치.\n  {_INSTALL_HINT}")
        sys.exit(1)


# ── 카드명 → 아이콘 주제 매핑 ────────────────────────────────────────────────
def _icon_subject(name: str) -> str:
    """
    카드 표시명에서 아이콘 주제 텍스트를 결정합니다.
    규칙: 구체적 실루엣 위주 — 동그란 문양/과녁 금지.
    """
    n = name

    if "권" in n or "장" in n:
        return "powerful fist impact, palm strike shockwave, strong arm silhouette"
    if "검" in n:
        return "sword silhouette, sword slash arc, gleaming blade stroke"
    if "대참" in n or "참" in n:
        return "great blade slashing diagonal, heavy sword cut, bold slash stroke"
    if "도" in n and ("법" in n or "패" in n or "기" in n):
        return "dao blade silhouette, heavy diagonal slash, broad sword shape"
    if "도" in n:
        return "dao blade silhouette, heavy diagonal slash stroke"
    if any(k in n for k in ("부동", "철벽", "호신")):
        return "defensive stance silhouette, solid guard posture, ink barrier stroke, NO circle NO ring"
    if "방어" in n or "방" in n:
        return "defensive arm guard, blocking stance, shield stroke, NO circle"
    if any(k in n for k in ("운기", "조식")):
        return "seated meditation figure, flowing breath mist, qi circulation strokes"
    if any(k in n for k in ("심법", "기세")):
        return "flowing qi energy trail, wind breath strokes, misty force"
    if "보법" in n or "유운" in n or "비연" in n or "보" == n[-1:]:
        return "footwork silhouette, swift feet movement, wind trail after steps"
    if "독" in n:
        return "poison mist swirl, dark vapour cloud drifting, NO emblem"
    if "추" in n:
        return "heavy weight dropping, gravity fist strike, plummeting force"
    if "붕" in n or "산악" in n:
        return "dual fist double strike, two fists impacting, mountain shatter"
    if "포효" in n:
        return "roaring figure silhouette, shockwave burst from mouth, sound force"
    if "포천" in n:
        return "three consecutive palm thrusts, triple strike silhouette, rapid hand"
    if "돌팔매" in n or "탄" in n:
        return "stone projectile arc, throwing rock motion, ranged impact"
    if "난도" in n or "난" == n[:1]:
        return "chaotic blade swing, rough slash silhouette, desperate cut"
    if "멱살" in n:
        return "grabbing collar silhouette, one hand gripping cloth, throw motion"
    if "주먹" in n:
        return "single fist punch silhouette, direct strike, knuckles forward"
    if "점혈" in n or "혈" in n:
        return "finger strike at pressure point, single extended finger thrust"
    if "공격" in n:
        return "direct attack slash, bold strike silhouette, forward thrust"
    if "기" in n:
        return "flowing qi energy trail, internal force aura, wind breath strokes"

    # 기본 폴백
    return "single bold brush slash, qi energy streak, martial force silhouette"


# ── 프롬프트 템플릿 ───────────────────────────────────────────────────────────
_POS_BASE = (
    "minimal ink-wash martial arts icon, white rice paper background, "
    "bold brush strokes, strong negative space, single object silhouette, "
    "centered composition, object fills 70% of frame, "
    "traditional Chinese ink painting style, monochromatic, high contrast"
)

_NEG_BASE = (
    "circle, target, concentric rings, emblem, logo, badge, seal, "
    "geometric pattern, mandala, yin yang, text, letters, numbers, "
    "watermark, multiple objects, busy background, gradient sphere, "
    "photo realistic, 3d render, western style"
)


def make_prompt(card_name: str) -> Tuple[str, str]:
    subject = _icon_subject(card_name)
    positive = f"{subject}, {_POS_BASE}"
    return positive, _NEG_BASE


# ── 파일명 유틸 (widgets.py 규칙과 통일) ─────────────────────────────────────
def _clean_filename(name: str) -> str:
    """한글/영문/숫자 유지, 공백→언더바, 파일명 위험 문자 제거."""
    bad = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    out = name.strip()
    for ch in bad:
        out = out.replace(ch, "_")
    out = out.replace(" ", "_")
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "unknown"


def _slug(name: str) -> str:
    """영문/숫자만 남긴 slug (widgets.py _slug와 동일)."""
    s = name.strip().lower()
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("_")
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "unknown"


# ── 카드 스펙 로드 ────────────────────────────────────────────────────────────
def load_card_specs() -> List[Tuple[str, str]]:
    """(card_id, display_name) 목록. CARD_REGISTRY에서 읽고, 실패 시 fallback."""
    try:
        from infra.loader import load_content
        load_content("content")
    except Exception:
        pass

    try:
        from content.registry import CARD_REGISTRY
        specs: List[Tuple[str, str]] = []
        for cid, tmpl in CARD_REGISTRY.items():
            disp = getattr(tmpl, "name", None) or str(cid)
            specs.append((str(cid), str(disp)))
        specs.sort(key=lambda x: x[0])
        if specs:
            return specs
    except Exception:
        pass

    # fallback
    return [
        ("basic_attack", "기본 공격"),
        ("basic_defense", "기본 방어"),
        ("unge_josik", "운기 조식"),
        ("samjaegong", "삼재공"),
        ("yukhapgwon", "육합권"),
        ("pocheonsam", "포천삼"),
        ("bokho_jang", "복호장"),
        ("yuund_ji", "유운지"),
    ]


# ── 이미지 후처리 ─────────────────────────────────────────────────────────────
def _center_crop_2to1(img):
    """정사각 이미지를 중앙 기준 가로 2:1로 크롭."""
    w, h = img.size
    new_h = h // 2
    top = (h - new_h) // 2
    return img.crop((0, top, w, top + new_h))


def _postprocess(pil_img, target_size: Tuple[int, int] = (512, 256)):
    """정사각 생성 이미지 → 중앙 크롭(2:1) → 512x256 리사이즈 → RGBA PNG."""
    from PIL import Image
    img = pil_img.convert("RGBA")
    img = _center_crop_2to1(img)
    img = img.resize(target_size, Image.LANCZOS)
    return img


# ── SD 파이프라인 로드 ────────────────────────────────────────────────────────
def _load_pipeline(model_id: str):
    """
    디바이스 자동 선택(MPS > CUDA > CPU) 후 파이프라인 반환.
    SD 1.x / SD 2.x: StableDiffusionPipeline
    SDXL:             StableDiffusionXLPipeline
    """
    import torch

    # 디바이스 결정
    if torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
        gen_device = "cpu"  # MPS Generator는 CPU 시드로 우회
        print("[디바이스] Apple MPS (float16)")
    elif torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16
        gen_device = "cuda"
        print(f"[디바이스] CUDA GPU ({torch.cuda.get_device_name(0)}, float16)")
    else:
        device = "cpu"
        dtype = torch.float32
        gen_device = "cpu"
        print("[디바이스] CPU (float32, 속도 느림)")

    is_xl = "xl" in model_id.lower() or "sdxl" in model_id.lower()

    if is_xl:
        from diffusers import StableDiffusionXLPipeline
        PipeClass = StableDiffusionXLPipeline
    else:
        from diffusers import StableDiffusionPipeline
        PipeClass = StableDiffusionPipeline

    print(f"[모델] {model_id}")
    print("       (첫 실행 시 모델 파일 다운로드 — 수 GB, 몇 분 소요)")

    kwargs = dict(torch_dtype=dtype)
    if not is_xl:
        kwargs["safety_checker"] = None
        kwargs["requires_safety_checker"] = False

    # float16 로드 실패 시(일부 Mac 환경) float32로 재시도
    try:
        pipe = PipeClass.from_pretrained(model_id, **kwargs)
    except Exception as e:
        if dtype == torch.float16:
            print(f"[경고] float16 로드 실패, float32로 재시도: {e}")
            kwargs["torch_dtype"] = torch.float32
            pipe = PipeClass.from_pretrained(model_id, **kwargs)
        else:
            raise

    pipe = pipe.to(device)

    # 메모리 절약 옵션 (CUDA)
    if device == "cuda":
        try:
            pipe.enable_xformers_memory_efficient_attention()
        except Exception:
            pass

    return pipe, gen_device


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Stable Diffusion 로컬 수묵 무공 아이콘 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
모델 추천:
  SD 2.1 (기본, 무난)  : --model stabilityai/stable-diffusion-2-1
  Dreamshaper (스타일) : --model Lykon/dreamshaper-8
  SDXL (최고화질)      : --model stabilityai/stable-diffusion-xl-base-1.0
        """,
    )
    parser.add_argument(
        "--model",
        default="stabilityai/stable-diffusion-2-1",
        help="HuggingFace 모델 ID 또는 로컬 경로",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="생성 개수 제한 (0=무제한, 테스트 시 5 권장)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="기존 파일도 덮어쓰기",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="재현 시드 (같은 시드 → 같은 이미지)",
    )
    parser.add_argument(
        "--steps", type=int, default=30,
        help="추론 스텝 수 (기본 30 / 빠른 테스트: 15)",
    )
    parser.add_argument(
        "--cfg", type=float, default=7.5,
        help="CFG guidance scale (기본 7.5)",
    )
    parser.add_argument(
        "--size", type=int, default=768,
        help="생성 해상도 (정사각, 기본 768 / SDXL 권장: 1024)",
    )
    parser.add_argument(
        "--only", type=str, default=None,
        help='특정 카드명/ID만 생성. 예: --only "육합권"',
    )
    args = parser.parse_args()

    # 라이브러리 확인
    _check_pillow()
    _check_diffusers()
    import torch

    # 카드 목록 로드
    specs = load_card_specs()

    # --only 필터
    if args.only:
        filtered = [
            (cid, dn) for cid, dn in specs
            if dn == args.only or cid == args.only
        ]
        if not filtered:
            print(f"[ERROR] '--only {args.only}'에 해당하는 카드 없음.")
            print(f"        등록된 카드: {[dn for _, dn in specs]}")
            sys.exit(1)
        specs = filtered

    # --limit
    if args.limit > 0:
        specs = specs[: args.limit]

    # 출력 디렉터리
    cards_dir = ROOT / "assets" / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    # 설정 출력
    print("=" * 60)
    print("[구운록] 수묵 무공 아이콘 생성 파이프라인")
    print("=" * 60)
    print(f"  모델   : {args.model}")
    print(f"  해상도 : {args.size}x{args.size} → 중앙 크롭 → 512x256")
    print(f"  스텝   : {args.steps} / CFG: {args.cfg} / 시드: {args.seed}")
    print(f"  대상   : {len(specs)}개 카드")
    print(f"  저장처 : {cards_dir}")
    print()

    # 파이프라인 로드
    pipe, gen_device = _load_pipeline(args.model)
    print()

    # Generator (시드 재현용)
    generator: Optional[torch.Generator] = None
    if args.seed is not None:
        generator = torch.Generator(device=gen_device).manual_seed(args.seed)

    generated = 0
    skipped   = 0
    failed    = 0

    for idx, (cid, disp_name) in enumerate(specs, 1):
        # 파일명 결정 (한글 주, slug 복사본)
        korean_fn = _clean_filename(disp_name)   # 예: "육합권"
        slug_fn   = _slug(disp_name)              # 예: "yukhapgwon" (영문 slug)
        out_korean = cards_dir / f"{korean_fn}.png"
        out_slug   = cards_dir / f"{slug_fn}.png"

        # 스킵 판단 (한글 파일명 기준)
        if out_korean.exists() and not args.force:
            print(f"[{idx:>2}/{len(specs)}] SKIP  {disp_name}")
            skipped += 1
            continue

        # 프롬프트
        pos_prompt, neg_prompt = make_prompt(disp_name)
        subject = _icon_subject(disp_name)

        print(f"[{idx:>2}/{len(specs)}] GEN   {disp_name}")
        print(f"          주제: {subject[:70]}")

        try:
            # 이미지 생성
            result = pipe(
                prompt=pos_prompt,
                negative_prompt=neg_prompt,
                width=args.size,
                height=args.size,
                num_inference_steps=args.steps,
                guidance_scale=args.cfg,
                generator=generator,
                num_images_per_prompt=1,
            )
            pil_img = result.images[0]

            # 후처리: 중앙 크롭(2:1) → 512x256 리사이즈
            final_img = _postprocess(pil_img, target_size=(512, 256))

            # 저장: 한글 파일명 (게임 card.name 직접 매칭)
            final_img.save(out_korean, format="PNG")
            print(f"          저장: {out_korean.name}")

            # 저장: slug 복사본 (widgets.py slug 로직 호환성)
            if slug_fn and slug_fn != "unknown" and slug_fn != korean_fn:
                shutil.copy2(out_korean, out_slug)
                print(f"          복사: {out_slug.name}")

            generated += 1

        except Exception as e:
            print(f"          !! FAIL: {e}")
            failed += 1

    # 결과 요약
    print()
    print("=" * 60)
    print(f"완료  생성: {generated}  스킵: {skipped}  실패: {failed}")
    print(f"저장 위치: {cards_dir}")
    if failed > 0:
        print()
        print("[실패 대응 팁]")
        print("  - 메모리 부족: --size 512 로 줄이기")
        print("  - 속도 너무 느림: --steps 15 로 줄이기")
        print("  - MPS 오류: 모델 경로 앞에 PYTORCH_ENABLE_MPS_FALLBACK=1 설정")


if __name__ == "__main__":
    main()
