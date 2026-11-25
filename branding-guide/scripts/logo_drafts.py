# -*- coding: utf-8 -*-
"""가게 이름과 브랜드 컬러로 로고 시안 SVG 3개와 미리보기 HTML을 만든다.

사용법:
    python logo_drafts.py --name "새벽빵집" --sub "DAWN BAKERY" \
        --main "#C8692B" --text "#2B1A10" --bg "#FFF6EC" --accent "#E9A23B" --out logo
결과:
    logo/logo-1-wordmark.svg   가게 이름 글자 로고
    logo/logo-2-badge.svg      사각 배지
    logo/logo-3-symbol.svg     이니셜 심볼 + 이름
    logo/preview.html          밝은 바탕·어두운 바탕 미리보기

- 외부 라이브러리 없이 돈다.
- 글꼴은 보는 기기에 깔린 고딕체(Pretendard, Noto Sans KR, 맑은 고딕 등)로 보인다.
  간판·인쇄에 쓰려면 디자인 툴에서 글자를 외곽선(아웃라인)으로 바꿔서 쓴다.
- 시안일 뿐이다. 쓰기 전에 키프리스(KIPRIS)에서 비슷한 상표가 있는지 확인한다.
"""
import argparse
import html
import os

FONT = "'Pretendard','Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',sans-serif"


def text_width(s, size):
    """대충 잡은 글자 폭. 한글·한자는 1em, 영문·숫자는 0.6em, 공백 0.3em."""
    w = 0
    for ch in s:
        if ch == " ":
            w += 0.3
        elif ord(ch) > 0x2E80:
            w += 1.0
        else:
            w += 0.62
    return w * size


def fit(s, max_w, start, min_size=18):
    size = start
    while size > min_size and text_width(s, size) > max_w:
        size -= 2
    return size


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{body}</svg>\n')


def wordmark(name, sub, c):
    W, H = 640, 240
    n = html.escape(name)
    size = fit(name, W - 80, 96)
    body = (f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>'
            f'<text x="{W/2}" y="128" text-anchor="middle" font-family="{FONT}" '
            f'font-weight="800" font-size="{size}" fill="{c["text"]}" letter-spacing="-1">{n}</text>'
            f'<rect x="{W/2 - 60}" y="150" width="120" height="8" fill="{c["main"]}"/>')
    if sub:
        body += (f'<text x="{W/2}" y="196" text-anchor="middle" font-family="{FONT}" '
                 f'font-weight="600" font-size="22" fill="{c["text"]}" letter-spacing="4">{html.escape(sub)}</text>')
    return svg(W, H, body)


def badge(name, sub, c):
    W, H = 420, 420
    n = html.escape(name)
    size = fit(name, W - 90, 80)
    body = (f'<rect width="{W}" height="{H}" fill="{c["main"]}"/>'
            f'<rect x="22" y="22" width="{W-44}" height="{H-44}" fill="none" stroke="{c["bg"]}" stroke-width="4"/>'
            f'<text x="{W/2}" y="{H/2 + size*0.35}" text-anchor="middle" font-family="{FONT}" '
            f'font-weight="800" font-size="{size}" fill="{c["bg"]}" letter-spacing="-1">{n}</text>'
            f'<rect x="{W/2 - 40}" y="{H/2 + size*0.35 + 26}" width="80" height="6" fill="{c["accent"]}"/>')
    if sub:
        body += (f'<text x="{W/2}" y="{H - 60}" text-anchor="middle" font-family="{FONT}" '
                 f'font-weight="600" font-size="20" fill="{c["bg"]}" letter-spacing="3">{html.escape(sub)}</text>')
    return svg(W, H, body)


def symbol(name, sub, c):
    W, H = 720, 240
    initial = html.escape(name.strip()[0]) if name.strip() else "?"
    n = html.escape(name)
    size = fit(name, W - 260, 84)
    body = (f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>'
            f'<rect x="40" y="40" width="160" height="160" fill="{c["text"]}"/>'
            f'<rect x="40" y="176" width="160" height="24" fill="{c["main"]}"/>'
            f'<text x="120" y="152" text-anchor="middle" font-family="{FONT}" font-weight="800" '
            f'font-size="104" fill="{c["bg"]}">{initial}</text>'
            f'<text x="236" y="{132 if sub else 150}" font-family="{FONT}" font-weight="800" '
            f'font-size="{size}" fill="{c["text"]}" letter-spacing="-1">{n}</text>')
    if sub:
        body += (f'<text x="240" y="182" font-family="{FONT}" font-weight="600" font-size="22" '
                 f'fill="{c["main"]}" letter-spacing="3">{html.escape(sub)}</text>')
    return svg(W, H, body)


def preview(files, c, name):
    cards = "".join(
        f'<figure><img src="{f}" alt="{html.escape(label)}"><figcaption>{html.escape(label)}</figcaption></figure>'
        for f, label in files)
    dark = "".join(f'<img src="{f}" alt="">' for f, _ in files)
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(name)} 로고 시안</title>
<style>
body{{margin:0;padding:24px 16px;font-family:{FONT};background:#f4f4f4;color:#222}}
h1{{font-size:22px}} p{{max-width:640px;line-height:1.6}}
.row{{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start}}
figure{{margin:0;background:#fff;padding:12px}} img{{max-width:100%;height:auto;display:block}}
figcaption{{font-size:14px;margin-top:8px}}
.dark{{background:{c["text"]};padding:20px;margin-top:28px}} .dark img{{max-width:280px;margin:8px}}
</style></head><body>
<h1>{html.escape(name)} 로고 시안 3개</h1>
<p>시안이에요. 간판·포장에 쓰기 전에 키프리스(KIPRIS)에서 비슷한 상표가 있는지 검색해 보세요.
인쇄용으로 쓸 때는 디자인 툴에서 글자를 외곽선으로 바꿔 주세요.</p>
<div class="row">{cards}</div>
<div class="dark"><p style="color:{c["bg"]}">작게 줄여 볼 때 (프로필 사진·스티커 크기)</p>{dark}</div>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="로고 시안 SVG 3개 만들기")
    ap.add_argument("--name", required=True, help="가게 이름")
    ap.add_argument("--sub", default="", help="아래 작은 글씨 (영문 이름, 업종 등)")
    ap.add_argument("--main", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--bg", required=True)
    ap.add_argument("--accent", required=True)
    ap.add_argument("--out", default="logo")
    a = ap.parse_args()

    c = {"main": a.main, "text": a.text, "bg": a.bg, "accent": a.accent}
    os.makedirs(a.out, exist_ok=True)
    made = [
        ("logo-1-wordmark.svg", "1 워드마크", wordmark(a.name, a.sub, c)),
        ("logo-2-badge.svg", "2 사각 배지", badge(a.name, a.sub, c)),
        ("logo-3-symbol.svg", "3 이니셜 심볼 + 이름", symbol(a.name, a.sub, c)),
    ]
    for fname, _, content in made:
        with open(os.path.join(a.out, fname), "w", encoding="utf-8") as f:
            f.write(content)
    with open(os.path.join(a.out, "preview.html"), "w", encoding="utf-8") as f:
        f.write(preview([(m[0], m[1]) for m in made], c, a.name))
    print("만든 파일:")
    for fname, label, _ in made:
        print(f"  {os.path.join(a.out, fname)}  ({label})")
    print(f"  {os.path.join(a.out, 'preview.html')}  (미리보기)")


if __name__ == "__main__":
    main()
