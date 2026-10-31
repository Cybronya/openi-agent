---
name: browser-cdp
description: 通过 Chrome DevTools Protocol 操作网页。适用于需要读取网页内容、点击元素、填写表单、截图、抓取结构化数据、多标签管理的任务。当用户要求"操作网页""读取这个页面""抓取网页数据""截图""测试网页流程"时使用本技能。无需安装 Playwright/Selenium/Node.js，仅需 Python 标准库加 websockets。
---

# Browser CDP

用 Chrome DevTools Protocol (CDP) 直接驱动本机 Chrome。相比模拟点击截图识别，CDP 能直接读 DOM、执行 JS、发带 Cookie 的请求，精度和效率都高一个量级。

## 何时用 / 何时不用

| 需求 | 工具 |
|------|------|
| 静态 HTML、纯文本、markdown | WebFetch（更轻） |
| JSON / REST API | curl / HTTP 客户端 |
| JS 渲染页面、点击、填表、截图、多步流程 | **CDP（本技能）** |
| 需要已登录会话的页面 | CDP + 登录态注入（见下文） |

## 快速开始

### 1. 启动带调试端口的 Chrome

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="C:\Users\<用户>\AppData\Local\Temp\wbchrome" \
  --no-first-run --no-default-browser-check \
  "<目标URL>"
```

**必须同时指定 `--user-data-dir`**，原因见下文「关键限制」。

### 2. 确认通道就绪

```bash
curl -s --noproxy '*' http://127.0.0.1:9222/json/version
```

**必须加 `--noproxy '*'`** —— 本机若设了 `HTTP_PROXY`，访问 127.0.0.1 会返回 502。

### 3. 使用脚本

脚本位于 `scripts/cdp.py`，依赖仅 `websockets`（`pip install websockets`）。

```bash
cd scripts
python cdp.py list                      # 列出所有页面目标
python cdp.py read                      # 读取正文、链接、按钮、表单字段
python cdp.py shot out.png              # 截图
python cdp.py click "手机登录"           # 按可见文本点击元素
python cdp.py nav "https://example.com" # 跳转页面
python cdp.py eval "document.title"     # 执行任意 JS 并返回结果
python cdp.py eval <port> <expr>        # 指定端口（多实例时）
```

`read` 返回 JSON，含 `text`（正文）、`links`（链接及 href）、`btns`（按钮）、`inputs`（表单字段名/类型/placeholder）——**先跑 read 拿到元素结构，再用 click/eval 精确操作**，不要盲猜 CSS 选择器。

### 4. 结构化数据抓取

```bash
python cdp.py eval "
JSON.stringify({
  cards: [...document.querySelectorAll('a[href*=\"/datasets/\"]')].slice(0,8)
    .map(a=>({t:a.innerText.trim(), h:a.getAttribute('href')}))
})"
```

### 5. 表单填写

```javascript
(()=>{
  const inp = [...document.querySelectorAll('input')].find(i=>i.name==='phone_number');
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  setter.call(inp, '13800138000');           // 用原生 setter 才触发框架响应
  inp.dispatchEvent(new Event('input',{bubbles:true}));
  inp.dispatchEvent(new Event('change',{bubbles:true}));
  return inp.value;
})()
```

### 6. 多标签管理

用 browser 级 WebSocket（`/json/version` 的 `webSocketDebuggerUrl`）：
`Target.createTarget` 开新标签，`Target.closeTarget` 关闭。

### 7. 移动端视口

```python
Emulation.setDeviceMetricsOverride
{"width":390,"height":844,"deviceScaleFactor":2,"mobile":True}
```
用完 `Emulation.clearDeviceMetricsOverride` 还原。

## 关键限制（务必先读）

### Chrome 136+ 屏蔽了默认 profile 的调试端口

Google 自 Chrome 136 起做了安全变更：**若 `--user-data-dir` 指向默认数据目录，`--remote-debugging-port` 与 `--remote-debugging-pipe` 会被直接忽略**，CDP 端点根本起不来。

这意味着：
- **无法接入用户日常使用的那个 Chrome**（它启动时没带调试参数，事后也无法补上）
- 想控制「用户正在用的浏览器」，唯一办法是**重启它**并带上 `--user-data-dir` + `--remote-debugging-port`
- 用户问「能不能直接操作我打开的页面」时，答案要如实说明这一限制

官方建议：自动化场景用 Chrome for Testing。

### 登录态无法从默认 profile 复制

- Chrome 156 起 Cookie 用 **app-bound 加密**，主密钥在 `Local State` 的 `app_bound_encrypted_key`，外部无法解密
- 复制 profile 到新目录后，新目录有**不同的加密密钥**，Chrome 读不了原 Cookie
- 复制 `Cookies` 文件 + `Local State` 也不行：Chrome 启动时会校验密钥，不匹配的条目直接丢弃

**唯一可靠解法：让用户在被控实例里登录一次**，或让用户以调试模式重启自己的 Chrome。

### 会话 Cookie 是易失的

`i_like_openi` 这类 session cookie（`is_persistent=0`）会随服务端轮换而失效。即使成功注入 Cookie，服务端也可能已把会话作废——这不是脚本的问题。

## 环境注意事项（Windows）

| 坑 | 现象 | 解法 |
|----|------|------|
| 代理劫持本地请求 | 访问 127.0.0.1:9222 返回 502 | `curl --noproxy '*'`；Python 用 `build_opener(ProxyHandler({}))` |
| PowerShell `Start-Process` 启动的 Chrome 立刻退出 | 端口连不上 | 改用 Bash 后台任务启动 |
| Cookies 库被 Chrome 独占锁 | `cp`/`robocopy /B` 均失败 (error 32) | 建 NTFS 卷影副本后从快照提取：`Win32_ShadowCopy.Create` + `\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\...` |
| 本机无 Node.js | agent-browser 类插件无法用 | 直接用 CDP，不依赖 Node |
| PyPI 下载慢 | `pip install playwright` 超时 | 避开 Playwright，CDP 无需重依赖 |

## 资源占用控制

**每次用完必须关闭实例并删除 profile 目录**，否则会持续堆积：

```bash
# 关闭（先取 /json/version 里的 webSocketDebuggerUrl，用 Target.closeTarget）
# 或直接按 profile 目录筛进程杀：
Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
  Where-Object { $_.CommandLine -like "*wbchrome*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Remove-Item "$env:LOCALAPPDATA\Temp\wbchrome" -Recurse -Force
```

单实例 profile 约 25–160 MB。Chrome 是多进程架构，一个实例通常带 5–10 个子进程，属正常。

## 脚本能力矩阵

| 命令 | 能力 |
|------|------|
| `read` | 正文文本 + 链接 + 按钮 + 表单字段 |
| `shot` | PNG 截图（支持整页 captureBeyondViewport） |
| `click` | 按可见文本定位并点击（自动跳过隐藏元素） |
| `nav` | 页面跳转 |
| `eval` | 执行任意 JS，支持 awaitPromise |
| `list` | 列出全部页面目标（标题/URL/ws 地址） |

## 调试建议

- 先 `read` 再操作，别猜选择器
- 点击后 `sleep 1~2` 再读，Vue/React 需要渲染时间
- 验证状态变化用「读回填值」而不是「看截图」
- 页面跨域 API 用页面内 `fetch(url, {credentials:'include'})`，天然带上 Cookie

---

## ★ 首选：autoConnect 直连（接管用户正在运行的浏览器）

**能直接操作用户已打开的页面，且完全共享登录态。** 这是本技能的推荐路径。

### 前置条件
用户在 Chrome 地址栏打开 `chrome://inspect/#remote-debugging` 并开启远程调试。
开启后，默认 profile 下会生成 `DevToolsActivePort` 文件（两行：port + /devtools/browser/<id>）。

### 直接用脚本
```bash
python tools/cdp_autoconnect.py pages                    # 列出标签页
python tools/cdp_autoconnect.py read openi               # 读页面内容
python tools/cdp_autoconnect.py eval "JS" openi          # 执行 JS
python tools/cdp_autoconnect.py shot out.png openi        # 截图
```

### 两个必踩的坑

**坑 1：Origin 头必须严格等于 `http://127.0.0.1:<port>`**
- ✅ `http://127.0.0.1:64911` → 101 Switching Protocols
- ❌ `http://localhost` / `chrome://inspect` / `devtools://devtools` / `null` → 403 Forbidden
- ❌ 完全不带 Origin → 握手挂起直到超时

**坑 2：同时只允许一个 autoConnect 客户端**
上一连接未释放时新握手会一直挂起（`opening handshake timeout`）。
→ 必须做长间隔多次重试；跑脚本前先确保没有别的 CDP/MCP 会话占用。

### 若用 MCP
- **必须用 `node` 直接启动**，不能用 `npx`（npx 会把带空格的 `--userDataDir` 截断）
- **必须加 `--allow-unrestricted-paths`**（否则文件写入被限制在 OS 临时目录）
- 工具调用需带 `pageId`，或加 `--no-page-id-routing` 免除
- `Page.captureScreenshot` 可能超时 → 用 MCP `take_screenshot` 走 base64 返回更可靠

---

## ★★★ 首选：常驻守护进程（零弹窗，2026-11-01 落地）

**用户明确反馈过痛点：每次申请控制都要点确定，多个弹窗一起点会导致超时。**
根因是 autoConnect 端点每建一个新连接都要弹窗授权。

**解法：守护进程与 Chrome 只建立一次连接并长期保持，后续操作走本地 TCP 端口。**

```bash
# 启动（后台常驻，一次授权）
python tools/cdp_daemon.py --serve

# 发命令（不弹窗）
python tools/cdp_daemon.py --client '{"cmd":"pages"}'
python tools/cdp_daemon.py --client '{"cmd":"read","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"outer"}'
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"sel","selector":"table"}'
python tools/cdp_daemon.py --client '{"cmd":"eval","expr":"document.title"}'
```

命令：`pages` / `read` / `html` / `eval` / `shot` / `ping`
端口默认 8765，可用 `--port` 改。

### HTML 直读（用户明确要求，替代截图）

| mode | 内容 | 实测体积 |
|------|------|---------|
| `outer` | 整页 outerHTML | 1.8 MB |
| `body` | body.innerHTML | 1.78 MB |
| `head` | head.innerHTML | — |
| `sel` | 选择器命中的 outerHTML | table 1.9 KB |

比截图好在：能拿属性/class/data-*；可选择器精准取片段；体积小两个数量级；无视觉歧义。

### 排障
- 端口 10061 拒绝 → 守护进程还卡在连接阶段，查其日志；或清理旧进程 `ps aux | grep cdp_daemon`
- 端口被占 → `netstat -ano | grep 8765`

---

## 在 JupyterLab 里执行代码（实测 2026-11-01）

### 定位 Launcher 卡片
```javascript
// 同名元素有两个：top 小的是 Notebook 区，top 大的是 Console 区
[...document.querySelectorAll('p')].filter(e=>e.innerText.trim()==='Python 3 (ipykernel)' && e.offsetParent!==null)
```
点 Notebook 区的那个 → 新建 `.ipynb`，URL 变 `/lab/tree/xxx.ipynb`，内核自动连接。

### 写入代码
```javascript
const cm = document.querySelector('.jp-Notebook .CodeMirror').CodeMirror;
cm.setValue("print('hi')");
```

### 执行代码 —— 不要用合成键盘事件
CodeMirror 6 **不响应** `dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',shiftKey:true}))`。
正确做法是点工具栏按钮：
```javascript
const btn = [...document.querySelectorAll('button')]
  .find(b => (b.getAttribute('aria-label')||b.title||'')==='Run the selected cells and advance');
btn.click();
```

### 读取输出
```javascript
[...document.querySelectorAll('.jp-OutputArea-output')].map(e=>e.innerText.trim()).filter(Boolean)
```

### ⚠️ 引号铁律
`eval` 的 JS 表达式**内部一律用单引号**。双引号会被 shell 吞掉，
表现为 `JSONDecodeError` 或表达式返回 null。
批量测试多条命令时的正确写法：
```bash
python tools/cdp_daemon.py --client "{\"cmd\":\"eval\",\"expr\":\"$JS_WITH_SINGLE_QUOTES\"}"
```

---

## JupyterLab 文件操作（实测 2026-11-01）

### 定位文件项
```javascript
// 名称在 .jp-DirListing-itemText 里（不是 .jp-DirListing-itemName）
[...document.querySelectorAll('.jp-DirListing-item')].filter(e=>e.offsetParent!==null)
```
判别目录/文件：title 属性里有 `Size:` 是文件，只有 `Path:` 是目录。

### 双击打开文件夹
派发**两轮** mousedown/mouseup/click（第二轮 `detail: 2`）+ 一个 `dblclick`：
```javascript
const target = items.find(e=>e.innerText.includes('目标名'));
const el = target.querySelector('.jp-DirListing-itemText');
const o = {bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,view:window};
el.dispatchEvent(new MouseEvent('mousedown',{...o,detail:1}));
el.dispatchEvent(new MouseEvent('mouseup',  {...o,detail:1}));
el.dispatchEvent(new MouseEvent('click',  {...o,detail:1}));
el.dispatchEvent(new MouseEvent('mousedown',{...o,detail:2}));
el.dispatchEvent(new MouseEvent('mouseup',  {...o,detail:2}));
el.dispatchEvent(new MouseEvent('click',  {...o,detail:2}));
el.dispatchEvent(new MouseEvent('dblclick',{...o,detail:2}));
```

### 读写文件 —— JupyterLab REST API
```javascript
const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
const r = await fetch(base + '/api/contents/' + path, {credentials:'include'});
const j = await r.json();   // {content, size, type}
```
base 例：`https://mlunotebook.openi.org.cn/notebook_<hash>_task0`

### ⚠️ async 求值陷阱
守护进程的 `eval` 对 async 函数返回 null。**必须整体用 JSON.stringify 包起来**：
```javascript
(async () => { ...; return JSON.stringify(out); })()
```

### ★ 用文件传 JS，别用命令行传
复杂表达式经 shell 传参时双引号会被吞（JSONDecodeError / 返回 null）。
根治：`tools/jlab.py` 从 .js 文件读入再执行。
```bash
python tools/jlab.py script.js [match串]
```

---

## 在云端容器里执行 shell 命令（内核 WebSocket 通道，实测 2026-11-01）

### 为什么必须用 WebSocket
| 方式 | 结果 |
|------|------|
| `POST /api/kernels/<id>/execute` | ❌ 该部署返回 404（端点被禁用） |
| UI 点 Run 按钮 / 合成 KeyboardEvent | ❌ 不可靠（CodeMirror 6 + JupyterLab 事件体系特殊） |
| `Input.dispatchKeyEvent` rawKeyDown | ❌ Shift+Enter 被吞或清空 cell |
| **内核 WebSocket** | ✅ 稳定，能拿到 stdout/stderr/退出码 |

### ⚠️ 头号坑：Runtime.evaluate 上下文隔离
**每次 eval 都是独立上下文，`window.__xxx` 变量不跨调用保留！**
→ 「建 WS → 发 execute_request → 收输出」必须**在同一个 JS 表达式内用 Promise 完成**。

```javascript
(async () => {
  const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
  const kr = await fetch(base + '/api/kernels', {credentials:'include'});
  const kid = (await kr.json())[0].id;
  const wsUrl = (location.protocol==='https:'?'wss:':'ws:') + '//' + location.host +
                base.replace(/^https?:\/\/[^/]+/,'') + '/api/kernels/' + kid + '/channels';
  const out = [];
  const res = await new Promise(resolve => {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => ws.send(JSON.stringify({
      header:{msg_id:'K'+Date.now(),msg_type:'execute_request',username:'user',session:'s'},
      parent_header:{}, metadata:{},
      content:{code: PYCODE, silent:false, store_history:false,
               user_expressions:{}, allow_stdin:false, stop_on_error:false}}));
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data), mt = m.header && m.header.msg_type, c = m.content||{};
      if (mt==='stream') out.push(c.text||'');
      else if (mt==='error') out.push('[ERROR] '+(c.ename||'')+': '+(c.evalue||''));
      else if (mt==='execute_reply') resolve('OK');
    };
    ws.onerror = () => resolve('WS_ERROR');
  });
  return res + '\n' + out.join('');
})()
```

### 工具
```bash
python tools/cloud_shell.py "<命令>"
python tools/cloud_shell.py --file <命令文件> [超时秒]
```
底层：`tools/jlab.py`（从 .js 文件读 JS 执行，避开 shell 引号地狱）

### JupyterLab REST API（读写文件）
```javascript
const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
const r = await fetch(base + '/api/contents/' + path, {credentials:'include'});
const j = await r.json();   // {content, size, type}
```
- `POST` 需要 `_xsrf` token（从 `document.cookie` 取）+ `X-XSRFToken` 头
- `GET /api/terminals` 可开终端（POST）
- `GET /api/kernels` 列内核（state / connections）

### pip 离线安装要点（sdist 必踩）
```bash
# sdist（如 fairscale / antlr4-python3-runtime）在 --no-index 下无法装
# 因为 pip 建隔离环境时要下载 setuptools → 必须加 --no-build-isolation
python -m pip install --no-index --find-links packages/batch2 --no-build-isolation --no-deps <包名>
# 另外：subprocess(shell=True) 走 /bin/sh，不支持 <(...) 进程替换 → 先落地临时清单文件
```
