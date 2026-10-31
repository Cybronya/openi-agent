#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通过 Chrome DevTools Protocol 读取/操作页面。"""
import asyncio, json, sys, base64
import websockets

PORT = int(sys.argv[3]) if len(sys.argv)>3 else 9222

async def http_json(path):
    import urllib.request
    # 本地 CDP 端点必须绕过系统代理
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:{PORT}{path}", timeout=10) as r:
        return json.loads(r.read().decode())

class CDP:
    def __init__(self, ws):
        self.ws = ws
        self._id = 0
        self._pending = {}
    async def send(self, method, params=None, sessionId=None):
        self._id += 1
        mid = self._id
        msg = {"id": mid, "method": method, "params": params or {}}
        if sessionId:
            msg["sessionId"] = sessionId
        await self.ws.send(json.dumps(msg))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=40)
            data = json.loads(raw)
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError(f"{method}: {data['error']}")
                return data.get("result", {})
            # 忽略事件

async def attach(target_ws):
    ws = await websockets.connect(target_ws, max_size=200*1024*1024, ping_interval=None)
    c = CDP(ws)
    return c, ws

async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "read"

    targets = await http_json("/json/list")
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        print(json.dumps({"error": "no page target"}))
        return

    tgt = None
    for t in pages:
        if "openi" in (t.get("url") or ""):
            tgt = t
            break
    if tgt is None:
        tgt = pages[0]

    c, ws = await attach(tgt["webSocketDebuggerUrl"])
    try:
        await c.send("Page.enable")
        await c.send("Runtime.enable")
        await c.send("DOM.enable")

        if cmd == "read":
            r = await c.send("Runtime.evaluate", {
                "expression": """(() => {
                    const txt = document.body ? document.body.innerText : '';
                    const links = [...document.querySelectorAll('a')].slice(0,60).map(a => (a.innerText||'').trim().slice(0,40) + ' -> ' + a.getAttribute('href'));
                    const btns = [...document.querySelectorAll('button,input[type=submit],input[type=button]')].slice(0,40).map(b => (b.innerText||b.value||'').trim());
                    const inputs = [...document.querySelectorAll('input,textarea,select')].slice(0,40).map(i => (i.tagName+':'+(i.name||i.id||'')+':'+(i.type||'')+':'+(i.placeholder||'')));
                    return JSON.stringify({
                        url: location.href,
                        title: document.title,
                        textLen: txt.length,
                        text: txt.slice(0, 6000),
                        links, btns, inputs
                    });
                })()""",
                "returnByValue": True,
            })
            print(r["result"]["value"])

        elif cmd == "shot":
            r = await c.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
            out = sys.argv[2] if len(sys.argv) > 2 else "shot.png"
            with open(out, "wb") as f:
                f.write(base64.b64decode(r["data"]))
            print("saved", out)

        elif cmd == "eval":
            expr = sys.argv[2]
            r = await c.send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            print(json.dumps(r, ensure_ascii=False)[:20000])

        elif cmd == "click":
            # 点击包含指定文本的元素
            needle = sys.argv[2]
            js = """(() => {
                const els = [...document.querySelectorAll('a,button,span,div,li,td')];
                const el = els.reverse().find(e => (e.innerText||'').trim() === %s && e.offsetParent !== null);
                if (el) { el.click(); return 'clicked: ' + el.innerText.trim(); }
                return 'not found';
            })()""" % json.dumps(needle)
            r = await c.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
            print(r["result"]["value"])

        elif cmd == "nav":
            url = sys.argv[2]
            await c.send("Page.navigate", {"url": url})
            await asyncio.sleep(3)
            print("navigated")

        elif cmd == "list":
            print(json.dumps(targets, ensure_ascii=False, indent=2))
    finally:
        await ws.close()

asyncio.run(main())
