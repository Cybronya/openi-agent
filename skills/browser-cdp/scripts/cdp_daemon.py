#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CDP 守护进程 —— 一次授权，长期复用。

问题背景
--------
Chrome 的 autoConnect 端点有两个约束：
  1. 每次建立新连接都要弹窗请求授权（用户点「允许」）
  2. 同时只允许一个客户端

若每次操作都跑一次脚本 → 反复弹窗；上一个连接未释放时新连接还会挂起超时。
用户「一起点了多个确定」反而让状态更乱。

解决
----
本脚本作为常驻服务，只与 Chrome 建立 **一次** 连接并长期保持。
后续所有操作通过本地 TCP 端口（默认 8765）发送 JSON 命令给它执行，
**不产生新的 Chrome 连接，因此不再弹窗**。

用法
----
启动服务（后台常驻）:
    python cdp_daemon.py --serve

发送命令:
    echo '{"cmd":"pages"}'             | python cdp_daemon.py --client
    echo '{"cmd":"read","match":"openi"}'   | python cdp_daemon.py --client
    echo '{"cmd":"html","mode":"body"}'      | python cdp_daemon.py --client
    echo '{"cmd":"eval","expr":"1+1"}'       | python cdp_daemon.py --client
    echo '{"cmd":"shot","out":"a.png"}'      | python cdp_daemon.py --client

也支持把整段 JSON 作为命令行参数传入（Windows 下更方便）:
    python cdp_daemon.py --client '{"cmd":"pages"}'

返回 JSON。
"""
import asyncio, json, sys, os, base64, socket, argparse

DEFAULT_PORT = 8765


def active_endpoint():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    p = os.path.join(base, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort')
    if not os.path.exists(p):
        return None
    lines = [l.strip() for l in open(p, encoding='utf-8').read().split('\n') if l.strip()]
    if len(lines) < 2:
        return None
    return lines[0], lines[1]


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self._id = 0

    async def send(self, method, params=None, sid=None, timeout=30):
        self._id += 1
        mid = self._id
        msg = {"id": mid, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        await self.ws.send(json.dumps(msg))
        while True:
            data = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=timeout))
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError(f"{method}: {data['error']}")
                return data.get("result", {})


class Session:
    """封装已连接的浏览器实例。"""

    def __init__(self, ws, cdp):
        self.ws = ws
        self.cdp = cdp
        self.lock = asyncio.Lock()

    async def pages(self, keyword=""):
        r = await self.cdp.send("Target.getTargets")
        pages = [t for t in r["targetInfos"] if t["type"] == "page"]
        if keyword:
            hit = [t for t in pages if keyword in t["url"]]
            if hit:
                pages = hit
        return pages

    async def attach(self, keyword="openi"):
        pages = await self.pages(keyword)
        if not pages:
            raise RuntimeError(f"没有匹配 '{keyword}' 的页面")
        tid = pages[0]["targetId"]
        s = await self.cdp.send("Target.attachToTarget", {"targetId": tid, "flatten": True})
        return tid, s["sessionId"]

    async def evaluate(self, expr, keyword="openi"):
        tid, sid = await self.attach(keyword)
        res = await self.cdp.send("Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": True}, sid)
        return res["result"].get("value")

    async def read(self, keyword="openi"):
        """结构化读取：正文 + 链接 + 按钮 + 表单 + 表格。"""
        expr = r"""(()=>{
          const t=document.body?document.body.innerText:'';
          const vis=a=>a.offsetParent!==null;
          const clean=s=>(s||'').trim().replace(/\s+/g,' ');
          return JSON.stringify({
            url:location.href, title:document.title, textLen:t.length, text:t.slice(0,6000),
            links:[...document.querySelectorAll('a')].filter(vis).slice(0,60)
                  .map(a=>clean(a.innerText).slice(0,40)+' -> '+a.getAttribute('href')),
            buttons:[...document.querySelectorAll('button')].filter(vis).slice(0,40)
                  .map(b=>clean(b.innerText)||String(b.className).slice(0,30)),
            inputs:[...document.querySelectorAll('input,textarea,select')].filter(vis).slice(0,40)
                  .map(i=>i.tagName+':'+(i.name||i.id||'')+':'+(i.type||'')+':'+(i.placeholder||'')),
            tables:[...document.querySelectorAll('table')].slice(0,5).map(tb=>({
              headers:[...tb.querySelectorAll('thead th')].map(th=>clean(th.innerText)),
              rows:[...tb.querySelectorAll('tbody tr')].slice(0,30)
                   .map(r=>[...r.querySelectorAll('td')].map(c=>clean(c.innerText).slice(0,40)))
            }))
          });})()"""
        return json.loads(await self.evaluate(expr, keyword))

    async def html(self, keyword="openi", mode="outer", selector=None):
        """取 HTML 源码。mode: outer / head / body / sel"""
        if mode == "sel":
            if not selector:
                raise RuntimeError("mode=sel 需要提供 selector")
            expr = ("(()=>{const el=document.querySelector(%s);"
                    "return el?el.outerHTML:'';})()" % json.dumps(selector))
        elif mode == "head":
            expr = "document.head ? document.head.innerHTML : ''"
        elif mode == "body":
            expr = "document.body ? document.body.innerHTML : ''"
        else:
            expr = "document.documentElement ? document.documentElement.outerHTML : ''"
        return await self.evaluate(expr, keyword)

    async def shot(self, out, keyword="openi"):
        tid, sid = await self.attach(keyword)
        cap = await self.cdp.send("Page.captureScreenshot", {"format": "png"}, sid, timeout=20)
        open(out, "wb").write(base64.b64decode(cap["data"]))
        return out

    async def new_tab(self, url):
        """用 CDP 直接开新标签页（绕过 window.open 的弹窗拦截）。"""
        r = await self.cdp.send("Target.createTarget", {"url": url})
        return r["targetId"]

    async def close_tab(self, url_part):
        r = await self.cdp.send("Target.getTargets")
        hit = [t for t in r["targetInfos"]
               if t["type"] == "page" and url_part in t["url"]]
        if not hit:
            raise RuntimeError(f"没有匹配 '{url_part}' 的标签页")
        await self.cdp.send("Target.closeTarget", {"targetId": hit[0]["targetId"]})
        return hit[0]["url"]

    async def dispatch(self, req):
        cmd = req.get("cmd", "")
        kw = req.get("match", "openi")
        if cmd == "pages":
            ps = await self.pages(req.get("match", ""))
            return {"ok": True, "count": len(ps),
                    "pages": [{"title": p.get("title", ""), "url": p["url"]} for p in ps]}
        if cmd == "newtab":
            tid = await self.new_tab(req.get("url", "https://openi.pcl.ac.cn/cloudbrains"))
            return {"ok": True, "targetId": tid, "url": req.get("url")}
        if cmd == "closetab":
            return {"ok": True, "closed": await self.close_tab(kw)}
        if cmd == "read":
            return {"ok": True, "data": await self.read(kw)}
        if cmd == "html":
            html = await self.html(kw, req.get("mode", "outer"), req.get("selector"))
            return {"ok": True, "mode": req.get("mode", "outer"),
                    "length": len(html), "html": html}
        if cmd == "eval":
            return {"ok": True, "result": await self.evaluate(req.get("expr", ""), kw)}
        if cmd == "shot":
            return {"ok": True, "saved": await self.shot(req.get("out", "shot.png"), kw)}
        if cmd == "ping":
            return {"ok": True, "pong": True}
        raise RuntimeError(f"未知命令: {cmd}")


async def connect(retries=12, gap=3.0):
    ep = active_endpoint()
    if not ep:
        raise RuntimeError(
            "DevToolsActivePort 不存在：请在 Chrome 打开 "
            "chrome://inspect/#remote-debugging 并开启远程调试")
    port, path = ep
    url = f"ws://127.0.0.1:{port}{path}"
    origin = f"http://127.0.0.1:{port}"
    last = None
    for i in range(retries):
        try:
            import websockets
            ws = await websockets.connect(url, origin=origin, open_timeout=6,
                                          max_size=200 * 1024 * 1024, ping_interval=None)
            return Session(ws, CDP(ws)), url
        except Exception as e:
            last = e
            if i < retries - 1:
                await asyncio.sleep(gap)
    raise RuntimeError(f"连接失败（重试 {retries} 次）：{last}")


async def serve_main(port):
    sess, url = await connect()
    print(f"[daemon] ✅ 已连接 Chrome: {url}", flush=True)
    print(f"[daemon] 监听 127.0.0.1:{port}，后续命令不再触发授权弹窗", flush=True)

    async def handle(reader, writer):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=300)
            if not line:
                writer.close(); return
            req = json.loads(line.decode('utf-8', 'ignore').strip() or '{}')
            async with sess.lock:
                out = await sess.dispatch(req)
        except Exception as e:
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        writer.write((json.dumps(out, ensure_ascii=False) + '\n').encode('utf-8'))
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, '127.0.0.1', port)
    async with server:
        await server.serve_forever()


def client_main(port, payload):
    try:
        s = socket.create_connection(('127.0.0.1', port), timeout=120)
        s.sendall((payload + '\n').encode('utf-8'))
        buf = b''
        while b'\n' not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        s.close()
        print(buf.decode('utf-8', 'ignore').strip())
    except Exception as e:
        print(json.dumps({"ok": False,
                          "error": f"无法连接守护进程(端口{port}): {e}"}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CDP 守护进程")
    ap.add_argument("--serve", action="store_true", help="以守护服务模式启动")
    ap.add_argument("--client", nargs="?", const="", help="客户端模式：发送命令")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()

    if args.client is not None:
        payload = args.client or sys.stdin.read().strip() or '{"cmd":"pages"}'
        client_main(args.port, payload)
    else:
        try:
            asyncio.run(serve_main(args.port))
        except KeyboardInterrupt:
            pass
