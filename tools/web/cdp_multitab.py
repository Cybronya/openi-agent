import asyncio, json, sys, base64, urllib.request
import websockets
PORT=9222
def http_json(p):
    op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open(f"http://127.0.0.1:{PORT}{p}",timeout=10) as r: return json.loads(r.read().decode())

async def main():
    # 用 browser 级 websocket 新建标签页
    ver=await asyncio.get_event_loop().run_in_executor(None, lambda: http_json("/json/version"))
    bws=ver["webSocketDebuggerUrl"]
    async with websockets.connect(bws,max_size=100*1024*1024,ping_interval=None) as ws:
        await ws.send(json.dumps({"id":1,"method":"Target.createTarget","params":{"url":"https://openi.pcl.ac.cn/modelbase"}}))
        while True:
            d=json.loads(await ws.recv())
            if d.get("id")==1:
                tid=d["result"]["targetId"]; break
        await asyncio.sleep(4)
        # 列出所有页面
        tg=await asyncio.get_event_loop().run_in_executor(None, lambda: http_json("/json/list"))
        pages=[{"title":t.get("title"),"url":t.get("url")} for t in tg if t.get("type")=="page"]
        print("TABS:",json.dumps(pages,ensure_ascii=False,indent=2))
        # 关闭刚才创建的
        async with websockets.connect(bws,ping_interval=None) as ws2:
            await ws2.send(json.dumps({"id":2,"method":"Target.closeTarget","params":{"targetId":tid}}))
asyncio.run(main())
