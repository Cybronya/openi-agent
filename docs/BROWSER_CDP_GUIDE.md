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

## 附录：MCP 方案（2026-10-31 新增，推荐）

### Chrome 144+ autoConnect —— 接管用户正在运行的浏览器

这是目前**唯一能直接操作用户已打开页面**的官方方案。

**原理**：Chrome 144+ 新增远程调试开关。用户在 `chrome://inspect/#remote-debugging` 显式开启后，
MCP server 可请求连接**当前活跃的 Chrome 实例**，Chrome 弹窗征求授权，用户点「允许」即接管。

**优点**：
- 不需要重启浏览器
- 不需要指定端口
- **完全共享登录状态** —— 你已登录的页面直接可操作，无需重新登录
- 调试期间 Chrome 顶部显示 "Chrome is being controlled by automated test software" 横幅

**配置**（已写入 `~/.workbuddy/mcp.json`）：
```json
{
  "mcpServers": {
    "chrome-devtools-autoconnect": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect", "--no-usage-statistics", "--no-performance-crux"],
      "env": { "PATH": "F://Program Files//Nodejs;%PATH%" }
    }
  }
}
```

**使用步骤**：
1. 用户在 Chrome 地址栏输入 `chrome://inspect/#remote-debugging`，回车，开启远程调试
2. MCP 发起连接时，Chrome 弹窗 → 点「允许」
3. 之后即可直接操作用户当前标签页

### 手动端口模式（已验证）

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl=http://127.0.0.1:9222", "--no-page-id-routing", "--no-usage-statistics"],
      "env": { "PATH": "F://Program Files//Nodejs;%PATH%" }
    }
  }
}
```

`--no-page-id-routing` 可让工具调用免填 pageId。

### 实测：32 个工具

```
click, close_page, drag, emulate, evaluate_script, fill, fill_form,
get_console_message, get_css_styles, get_network_request, handle_dialog,
hover, lighthouse_audit, list_console_messages, list_network_requests,
list_pages, navigate_page, new_page, performance_analyze_insight,
performance_start_trace, performance_stop_trace, press_key, resize_page,
screencast_start, screencast_stop, select_page, take_heapsnapshot,
take_screenshot, take_snapshot, type_text, upload_file, wait_for
```

### Node.js 环境（本机已配置）

- 安装位置：`F:/Program Files\Nodejs`（v22.14.0）
- 已写入用户级 PATH，`node` / `npm` / `npx` 新终端直接可用
- npm 全局 prefix = `F:/Program Files\Nodejs`
- `chrome-devtools-mcp@latest` 已全局安装
- 下载源：`https://npmmirror.com/mirrors/node/`（国内可用）

---

## 附录二：autoConnect 直连方案（2026-10-31 23:45 实测通过）★推荐

**这是唯一能直接操作「用户正在运行的浏览器」的方案**，且完全共享登录态。

### 原理

Chrome 144+ 在用户于 `chrome://inspect/#remote-debugging` 显式开启远程调试后，
会在默认 profile 生成 `DevToolsActivePort` 文件：

```
64911
/devtools/browser/26bb7c00-91d4-4cbc-bea3-f039f7b25b92
```

读出后拼成 `ws://127.0.0.1:64911/devtools/browser/<id>` 直连即可。

### 两个关键坑（实测踩过）

**坑 1：Origin 头必须严格等于 `http://127.0.0.1:<port>`**

| Origin | 结果 |
|--------|------|
| `http://127.0.0.1:64911` | ✅ 101 Switching Protocols |
| `http://localhost` | ❌ 403 Forbidden |
| `http://localhost:9222` | ❌ 403 Forbidden |
| `chrome://inspect` | ❌ 403 Forbidden |
| `devtools://devtools` | ❌ 403 Forbidden |
| `null` | ❌ 403 Forbidden |
| 不带 Origin | ❌ 握手挂起直到超时 |

**坑 2：同时只允许一个 autoConnect 客户端**
上一个连接未释放时，新握手会一直挂起（`opening handshake timeout`）。
解法：用较长间隔多次重试（见 `tools/cdp_autoconnect.py` 的 `connect()`）。

### 用法

```bash
python tools/cdp_autoconnect.py pages                    # 列出所有标签页
python tools/cdp_autoconnect.py read openi               # 读取页面内容
python tools/cdp_autoconnect.py eval "JS" openi          # 执行 JS
python tools/cdp_autoconnect.py shot out.png openi        # 截图
```

### MCP 配置（已写入 ~/.workbuddy/mcp.json）

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "node",
      "args": [
        "F://Program Files//Nodejs//node_modules//chrome-devtools-mcp//build//src//bin//chrome-devtools-mcp.js",
        "--autoConnect",
        "--userDataDir",
        "C://Users//Administrator//AppData//Local//Google//Chrome//User Data",
        "--no-usage-statistics",
        "--no-performance-crux",
        "--allow-unrestricted-paths"
      ],
      "env": { "PATH": "F://Program Files//Nodejs;%PATH%" }
    }
  }
}
```

**必须用 `node` 直接启动 MCP 入口，不能用 `npx`** —— npx 会把带空格的
`--userDataDir` 路径截断成 `...\Chrome\User`，导致找不到 DevToolsActivePort。

**必须加 `--allow-unrestricted-paths`** —— 否则 MCP 的文件写入工具被限制在
OS 临时目录，无法写入工作区。

**MCP 工具调用需带 `pageId`**（默认开启 page-id-routing），
或加 `--no-page-id-routing` 免除。

### 实测验证结果（2026-10-31 23:50）

通过 autoConnect 读取用户真实登录的 `https://openi.pcl.ac.cn/cloudbrains`：
- 用户名 `cybronya`
- 计算任务表 12 行，含任务类型/状态/算力资源/创建时间/运行时长/项目
- 智算中心：启智混合智算集群（METAX-GPGPU C500）、天数云（ILUVATAR-GPGPU MR-V100）
- 任务名：cybro202610270033988、comfyui_audio、cybro202610030057865、cybro202610020278347
- 截图证据：`docs/screenshots/shot_autoconnect_logged_in.png`

### 三种方案对比

| 方案 | 接管用户浏览器 | 登录态 | 依赖 | 适用 |
|------|--------------|--------|------|------|
| **autoConnect 直连** | ✅ | ✅ 完全共享 | Python + websockets | **首选** |
| MCP autoConnect | ✅ | ✅ 完全共享 | Node + chrome-devtools-mcp | 需要 32 个工具/lighthouse/perf trace 时 |
| 独立实例 + browserUrl | ❌ | 需重登 | 同上 | 隔离测试、CI |

---

## 附录三：常驻守护进程 + HTML 直读（2026-11-01 00:10 落地）

### 为什么需要守护进程

Chrome 的 autoConnect 端点**每次建立新连接都要弹窗请求授权**。
如果每执行一个操作就跑一次脚本 → 用户要反复点「允许」；
用户「一起点了多个确定」会让状态混乱，且上一个连接未释放时新连接直接挂起超时。

**解法：常驻守护进程 —— 一次授权，长期复用。**

守护进程与 Chrome 只建立**一次**连接并长期保持，
后续所有操作通过本地 TCP 端口（默认 8765）发送 JSON 命令，
**不产生新的 Chrome 连接，因此完全不弹窗**。

### 启动

```bash
# 后台常驻（推荐）
python tools/cdp_daemon.py --serve

# 前台（调试用）
python -u tools/cdp_daemon.py --serve
```

启动成功后输出：
```
[daemon] ✅ 已连接 Chrome: ws://127.0.0.1:64911/devtools/browser/<id>
[daemon] 监听 127.0.0.1:8765，后续命令不再触发授权弹窗
```

### 发命令

```bash
python tools/cdp_daemon.py --client '{"cmd":"pages"}'
python tools/cdp_daemon.py --client '{"cmd":"read","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"body","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"sel","selector":"table","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"eval","expr":"document.title","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"shot","out":"a.png","match":"openi"}'
```

也支持管道：`echo '{"cmd":"pages"}' | python tools/cdp_daemon.py --client`

### 命令一览

| cmd | 说明 |
|-----|------|
| `pages` | 列出所有标签页（`match` 留空则不过滤） |
| `read` | 结构化读取：正文 + 链接 + 按钮 + 表单 + **表格（表头+行）** |
| `html` | **取 HTML 源码**，mode = outer / head / body / sel |
| `eval` | 执行任意 JS（支持 awaitPromise） |
| `shot` | 截图 |
| `ping` | 健康检查 |

### HTML 直读（替代截图）

```bash
# 整页源码（实测 cloudbrains 页面 1.8 MB）
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"outer","match":"openi"}'

# 只取 <body> 内容
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"body"}'

# 只取某个选择器（实测 table 1895 字符）
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"sel","selector":"table"}'

# 独立脚本也支持（每次会重新连接 → 会弹窗）
python tools/cdp_autoconnect.py html body openi
```

**HTML 直读比截图好在**：
- 精确拿到属性、class、data-* 等截图里看不到的信息
- 可用 CSS 选择器精准定位片段，不必传输整页
- 体积小（table 片段 1.9 KB vs 整页 1.8 MB）
- 无视觉歧义，解析后可精确定位字段

### 实测数据（2026-11-01 00:12）

- 连续执行 5 条命令：**全部成功，零弹窗** ✓
- `html outer` → 1,801,498 字符完整源码
- `html sel` (table) → 1,895 字符
- `read` → 正文 944 字 / 60 链接 / 5 按钮 / 23 表单 / 5 张表格（含表头与行数据）

### 排障：端口起不来

若 `连接守护进程(端口8765): 10061 拒绝`：
1. 守护进程可能还卡在连接 Chrome 阶段 → 看它的日志输出
2. 可能有旧守护进程残留 → `ps aux | grep cdp_daemon` 清理
3. 端口被占 → `netstat -ano | grep 8765`
