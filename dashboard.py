#!/usr/bin/env python3
"""
Analytics pipeline dashboard.

Run:   python3 dashboard.py
Open:  http://localhost:8090

Serves one web page and forwards its requests to the Producer (8082) and
Reporter (8084), so the browser never talks to them directly (no CORS setup
needed). It signs its own demo login token for app1 with the same secret
the services use, so no token file is needed.
Uses only the Python standard library.
"""
import base64
import hashlib
import hmac
import json
import os
import socket
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8090
PRODUCER = "http://localhost:8082"
REPORTER = "http://localhost:8084"
# Same secret as secret.key / jwt.secret in the services' application.properties.
# The surrounding quotes are part of the key, because the properties file includes them.
SECRET = '"qwert123qwer123qweqwertyu2446dtrde56er6d6ttfy"'
APP_ID = os.environ.get("APP_ID", "app1")
CHECKS = {
    "producer": 8082, "consumer": 8083, "reporter": 8084,
    "kafka": 9094, "postgres": 5432, "redis": 6379,
}


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def read_token():
    """Build an HS256 JWT: {"sub","appId","token_version":1,"type":"access_token"}."""
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = {"sub": APP_ID, "appId": APP_ID, "token_version": 1, "type": "access_token"}
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    sig = hmac.new(SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{b64(sig)}"


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def forward(method, url, token, body=None):
    headers = {"Authorization": "Bearer " + token} if token else {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # service not running, timeout...
        return 502, ("Could not reach " + url + ": " + str(e)).encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def token(self):
        return self.headers.get("X-Token") or read_token()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self.send(200, PAGE, "text/html; charset=utf-8")
        if self.path == "/api/status":
            st = {k: port_open(p) for k, p in CHECKS.items()}
            st["token"] = bool(read_token())
            return self.send(200, json.dumps(st))
        if self.path.startswith("/api/report/"):
            app = self.path.rsplit("/", 1)[-1]
            code, body = forward("GET", REPORTER + "/analytics/report/" + app, self.token())
            return self.send(code, body, "text/plain; charset=utf-8")
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path == "/api/produce":
            n = int(self.headers.get("Content-Length") or 0)
            code, body = forward("POST", PRODUCER + "/analytics/produce", self.token(), self.rfile.read(n))
            return self.send(code, body, "text/plain; charset=utf-8")
        self.send(404, "not found", "text/plain")


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analytics Pipeline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  color-scheme:light;
  --bg:#f4f3ef; --surface:#fcfcfb; --surface-2:#efeee9; --line:#dedcd5;
  --ink:#0b0b0b; --ink-2:#52514e; --ink-3:#85847e;
  --accent:#2a78d6; --accent-soft:#cde2fb;
  --s1:#2a78d6; --s2:#eb6834;
  --good:#008300; --bad:#d03b3a; --warn:#b77800;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --sans:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --bg:#121211; --surface:#1a1a19; --surface-2:#232321; --line:#33332f;
  --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#8a897f;
  --accent:#3987e5; --accent-soft:#1c3556;
  --s1:#3987e5; --s2:#d95926;
  --good:#3fae3f; --bad:#e66767; --warn:#d9a030;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--sans)}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:22px}
h1{font-size:26px;font-weight:600;margin:0;letter-spacing:-.01em}
.sub{color:var(--ink-2);margin:2px 0 0}
.app-pick{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:13px;color:var(--ink-2)}
.app-pick input{width:90px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px}
.card h2{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2);margin:0 0 14px}

/* pipeline */
.pipe{display:grid;grid-template-columns:repeat(6,1fr);gap:0;align-items:center;margin-bottom:18px;position:relative}
.node{position:relative;z-index:1;text-align:center;padding:12px 6px;border:1px solid var(--line);border-radius:10px;background:var(--surface);margin:0 10px;transition:border-color .2s,box-shadow .2s}
.node b{display:block;font-size:14px;font-weight:600}
.node small{display:block;font-family:var(--mono);font-size:11px;color:var(--ink-3)}
.node .dot{position:absolute;top:8px;right:8px;width:8px;height:8px;border-radius:50%;background:var(--ink-3)}
.node.up .dot{background:var(--good)} .node.down .dot{background:var(--bad)}
.node.down{border-style:dashed}
.node.flash{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.wire{position:absolute;top:50%;left:8%;right:8%;height:2px;background:var(--line);z-index:0}
.packet{position:absolute;top:50%;width:10px;height:10px;margin:-5px 0 0 -5px;border-radius:50%;background:var(--accent);z-index:2;box-shadow:0 0 0 3px var(--accent-soft)}
.pipe-note{font-size:13px;color:var(--ink-2);margin:-6px 0 18px;min-height:20px}

.grid{display:grid;grid-template-columns:340px 1fr;gap:18px}
@media (max-width:900px){.grid{grid-template-columns:1fr}.pipe{grid-template-columns:repeat(3,1fr);row-gap:12px}.wire{display:none}}

/* form */
label{display:block;font-size:12px;color:var(--ink-2);margin:10px 0 4px}
input,select{width:100%;font:14px var(--sans);color:var(--ink);background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
input:focus,select:focus{outline:2px solid var(--accent);outline-offset:-1px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.btn{font:500 14px var(--sans);border-radius:8px;padding:9px 14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);cursor:pointer}
.btn:hover{border-color:var(--ink-3)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn.primary:hover{filter:brightness(1.08)}
.btn.on{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.btns .btn{flex:1}

/* stats */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
@media (max-width:700px){.tiles{grid-template-columns:repeat(2,1fr)}}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile .k{font-size:12px;color:var(--ink-2)}
.tile .v{font-family:var(--mono);font-size:30px;font-weight:500;line-height:1.2;margin-top:2px}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:700px){.charts{grid-template-columns:1fr}}

/* bar chart */
.bars{display:flex;flex-direction:column;gap:10px}
.bar{display:grid;grid-template-columns:90px 1fr 44px;align-items:center;gap:10px;font-size:13px;position:relative;padding:2px 0;cursor:default}
.bar .name{color:var(--ink-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar .track{height:18px;position:relative}
.bar .fill{position:absolute;left:0;top:0;bottom:0;border-radius:0 4px 4px 0;background:var(--s1);transition:width .4s ease;min-width:2px}
.bar .num{font-family:var(--mono);text-align:right;color:var(--ink)}
.bar:hover .fill{filter:brightness(1.1)}
.empty{color:var(--ink-3);font-size:13px;padding:10px 0}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--surface);font-size:12px;padding:6px 9px;border-radius:6px;opacity:0;transition:opacity .1s;z-index:9;white-space:nowrap}
.tip b{font-family:var(--mono);font-weight:500}

/* log */
.log{margin-top:18px}
.log ol{list-style:none;margin:0;padding:0;font-family:var(--mono);font-size:12px;max-height:240px;overflow:auto}
.log li{display:grid;grid-template-columns:62px 84px 1fr;gap:10px;padding:6px 0;border-top:1px solid var(--line)}
.log li:first-child{border-top:0}
.log .t{color:var(--ink-3)}
.badge{display:inline-flex;align-items:center;gap:4px;font-weight:500}
.ok{color:var(--good)} .err{color:var(--bad)}
.json{white-space:pre-wrap;word-break:break-all;color:var(--ink-2)}
details{margin-top:12px} summary{cursor:pointer;font-size:13px;color:var(--ink-2)}
pre{font:12px/1.5 var(--mono);background:var(--surface-2);padding:10px;border-radius:8px;overflow:auto;margin:8px 0 0}
.banner{display:none;margin-bottom:16px;padding:10px 14px;border-radius:10px;border:1px solid var(--bad);color:var(--ink);background:var(--surface);font-size:14px}
.banner.show{display:block}
</style>
</head>
<body>
<div class="tip" id="tip"></div>
<div class="wrap">
  <header>
    <div>
      <h1>Analytics Pipeline</h1>
      <p class="sub">Send events through Producer &rarr; Kafka &rarr; Consumer &rarr; PostgreSQL and watch the Reporter count them.</p>
    </div>
    <div class="app-pick">viewing report for <input id="app" value="app1" aria-label="App id"></div>
  </header>

  <div class="banner" id="banner"></div>

  <div class="pipe" id="pipe">
    <div class="wire"></div>
    <div class="node" data-k="producer"><span class="dot"></span><b>Producer</b><small>:8082</small></div>
    <div class="node" data-k="redis"><span class="dot"></span><b>Redis</b><small>token check</small></div>
    <div class="node" data-k="kafka"><span class="dot"></span><b>Kafka</b><small>:9094</small></div>
    <div class="node" data-k="consumer"><span class="dot"></span><b>Consumer</b><small>:8083</small></div>
    <div class="node" data-k="postgres"><span class="dot"></span><b>PostgreSQL</b><small>:5432</small></div>
    <div class="node" data-k="reporter"><span class="dot"></span><b>Reporter</b><small>:8084</small></div>
  </div>
  <p class="pipe-note" id="note">Green dot = running. Send an event to watch it travel.</p>

  <div class="grid">
    <div>
      <div class="card">
        <h2>Send an event</h2>
        <div class="row">
          <div><label for="eventType">Event type</label>
            <select id="eventType"><option>login</option><option>purchase</option><option>signup</option><option>page_view</option><option>logout</option></select></div>
          <div><label for="deviceType">Device</label>
            <select id="deviceType"><option>mobile</option><option>desktop</option></select></div>
        </div>
        <div class="row">
          <div><label for="userId">User id</label><input id="userId" value="u1"></div>
          <div><label for="userName">User name</label><input id="userName" value="Rakshit"></div>
        </div>
        <label for="browser">Browser</label>
        <select id="browser"><option>chrome</option><option>safari</option><option>firefox</option><option>edge</option></select>
        <div class="btns">
          <button class="btn primary" id="send">Send event</button>
          <button class="btn" id="random">Random</button>
        </div>
        <div class="btns">
          <button class="btn" id="sim">Simulate traffic</button>
          <button class="btn" id="sec">Test security</button>
        </div>
        <details>
          <summary>What gets sent</summary>
          <pre id="preview"></pre>
        </details>
      </div>
    </div>

    <div>
      <div class="tiles">
        <div class="tile"><div class="k">Total events</div><div class="v" id="tTotal">&ndash;</div></div>
        <div class="tile"><div class="k">Unique users</div><div class="v" id="tUnique">&ndash;</div></div>
        <div class="tile"><div class="k">Mobile</div><div class="v" id="tMobile">&ndash;</div></div>
        <div class="tile"><div class="k">Desktop</div><div class="v" id="tDesktop">&ndash;</div></div>
      </div>
      <div class="charts">
        <div class="card"><h2>Events by type</h2><div class="bars" id="evBars"></div></div>
        <div class="card"><h2>Events by device</h2><div class="bars" id="devBars"></div></div>
      </div>
      <div class="card log">
        <h2>Activity</h2>
        <ol id="log"></ol>
      </div>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
const order = ["producer","redis","kafka","consumer","postgres","reporter"];
let status = {};

function payload(){
  return {eventType:$("eventType").value, userId:$("userId").value.trim(), userName:$("userName").value.trim(),
          deviceType:$("deviceType").value, browser:$("browser").value, timestamp:Date.now()};
}
function showPreview(){ $("preview").textContent = JSON.stringify(payload(), null, 2); }
document.querySelectorAll("input,select").forEach(el => el.addEventListener("input", showPreview));
showPreview();

function log(ok, label, text){
  const li = document.createElement("li");
  const t = new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"});
  li.innerHTML = `<span class="t">${t}</span><span class="badge ${ok?"ok":"err"}">${ok?"✓":"✕"} ${label}</span><span class="json"></span>`;
  li.querySelector(".json").textContent = text;
  $("log").prepend(li);
  while ($("log").children.length > 60) $("log").lastChild.remove();
}

/* ---------- pipeline animation ---------- */
function nodeEl(k){ return document.querySelector(`.node[data-k="${k}"]`); }
function flash(k){ const n = nodeEl(k); n.classList.add("flash"); setTimeout(()=>n.classList.remove("flash"), 450); }
function animate(stops){
  const pipe = $("pipe"), pr = pipe.getBoundingClientRect();
  if (getComputedStyle(pipe.querySelector(".wire")).display === "none") { stops.forEach((k,i)=>setTimeout(()=>flash(k), i*220)); return; }
  const p = document.createElement("div"); p.className = "packet"; pipe.appendChild(p);
  const xs = stops.map(k => { const r = nodeEl(k).getBoundingClientRect(); return r.left - pr.left + r.width/2; });
  p.style.left = xs[0] + "px"; flash(stops[0]);
  const frames = xs.map(x => ({left: x + "px"}));
  const a = p.animate(frames, {duration: 260*(xs.length-1), easing:"ease-in-out", fill:"forwards"});
  stops.slice(1).forEach((k,i)=>setTimeout(()=>flash(k), 260*(i+1)));
  a.onfinish = () => p.remove();
}

/* ---------- status ---------- */
async function refreshStatus(){
  try {
    status = await (await fetch("/api/status")).json();
  } catch(e) { status = {}; }
  order.forEach(k => { const n = nodeEl(k); n.classList.toggle("up", !!status[k]); n.classList.toggle("down", !status[k]); });
  const down = order.filter(k => !status[k]);
  const b = $("banner");
  if (down.length) { b.textContent = "Not running: " + down.join(", ") + ". Start them, and this page will pick them up automatically."; b.classList.add("show"); }
  else b.classList.remove("show");
}

/* ---------- report ---------- */
function bars(el, entries, color){
  if (!entries.length) { el.innerHTML = '<div class="empty">No events yet</div>'; return; }
  const max = Math.max(...entries.map(e=>e[1]), 1);
  const total = entries.reduce((s,e)=>s+e[1],0);
  el.innerHTML = "";
  entries.forEach(([name, v]) => {
    const row = document.createElement("div"); row.className = "bar";
    row.innerHTML = `<span class="name"></span><span class="track"><span class="fill"></span></span><span class="num">${v}</span>`;
    row.querySelector(".name").textContent = name;
    const f = row.querySelector(".fill"); f.style.background = color; f.style.width = (v/max*100) + "%";
    row.addEventListener("mousemove", ev => tip(ev, `${name}: <b>${v}</b> (${total ? Math.round(v/total*100) : 0}%)`));
    row.addEventListener("mouseleave", hideTip);
    el.appendChild(row);
  });
}
function tip(ev, html){ const t = $("tip"); t.innerHTML = html; t.style.left = (ev.clientX+12)+"px"; t.style.top = (ev.clientY-30)+"px"; t.style.opacity = 1; }
function hideTip(){ $("tip").style.opacity = 0; }

let lastTotal = null;
async function refreshReport(){
  const app = $("app").value.trim() || "app1";
  let r, text;
  try { r = await fetch("/api/report/" + encodeURIComponent(app)); text = await r.text(); } catch(e) { return; }
  if (!r.ok) { return; }
  let d; try { d = JSON.parse(text); } catch(e) { return; }
  $("tTotal").textContent = d.totalUsers ?? 0;
  $("tUnique").textContent = d.uniqueUsers ?? 0;
  $("tMobile").textContent = d.devices?.mobile ?? 0;
  $("tDesktop").textContent = d.devices?.desktop ?? 0;
  const css = getComputedStyle(document.documentElement);
  bars($("evBars"), Object.entries(d.events || {}).sort((a,b)=>b[1]-a[1]), css.getPropertyValue("--s1"));
  bars($("devBars"), [["mobile", d.devices?.mobile ?? 0], ["desktop", d.devices?.desktop ?? 0]], css.getPropertyValue("--s1"));
  if (lastTotal !== null && d.totalUsers > lastTotal) flash("reporter");
  lastTotal = d.totalUsers;
}

/* ---------- actions ---------- */
async function send(body){
  animate(["producer","redis","kafka","consumer","postgres"]);
  let r, text;
  try { r = await fetch("/api/produce", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)}); text = await r.text(); }
  catch(e) { log(false, "send", String(e)); return; }
  const ok = r.ok;
  log(ok, ok ? "sent" : r.status, ok ? `${body.eventType} · ${body.userId} · ${body.deviceType}  →  ${text}` : (text || "HTTP " + r.status + (r.status===401||r.status===403 ? " – token rejected (check Redis keys)" : "")));
  $("note").textContent = ok ? "Producer replied “Request queued”. The Consumer saves it a moment later; the report refreshes every 2 seconds." : "The Producer rejected the event.";
  setTimeout(refreshReport, 600);
}
const pick = a => a[Math.floor(Math.random()*a.length)];
function randomEvent(){
  return {eventType:pick(["login","login","page_view","page_view","purchase","signup","logout"]),
          userId:"u"+(1+Math.floor(Math.random()*8)), userName:pick(["Rakshit","Asha","Dev","Meera","Sam","Lina"]),
          deviceType:Math.random()<.62?"mobile":"desktop", browser:pick(["chrome","safari","firefox","edge"]), timestamp:Date.now()};
}
$("send").onclick = () => send(payload());
$("random").onclick = () => send(randomEvent());
let sim = null;
$("sim").onclick = () => {
  if (sim) { clearInterval(sim); sim = null; $("sim").classList.remove("on"); $("sim").textContent = "Simulate traffic"; return; }
  $("sim").classList.add("on"); $("sim").textContent = "Stop simulation";
  sim = setInterval(() => send(randomEvent()), 900);
};
$("sec").onclick = async () => {
  const other = ($("app").value.trim() === "app2") ? "app1" : "app2";
  animate(["reporter"]);
  const r = await fetch("/api/report/" + other); const text = await r.text();
  const blocked = !r.ok;
  log(blocked, blocked ? "blocked" : "LEAK", `Asked for ${other}'s report with app1's token → HTTP ${r.status} ${text}`);
  $("note").textContent = blocked ? `Security works: app1's token can't read ${other}'s report.` : "Warning: the Reporter returned another app's data.";
};
$("app").addEventListener("change", () => { lastTotal = null; refreshReport(); });

refreshStatus(); refreshReport();
setInterval(refreshStatus, 3000);
setInterval(refreshReport, 2000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print(f"Dashboard running at http://localhost:{PORT}  (Ctrl + C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
