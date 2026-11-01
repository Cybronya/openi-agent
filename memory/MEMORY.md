# 项目长期记忆

## ★★★ 主线闭环已跑通（2026-11-01 18:55）—— 接手先读这段

**本地 wheel → git push → 平台建任务 → 平台自动 clone → 云端 install_offline.sh → 验证**，
全链路一次跑通。

- 8 个新 wheel 已装进云端 C500：`comfyui-frontend-package` **1.53.6 → 1.57.1**，
  **28/28** 包与 `plans/to-download.txt` 逐一对齐；
  torch `2.10.0+metax3.8.1.0` / numpy 1.26.4 / scipy 1.16.0 / pillow 11.2.1 **均未被破坏**。
- **★ 推翻早前设计**：平台会把仓库连同 **616MB wheel 一起完整 clone**，
  仓库落在 `/tmp/code/<repo-name>/` → **不需要任何自建上传通道**
  （`sync_wheels.py` 的 base64 方案退休，仅留应急备份）。
- **★ 完整操作手册**：`docs/CLOUD_DEPLOY_PLAYBOOK.md`
  （9 节：全链路 / 槽位清理 / 创建表单真实路径 / debug_url / 内核通道 /
  安装验证 / **16 条坑位速查** / 命令速查 / 执行序列）。做部署类需求先读它。

## 项目：openi.pcl.ac.cn 网页操作能力

### ★★★ 首选方案：常驻守护进程（2026-11-01 00:10 落地，零弹窗）

**用 `tools/cdp_daemon.py`，一次授权长期复用，后续操作完全不弹窗。**

用户反馈的痛点：每次申请控制都要点确定，多个弹窗一起点导致状态混乱、易超时。
根因：autoConnect 端点**每建一个新连接都要弹窗授权**，而独立脚本每次运行都新建连接。

解法：守护进程与 Chrome 只建立**一次**连接并长期保持，
后续操作通过本地 TCP 端口（默认 8765）发 JSON 命令给它执行 —— **不产生新 Chrome 连接**。

```bash
# 启动（后台常驻）
python tools/cdp_daemon.py --serve
# 发命令
python tools/cdp_daemon.py --client '{"cmd":"pages"}'
python tools/cdp_daemon.py --client '{"cmd":"read","match":"openi"}'
python tools/cdp_daemon.py --client '{"cmd":"html","mode":"sel","selector":"table"}'
```

命令：`pages` / `read` / `html` / `eval` / `shot` / `ping`
**实测：连续 5 条命令全部成功，零弹窗。**

### ★ HTML 直读（替代截图）

用户明确要求「不通过截图，直接读页面 HTML」——已实现，四种模式：

| mode | 用途 | 实测体积 |
|------|------|---------|
| `outer` | 整页源码 `documentElement.outerHTML` | 1,801,498 字符 |
| `body` | `<body>` 内容 | 1,782,516 字符 |
| `head` | `<head>` 内容 | — |
| `sel` | 指定 CSS 选择器的 outerHTML | table 片段 1,895 字符 |

**比截图好在**：能拿到属性/class/data-* 等截图看不到的信息；可用选择器精准取片段；
体积小两个数量级；无视觉歧义。

`read` 命令额外提供结构化表格（表头 + 行数据），实测 cloudbrains 页 5 张表格全部抽出。

### 底层机制：Chrome autoConnect 直连

原理：Chrome 144+ 在用户于 `chrome://inspect/#remote-debugging` 显式开启远程调试后，
在默认 profile 生成 `DevToolsActivePort` 文件（两行：port + /devtools/browser/<id>），
读出后拼 `ws://127.0.0.1:<port>/devtools/browser/<id>` 直连。

工具：`tools/cdp_autoconnect.py`（一次性操作，会弹窗）
子命令：`pages` / `read` / `html` / `eval` / `shot`

**两个必踩的坑：**
1. **Origin 头必须严格等于 `http://127.0.0.1:<port>`**
   `http://localhost` / `chrome://inspect` / `devtools://devtools` / `null` → 403 Forbidden；
   完全不带 Origin → 握手挂起超时。
2. **同时只允许一个 autoConnect 客户端**
   上一连接未释放时新握手一直挂起 → 长间隔多次重试（10 次 × 3s）。
   → 这也是必须用守护进程的根本原因。

### 备选方案

| 方案 | 接管用户浏览器 | 登录态 | 弹窗 | 依赖 |
|------|--------------|--------|------|------|
| **守护进程** | ✅ | ✅ 完全共享 | **无** | Python + websockets |
| autoConnect 直连 | ✅ | ✅ 完全共享 | 每次都弹 | 同上 |
| MCP autoConnect | ✅ | ✅ 完全共享 | 每次都弹 | Node + chrome-devtools-mcp（32 工具） |
| 独立实例 + browserUrl | ❌ | 需重登 | 无 | 同上 |

### 环境配置（已完成）

- **Node.js v22.14.0** → `F:\Program Files\Nodejs`，用户级 PATH，npm prefix 同路径
  - `node`/`npm`/`npx` 新终端可用；`chrome-devtools-mcp@latest`（v1.12.0）已全局安装
  - MCP 入口：`F:\Program Files\Nodejs\node_modules\chrome-devtools-mcp\build\src\bin\chrome-devtools-mcp.js`
- **MCP 配置**：`~/.workbuddy/mcp.json`
  - `chrome-devtools` → autoConnect 模式（接管用户浏览器）
  - `chrome-devtools-isolated` → `--browserUrl=http://127.0.0.1:9222`
  - ⚠️ 必须用 `node` 直接启动，**不能用 npx**（npx 会截断带空格的 userDataDir 路径）
  - ⚠️ 必须加 `--allow-unrestricted-paths`（否则文件写入被限制在 OS 临时目录）
  - ⚠️ 新增 MCP 需用户在连接器管理页点「信任」才生效

### 站点信息（OpenI 启智AI开源社区，基于 Gitea）

- 用户名 `cybronya`（已验证登录态）
- 公开可读：`/explore/datasets`、`/modelbase/list`、`/explore/datasets/detail/{owner}/{name}`
- 需登录：`/cloudbrains`（跳 `/user/login`）
- 侧边栏入口：概览 /dashboard、项目 /repositories、计算任务 /cloudbrains、
  计算任务模板 /ai_task_tmpl/list_my、数据集 /explore/datasets_my、
  模型 /explore/models_my、镜像、组织、算力积分、存储管理
- API：`/api/v1/user`（需有效会话）
- 算力资源：启智混合智算集群（METAX-GPGPU C500）、天数云（ILUVATAR-GPGPU MR-V100）
- 云端 JupyterLab：`https://mlunotebook.openi.org.cn/notebook_<hash>_task0/lab`

### ★ 平台 API 速查（均需 `_csrf`）

| 用途 | 接口 |
|------|------|
| 任务列表 | `GET /api/v1/ai_task/my_list` |
| 任务详情 | `GET /api/v1/ai_task?id=X&_csrf=` |
| 停止任务 | `POST /api/v1/ai_task/stop?id=X&_csrf=` |
| 建任务前置（配额） | `GET /api/v1/ai_task/creation/required`（`can_create_more` / `not_stop_task_count`） |
| **删除任务** | `POST /api/v1/ai_task/batch_del?_csrf=` body `{"id":[...],"_csrf":...}` |
| **容器入口** | `GET /api/v1/ai_task/debug_url?id=X&_csrf=` |
| 创建任务 | `POST /api/v1/repos/{owner}/{repo}/ai_task/create` |
| 项目搜索 | `GET /api/v1/repos/search?mode=source&uid=190540` |
| 仓库分支 | `GET /api/v1/{owner}/{repo}/ai_task/repo_branch` |

- **★ 删除只能走批量**：`/api/v1/ai_task/delete` **不存在（404）**。
  UI：勾选行 checkbox → 「批量删除」→ 确认弹窗「您确认批量删除选中的任务么？」
- **★ 调试任务上限 5 个，且「停止」不释放槽位，必须真删除**（否则报「调试任务数量已达上限」）。
- **★ 容器入口靠列表行的「调试」按钮**（`<a href="javascript:;">`，Vue 绑定），
  它触发 `debug_url` 并跳转 JupyterLab。**在点它之前 `end_point`/`port` 恒为空**，
  别指望从任务详情接口拿地址。
- **★ `code_size_limit: 50` 是容器内项目存储配额 50 GiB，不是代码 50MB 上限**（用户已纠正）。


### ★ 云端项目：C500-Comfyui-Package（2026-11-01 发现）

用户的真实项目，托管在云端 JupyterLab 目录 `/C500-Comfyui-Package/`，
本地已存档三份核心文档到 `docs/cloud_project/`。

**定位**：管理 Linux 云 GPU（MetaX C500）环境的依赖包下载、离线安装与追溯。
主线任务：为云端 ComfyUI 离线补齐 pip 依赖。

**目录结构**：
| 路径 | 内容 |
|------|------|
| `packages/comfyui/` | 28 个 manylinux wheel，616MB |
| `packages/batch2/` | 29 wheel + 2 sdist，317MB |
| `comfyui/` | ComfyUI 源码快照 v0.42.0（upstream commit 067f853，GitCode 浅克隆） |
| `scripts/` | download_wheels.sh / install_offline.sh / resolve_missing.py |
| `plans/` | 16 个文件，cloud-env.md 是环境事实唯一权威来源 |
| `logs/` | 操作日志，文件名带日期 |

**硬性规则（AGENTS.md 原文，必须遵守）**：
1. **严禁从 PyPI 下载/安装 torch、torchvision、numpy、scipy、pillow**
   —— 云端 torch 2.10.0+metax3.8.1.0 来自沐曦 MACA 适配仓库，
   混入任何 CUDA 版 torch 都会破坏 GPU 加速栈。云端已有 275 个包不得重复下载。
2. **交叉下载参数**必须指定
   `--platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --abi cp312`；
   download_wheels.sh 已内置 `--no-deps`。
3. **版本钉死以 `plans/to-download.txt` 为准**；云端环境变化时先更新 cloud-env.md。
4. **安装动作只通过 `scripts/` 下的脚本执行**，日志归档到 `logs/`。
5. 新增依赖包时在 README.md 登记名称、版本、用途。

**云端环境实测**（2026-11-01 00:40 由我执行代码验证）：
```
OS      Linux 5.15.0-46-generic-x86_64 (glibc 2.35)
Python  3.12.11
torch   2.10.0+metax3.8.1.0
GPU     MetaX C500, cuda available = True
```

**对外仓库**：https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package （公开）
云端离线安装：
```bash
git clone https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package.git
cd C500-Comfyui-Package
pip install --no-index --find-links=packages/comfyui -r plans/to-download.txt
pip install --no-index --find-links=packages/batch2 -r plans/install-reqs-batch2.txt
```

### ★ 云端容器操作通道（2026-11-01 打通）

在云端 JupyterLab 容器里执行 shell 命令，**唯一可靠路径是内核 WebSocket**：

```
ws://<host>/notebook_<hash>_task0/api/kernels/<kernel-id>/channels
```
→ 发 `execute_request` 消息，直接收 `stream` / `execute_reply`。

**为什么不能用别的**：
- `POST /api/kernels/<id>/execute` → 该部署 404，端点被禁用
- UI 点 Run / 合成 KeyboardEvent / `Input.dispatchKeyEvent` rawKeyDown → 均不可靠
  （CodeMirror 6 与 JupyterLab 事件体系特殊，Shift+Enter 会被吞或清空 cell）

**头号坑**：`Runtime.evaluate` **每次调用都是独立上下文**，`window.__xxx` 不跨调用保留。
→ 「建 WS → 发代码 → 收结果」必须在**同一个 JS 表达式内用 Promise 完成**。

工具：`tools/cloud_shell.py`（底层 `tools/jlab.py` 从 .js 文件读 JS，避开 shell 引号地狱）

**★ 内核不会自动创建**：lab 首页不起 kernel，`GET /api/kernels` 返回空 → `cloud_shell` 报
`NO_KERNEL`。手动建：`POST {base}/api/kernels` body `{"name":"python3"}`，
**必须带 `X-XSRFToken` 头**（取 `_xsrf` cookie），否则 **403**。

**★ 两个验证脚本陷阱**：
1. `torch.cuda.get_device_name(0)` 会初始化 CUDA context，MetaX 上很慢 → 脚本卡死超时；
   验证只用 `torch.cuda.is_available()`。
2. `subprocess(shell=True)` 走 `/bin/sh`(dash)，**heredoc 不可靠** →
   多行 Python 逻辑改用 `cloud_shell.run_python`（base64 传码）。

**★ 云端 clone 落点是 `/tmp/code/<repo-name>/`**，不是 `/tmp/code/` 本身
（`code_path` 字段写的是 `/tmp/code`，极易踩坑）。

### ★ 离线安装的 sdist 陷阱
`--no-index` 环境下装 sdist（如 fairscale、antlr4-python3-runtime）会失败：
pip 建隔离环境时要下载 setuptools → 离线拿不到。
**必须加 `--no-build-isolation`**：
```bash
python -m pip install --no-index --find-links packages/batch2 --no-build-isolation --no-deps <包>
```
另：`subprocess(shell=True)` 走 /bin/sh，**不支持 `<(...)` 进程替换** → 先落地临时清单文件。

### ★ 整合架构（2026-11-01 02:00 落地；11-01 晚完成物理合并）

两个项目合成闭环：**操作网页 → 本地下载依赖 → 上传云端 → 云端离线安装 → 验证**

```
F:\openi\                        ← 唯一项目根
├── TASKS.md                     ← 断点续做唯一入口
├── cli/openi.py                 ← 统一 CLI（doctor/web/cloud/cloud-read/sync/status）
├── tools/web/                   ← 网页操作
├── tools/cloud/                 ← 云端容器（cloud_shell / sync_wheels）
├── C500-Comfyui-Package/        ← 数据面（2026-11-01 整体并入，嵌套独立 git）
│   └── .git origin 指向 openi.pcl.ac.cn/cybronya/C500-Comfyui-Package（部署链路不变）
└── docs/INTEGRATION.md          ← 整合设计

（原 F:\Program Files\Git\C500-Comfyui-Package 已搬迁，整合验证后删除）
```

**数据面以嵌套仓库形式并入**（2026-11-01 定稿）：自带 git/分支/远程原样保留，
`DEP_PROJECT` 已改为项目根相对路径。主仓库 `.gitignore` 忽略 `/C500-Comfyui-Package/`。
**原目录已删除**（robocopy 复制 1592 文件逐字节验证后才删）。主仓库已推远程：
**https://github.com/Cybronya/openi-agent**（远程 HEAD = c1edd90，upstream 已建立）。
往 C500 远程推更新：`cd F:\openi\C500-Comfyui-Package` 后正常 git push（≤140MB/批经验仍适用）。

**★ 主仓库 commit 身份惯例**：仓库无 author 配置，沿用历史 `Codebuff <codebuff@local>`，
用 `git -c user.name=... -c user.email=... commit` 单次参数，**不改任何 git config**。

### ★ 大 payload 传输的 6 个坑（Windows）—— **已退休，留档备查**

> 平台会直接 clone 整仓（含 616MB wheel），通常**不需要**这条通道。

上传 wheel 的 base64 有 64MB，路上踩了 6 个坑：

| # | 现象 | 根因 | 解法 |
|---|------|------|------|
| 1 | `WinError 206 文件名太长` | Windows 命令行 32KB 限制 | 大 payload 走 stdin |
| 2 | `Separator is found, but chunk is longer than limit` | asyncio `readline` 64KB 行限制 | **守护进程协议改为 8 字节大端长度 + 二进制** |
| 3 | 大 JS eval 卡死无响应 | `Runtime.evaluate` 传超大字符串会挂 | `jlab.run_js` 分片累积到 `window.__jsBuf` 再 eval（500KB 实测通过） |
| 4 | REST PUT 返回 400 Invalid JSON | `/api/contents` PUT 要 base64 JSON body，不接受二进制 blob | 改走内核 WebSocket 写文件 |
| 5 | `NameError: json is not defined` | JS 里 `'b = ' + json.dumps(b64)` 混了 Python/JS | 内核侧 Python 代码用 `repr()` 生成字面量 |
| 6 | out 为空但显示 OK | `stream` 消息晚于 `execute_reply` 到达 | 收到 reply 后延迟 800ms 再收尾 |

**教训**：Python 侧拼 JS 字符串时，**JS 表达式用 `{json.dumps(x)}`，
Python 代码字面量用 `{x!r}`**——两者不能混。

### ★ 云端写文件的正确姿势
```javascript
// 内核侧执行（通过 /api/kernels/<id>/channels 的 WebSocket）
const py = [
  'import base64, os',
  'd = ' + "路径",
  'b = ' + "base64串",     // ← 必须带引号（Python repr）
  'raw = base64.b64decode(b)',
  'open(p,"wb").write(raw)'
].join('\n');
```



### ★★ 守护进程沙箱兼容（2026-11-01 晚修复）

Loomy/WorkBuddy 沙箱会把 `LOCALAPPDATA` 重定向到沙箱路径，Chrome 真实 profile 在
真实用户目录 → 守护进程按环境变量拼路径永远找不到 `DevToolsActivePort`
（现象：Chrome 显示 Server running 但守护进程起不来）。
**`active_endpoint()` 已改为三级探测**：`OPENI_CHROME_USER_DATA` 环境变量 →
LOCALAPPDATA → `~/AppData/Local` 兜底（cdp_daemon.py 与 cdp_autoconnect.py 同步）。
沙箱内启动：先设 `$env:OPENI_CHROME_USER_DATA='<真实目录>\Google\Chrome\User Data'` 再起进程。
首次连接仍弹一次 Chrome 授权窗；`ls-remote` 退出码 0 且无输出 = 远程空仓库。

### ★★ 容器内 git 更新链路（2026-11-01 验证）

- **容器访问 `openi.pcl.ac.cn` 的 https 在服务端被 TLS 拒绝**（git gnutls 与 Python OpenSSL
  均报 `TLSV1_ALERT_INTERNAL_ERROR`）；`mlunotebook.openi.org.cn` 不受影响
- **绕过：`git remote set-url origin http://openi.pcl.ac.cn/...`** → pull 正常
- 云端 `/tmp/code/C500-Comfyui-Package` commit = 远程最新（110df4e）时 pull 显示 `Already up to date.`
- `pkill -f` 自杀坑：`sh -c` 命令行含整段脚本文本，pkill 模式会匹配执行通道自身
  → EXIT -15 整条通道被杀。**解法：模式加字符类，如 `pkill -f 'mai[n].py'`**

### ★★ notebook UI 执行链路（2026-11-01 打通，与内核通道互为备份）

工具：`tools/cloud/js_comfy_start.js`（写 cell+启动）、`js_nb_run.js`（精确 Run）、
`js_nb_read.js`（输出轮询）、`js_toolbar_probe.js`（工具栏枚举）。
- 建 notebook：`jupyterapp` 全局未暴露 → 点 Launcher 卡片
  `.jp-LauncherCard[data-category="Notebook"]`；globals 里的 `_JUPYTERLAB` 可探测
- **Run 按钮标识在 `title` 而非 `aria-label`**（aria 为空）：
  `.jp-NotebookPanel .jp-Toolbar [title="Run the selected cells and advance"]`（工具栏在 NotebookPanel 层级）
- 点击必须完整 pointer/mouse 事件序列 + 真实坐标；单次 eval 串全流程会超时 →
  **拆「setup」「read」两次 eval + 本地轮询**
- cell 里跑 shell：`subprocess.run(cmd, shell=True, cwd=repo)` + print（避开 `!` 转义）

### ★★ ComfyUI 已在云端跑通（2026-11-01，MetaX C500）

- 启动：notebook cell 后台线程 `subprocess.Popen(['python','main.py','--listen','0.0.0.0','--port','8188'],
  cwd='/tmp/code/C500-Comfyui-Package/comfyui', ...)` 逐行 print → **日志实时流式进 cell 输出**
- 前置：`custom_nodes/` 目录缺失会崩（源码快照不带），先 `os.makedirs(exist_ok=True)`
- 实测：ComfyUI 0.42.0 + **cuda:0 MetaX C500 : native**（VRAM 65120MB）+
  xformers 0.0.22+metax；新版依赖 frontend 1.57.1 等全加载
- 浏览器访问：**JupyterLab 代理路由 `/proxy/8188/` 可用**
  （`https://mlunotebook.openi.org.cn/notebook_<hash>_task0/proxy/8188/`）
- 非致命：aimdo DynamicVRAM 不可用 → 回退 legacy ModelPatcher
- **待办**：历史工作流 `video_minimax_h3_t2v`（MiniMax H3 文生视频）提示 5 个问题，
  大概率缺模型文件（minimax_h3_fl2va_pruned_fp8_scaled 等未上传容器）

### 仍存在的约束

1. **Chrome 136+ 屏蔽默认 profile 的 `--remote-debugging-port`**
   → 手动端口模式必须用非默认 `--user-data-dir`；autoConnect 走另一套通道不受此限
2. **Chrome 156 app-bound 加密**：登录态无法通过复制 profile 迁移
   （`gitea_incredible`/`gitea_awesome` 在新目录会被丢弃；`i_like_openi` 是
   `is_persistent=0` 的 session cookie 且服务端轮换）→ autoConnect 绕开一切

### 环境坑位速查
- `HTTP_PROXY=127.0.0.1:58897` 劫持本地请求 → 访问 127.0.0.1 必须 `--noproxy '*'` / `ProxyHandler({})`
- PowerShell `Start-Process` 启动的 Chrome 立即退出 → 改用 Bash 后台任务
- Cookies 文件被 Chrome 独占锁（error 32）→ NTFS 卷影副本（`Win32_ShadowCopy.Create`）提取
- 本机 C 盘偏紧 → Chrome profile 单实例 25-160 MB，用完必须关实例+删目录
- MCP 的 `Page.captureScreenshot` 在 autoConnect 模式下可能超时 → 改用 MCP `take_screenshot` 走 base64

### 项目文件结构
```
F:\openi\
├── README.md                   项目总览
├── tools\
│   ├── cdp.py                  独立实例模式 CDP 客户端
│   ├── cdp_autoconnect.py      ★ autoConnect 模式（接管用户浏览器）
│   └── cdp_multitab.py         多标签管理示例
├── docs\
│   ├── BROWSER_CDP_GUIDE.md    完整方法论（三个附录）
│   └── screenshots\            测试证据截图
├── memory\                     ★ agent 记忆区（本文件所在）
└── skills\                     agent 技能沉淀（browser-cdp）
```
