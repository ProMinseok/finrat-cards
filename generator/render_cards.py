"""finrat_ai 카드뉴스 렌더러.

사용법: python3 render_cards.py spec.json OUT_DIR
spec.json 형식은 generator/SPEC.md 참고. 1080x1350 PNG를 OUT_DIR/<prefix>_01.png ... 로 만든다.
"""
import asyncio, json, os, sys, html
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
Y, UP, DN, MUTED, SUB, BOX, LINE = "#FFC53D", "#FF6B6B", "#5B9BFF", "#9AA6BC", "#C9D1E0", "#161F33", "#26324A"
SG = "font-family:'Space Grotesk',sans-serif;"
GRID = "background-image:linear-gradient(rgba(255,255,255,0.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.035) 1px,transparent 1px);background-size:54px 54px;"
HANDLE = "@finrat_ai"

def t(s):  # 텍스트: <br>만 허용
    return html.escape(str(s)).replace("&lt;br&gt;", "<br>")

def col(d):
    return {"up": UP, "down": DN}.get(d, "#F3F5F9")

def label(s):
    return f'<span style="font-size:30px;font-weight:700;color:{MUTED}">{t(s)}</span>' if s else ""

def b_rows(b):
    out = []
    for i, r in enumerate(b["rows"]):
        last = "border-bottom:2px solid %s;" % LINE if i == len(b["rows"]) - 1 else ""
        out.append(f'''<div style="display:grid;grid-template-columns:250px 1fr auto;align-items:baseline;gap:20px;padding:20px 0;border-top:2px solid {LINE};{last}">
<span style="font-size:30px;font-weight:700">{t(r["name"])}</span>
<span style="{SG}font-size:54px;font-weight:700;letter-spacing:-1.5px">{t(r["value"])}</span>
<span style="{SG}font-size:36px;font-weight:700;color:{col(r.get("dir"))}">{t(r.get("change",""))}</span></div>''')
    return f'<div style="display:flex;flex-direction:column;gap:14px">{label(b.get("label"))}<div style="display:flex;flex-direction:column">{"".join(out)}</div></div>'

def b_boxes(b):
    items = "".join(f'''<div style="background:{BOX};padding:24px 28px;display:flex;flex-direction:column;gap:8px">
<span style="font-size:33px;font-weight:900;line-height:1.3">{t(i["title"])}</span>
<span style="font-size:27px;line-height:1.5;color:{SUB}">{t(i.get("body",""))}</span></div>''' for i in b["items"])
    return f'<div style="display:flex;flex-direction:column;gap:14px">{label(b.get("label"))}{items}</div>'

def b_timeline(b):
    out = []
    for i, r in enumerate(b["items"]):
        last = "border-bottom:2px solid %s;" % LINE if i == len(b["items"]) - 1 else ""
        out.append(f'''<div style="display:grid;grid-template-columns:190px 1fr;gap:20px;padding:18px 0;border-top:2px solid {LINE};{last}">
<span style="{SG}font-size:38px;font-weight:700;color:{Y};line-height:1.2">{t(r["time"])}</span>
<div style="display:flex;flex-direction:column;gap:4px"><span style="font-size:31px;font-weight:900;line-height:1.3">{t(r["title"])}</span>
<span style="font-size:25px;line-height:1.4;color:{SUB}">{t(r.get("body",""))}</span></div></div>''')
    return f'<div style="display:flex;flex-direction:column;gap:14px">{label(b.get("label"))}<div style="display:flex;flex-direction:column">{"".join(out)}</div></div>'

def b_scenarios(b):
    tone = {"up": "#FF8A8A", "down": "#7FB2FF"}
    items = "".join(f'''<div style="background:{BOX};padding:22px 24px;display:flex;flex-direction:column;gap:6px">
<span style="font-size:27px;font-weight:900;color:{tone.get(i.get("tone"), Y)}">{t(i["title"])}</span>
<span style="font-size:24px;line-height:1.4;color:{SUB}">{t(i.get("body",""))}</span></div>''' for i in b["items"])
    note = f'<span style="font-size:23px;color:{MUTED}">{t(b["note"])}</span>' if b.get("note") else ""
    return f'''<div style="display:flex;flex-direction:column;gap:14px">{label(b.get("label"))}
<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px">{items}</div>{note}</div>'''

def b_compare(b):
    h = b["header"]
    head = f'<div style="display:grid;grid-template-columns:minmax(0,1fr) 170px 190px;gap:16px;padding-bottom:12px;font-size:24px;color:{MUTED}"><span>{t(h[0])}</span><span style="text-align:right">{t(h[1])}</span><span style="text-align:right">{t(h[2])}</span></div>'
    out = []
    for i, r in enumerate(b["rows"]):
        last = "border-bottom:2px solid %s;" % LINE if i == len(b["rows"]) - 1 else ""
        out.append(f'''<div style="display:grid;grid-template-columns:minmax(0,1fr) 170px 190px;align-items:baseline;gap:16px;padding:20px 0;border-top:2px solid {LINE};{last}">
<span style="font-size:30px;font-weight:700">{t(r["name"])}</span>
<span style="{SG}font-size:40px;font-weight:700;color:{SUB};text-align:right">{t(r["a"])}</span>
<span style="{SG}font-size:48px;font-weight:700;color:{Y};text-align:right">{t(r["b"])}</span></div>''')
    return f'<div style="display:flex;flex-direction:column">{head}{"".join(out)}</div>'

def b_bars(b):
    mx = max(abs(float(i["pct"])) for i in b["items"]) or 1
    n = len(b["items"])
    items = "".join(f'''<div style="display:flex;flex-direction:column;gap:10px;justify-content:flex-end">
<span style="{SG}font-size:32px;font-weight:700;color:{UP if float(i["pct"])>=0 else DN}">{t(i["value"])}</span>
<div style="height:{max(8,int(abs(float(i["pct"]))/mx*100))}px;background:{UP if float(i["pct"])>=0 else DN}"></div>
<span style="font-size:26px;color:{SUB}">{t(i["label"])}</span></div>''' for i in b["items"])
    return f'''<div style="display:flex;flex-direction:column;gap:18px">{label(b.get("label"))}
<div style="display:grid;grid-template-columns:repeat({n},minmax(0,1fr));gap:16px;align-items:end;height:180px">{items}</div></div>'''

def b_stats(b):  # 수급 등 2~4칸 숫자 타일
    n = len(b["items"])
    items = "".join(f'''<div style="background:{BOX};padding:24px;display:flex;flex-direction:column;gap:8px">
<span style="font-size:27px;color:{SUB}">{t(i["name"])}</span>
<span style="font-size:{34 if n>3 else 38}px;font-weight:900;white-space:nowrap;color:{col(i.get("dir"))}">{t(i["value"])}</span></div>''' for i in b["items"])
    return f'''<div style="display:flex;flex-direction:column;gap:18px">{label(b.get("label"))}
<div style="display:grid;grid-template-columns:repeat({n},minmax(0,1fr));gap:16px">{items}</div></div>'''

def b_numbered(b):
    items = "".join(f'''<div style="display:grid;grid-template-columns:64px 1fr;gap:20px;background:{BOX};padding:22px 28px">
<span style="{SG}font-size:44px;font-weight:700;color:{Y};line-height:1.1">{n+1}</span>
<div style="display:flex;flex-direction:column;gap:8px"><span style="font-size:34px;font-weight:900;line-height:1.3">{t(i["title"])}</span>
<span style="font-size:27px;line-height:1.5;color:{SUB}">{t(i.get("body",""))}</span></div></div>''' for n, i in enumerate(b["items"]))
    return f'<div style="display:flex;flex-direction:column;gap:14px">{label(b.get("label"))}{items}</div>'

BLOCKS = dict(rows=b_rows, boxes=b_boxes, timeline=b_timeline, scenarios=b_scenarios, compare=b_compare,
              bars=b_bars, stats=b_stats, numbered=b_numbered)

def root(inner, grid=False, layout="gap:30px"):
    return f'''<div style="width:1080px;height:1350px;box-sizing:border-box;padding:88px 88px 72px;background-color:#0D1320;{GRID if grid else ""}
color:#F3F5F9;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;display:flex;flex-direction:column;word-break:keep-all;{layout}">{inner}</div>'''

def cover(c):
    chips = "".join(f'<span style="padding:12px 22px;border:2px solid #33405A;font-size:28px;font-weight:500">{t(x)}</span>' for x in c.get("chips", []))
    big_color = {"up": UP, "down": DN}.get(c.get("big_dir"), Y)
    big = f'<span style="{SG}font-size:{c.get("big_size",180)}px;font-weight:700;letter-spacing:-6px;line-height:0.95;color:{big_color}">{t(c["big"])}</span>' if c.get("big") else ""
    inner = f'''<div style="display:flex;justify-content:space-between;align-items:center">
<span style="{SG}font-size:30px;font-weight:700">{HANDLE}</span>
<span style="{SG}font-size:28px;font-weight:500;color:{MUTED}">{t(c["date_label"])}</span></div>
<div style="display:flex;flex-direction:column;gap:28px">
<span style="font-size:34px;font-weight:700;color:{MUTED}">{t(c["kicker"])}</span>{big}
<h1 style="margin:0;font-size:78px;font-weight:900;line-height:1.18;letter-spacing:-2.5px">{t(c["headline"])}</h1>
<div style="display:flex;flex-wrap:wrap;gap:14px;margin-top:8px">{chips}</div></div>
<div style="display:flex;justify-content:space-between;align-items:center;border-top:2px solid {LINE};padding-top:32px">
<span style="font-size:28px;color:{MUTED}">{t(c.get("footer",""))}</span>
<div style="display:flex;align-items:center;gap:12px;font-size:30px;font-weight:700;color:{Y}"><span>넘겨보기</span>
<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div></div>'''
    return root(inner, grid=True, layout="justify-content:space-between")

def body(c):
    inner = f'''<div style="display:flex;justify-content:flex-end"><span style="font-size:26px;color:{MUTED}">{t(c.get("kicker_right",""))}</span></div>
<h2 style="margin:0;font-size:62px;font-weight:900;letter-spacing:-2px;line-height:1.2">{t(c["title"])}</h2>''' + "".join(BLOCKS[b["type"]](b) for b in c["blocks"])
    return root(inner, layout="gap:%dpx" % c.get("gap", 30))

def cta(c):
    chips = "".join(f'<span style="padding:12px 22px;background:{BOX};font-size:28px">{t(x)}</span>' for x in c.get("chips", []))
    inner = f'''<div></div><div style="display:flex;flex-direction:column;gap:36px">
<span style="{SG}font-size:120px;font-weight:700;letter-spacing:-4px;line-height:1;color:{Y}">{t(c["big"])}</span>
<h2 style="margin:0;font-size:66px;font-weight:900;letter-spacing:-2px;line-height:1.25">{t(c["headline"])}</h2>
<div style="display:flex;flex-wrap:wrap;gap:14px">{chips}</div>
<span style="font-size:36px;font-weight:700">팔로우 <span style="color:{Y}">{HANDLE}</span> · 저장해두고 다시 보기</span></div>
<div style="display:flex;flex-direction:column;gap:10px;border-top:2px solid {LINE};padding-top:28px;font-size:22px;line-height:1.5;color:{MUTED}">
<span>출처: {t(c["source"])}</span>
<span>본 콘텐츠는 정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 않습니다. 투자 판단과 그 결과의 책임은 투자자 본인에게 있습니다.</span></div>'''
    return root(inner, grid=True, layout="justify-content:space-between")

KINDS = dict(cover=cover, body=body, cta=cta)

async def main(spec_path, out_dir):
    spec = json.load(open(spec_path))
    os.makedirs(out_dir, exist_ok=True)
    fonts = f'''<style>body{{margin:0}}
@font-face{{font-family:'Space Grotesk';font-weight:500;src:url(file://{HERE}/fonts/space-grotesk-latin-500-normal.woff2)}}
@font-face{{font-family:'Space Grotesk';font-weight:700;src:url(file://{HERE}/fonts/space-grotesk-latin-700-normal.woff2)}}</style>'''
    async with async_playwright() as p:
        exe = "/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None
        b = await p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        warn = []
        for i, c in enumerate(spec["cards"], 1):
            page = f'<!doctype html><html lang="ko"><head><meta charset="utf-8">{fonts}</head><body>{KINDS[c["kind"]](c)}</body></html>'
            tmp = os.path.join(out_dir, "_tmp.html"); open(tmp, "w").write(page)
            await pg.goto("file://" + tmp); await pg.wait_for_timeout(300)
            h = await pg.evaluate("document.body.firstElementChild.scrollHeight")
            if h > 1350: warn.append(f"card {i}: content overflows ({h}px > 1350) — shorten text")
            path = os.path.join(out_dir, f'{spec["prefix"]}_{i:02d}.png')
            await pg.screenshot(path=path); print(path)
        os.remove(tmp); await b.close()
        for w in warn: print("WARNING:", w)
        if warn: sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
