#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""接管用户正在运行的 Chrome（Chrome 144+ autoConnect 通道）。

原理
----
Chrome 144+ 在用户于 `chrome://inspect/#remote-debugging` 显式开启远程调试后，
会在默认 profile 下生成 `DevToolsActivePort` 文件，内容为两行：
    <port>
    /devtools/browser/<browser-id>
读出后拼成 `ws://127.0.0.1:<port>/devtools/browser/<id>` 即可直连。

关键约束
--------
1. **Origin 头必须严格等于 `http://127.0.0.1:<port>`**
   带其它 Origin（http://localhost、chrome://inspect、devtools://devtools 等）
   一律返回 403 Forbidden；完全不带 Origin 则握手挂起直到超时。
   这是本方案最容易踩的坑。
2. **同时只允许一个 autoConnect 客户端**
   上一个连接未释放时，新握手会一直挂起（opening handshake timeout）。
   因此这里用较长间隔多次重试。
3. 无需重启浏览器、无需 --remote-debugging-port，**完全共享登录态**。

用法
----
    python cdp_autoconnect.py pages                    列出所有标签页
    python cdp_autoconnect.py read [URL匹配串]          读取页面内容
    python cdp_autoconnect.py shot 输出.png [URL匹配串]  截图
    python cdp_autoconnect.py eval "JS表达式" [URL匹配串] 执行 JS
    python cdp_autoconnect.py html outer|head|body|sel [URL匹配串] [选择器]
                                                取 HTML 源码（不需截图）
"""
import asyncio, json, sys, os, base64
import websockets


def active_endpoint():
    """从 DevToolsActivePort 读取 (port, browser_path)。未开启则返回 None。

    兼容沙箱环境：Loomy/WorkBuddy 会重定向 LOCALAPPDATA，
    此时按 OPENI_CHROME_USER_DATA 环境变量或真实用户目录兜底。
    """
    dirs = []
    env_dir = os.environ.get('OPENI_CHROME_USER_DATA')
    if env_dir:
        dirs.append(env_dir)
    la = os.environ.get('LOCALAPPDATA')
    if la:
        dirs.append(os.path.join(la, 'Google', 'Chrome', 'User Data'))
    dirs.append(os.path.join(os.path.expanduser('~'), 'AppData', 'Local',
                             'Google', 'Chrome', 'User Data'))
    for d in dirs:
        p = os.path.join(d, 'DevToolsActivePort')
        if not os.path.exists(p):
            continue
        lines = [l.strip() for l in open(p, encoding='utf-8').read().split('\n') if l.strip()]
        if len(lines) >= 2:
            return lines[0], lines[1]
    return None


class CDP:
    """最小 CDP 客户端：支持 sessionId 路由，非响应消息（事件）直接跳过。"""

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


async def connect(retries=10, gap=3.0):
    """连接 autoConnect 端点，带重试以应对前一个连接尚未释放的情况。"""
    ep = active_endpoint()
    if not ep:
        raise RuntimeError(
            "DevToolsActivePort 不存在：请在 Chrome 地址栏打开 "
            "chrome://inspect/#remote-debugging 并开启远程调试")
    port, path = ep
    url = f"ws://127.0.0.1:{port}{path}"
    origin = f"http://127.0.0.1:{port}"   # 必须严格匹配，否则 403
    last = None
    for i in range(retries):
        try:
            ws = await websockets.connect(
                url, origin=origin, open_timeout=6,
                max_size=200 * 1024 * 1024, ping_interval=None)
            return ws, CDP(ws), url
        except Exception as e:
            last = e
            if i < retries - 1:
                await asyncio.sleep(gap)
    raise RuntimeError(
        f"连接失败（重试 {retries} 次）：{last}。"
        f"提示：Chrome 同时只允许一个 autoConnect 客户端，"
        f"请确认没有其它 CDP/MCP 会话正在占用。")


async def pick(c, keyword="openi"):
    """列出页面目标；keyword 非空时只保留 URL 含该串的。"""
    r = await c.send("Target.getTargets")
    pages = [t for t in r["targetInfos"] if t["type"] == "page"]
    if keyword:
        hit = [t for t in pages if keyword in t["url"]]
        if hit:
            pages = hit
    return pages


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pages"
    ws, c, url = await connect()
    try:
        if cmd == "pages":
            pages = await pick(c, "")
            print(json.dumps({
                "ok": True, "endpoint": url, "count": len(pages),
                "pages": [{"title": p.get("title", ""), "url": p["url"]} for p in pages],
            }, ensure_ascii=False, indent=2))
            return

        kw = sys.argv[3] if len(sys.argv) > 3 else "openi"
        pages = await pick(c, kw)
        if not pages:
            print(json.dumps({"ok": False, "error": f"没有匹配 '{kw}' 的页面"},
                             ensure_ascii=False))
            return
        tid = pages[0]["targetId"]
        s = await c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})
        sid = s["sessionId"]

        if cmd == "read":
            res = await c.send("Runtime.evaluate", {"expression": """(()=>{
              const t=document.body?document.body.innerText:'';
              return JSON.stringify({
                url:location.href, title:document.title, textLen:t.length, text:t.slice(0,4000),
                links:[...document.querySelectorAll('a')].filter(a=>a.offsetParent).slice(0,40)
                      .map(a=>((a.innerText||'').trim().slice(0,36))+' -> '+a.getAttribute('href'))
              });})()""", "returnByValue": True}, sid)
            print(json.dumps({"ok": True, "data": json.loads(res["result"]["value"])},
                             ensure_ascii=False, indent=2))

        elif cmd == "shot":
            out = sys.argv[2] if len(sys.argv) > 2 else "autoconnect.png"
            cap = await c.send("Page.captureScreenshot", {"format": "png"}, sid, timeout=15)
            open(out, "wb").write(base64.b64decode(cap["data"]))
            print(json.dumps({"ok": True, "saved": out, "targetId": tid}, ensure_ascii=False))

        elif cmd == "html":
            # 直接取 HTML 源码（不依赖截图）
            mode = sys.argv[2] if len(sys.argv) > 2 else "outer"
            selector = sys.argv[4] if len(sys.argv) > 4 else None
            if mode == "sel":
                if not selector:
                    raise RuntimeError("mode=sel 需要提供选择器作为第4个参数")
                expr = ("(()=>{const el=document.querySelector(%s);"
                        "return el?el.outerHTML:'';})()" % json.dumps(selector))
            elif mode == "head":
                expr = "document.head ? document.head.innerHTML : ''"
            elif mode == "body":
                expr = "document.body ? document.body.innerHTML : ''"
            else:
                expr = "document.documentElement ? document.documentElement.outerHTML : ''"
            html = await c.send("Runtime.evaluate", {
                "expression": expr, "returnByValue": True}, sid)
            val = html["result"].get("value") or ""
            print(json.dumps({"ok": True, "mode": mode, "length": len(val), "html": val},
                             ensure_ascii=False, indent=2))

        elif cmd == "eval":
            res = await c.send("Runtime.evaluate", {
                "expression": sys.argv[2], "returnByValue": True, "awaitPromise": True}, sid)
            print(json.dumps({"ok": True, "result": res["result"].get("value")},
                             ensure_ascii=False, indent=2))
    finally:
        await ws.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print(json.dumps({
            "ok": False, "error": f"{type(e).__name__}: {e}",
            "trace": traceback.format_exc()[-600:],
        }, ensure_ascii=False))
        sys.exit(1)
