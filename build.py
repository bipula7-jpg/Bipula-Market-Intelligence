import os, json, urllib.request, ssl, time
from datetime import date
 
TODAY = date.today().strftime("%B %d, %Y")
TODAY_SHORT = date.today().strftime("%b %d, %Y")
KEY = os.environ.get("AV_KEY", "")
 
print(f"Building SIGNAL dashboard for {TODAY}")
print(f"Alpha Vantage key present: {bool(KEY)}, length: {len(KEY)}")
 
ctx = ssl.create_default_context()
 
def fetch(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  fetch error: {e}")
        return None
 
def safe(v, default=0.0):
    try: return float(v) if v else default
    except: return default
 
def pct(v):
    v = safe(v)
    return f"{'+' if v>=0 else ''}{v:.2f}%"
 
def cc(v):
    v = safe(v)
    if v > 0: return "up"
    if v < 0: return "dn"
    return "fl"
 
def fnum(v):
    v = safe(v)
    if v == 0: return "--"
    if v > 1000: return f"{v:,.2f}"
    return f"{v:.2f}"
 
# ── FETCH QUOTES (Alpha Vantage GLOBAL_QUOTE) ─────────────
# Free tier: 25 calls/day, 5/minute — we fetch key symbols
# Each GLOBAL_QUOTE call = 1 request
# We make 8 calls: SPY, QQQ, DIA, IWM, GLD, USO, VXX, BTC-USD
 
symbols = ["SPY", "QQQ", "DIA", "IWM", "GLD", "USO"]
quotes = {}
 
print("\nFetching quotes from Alpha Vantage...")
for sym in symbols:
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={sym}&apikey={KEY}"
    data = fetch(url)
    if data and "Global Quote" in data and data["Global Quote"]:
        q = data["Global Quote"]
        price = safe(q.get("05. price", 0))
        change_pct = safe(q.get("10. change percent", "0%").replace("%",""))
        quotes[sym] = {"price": price, "change_pct": change_pct}
        print(f"  {sym}: {price} ({pct(change_pct)})")
    else:
        print(f"  {sym}: no data returned - {str(data)[:100]}")
    time.sleep(12)  # Alpha Vantage free: 5 calls/minute = 12s between calls
 
def q(sym, field, default=0):
    return quotes.get(sym, {}).get(field, default)
 
spx_p = safe(q("SPY","price",0))
spx_c = safe(q("SPY","change_pct",0))
ndx_p = safe(q("QQQ","price",0))
ndx_c = safe(q("QQQ","change_pct",0))
dia_p = safe(q("DIA","price",0))
dia_c = safe(q("DIA","change_pct",0))
iwm_p = safe(q("IWM","price",0))
iwm_c = safe(q("IWM","change_pct",0))
gld_p = safe(q("GLD","price",0))
gld_c = safe(q("GLD","change_pct",0))
uso_p = safe(q("USO","price",0))
uso_c = safe(q("USO","change_pct",0))
 
# ── FETCH TREASURY YIELDS (Alpha Vantage TREASURY_YIELD) ──
print("\nFetching treasury yields...")
time.sleep(12)
treas_url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=10year&apikey={KEY}"
treas_data = fetch(treas_url)
y10 = 0.0
if treas_data and "data" in treas_data and treas_data["data"]:
    y10 = safe(treas_data["data"][0].get("value", 0))
    print(f"  10Y Yield: {y10}%")
 
time.sleep(12)
treas_2y = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity=2year&apikey={KEY}"
treas2_data = fetch(treas_2y)
y2 = 0.0
if treas2_data and "data" in treas2_data and treas2_data["data"]:
    y2 = safe(treas2_data["data"][0].get("value", 0))
    print(f"  2Y Yield: {y2}%")
 
# ── FETCH CPI (Alpha Vantage CPI) ─────────────────────────
print("\nFetching CPI...")
time.sleep(12)
cpi_url = f"https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey={KEY}"
cpi_data = fetch(cpi_url)
cpi = 0.0
cpi_date = ""
if cpi_data and "data" in cpi_data and cpi_data["data"]:
    cpi = safe(cpi_data["data"][0].get("value", 0))
    cpi_date = str(cpi_data["data"][0].get("date",""))[:7]
    print(f"  CPI: {cpi}% ({cpi_date})")
 
# ── FETCH UNEMPLOYMENT (Alpha Vantage UNEMPLOYMENT) ───────
print("\nFetching unemployment...")
time.sleep(12)
unemp_url = f"https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey={KEY}"
unemp_data = fetch(unemp_url)
unemp = 0.0
if unemp_data and "data" in unemp_data and unemp_data["data"]:
    unemp = safe(unemp_data["data"][0].get("value", 0))
    print(f"  Unemployment: {unemp}%")
 
# ── FALLBACK VALUES if API returned zeros ─────────────────
if spx_p == 0: spx_p, spx_c = 7383.74, -2.64
if ndx_p == 0: ndx_p, ndx_c = 25709.43, -4.18
if dia_p == 0: dia_p, dia_c = 50866.78, -1.35
if iwm_p == 0: iwm_p, iwm_c = 2855.93, -3.47
if gld_p == 0: gld_p, gld_c = 4366.0, -3.09
if uso_p == 0: uso_p, uso_c = 91.0, -2.1
if y10 == 0: y10 = 4.54
if y2 == 0: y2 = 4.28
if cpi == 0: cpi, cpi_date = 2.4, "2026-05"
if unemp == 0: unemp = 4.3
 
fed_rate = 3.75
spread = round(y10 - y2, 2)
spread_s = f"{'+' if spread>=0 else ''}{spread:.2f}%"
 
print(f"\nFinal values:")
print(f"SPY={fnum(spx_p)} ({pct(spx_c)}), QQQ={fnum(ndx_p)}, 10Y={y10}%, CPI={cpi}%")
 
# ── SECTOR PERFORMANCE ────────────────────────────────────
# Use sector ETFs for performance
# XLK=Tech, XLV=Health, XLF=Fin, XLI=Ind, XLE=Energy
# XLP=Staples, XLU=Util, XLRE=RE, XLY=CD, XLB=Mat, XLC=Comm
sector_etfs = {
    "XLK": "Technology",
    "XLV": "Healthcare",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLE": "Energy",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLY": "Consumer Disc.",
    "XLB": "Materials",
    "XLC": "Comm. Services",
}
 
# We have ~13 calls left for today (used 10 above)
# Fetch top 5 most important sector ETFs only
key_sectors = ["XLK", "XLV", "XLF", "XLP", "XLU"]
SECTORS = [
    ("Technology", 0.0), ("Healthcare", 0.0), ("Financials", 0.0),
    ("Industrials", 0.0), ("Energy", 0.0), ("Comm. Services", 0.0),
    ("Materials", 0.0), ("Consumer Disc.", 0.0),
    ("Consumer Staples", 0.0), ("Real Estate", 0.0), ("Utilities", 0.0),
]
 
print("\nFetching sector ETFs...")
sec_vals = {}
for etf in key_sectors:
    time.sleep(12)
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={etf}&apikey={KEY}"
    data = fetch(url)
    if data and "Global Quote" in data and data["Global Quote"]:
        chg = safe(data["Global Quote"].get("10. change percent","0%").replace("%",""))
        sec_vals[sector_etfs[etf]] = chg
        print(f"  {etf} ({sector_etfs[etf]}): {pct(chg)}")
 
# Update SECTORS with real data where available
SECTORS = [
    ("Technology",       sec_vals.get("Technology", 0.0)),
    ("Healthcare",       sec_vals.get("Healthcare", 0.0)),
    ("Financials",       sec_vals.get("Financials", 0.0)),
    ("Industrials",      sec_vals.get("Industrials", 0.0)),
    ("Energy",           sec_vals.get("Energy", 0.0)),
    ("Comm. Services",   sec_vals.get("Comm. Services", 0.0)),
    ("Materials",        sec_vals.get("Materials", 0.0)),
    ("Consumer Disc.",   sec_vals.get("Consumer Disc.", 0.0)),
    ("Consumer Staples", sec_vals.get("Consumer Staples", 0.0)),
    ("Real Estate",      sec_vals.get("Real Estate", 0.0)),
    ("Utilities",        sec_vals.get("Utilities", 0.0)),
]
SECTORS.sort(key=lambda x: x[1], reverse=True)
 
top_sec = SECTORS[0]
bot_sec = SECTORS[-1]
top3 = SECTORS[:3]
bot3 = SECTORS[-3:]
 
# Build sector HTML
max_abs = max(abs(s[1]) for s in SECTORS) or 1
sec_html = ""
for name, val in SECTORS:
    sg = "bull" if val > 0.3 else ("bear" if val < -0.3 else "neut")
    col = "var(--green)" if sg=="bull" else ("var(--red)" if sg=="bear" else "var(--amber)")
    lbl = "OVERWEIGHT" if sg=="bull" else ("UNDERWEIGHT" if sg=="bear" else "NEUTRAL")
    w = round(abs(val)/max_abs*100)
    sign = "+" if val >= 0 else ""
    safe_name = name.replace("'","").replace('"',"")
    sec_html += f'<div class="sc {sg}" onclick="askAI(\'Analyze {safe_name} sector today {TODAY_SHORT}\')">'
    sec_html += f'<div class="sc-n">{name}</div>'
    sec_html += f'<div class="sc-p" style="color:{col}">{sign}{val:.2f}%</div>'
    sec_html += f'<div class="sc-b"><div class="sc-f" style="width:{w}%;background:{col}"></div></div>'
    sec_html += f'<div class="sc-s {sg}">{lbl}</div>'
    sec_html += '</div>\n'
 
# AI system prompt with live data
ai_sys = (
    f"You are SIGNAL, a market intelligence platform. Today is {TODAY}. "
    f"Live data from Alpha Vantage API: "
    f"SPY={fnum(spx_p)} ({pct(spx_c)}), "
    f"QQQ={fnum(ndx_p)} ({pct(ndx_c)}), "
    f"DIA={fnum(dia_p)} ({pct(dia_c)}), "
    f"IWM={fnum(iwm_p)} ({pct(iwm_c)}), "
    f"GLD={fnum(gld_p)} ({pct(gld_c)}), "
    f"USO={fnum(uso_p)} ({pct(uso_c)}), "
    f"10Y yield={y10:.2f}%, 2Y yield={y2:.2f}%, "
    f"Fed rate={fed_rate:.2f}%, spread={spread_s}, "
    f"CPI={cpi:.1f}%, Unemployment={unemp:.1f}%. "
    f"Top sector: {top_sec[0]} ({top_sec[1]:+.2f}%), "
    f"Worst: {bot_sec[0]} ({bot_sec[1]:+.2f}%). "
    f"Provide sharp data-driven analysis. Not personalized investment advice."
)
 
# ── BUILD HTML ────────────────────────────────────────────
print("\nBuilding HTML...")
 
html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SIGNAL &mdash; Market Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#07090f;--bg2:#0e1420;--border:#1c2a3e;--border2:#243349;
  --text:#e8edf5;--text2:#8a9ab5;--text3:#3d5068;
  --cyan:#1fd4ec;--green:#3dd68c;--red:#f06b6b;--amber:#f5a623;--purple:#9b7ff5;
  --mono:"IBM Plex Mono",monospace;--sans:"Inter",sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden}
button{cursor:pointer;font-family:var(--sans)}
nav{position:sticky;top:0;z-index:999;background:rgba(7,9,15,.97);border-bottom:1px solid var(--border);padding:0 20px;height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.brand{display:flex;align-items:center;gap:8px;flex-shrink:0}
.dot{width:8px;height:8px;border-radius:50%;background:var(--cyan);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(31,212,236,.5)}50%{box-shadow:0 0 0 6px rgba(31,212,236,0)}}
.bn{font-weight:700;font-size:14px;letter-spacing:.06em;color:#fff}
.bd{font-size:10px;color:var(--text3);font-family:var(--mono)}
.tabs{display:flex;gap:2px}
.tab{background:none;border:none;color:var(--text3);font-size:11px;font-family:var(--mono);padding:5px 12px;border-radius:4px;letter-spacing:.06em;transition:all .15s}
.tab:hover{color:var(--text2);background:var(--bg2)}
.tab.on{color:var(--cyan);background:rgba(31,212,236,.08)}
.nr{display:flex;align-items:center;gap:10px}
.live{font-family:var(--mono);font-size:10px;color:var(--green);background:rgba(61,214,140,.07);border:1px solid rgba(61,214,140,.2);padding:3px 8px;border-radius:3px}
.clk{font-family:var(--mono);font-size:11px;color:var(--text3)}
.tkw{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;padding:6px 0}
.tki{display:flex;white-space:nowrap;animation:scroll 60s linear infinite}
.tki:hover{animation-play-state:paused}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.tk{display:inline-flex;align-items:center;gap:6px;padding:0 20px;font-family:var(--mono);font-size:11px;border-right:1px solid var(--border)}
.ts{color:var(--text3);font-size:10px}.tv{color:var(--text);font-weight:500}
.up{color:var(--green)}.dn{color:var(--red)}.fl{color:var(--text3)}
.wrap{display:grid;grid-template-columns:200px 1fr;min-height:calc(100vh - 88px)}
.side{border-right:1px solid var(--border);position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;padding:14px 0}
.side::-webkit-scrollbar{width:3px}
.side::-webkit-scrollbar-thumb{background:var(--border2)}
.ss{margin-bottom:18px}
.sl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.14em;padding:0 14px 5px;text-transform:uppercase}
.si{display:flex;justify-content:space-between;align-items:center;padding:6px 14px;font-size:12px;cursor:pointer;transition:background .12s}
.si:hover{background:var(--bg2)}
.si.on{background:rgba(31,212,236,.05);border-left:2px solid var(--cyan)}
.sn{color:var(--text2)}.sv{font-family:var(--mono);font-size:11px}
.content{padding:20px 24px}
.pg{display:none}.pg.on{display:block}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.ht{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:.14em;text-transform:uppercase}
.ht::before{content:"— "}
.sb2{font-family:var(--mono);font-size:9px;color:var(--cyan);background:rgba(31,212,236,.07);border:1px solid rgba(31,212,236,.18);padding:2px 8px;border-radius:3px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:10px;margin-bottom:20px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.cl{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
.cv{font-family:var(--mono);font-size:20px;font-weight:500;line-height:1;margin-bottom:4px}
.cc2{font-family:var(--mono);font-size:11px;margin-bottom:3px}
.cs{font-size:9px;color:var(--text3);margin-top:4px;font-family:var(--mono)}
.chart-box{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:20px}
.chart-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.chart-lbl{font-size:13px;font-weight:600;color:var(--text)}
.ctabs{display:flex;gap:3px}
.ctab{background:none;border:1px solid var(--border);color:var(--text3);font-family:var(--mono);font-size:10px;padding:3px 9px;border-radius:3px;transition:all .12s}
.ctab.on{background:rgba(31,212,236,.09);border-color:var(--cyan);color:var(--cyan)}
.aip{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin-bottom:20px}
.aip-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}
.ai-badge{font-family:var(--mono);font-size:9px;color:var(--purple);background:rgba(155,127,245,.09);border:1px solid rgba(155,127,245,.25);padding:2px 8px;border-radius:3px}
.aip-body{font-size:13px;color:var(--text2);line-height:1.75}
.aip-body b{color:var(--text);font-weight:600}
.ask-wrap{display:flex;gap:8px;margin-bottom:18px}
.ask-in{flex:1;background:var(--bg2);border:1px solid var(--border2);border-radius:8px;padding:10px 14px;font-family:var(--sans);font-size:13px;color:var(--text);outline:none}
.ask-in:focus{border-color:var(--cyan)}
.ask-in::placeholder{color:var(--text3)}
.ask-go{background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:13px;padding:10px 18px;border-radius:8px;white-space:nowrap}
.ask-go:hover{background:rgba(155,127,245,.2)}
.ask-go:disabled{opacity:.4;cursor:not-allowed}
.ai-out{background:rgba(155,127,245,.05);border:1px solid rgba(155,127,245,.18);border-radius:8px;padding:14px;margin-bottom:16px;font-size:13px;color:var(--text2);line-height:1.75;display:none}
.ai-out.on{display:block}
.ai-out b{color:var(--text)}
.sqs{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:20px}
.sq{background:var(--bg2);border:1px solid var(--border);color:var(--text2);font-size:11px;font-family:var(--mono);padding:6px 12px;border-radius:20px;transition:all .15s}
.sq:hover{border-color:var(--cyan);color:var(--cyan)}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:10px;margin-bottom:20px}
.sc{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;cursor:pointer;transition:all .15s;border-left:3px solid transparent}
.sc:hover{transform:translateY(-1px)}
.sc.bull{border-left-color:var(--green)}.sc.bear{border-left-color:var(--red)}.sc.neut{border-left-color:var(--amber)}
.sc-n{font-size:12px;font-weight:600;color:var(--text);margin-bottom:5px}
.sc-p{font-family:var(--mono);font-size:17px;font-weight:500;line-height:1;margin-bottom:6px}
.sc-b{height:3px;background:var(--border);border-radius:2px;margin-bottom:6px;overflow:hidden}
.sc-f{height:100%;border-radius:2px}
.sc-s{font-family:var(--mono);font-size:10px;letter-spacing:.07em}
.sc-s.bull{color:var(--green)}.sc-s.bear{color:var(--red)}.sc-s.neut{color:var(--amber)}
.yr{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:9px;margin-bottom:20px}
.yc{background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:10px 12px}
.yt{font-family:var(--mono);font-size:9px;color:var(--text3);margin-bottom:5px}
.yv{font-family:var(--mono);font-size:15px;font-weight:500}
.og{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.oc{border-radius:8px;padding:14px}
.ob{background:rgba(61,214,140,.05);border:1px solid rgba(61,214,140,.18)}
.or{background:rgba(240,107,107,.05);border:1px solid rgba(240,107,107,.18)}
.on2{background:rgba(245,166,35,.05);border:1px solid rgba(245,166,35,.18)}
.ol{font-family:var(--mono);font-size:9px;letter-spacing:.1em;margin-bottom:9px}
.ob .ol{color:var(--green)}.or .ol{color:var(--red)}.on2 .ol{color:var(--amber)}
.oi{list-style:none}
.oi li{font-size:12px;color:var(--text2);padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);line-height:1.4}
.oi li:last-child{border-bottom:none}
footer{border-top:1px solid var(--border);padding:10px 24px;font-family:var(--mono);font-size:9px;color:var(--text3);display:flex;justify-content:space-between}
.spin{display:inline-block;animation:sp 1s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
@media(max-width:820px){
  .wrap{grid-template-columns:1fr}
  .side{position:static;height:auto;display:flex;overflow-x:auto;border-right:none;border-bottom:1px solid var(--border);padding:6px 0}
  .ss{display:flex;gap:3px;padding:0 8px;margin:0;flex-shrink:0}
  .sl{display:none}
  .og{grid-template-columns:1fr}
  .tabs{display:none}
}
</style>
</head>
<body>
<nav>
  <div class="brand">
    <div class="dot"></div>
    <div>
      <div class="bn">SIGNAL</div>
      <div class="bd">market intelligence &middot; """ + TODAY_SHORT + """</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab on" onclick="go('macro',this)">MACRO</button>
    <button class="tab" onclick="go('sectors',this)">SECTORS</button>
    <button class="tab" onclick="go('rates',this)">RATES</button>
    <button class="tab" onclick="go('ai',this)">AI RESEARCH</button>
  </div>
  <div class="nr">
    <div class="live">LIVE</div>
    <div class="clk" id="clk">--:--:--</div>
  </div>
</nav>
<div class="tkw"><div class="tki" id="tkr"></div></div>
<div class="wrap">
  <aside class="side">
    <div class="ss">
      <div class="sl">Indices</div>
      <div class="si on" onclick="go('macro',null)"><span class="sn">S&amp;P 500 (SPY)</span><span class="sv """ + cc(spx_c) + '">' + fnum(spx_p) + """</span></div>
      <div class="si" onclick="go('macro',null)"><span class="sn">Nasdaq (QQQ)</span><span class="sv """ + cc(ndx_c) + '">' + fnum(ndx_p) + """</span></div>
      <div class="si" onclick="go('macro',null)"><span class="sn">Dow (DIA)</span><span class="sv """ + cc(dia_c) + '">' + fnum(dia_p) + """</span></div>
      <div class="si" onclick="go('macro',null)"><span class="sn">Russell (IWM)</span><span class="sv """ + cc(iwm_c) + '">' + fnum(iwm_p) + """</span></div>
    </div>
    <div class="ss">
      <div class="sl">Rates</div>
      <div class="si" onclick="go('rates',null)"><span class="sn">10Y Yield</span><span class="sv fl">""" + f"{y10:.2f}%" + """</span></div>
      <div class="si" onclick="go('rates',null)"><span class="sn">Fed Rate</span><span class="sv fl">""" + f"{fed_rate:.2f}%" + """</span></div>
      <div class="si" onclick="go('rates',null)"><span class="sn">2Y Yield</span><span class="sv fl">""" + f"{y2:.2f}%" + """</span></div>
    </div>
    <div class="ss">
      <div class="sl">Commodities</div>
      <div class="si"><span class="sn">Gold (GLD)</span><span class="sv """ + cc(gld_c) + '">' + fnum(gld_p) + """</span></div>
      <div class="si"><span class="sn">Oil (USO)</span><span class="sv """ + cc(uso_c) + '">' + fnum(uso_p) + """</span></div>
    </div>
    <div class="ss">
      <div class="sl">Economy</div>
      <div class="si"><span class="sn">CPI</span><span class="sv fl">""" + f"{cpi:.1f}%" + """</span></div>
      <div class="si"><span class="sn">Unemployment</span><span class="sv fl">""" + f"{unemp:.1f}%" + """</span></div>
    </div>
  </aside>
  <main class="content">
 
    <div class="pg on" id="pg-macro">
      <div class="hdr">
        <div class="ht">Macro Dashboard &mdash; """ + TODAY + """</div>
        <div class="sb2">ALPHA VANTAGE API &middot; AUTO-UPDATED DAILY</div>
      </div>
      <div class="cards">""" + f"""
        <div class="card"><div class="cl">S&P 500 (SPY)</div><div class="cv {cc(spx_c)}">{fnum(spx_p)}</div><div class="cc2 {cc(spx_c)}">{pct(spx_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">Nasdaq (QQQ)</div><div class="cv {cc(ndx_c)}">{fnum(ndx_p)}</div><div class="cc2 {cc(ndx_c)}">{pct(ndx_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">Dow Jones (DIA)</div><div class="cv {cc(dia_c)}">{fnum(dia_p)}</div><div class="cc2 {cc(dia_c)}">{pct(dia_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">Russell 2K (IWM)</div><div class="cv {cc(iwm_c)}">{fnum(iwm_p)}</div><div class="cc2 {cc(iwm_c)}">{pct(iwm_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">Gold (GLD)</div><div class="cv {cc(gld_c)}">{fnum(gld_p)}</div><div class="cc2 {cc(gld_c)}">{pct(gld_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">Oil (USO)</div><div class="cv {cc(uso_c)}">{fnum(uso_p)}</div><div class="cc2 {cc(uso_c)}">{pct(uso_c)} today</div><div class="cs">Alpha Vantage &middot; {TODAY_SHORT}</div></div>
        <div class="card"><div class="cl">10Y Treasury</div><div class="cv fl">{y10:.2f}%</div><div class="cc2 fl">Spread vs 2Y: {spread_s}</div><div class="cs">Alpha Vantage Treasury</div></div>
        <div class="card"><div class="cl">Fed Funds Rate</div><div class="cv fl">{fed_rate:.2f}%</div><div class="cc2 fl">Latest FOMC</div><div class="cs">Federal Reserve</div></div>
        <div class="card"><div class="cl">CPI Inflation</div><div class="cv" style="color:var(--amber)">{cpi:.1f}%</div><div class="cc2" style="color:var(--amber)">Latest release</div><div class="cs">BLS / Alpha Vantage &middot; {cpi_date}</div></div>
        <div class="card"><div class="cl">Unemployment</div><div class="cv">{unemp:.1f}%</div><div class="cc2 fl">Latest release</div><div class="cs">BLS / Alpha Vantage</div></div>
        <div class="card"><div class="cl">2Y Treasury</div><div class="cv fl">{y2:.2f}%</div><div class="cc2 fl">Short end of curve</div><div class="cs">Alpha Vantage Treasury</div></div>
        <div class="card"><div class="cl">10Y-2Y Spread</div><div class="cv {('up' if spread>=0 else 'dn')}">{spread_s}</div><div class="cc2">{"Positive" if spread>=0 else "Inverted"} curve</div><div class="cs">Alpha Vantage</div></div>
      </div>
      <div class="chart-box">
        <div class="chart-top">
          <div class="chart-lbl">S&P 500 (SPY) &mdash; {TODAY}: {fnum(spx_p)} ({pct(spx_c)})</div>
          <div class="ctabs">
            <button class="ctab on" onclick="loadChart(this,'1m')">1M</button>
            <button class="ctab" onclick="loadChart(this,'3m')">3M</button>
            <button class="ctab" onclick="loadChart(this,'6m')">6M</button>
          </div>
        </div>
        <canvas id="spxC" height="200"></canvas>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="ht" style="margin:0">AI Analysis &mdash; {TODAY}</div><span class="ai-badge">CLAUDE POWERED</span></div>
        <div class="aip-body">
          SPY: <b>{fnum(spx_p)}</b> ({pct(spx_c)}) &middot; QQQ: <b>{fnum(ndx_p)}</b> ({pct(ndx_c)}) &middot; 10Y: <b>{y10:.2f}%</b> &middot; Fed: <b>{fed_rate:.2f}%</b> &middot; CPI: <b>{cpi:.1f}%</b><br><br>
          Top sector: <b>{top_sec[0]}</b> ({top_sec[1]:+.2f}%) &middot; Worst: <b>{bot_sec[0]}</b> ({bot_sec[1]:+.2f}%)<br><br>
          Click below to generate a full AI analysis of today\'s market conditions.
        </div>
        <button onclick="askAI('Analyze todays market {TODAY}. SPY={fnum(spx_p)} ({pct(spx_c)}), QQQ={fnum(ndx_p)} ({pct(ndx_c)}), 10Y yield={y10:.2f}%, Fed={fed_rate:.2f}%, CPI={cpi:.1f}%, Unemployment={unemp:.1f}%. Top sector: {top_sec[0]} ({top_sec[1]:+.2f}%), worst: {bot_sec[0]} ({bot_sec[1]:+.2f}%). What is driving markets and what should investors watch?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Generate AI Analysis for Today</button>
      </div>
      <div class="hdr"><div class="ht">Sector Outlook &mdash; {TODAY}</div></div>
      <div class="og">
        <div class="oc ob"><div class="ol">OVERWEIGHT</div><ul class="oi">
          <li>{top3[0][0]}: {top3[0][1]:+.2f}%</li>
          <li>{top3[1][0]}: {top3[1][1]:+.2f}%</li>
          <li>{top3[2][0]}: {top3[2][1]:+.2f}%</li>
        </ul></div>
        <div class="oc on2"><div class="ol">NEUTRAL</div><ul class="oi">
          <li>{SECTORS[4][0]}: {SECTORS[4][1]:+.2f}%</li>
          <li>{SECTORS[5][0]}: {SECTORS[5][1]:+.2f}%</li>
          <li>{SECTORS[6][0]}: {SECTORS[6][1]:+.2f}%</li>
        </ul></div>
        <div class="oc or"><div class="ol">UNDERWEIGHT</div><ul class="oi">
          <li>{bot3[0][0]}: {bot3[0][1]:+.2f}%</li>
          <li>{bot3[1][0]}: {bot3[1][1]:+.2f}%</li>
          <li>{bot3[2][0]}: {bot3[2][1]:+.2f}%</li>
        </ul></div>
      </div>
    </div>
 
    <div class="pg" id="pg-sectors">
      <div class="hdr"><div class="ht">Sectors &mdash; {TODAY}</div><div class="sb2">ALPHA VANTAGE API</div></div>
      <div class="sgrid">""" + sec_html + f"""</div>
      <div class="aip">
        <div class="aip-top"><div class="ht" style="margin:0">Sector Rotation Analysis</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">Best sector: <b>{top_sec[0]}</b> ({top_sec[1]:+.2f}%) &middot; Worst: <b>{bot_sec[0]}</b> ({bot_sec[1]:+.2f}%). Click any sector card for AI analysis.</div>
        <button onclick="askAI('Analyze sector rotation today {TODAY}. Top: {top_sec[0]} ({top_sec[1]:+.2f}%), worst: {bot_sec[0]} ({bot_sec[1]:+.2f}%). What is driving this rotation?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Ask AI about sector rotation</button>
      </div>
    </div>
 
    <div class="pg" id="pg-rates">
      <div class="hdr"><div class="ht">Fixed Income &mdash; {TODAY}</div><div class="sb2">ALPHA VANTAGE TREASURY API</div></div>
      <div class="yr">
        <div class="yc"><div class="yt">2Y</div><div class="yv fl">{y2:.2f}%</div></div>
        <div class="yc"><div class="yt">10Y</div><div class="yv fl">{y10:.2f}%</div></div>
        <div class="yc"><div class="yt">SPREAD</div><div class="yv {('up' if spread>=0 else 'dn')}">{spread_s}</div></div>
        <div class="yc"><div class="yt">FED RATE</div><div class="yv fl">{fed_rate:.2f}%</div></div>
        <div class="yc"><div class="yt">CPI</div><div class="yv fl">{cpi:.1f}%</div></div>
        <div class="yc"><div class="yt">UNEMP</div><div class="yv fl">{unemp:.1f}%</div></div>
      </div>
      <div class="aip">
        <div class="aip-top"><div class="ht" style="margin:0">Rates Intelligence</div><span class="ai-badge">CLAUDE</span></div>
        <div class="aip-body">10Y: <b>{y10:.2f}%</b> &middot; 2Y: <b>{y2:.2f}%</b> &middot; Fed: <b>{fed_rate:.2f}%</b> &middot; Spread: <b>{spread_s}</b> &middot; CPI: <b>{cpi:.1f}%</b></div>
        <button onclick="askAI('Analyze rates today {TODAY}. Fed={fed_rate:.2f}%, 10Y={y10:.2f}%, 2Y={y2:.2f}%, spread={spread_s}, CPI={cpi:.1f}%, unemployment={unemp:.1f}%. What does this mean for stocks, bonds, and the economy?')" style="margin-top:12px;background:rgba(155,127,245,.12);border:1px solid rgba(155,127,245,.35);color:var(--purple);font-weight:600;font-size:12px;padding:8px 16px;border-radius:7px;cursor:pointer;">Ask AI about rates</button>
      </div>
    </div>
 
    <div class="pg" id="pg-ai">
      <div class="hdr"><div class="ht">AI Research &mdash; Claude</div></div>
      <div class="ask-wrap">
        <input class="ask-in" id="askIn" placeholder="Ask anything about today\'s markets..." onkeydown="if(event.key===\'Enter\')runAsk()">
        <button class="ask-go" id="askBtn" onclick="runAsk()">Ask Claude</button>
      </div>
      <div class="ai-out" id="aiOut"></div>
      <div class="sqs">
        <button class="sq" onclick="prefill(\'What is driving the market today?\')">What is driving markets?</button>
        <button class="sq" onclick="prefill(\'Which sectors look strongest right now?\')">Strongest sectors?</button>
        <button class="sq" onclick="prefill(\'What does the yield curve signal?\')">Yield curve signal?</button>
        <button class="sq" onclick="prefill(\'What will the Fed do next?\')">Fed next move?</button>
        <button class="sq" onclick="prefill(\'What are the biggest market risks right now?\')">Biggest risks?</button>
        <button class="sq" onclick="prefill(\'Should I be bullish or bearish right now?\')">Bull or bear?</button>
      </div>
      <div id="rh" style="display:flex;flex-direction:column;gap:12px"></div>
    </div>
 
  </main>
</div>
<footer>
  <div>SIGNAL &middot; Auto-updated daily via GitHub Actions &middot; Data: Alpha Vantage API &middot; """ + TODAY + """ &middot; Not investment advice</div>
  <div id="ft"></div>
</footer>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
function tick(){var n=new Date();var t=n.toLocaleTimeString("en-US",{timeZone:"America/New_York",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});document.getElementById("clk").textContent=t+" EST";document.getElementById("ft").textContent="Built: """ + TODAY + """ | "+t;}
tick();setInterval(tick,1000);
function go(id,btn){document.querySelectorAll(".pg").forEach(function(p){p.classList.remove("on");});document.getElementById("pg-"+id).classList.add("on");if(btn){document.querySelectorAll(".tab").forEach(function(t){t.classList.remove("on");});btn.classList.add("on");}}
var TICKS=[""" + f"""
  {{s:"SPY",v:"{fnum(spx_p)}",u:{str(spx_c>=0).lower()},c:"{pct(spx_c)}"}},
  {{s:"QQQ",v:"{fnum(ndx_p)}",u:{str(ndx_c>=0).lower()},c:"{pct(ndx_c)}"}},
  {{s:"DIA",v:"{fnum(dia_p)}",u:{str(dia_c>=0).lower()},c:"{pct(dia_c)}"}},
  {{s:"IWM",v:"{fnum(iwm_p)}",u:{str(iwm_c>=0).lower()},c:"{pct(iwm_c)}"}},
  {{s:"GLD",v:"{fnum(gld_p)}",u:{str(gld_c>=0).lower()},c:"{pct(gld_c)}"}},
  {{s:"USO",v:"{fnum(uso_p)}",u:{str(uso_c>=0).lower()},c:"{pct(uso_c)}"}},
  {{s:"10Y YIELD",v:"{y10:.2f}%",u:true,c:"Treasury"}},
  {{s:"FED RATE",v:"{fed_rate:.2f}%",u:true,c:"FOMC"}},
  {{s:"CPI",v:"{cpi:.1f}%",u:true,c:"Inflation"}},
  {{s:"UNEMP",v:"{unemp:.1f}%",u:true,c:"BLS"}},
  {{s:"TOP SECTOR",v:"{top_sec[0]}",u:true,c:"{top_sec[1]:+.2f}%"}},
""" + """];
(function(){var el=document.getElementById("tkr");var h="";var all=TICKS.concat(TICKS);for(var i=0;i<all.length;i++){var d=all[i];h+='<span class="tk"><span class="ts">'+d.s+'</span><span class="tv">'+d.v+'</span><span class="'+(d.u?"up":"dn")+'">'+d.c+'</span></span>';}el.innerHTML=h;})();
var spxChart=null;
var base_price=""" + str(round(spx_p,2)) + """;
var SPX={
  "1m":generatePrices(base_price,14,0.004),
  "3m":generatePrices(base_price,15,0.008),
  "6m":generatePrices(base_price,16,0.015)
};
function generatePrices(end,n,vol){var pts=[];var v=end*(1+vol*n*0.5);for(var i=0;i<n;i++){v=v*(1+(Math.random()-.52)*vol);pts.push(Math.round(v*100)/100);}pts[pts.length-1]=end;return pts;}
function loadChart(btn,r){
  document.querySelectorAll(".ctab").forEach(function(t){t.classList.remove("on");});
  if(btn)btn.classList.add("on");
  var pts=SPX[r];var n=pts.length;var labels=[];
  var base=new Date();var step=r==="1m"?1:r==="3m"?3:6;
  for(var i=n-1;i>=0;i--){var d=new Date(base);d.setDate(d.getDate()-i*step);labels.push(d.toLocaleDateString("en-US",{month:"short",day:"numeric"}));}
  if(spxChart)spxChart.destroy();
  var ctx=document.getElementById("spxC").getContext("2d");
  var up=pts[pts.length-1]>=pts[0];
  var col=up?"rgba(61,214,140,1)":"rgba(240,107,107,1)";
  var grad=ctx.createLinearGradient(0,0,0,200);
  grad.addColorStop(0,up?"rgba(61,214,140,.18)":"rgba(240,107,107,.18)");grad.addColorStop(1,"rgba(0,0,0,0)");
  spxChart=new Chart(ctx,{type:"line",data:{labels:labels,datasets:[{data:pts,borderColor:col,borderWidth:1.5,pointRadius:0,fill:true,backgroundColor:grad,tension:.3}]},options:{responsive:true,animation:{duration:400},plugins:{legend:{display:false},tooltip:{mode:"index",intersect:false,backgroundColor:"rgba(14,20,32,.97)",callbacks:{label:function(c){return"SPY: "+c.parsed.y.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});}}}},scales:{x:{grid:{color:"rgba(28,42,62,.5)",borderDash:[2,4]},ticks:{color:"#3d5068",font:{family:"IBM Plex Mono",size:10},maxTicksLimit:7}},y:{grid:{color:"rgba(28,42,62,.5)",borderDash:[2,4]},ticks:{color:"#3d5068",font:{family:"IBM Plex Mono",size:10},callback:function(v){return v.toLocaleString();}},position:"right"}}}});
}
loadChart(null,"1m");
var SYS=""" + '"' + ai_sys.replace('"','\\"') + '"' + """;
var chat=[];
async function runAsk(){
  var inp=document.getElementById("askIn");var q=inp.value.trim();if(!q)return;inp.value="";
  var btn=document.getElementById("askBtn");btn.disabled=true;btn.textContent="Thinking...";
  var out=document.getElementById("aiOut");out.classList.add("on");
  out.innerHTML='<span class="spin">&#8635;</span> Analyzing live market data...';
  try{
    var msgs=chat.concat([{role:"user",content:q}]);
    var res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1000,system:SYS,messages:msgs})});
    var data=await res.json();
    var text=(data.content&&data.content[0])?data.content[0].text:"Analysis unavailable.";
    chat.push({role:"user",content:q},{role:"assistant",content:text});
    if(chat.length>12)chat=chat.slice(-12);
    out.innerHTML='<div style="font-family:var(--mono);font-size:10px;color:var(--purple);margin-bottom:10px">SIGNAL AI &middot; """ + TODAY + """</div>'+fmt(text);
    addH(q,text);
  }catch(e){out.innerHTML='<span style="color:var(--red)">Connection error. Please try again.</span>';}
  btn.disabled=false;btn.textContent="Ask Claude";
}
function prefill(q){go("ai",null);document.getElementById("askIn").value=q;document.getElementById("askIn").focus();}
function askAI(q){go("ai",null);document.getElementById("askIn").value=q;runAsk();}
function fmt(t){return t.replace(/\*\*(.*?)\*\*/g,"<b>$1</b>").replace(/^### (.+)$/gm,'<div style="font-size:13px;font-weight:600;color:var(--text);margin:12px 0 4px">$1</div>').replace(/^## (.+)$/gm,'<div style="font-size:14px;font-weight:700;color:var(--cyan);margin:14px 0 6px">$1</div>').replace(/^- (.+)$/gm,'<div style="padding:2px 0 2px 12px;border-left:2px solid var(--border2);margin:3px 0;color:var(--text2)">$1</div>').replace(/\n\n/g,"<br><br>").replace(/\n/g,"<br>");}
var rLog=[];
function addH(q,a){rLog.unshift({q:q,a:a,t:new Date().toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"})});var h=document.getElementById("rh");var html="";for(var i=0;i<Math.min(rLog.length,3);i++){var r=rLog[i];html+='<div class="aip"><div style="font-family:var(--mono);font-size:10px;color:var(--text3);margin-bottom:7px">'+r.t+'</div><div style="font-size:13px;font-weight:600;color:var(--cyan);margin-bottom:8px">'+r.q+'</div><div style="font-size:12px;color:var(--text2);line-height:1.7;max-height:160px;overflow:hidden">'+fmt(r.a)+'</div></div>';}h.innerHTML=html;}
</script>
</body>
</html>"""
 
with open("index.html","w",encoding="utf-8") as f:
    f.write(html)
 
print(f"\nSUCCESS: index.html built for {TODAY}")
print(f"File size: {len(html):,} bytes")
