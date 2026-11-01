# TASKS.md — 项目总控台

> **这是断点续做的唯一入口。** 任何 agent 接手时先读这里，再读 `memory/MEMORY.md`。

## 项目定位

一个完整闭环：**操作网页 → 本地下载依赖 → 上传云端 → 云端离线安装 → 验证**。

由两个既有项目整合而成：

| 来源 | 路径 | 角色 | 能力 |
|------|------|------|------|
| 网页操作 | `F:\openi` | **控制面** | CDP 接管浏览器、读取/操作页面、云端容器命令执行、CLI |
| 依赖管理 | `F:\openi\C500-Comfyui-Package`（已并入，嵌套独立 git） | **数据面** | 依赖解析、离线 wheel 下载、多批次安装、git 分发 |

## 整合后结构

```
F:\openi\
├── TASKS.md                  ← 本文件，断点续做入口
├── README.md                 项目总览
├── cli\
│   └── openi.py              ★ 统一 CLI（doctor/web/cloud/cloud-read/sync/status）
├── tools\
│   ├── web\                  网页操作
│   │   ├── cdp_daemon.py         ★ 常驻守护进程（一次授权，零弹窗）
│   │   ├── cdp_autoconnect.py    autoConnect 直连（会弹窗）
│   │   ├── cdp.py                 独立实例模式
│   │   ├── jlab.py                ★ 从 .js 文件执行 JS（避 shell 引号地狱 + 大 payload 分片）
│   │   ├── nb_exec.py             笔记本代码执行
│   │   ├── watch_status.py        状态轮询
│   │   └── cdp_multitab.py        多标签示例
│   └── cloud\                云端容器
│       ├── cloud_shell.py        ★ 内核 WebSocket 执行 shell
│       ├── sync_wheels.py        ★ 本地→云端 wheel 同步
│       └── cloud_exec.py         笔记本 UI 方式执行（备用）
├── C500-Comfyui-Package\     ★ 数据面（2026-11-01 整体并入，嵌套保留独立 git，
│                               origin 指向 OpenI 远程，云端部署链路不变）
│   ├── packages\                 离线 wheel（comfyui 28 个 + batch2，约 981MB）
│   ├── comfyui\                  ComfyUI v0.42.0 源码快照
│   ├── plans\                    清单（to-download.txt 版本权威 / cloud-env.md 环境权威）
│   ├── scripts\                  download_wheels.sh / install_offline.sh / probe_*.py
│   └── logs\                     操作日志
├── docs\
│   ├── INTEGRATION.md         ★ 整合设计文档
│   ├── BROWSER_CDP_GUIDE.md   网页操作完整方法论
│   ├── cloud_project\         云端项目文档存档
│   └── screenshots\
├── memory\                    ★ agent 记忆区（MEMORY.md + 每日日记）
└── skills\                    agent 技能沉淀（browser-cdp）
```

数据面已整体并入本仓库根下（原 `F:\Program Files\Git\C500-Comfyui-Package` 已搬迁），
嵌套保留独立 git 与远程推送通道，主仓库 `.gitignore` 忽略该子目录。

---

## 进度总览

**完成度：6 / 6 阶段**（100%）｜主线闭环已端到端跑通并留档

| # | 阶段 | 状态 | 说明 |
|---|------|------|------|
| 0 | 环境准备 | ✅ 完成 | Node v22.14.0 于 `F:\Program Files\Nodejs`；chrome-devtools-mcp v1.12.0；Python + websockets |
| 1 | 网页操作能力 | ✅ 完成 | CDP 守护进程打通，8 项能力全通过，零弹窗 |
| 2 | 云端容器执行 | ✅ 完成 | 内核 WebSocket 通道打通，shell/安装/验证全通 |
| 3 | **整合架构** | ✅ 完成 | 目录分类、CLI（6 子命令）、TASKS.md 断点机制、INTEGRATION.md |
| 4 | **本地↔云端同步** | ✅ 完成 | 8 个新 wheel 已 push 远程；建任务 920100 克隆最新代码 |
| 5 | **脚本缺陷修复** | ✅ 完成 | install_offline.sh 已修并提交（110df4e） |
| 6 | **部署验证** | ✅ 完成 | 任务 920100 RUNNING → 进容器安装 → 28/28 版本对齐，frontend 升到 1.57.1，torch 栈完好 |
| + | **ComfyUI 云端启动** | ✅ 完成 | 0.42.0 @ MetaX C500 native（notebook 后台线程方式，日志流式可见），浏览器经 `/proxy/8188/` 访问 |

**数据面已并入本仓库**（2026-11-01 晚）：`C500-Comfyui-Package/` 嵌套独立 git，
原目录已删除；主仓库已推 https://github.com/Cybronya/openi-agent（c1edd90）。

---

## 阶段 4：本地→云端同步 🔄 进行中

### 背景
本地 `packages/comfyui/` 已有 ComfyUI v0.42.0 对应的新版 wheel，
但**云端还是旧版**，导致云端 `pip list` 与 ComfyUI requirements 不符。

### 版本差异（8 个包）
| 包 | 本地/requirements | 云端实装 |
|----|------------------|---------|
| comfyui-frontend-package | 1.57.1 | 1.53.6 |
| comfyui-workflow-templates | 0.11.96 | 0.11.70 |
| comfyui-embedded-docs | 0.5.14 | 0.5.12 |
| comfy-aimdo | 0.6.0 | 0.5.5 |
| comfy-kitchen | 0.2.40 | 0.2.35 |
| comfyui-workflow-templates-core | 0.3.387 | 0.3.361 |
| comfyui-workflow-templates-json | 0.1.122 | 0.1.96 |
| comfyui-workflow-templates-media-assets-02 | 0.1.23 | 0.1.6 |

### 已完成
- [x] 差异检测（`sync_wheels.py --dry-run`）：精确识别 8 个缺失 + 8 个云端多余
- [x] 上传通道打通：base64 → 内核 WebSocket → 容器内写文件
- [x] 大 payload 分片机制（`jlab.run_js`）：500KB JS 实测通过
- [x] 8 个新版 wheel 已随 git commit 110df4e push 到远程仓库（替代原计划的逐包上传）
- [x] 通过平台「创建计算任务」表单建任务 920100，克隆 master(110df4e) 到容器 /tmp/code
- [x] 任务 920100 RUNNING → 点「调试」拿 JupyterLab 地址 → 进容器验证 /tmp/code 含 8 个新 wheel
- [x] 云端执行 `bash scripts/install_offline.sh`（core 28 包）→ 安装成功，RC=0
- [x] 版本核对 **28/28 全对齐**；frontend 1.53.6→**1.57.1**；torch 2.10.0+metax3.8.1.0 /
      numpy 1.26.4 / scipy 1.16.0 / pillow 11.2.1 **均未被破坏**

**★ 结论（推翻早前设计）**：**平台会把仓库连同 616MB wheel 一起完整 clone**，
仓库落在 `/tmp/code/<repo-name>/` → **无需任何自建上传通道**，
`tools/cloud/sync_wheels.py` 的 base64 传输方案可退休，仅留作应急备份。

**下一步（剩余待办）**：
1. ~~`bash scripts/install_offline.sh all` 装 batch2~~ ✅ **已完成（2026-11-01 晚）**：
   31 包全部安装成功（含 2 个 sdist 经 `--no-build-isolation` 构建），
   import 验证 **15/15 OK**；torch `2.10.0+metax3.8.1.0` / numpy 1.26.4 /
   scipy 1.16.0 / pillow 11.2.1 **均未被破坏**
2. 云端任务 920100 持续 RUNNING 的计费问题待确认
3. 装 `libportaudio2` 解决 sounddevice 导入失败

### ★ 容器内 git 更新链路（2026-11-01 晚验证）

- **容器访问 `openi.pcl.ac.cn` 的 https 在服务端被 TLS 拒绝**（gnutls/OpenSSL 均报
  `TLSV1_ALERT_INTERNAL_ERROR`；`mlunotebook.openi.org.cn` 不受影响）
- **绕过方法：git remote 改用 `http://` 协议**，pull 正常（实测 `Already up to date.`）
- 云端 `/tmp/code/C500-Comfyui-Package` 当前 commit = `110df4e` = 远程最新
- **notebook UI 执行链路已打通**（`tools/cloud/js_nb_*.js`）：
  建 notebook（Launcher 卡片 fallback）→ CodeMirror.setValue 写入 →
  工具栏 Run 按钮**真实点击**（`[title="Run..."]` 是 **title 而非 aria-label**！
  坐标 (502,73)，完整 pointer/mouse 事件序列）→ 轮询 `.jp-OutputArea-output`。
  与内核 WebSocket 通道（`cloud_shell.py`）结果一致，互为备份
- 守护进程沙箱兼容：`active_endpoint()` 现支持 `OPENI_CHROME_USER_DATA` 环境变量
  覆盖 + 真实用户目录兜底（沙箱会重定向 LOCALAPPDATA）

> 完整操作手册见 **`docs/CLOUD_DEPLOY_PLAYBOOK.md`**（含表单真实路径、全部 API、16 条坑位速查）。

### 上传通道的技术要点（踩了 6 个坑）
1. **Windows 命令行 32KB 限制** → 大 payload 走 stdin
2. **asyncio readline 64KB 限制** → 守护进程协议改为 8 字节长度前缀 + 二进制
3. **Runtime.evaluate 大字符串卡死** → `jlab.run_js` 分片累积到 `window.__jsBuf` 再执行
4. **REST PUT 不接受二进制 blob** → 报 400 Invalid JSON，必须用 base64 JSON body；本项目改走内核通道
5. **Python 字符串字面量缺引号** → 内核侧代码要用 `repr()` 生成，不是 `json.dumps()`
6. **stream 消息晚于 execute_reply** → 收到 reply 后延迟 800ms 再收尾

---

## 阶段 5：脚本缺陷修复 ✅ 完成

### `scripts/install_offline.sh` 的 4 个 bug（已修，commit 110df4e）
1. ~~注释行未过滤~~ → 已修（原本就有 case 分支，但安装时没清洗）
2. ~~extras 未剥离~~ → 已修（`qrcode[pil]` → `qrcode`）
3. ~~版本约束未剥离~~ → 已修（原本就有 `${pin%%[=<>!~]*}`）
4. **sdist 装不上** → 已修：加 `--no-build-isolation`
   （离线 `--no-index` 下 pip 建隔离环境要下载 setuptools）

### 附带修复
- 安装时清单清洗去注释/空行，改用临时文件（避开 `sh` 不支持 `<()` 进程替换）
- `all` 模式 case 分支格式修正

### 验证
```
$ bash scripts/install_offline.sh check
[OK] ComfyUI 依赖（v0.42.0 对应版本） 清单内 28 个包全部就位
[DONE] 全部校验通过（未安装）

$ bash scripts/install_offline.sh packages/batch2 plans/to-download-batch2.txt
[OK] 自定义批次 清单内 31 个包全部就位
```

---

## 待办补充区

> 新发现的待办写在这里，按优先级排列。

### P1 — 重要
- [ ] **ComfyUI 工作流缺模型文件**：历史工作流 `video_minimax_h3_t2v`（MiniMax H3 文生视频）
      提示 5 个问题，safetensors（unet/clip/vae/audio_vae）未上传容器。
      ComfyUI 本体已跑通，补齐模型即可出片（体积大，走 git 仓库或分块上传待定）。
- [ ] **云端 PortAudio 缺失**：`sounddevice` 已装但 import 失败（`OSError: PortAudio library not found`）。
      需在云端容器装 `libportaudio2`（apt），非 Python 包问题。
- [ ] **云端任务计费**：GPU 实例一直 RUNNING，已超 2 小时。需确认是否继续占用。
- [ ] **云端旧版 wheel 清理**：云端有 8 个已被 v0.42.0 替代的旧 wheel，
      与本地 git commit `1b27e16` 的清理不一致 → 需同步删除。

### P2 — 改进
- [ ] `download_wheels.sh` 集成进 CLI（`openi download`）—— 本地下载依赖环节还没串进 CLI
- [ ] 依赖解析结果与云端 freeze 自动对账（`plans/cloud-full-freeze.txt`）
- [ ] 同步进度可视化（`scripts/progress.py`）
- [ ] `openi sync` 支持增量（只传变更文件）

### P3 — 增强
- [ ] `openi doctor` 增加云端内核状态检查
- [ ] 云端状态快照存档（便于回溯）
- [ ] 文档站化（docs → 索引页）

---

## 断点续做指引

**接手时按这个顺序**：
1. 读本文件 → 知道做到哪了
2. 读 `memory/MEMORY.md` → 知道技术决策与踩过的坑
3. 读 `memory/2026-11-01.md` → 知道详细过程
4. 按上面「下一步」继续

**每次做完一件事**：
1. 更新本文件对应阶段的 checkbox
2. 追加 `memory/YYYY-MM-DD.md`
3. 若是技术决策，写进 `memory/MEMORY.md`

**注意事项**：
- `tools/web/cdp_daemon.py` 若未运行，先起它：
  ```bash
  python -u tools/web/cdp_daemon.py --serve
  ```
  端口 8765。Git Bash 下 `kill` 不掉旧进程，用 PowerShell
  `Stop-Process -Id <pid> -Force`（`netstat -ano | grep 8765` 查 PID）。
- 云端容器需 JupyterLab 页面已打开且 `chrome://inspect/#remote-debugging` 已开启。
- 上传大文件后守护进程可能短暂卡顿（Runtime.evaluate 大字符串），
  必要时重启守护进程。
