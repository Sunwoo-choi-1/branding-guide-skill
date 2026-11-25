# -*- coding: utf-8 -*-
"""사진(로고·상품·가게)에서 대표색을 뽑아 HEX, 비율, 역할 후보, 글자 대비를 보여 준다.

사용법:
    python palette.py 로고.png 상품1.jpg 가게.jpg
    python palette.py 사진.jpg --colors 6 --json

- Pillow만 쓴다 (pip install pillow).
- 첫 번째 사진에 가중치를 더 준다. 로고가 있으면 맨 앞에 넣는다.
- 투명한 부분(로고 PNG 배경)은 빼고 센다.
"""
import argparse
import colorsys
import json
import sys

from PIL import Image


def load_pixels(path, size=160):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size, size))
    data = im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()
    return [p[:3] for p in data if p[3] > 128]


def quantize(pixels, n):
    if not pixels:
        return []
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    method = getattr(getattr(Image, "Quantize", Image), "MEDIANCUT", 0)
    q = strip.quantize(colors=max(2, n), method=method)
    pal = q.getpalette()
    out = []
    for count, idx in q.getcolors():
        out.append([count, tuple(pal[idx * 3: idx * 3 + 3])])
    return out


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def merge(colors, threshold=30):
    merged = []
    for count, rgb in sorted(colors, reverse=True):
        for m in merged:
            if dist(m[1], rgb) < threshold:
                total = m[0] + count
                m[1] = tuple(round((m[1][i] * m[0] + rgb[i] * count) / total) for i in range(3))
                m[0] = total
                break
        else:
            merged.append([count, rgb])
    return sorted(merged, reverse=True)


def hexof(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hls(rgb):
    return colorsys.rgb_to_hls(*(c / 255 for c in rgb))


def from_hls(h, l, s):
    return tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, l, s))


def assign_roles(colors):
    """colors: [(ratio, rgb)] → 역할 dict. 사진에 없는 색은 '제안'으로 만든다."""
    pool = list(colors)
    roles = {}

    lightest = max(pool, key=lambda c: luminance(c[1]))
    darkest = min(pool, key=lambda c: luminance(c[1]))

    # 배경: 가장 밝은 색이 충분히 밝으면 그대로, 아니면 메인 색을 아주 옅게
    if luminance(lightest[1]) > 0.75:
        roles["배경"] = (lightest[1], "사진")
    # 글자: 가장 어두운 색이 충분히 어두우면 그대로
    if luminance(darkest[1]) < 0.06:
        roles["글자"] = (darkest[1], "사진")

    used = {roles[k][0] for k in roles}
    chroma = [c for c in pool if c[1] not in used]
    # 메인: 남은 색 중 비율이 크고 채도가 있는 색
    def main_score(c):
        lum = luminance(c[1])
        mid = 1.0 if 0.05 < lum < 0.7 else 0.35  # 너무 어둡거나 밝은 색은 메인으로 약하다
        return c[0] * (0.2 + hls(c[1])[2]) * mid
    chroma.sort(key=main_score, reverse=True)
    if chroma:
        roles["메인"] = (chroma[0][1], "사진")
    rest = chroma[1:]
    # 강조: 메인과 색상이 가장 다르고 채도가 높은 색
    if rest:
        mh = hls(roles["메인"][0])[0]
        def score(c):
            h, l, s = hls(c[1])
            dh = min(abs(h - mh), 1 - abs(h - mh))
            return s * (0.4 + dh)
        acc = max(rest, key=score)
        roles["강조"] = (acc[1], "사진")
        rest = [c for c in rest if c is not acc]
    if rest:
        roles["서브"] = (rest[0][1], "사진")

    main = roles.get("메인", (pool[0][1], "사진"))[0]
    h, l, s = hls(main)
    if "배경" not in roles:
        roles["배경"] = (from_hls(h, 0.95, min(s, 0.45)), "제안")
    if "글자" not in roles:
        roles["글자"] = (from_hls(h, 0.14, min(s, 0.5)), "제안")
    if "서브" not in roles:
        roles["서브"] = (from_hls(h, 0.75, min(s, 0.5)), "제안")
    if "강조" not in roles:
        roles["강조"] = (from_hls((h + 0.08) % 1, 0.55, 0.8), "제안")
    return roles


def main():
    ap = argparse.ArgumentParser(description="사진에서 브랜드 컬러 후보 뽑기")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--colors", type=int, default=6, help="뽑을 대표색 개수 (기본 6)")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args()

    raw = []
    for i, path in enumerate(args.images):
        try:
            px = load_pixels(path)
        except Exception as e:  # 열 수 없는 파일은 건너뛴다
            print(f"[건너뜀] {path}: {e}", file=sys.stderr)
            continue
        weight = 2 if i == 0 else 1
        for count, rgb in quantize(px, args.colors * 2):
            raw.append([count * weight, rgb])
    if not raw:
        sys.exit("읽을 수 있는 사진이 없어요.")

    colors = merge(raw)[: args.colors]
    total = sum(c[0] for c in colors)
    ranked = [(c[0] / total, c[1]) for c in colors]
    roles = assign_roles(ranked)

    bg, tx = roles["배경"][0], roles["글자"][0]
    checks = {
        "글자/배경": round(contrast(tx, bg), 2),
        "글자/메인": round(contrast(tx, roles["메인"][0]), 2),
        "배경/메인": round(contrast(bg, roles["메인"][0]), 2),
    }

    if args.json:
        print(json.dumps({
            "colors": [{"hex": hexof(rgb), "ratio": round(r, 3)} for r, rgb in ranked],
            "roles": {k: {"hex": hexof(v[0]), "source": v[1]} for k, v in roles.items()},
            "contrast": checks,
        }, ensure_ascii=False, indent=2))
        return

    print("■ 사진에서 나온 대표색 (많은 순)")
    for r, rgb in ranked:
        print(f"  {hexof(rgb)}  {r * 100:5.1f}%")
    print("\n■ 역할 후보 ('제안'은 사진에 없어서 메인 색으로 만든 색)")
    for k in ["메인", "서브", "강조", "배경", "글자"]:
        rgb, src = roles[k]
        print(f"  {k:<3} {hexof(rgb)}  ({src})")
    print("\n■ 글자 대비 (4.5 이상이면 본문 글자로 OK, 3 이상이면 큰 제목만 OK)")
    for k, v in checks.items():
        mark = "OK" if v >= 4.5 else ("제목만" if v >= 3 else "부족")
        print(f"  {k:<6} {v:>5}  {mark}")
    print("\n비율 추천: 배경 60 · 메인 30 · 강조 10")


if __name__ == "__main__":
    main()
