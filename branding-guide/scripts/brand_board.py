# -*- coding: utf-8 -*-
"""brand.json → 브랜드 보드 + 이번 달 마케팅 카드 + 브랜드 컬러 인스타 게시물 시안 (HTML 한 파일, 4:5 세 장).

사용법:
    python brand_board.py brand.json --out brand-board.html

- 외부 라이브러리 없이 돈다. 글꼴은 구글 폰트(Noto Sans KR)를 불러오고, 안 되면 기기 고딕체로 보인다.
- 세 장 모두 4:5(1080×1350) 비율이라 인스타에 그대로 올릴 수 있다. 화면 폭에 맞춰 줄었다 늘었다 한다.
- 로고 이미지가 있으면 brand.json의 "logo_image"에 파일 경로를 넣는다. 없으면 이니셜 심볼을 그린다.

brand.json 예:
{
  "type": "가게",   ← 가게 / 브랜드 / 계정 / 퍼스널 (제목 문구가 바뀜)
  "name": "새벽빵집", "sub": "DAWN BAKERY",
  "one_line": "새벽 5시에 반죽해서 아침 8시에 내는 동네 빵집",
  "colors": {"메인": "#C8692B", "서브": "#E9C9A8", "강조": "#E9A23B", "배경": "#FFF6EC", "글자": "#2B1A10"},
  "color_names": {"메인": "구운 껍질", "서브": "밀가루 반죽", "강조": "버터", "배경": "아침 햇살", "글자": "진한 커피"},
  "why": "빵 설명을 들으면서 믿고 고를 수 있어서",
  "persona": "출근길에 '오늘은 이게 잘 나왔어요' 하고 챙겨 주는 동네 이웃",
  "traits": ["다정한", "부지런한", "솔직한"],
  "selling_points": [{"title": "새벽 5시 반죽", "proof": "매일 5시에 반죽 시작, 8시에 냄"}, ...3개],
  "tone": {"ai": "정성 가득한 수제 소금빵으로 특별한 아침을 선사합니다", "ours": "오늘 아침 7시에 구운 소금빵, 점심 전에 다 나가요"},
  "post": {"headline": "오늘 아침 7시에 구운 소금빵", "emphasis": "7시", "body": "점심 전에 다 나가요", "tag": "오전 품절"},
  "messages": ["새벽 5시에 반죽해요", "고를 때 하나씩 설명해 드려요", "그날 구운 것만 팔아요"],
  "weeks": [{"todo": "플레이스 소개글 바꾸기", "done": "검색해서 온 손님이 바로 알아요"}, ...4개],
  "channels": "네이버 플레이스 · 인스타그램",
  "logo_image": "",
  "credit": "Branding guide로 만든 브랜드 보드"
}
"""
import argparse
import base64
import html
import json
import mimetypes
import os

FONT = "'Noto Sans KR','Pretendard','Apple SD Gothic Neo','Malgun Gothic',sans-serif"


def esc(s):
    return html.escape(str(s or ""))


def lum(hexc):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def on(color, c):
    """color 위에 올릴 글자색: 배경색과 글자색 중 대비가 큰 쪽."""
    def ratio(a, b):
        la, lb = sorted([lum(a), lum(b)], reverse=True)
        return (la + 0.05) / (lb + 0.05)
    return c["글자"] if ratio(color, c["글자"]) >= ratio(color, c["배경"]) else c["배경"]


def logo_html(d, c, size_cqw):
    path = d.get("logo_image")
    if path and os.path.exists(path):
        mime = mimetypes.guess_type(path)[0] or "image/png"
        data = base64.b64encode(open(path, "rb").read()).decode()
        return (f'<img class="logo-img" style="height:{size_cqw}cqw" '
                f'src="data:{mime};base64,{data}" alt="{esc(d["name"])} 로고">')
    initial = esc(d["name"].strip()[:1])
    return (f'<svg class="logo-svg" style="height:{size_cqw}cqw;width:{size_cqw}cqw" viewBox="0 0 160 160" '
            f'role="img" aria-label="{esc(d["name"])} 로고">'
            f'<rect width="160" height="160" fill="{c["글자"]}"/>'
            f'<rect y="136" width="160" height="24" fill="{c["메인"]}"/>'
            f'<text x="80" y="112" text-anchor="middle" font-family="{FONT}" font-weight="900" '
            f'font-size="104" fill="{c["배경"]}">{initial}</text></svg>')


def emphasize(text, word, color):
    t = esc(text)
    if word and esc(word) in t:
        return t.replace(esc(word), f'<span style="color:{color}">{esc(word)}</span>', 1)
    return t


LABELS = {
    "가게": ("손님이 우리를 고르는 이유", "우리 가게가 사람이라면"),
    "브랜드": ("고객이 우리를 고르는 이유", "우리 브랜드가 사람이라면"),
    "계정": ("팔로워가 이 계정을 찾는 이유", "이 계정이 사람이라면"),
    "퍼스널": ("사람들이 나를 찾는 이유", "나를 한 사람으로 소개하면"),
}


def build(d):
    c = d["colors"]
    why_label, persona_label = LABELS.get(d.get("type", "가게"), LABELS["가게"])
    names = d.get("color_names", {})
    roles = ["메인", "서브", "강조", "배경", "글자"]

    swatches = "".join(
        f'<div class="sw" style="background:{c[r]};color:{on(c[r], c)}">'
        f'<b>{esc(r)}</b><span>{esc(names.get(r, ""))}</span><code>{esc(c[r].upper())}</code></div>'
        for r in roles)

    traits = "".join(f'<span class="trait">{esc(t)}</span>' for t in d.get("traits", [])[:3])
    sps = "".join(
        f'<li><em style="background:{c["메인"]};color:{on(c["메인"], c)}">{i}</em>'
        f'<div><b>{esc(sp.get("title"))}</b><small>{esc(sp.get("proof"))}</small></div></li>'
        for i, sp in enumerate(d.get("selling_points", [])[:3], 1))

    tone = d.get("tone", {})
    post = d.get("post", {})
    msgs = "".join(
        f'<li><em style="background:{c["메인"]};color:{on(c["메인"], c)}">{i}</em><div><b>{esc(m)}</b></div></li>'
        for i, m in enumerate(d.get("messages", [])[:3], 1))
    weeks = "".join(
        f'<div class="wk"><i></i><span class="wn">{i}주</span>'
        f'<div><b>{esc(w.get("todo"))}</b><small>{esc(w.get("done", ""))}</small></div></div>'
        for i, w in enumerate(d.get("weeks", [])[:4], 1))
    channels = d.get("channels", "")
    credit = d.get("credit", "")

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(d["name"])} 브랜드 보드</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#e9e9e9;font-family:{FONT};word-break:keep-all;color:{c["글자"]};padding:24px 16px}}
.wrap{{max-width:1080px;margin:0 auto 28px;container-type:inline-size}}
.board{{width:100%;aspect-ratio:4/5;background:{c["배경"]};padding:6cqw;display:flex;flex-direction:column;gap:3.4cqw;overflow:hidden}}
.head{{display:flex;align-items:center;gap:3.6cqw}}
.logo-img{{width:auto;display:block}} .logo-svg{{display:block;flex:none}}
.head h1{{font-size:7.6cqw;font-weight:900;letter-spacing:-.04em;line-height:1.05}}
.head p{{font-size:2.9cqw;font-weight:500;margin-top:1.2cqw;line-height:1.4}}
.sub{{font-size:2cqw;font-weight:700;letter-spacing:.3em;color:{c["메인"]};margin-top:.8cqw}}
.pal{{display:grid;grid-template-columns:repeat(5,1fr);height:22cqw}}
.sw{{padding:1.8cqw 1.6cqw;display:flex;flex-direction:column;gap:.6cqw;font-size:2.2cqw}}
.sw b{{font-size:2.6cqw;font-weight:900}} .sw span{{opacity:.85;line-height:1.3}}
.sw code{{margin-top:auto;font-family:{FONT};font-weight:700;font-size:2.3cqw;letter-spacing:.02em}}
.sw:nth-child(4){{box-shadow:inset 0 0 0 .3cqw {c["서브"]}}}
.ratio{{display:flex;height:1.6cqw;margin-top:-2.2cqw}}
.ratio i{{display:block}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:4cqw;flex:1;min-height:0}}
h2{{font-size:2.2cqw;font-weight:700;color:{c["메인"]};border-bottom:.3cqw solid {c["글자"]};padding-bottom:.9cqw;margin-bottom:1.6cqw}}
.big{{font-size:3.6cqw;font-weight:900;line-height:1.3;letter-spacing:-.02em}}
.persona{{font-size:2.7cqw;line-height:1.5;margin-top:3cqw}}
.traits{{display:flex;gap:1.2cqw;margin-top:1.6cqw;flex-wrap:wrap}}
.trait{{font-size:2.4cqw;font-weight:700;border:.3cqw solid {c["글자"]};padding:.6cqw 1.6cqw}}
ol{{list-style:none;display:flex;flex-direction:column;gap:2cqw}}
li{{display:flex;gap:1.8cqw;align-items:flex-start}}
li em{{font-style:normal;font-weight:900;font-size:2.6cqw;width:4.6cqw;height:4.6cqw;display:flex;align-items:center;justify-content:center;flex:none}}
li b{{font-size:3cqw;font-weight:900;display:block;line-height:1.25}}
li small{{font-size:2.3cqw;line-height:1.4;display:block;margin-top:.4cqw;opacity:.85}}
.tone{{display:grid;grid-template-columns:1fr 1fr;border-top:.3cqw solid {c["글자"]}}}
.tone div{{padding:2.2cqw 0;font-size:2.6cqw;line-height:1.45}}
.tone div:first-child{{padding-right:3cqw}}
.tone div+div{{background:{c["메인"]};color:{on(c["메인"], c)};padding:2.2cqw 2.6cqw;font-weight:700}}
.tone label{{display:block;font-size:2cqw;font-weight:700;margin-bottom:.6cqw}}
.tone s{{text-decoration-thickness:.25cqw;opacity:.7}}
.credit{{font-size:1.8cqw;opacity:.6;text-align:right;margin-top:-1.6cqw}}
/* 게시물 시안 */
.post{{background:{c["배경"]};display:flex;flex-direction:column;justify-content:space-between}}
.post .top{{display:flex;justify-content:space-between;align-items:center}}
.post .top span{{font-size:2.6cqw;font-weight:900}}
.post .tag{{background:{c["강조"]};color:{on(c["강조"], c)};font-size:3.2cqw;font-weight:900;padding:1.2cqw 2.4cqw;display:inline-block}}
.post h3{{font-size:10cqw;font-weight:900;line-height:1.15;letter-spacing:-.04em}}
.post p{{font-size:4.2cqw;font-weight:700;margin-top:3cqw}}
.post .bar{{height:2.4cqw;background:{c["메인"]};width:30cqw;margin-top:4cqw}}
.post .foot{{font-size:2.6cqw;border-top:.3cqw solid {c["글자"]};padding-top:2cqw;display:flex;justify-content:space-between}}
/* 마케팅 카드 */
.mk .top{{display:flex;align-items:center;gap:2.4cqw}}
.mk .top div span{{font-size:2.6cqw;font-weight:700;color:{c["메인"]}}}
.mk h3{{font-size:7.4cqw;font-weight:900;letter-spacing:-.04em;line-height:1.1}}
.mk ol b{{font-size:3.4cqw}}
.wks{{display:flex;flex-direction:column}}
.wk{{display:grid;grid-template-columns:4.2cqw 7cqw 1fr;gap:2cqw;align-items:start;padding:2cqw 0;border-bottom:.2cqw solid {c["서브"]}}}
.wk i{{display:block;width:4.2cqw;height:4.2cqw;border:.35cqw solid {c["글자"]};margin-top:.2cqw}}
.wk .wn{{font-size:3cqw;font-weight:900;color:{c["메인"]};line-height:4.6cqw}}
.wk b{{font-size:3cqw;font-weight:900;display:block;line-height:1.3}}
.wk small{{font-size:2.3cqw;display:block;margin-top:.4cqw;opacity:.8}}
.mk .foot{{font-size:2.3cqw;display:flex;justify-content:space-between;margin-top:auto}}
.cap{{max-width:1080px;margin:0 auto 10px;font-size:14px;color:#333}}
</style></head><body>

<p class="cap">① 브랜드 보드 (4:5, 인스타에 그대로 올릴 수 있어요)</p>
<div class="wrap"><section class="board" id="board">
  <div class="head">{logo_html(d, c, 15)}
    <div><h1>{esc(d["name"])}</h1>{f'<div class="sub">{esc(d.get("sub"))}</div>' if d.get("sub") else ""}
    <p>{esc(d.get("one_line"))}</p></div>
  </div>
  <div class="pal">{swatches}</div>
  <div class="ratio"><i style="flex:60;background:{c["배경"]};box-shadow:inset 0 0 0 .3cqw {c["서브"]}"></i><i style="flex:30;background:{c["메인"]}"></i><i style="flex:10;background:{c["강조"]}"></i></div>
  <div class="grid">
    <div><h2>{esc(why_label)}</h2><p class="big">{esc(d.get("why"))}</p>
      <p class="persona"><b>{esc(persona_label)}</b><br>{esc(d.get("persona"))}</p>
      <div class="traits">{traits}</div></div>
    <div><h2>셀링포인트</h2><ol>{sps}</ol></div>
  </div>
  <div class="tone">
    <div><label>AI 말투</label><s>{esc(tone.get("ai"))}</s></div>
    <div><label>우리 말투</label>{esc(tone.get("ours"))}</div>
  </div>
  {f'<p class="credit">{esc(credit)}</p>' if credit else ""}
</section></div>

<p class="cap">② 이번 달 마케팅 카드 (캡처해 두면 할 일 목록이 돼요)</p>
<div class="wrap"><section class="board mk" id="marketing">
  <div class="top">{logo_html(d, c, 9)}<div><span>{esc(d["name"])}</span><h3>{esc(d.get("month_label", "이번 달 마케팅"))}</h3></div></div>
  <div><h2>핵심 메시지 — 어디서든 이 세 가지를 반복해요</h2><ol>{msgs}</ol></div>
  <div><h2>4주 실행표 — 한 주에 하나, 30분 안에</h2><div class="wks">{weeks}</div></div>
  <div class="foot"><span>{esc(("채널: " + channels) if channels else "")}</span><span>{esc(credit)}</span></div>
</section></div>

<p class="cap">③ 이 브랜드 컬러로 만든 인스타 게시물 시안</p>
<div class="wrap"><section class="board post" id="post">
  <div class="top">{logo_html(d, c, 9)}<span>{esc(d["name"])}</span></div>
  <div>{f'<div class="tag">{esc(post.get("tag"))}</div>' if post.get("tag") else ""}
    <h3 style="margin-top:4cqw">{emphasize(post.get("headline"), post.get("emphasis"), c["메인"])}</h3>
    <p>{esc(post.get("body"))}</p><div class="bar"></div></div>
  <div class="foot"><span>{esc(d.get("one_line"))}</span></div>
</section></div>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="브랜드 보드 + 게시물 시안 만들기")
    ap.add_argument("json")
    ap.add_argument("--out", default="brand-board.html")
    a = ap.parse_args()
    d = json.load(open(a.json, encoding="utf-8"))
    for r in ["메인", "서브", "강조", "배경", "글자"]:
        if r not in d.get("colors", {}):
            raise SystemExit(f"colors에 '{r}'이 없어요.")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(build(d))
    print("만든 파일:", a.out)


if __name__ == "__main__":
    main()
