# 整合设计：网页操作 + 依赖管理

> 两个既有项目如何合成一条完整闭环。

## 一、为什么要整合

现状是两个割裂的项目：

| 项目 | 能做 | 不能做 |
|------|------|--------|
| `F:\openi`（网页操作） | 接管浏览器、读页面、云端执行 shell | 不知道依赖怎么管、装哪去 |
| `F:\Program Files\Git\C500-Comfyui-Package`（依赖管理） | 解析依赖、离线下载、多批次安装 | 没法操作网页、没法在云端执行验证 |

真实工作流是交叉的：

```
看云端任务状态(网页) → 发现缺包 → 本地下载 wheel(依赖) → 上传云端(网页+文件)
→ 云端安装(网页+shell) → 验证(网页读页面 / shell 跑 python)
```

整合后由 `cli/openi.py` 一条命令串起来。

## 二、整合方式：保留双项目，共享能力

**不搬动依赖项目的文件**。理由：
1. 它有完整的 git 历史（`1b27e16` 等），搬动会破坏
2. `.freebuff/` 里有分批推送脚本，与 git 深度耦合
3. `packages/` 有 982 MB，不适合复制

改为**能力映射 + 统一入口**：

```
F:\openi\                          ← 控制面（网页操作 + CLI + 记忆）
├── cli/openi.py                   统一入口
├── tools/web/                     网页操作能力
├── tools/cloud/                   云端操作能力
└── docs/

F:\Program Files\Git\C500-Comfyui-Package\   ← 数据面（依赖资产）
├── packages/{comfyui,batch2}/     wheel 仓库
├── plans/                         清单与依赖档案
├── scripts/                       下载/安装脚本
└── logs/                          操作日志
```

`tools/cloud/sync_wheels.py` 里的 `DEP_PROJECT` 常量指向数据面，
形成「控制面操作数据面」的关系。

## 三、能力矩阵

| 需求 | 命令 | 底层 | 状态 |
|------|------|------|------|
| 环境自检 | `openi doctor` | 检查 8 项 | ✅ |
| 看项目状态 | `openi status` | git log + 页面列表 + 任务进度 | ✅ |
| 读网页 | `openi web read openi` | CDP daemon → Runtime.evaluate | ✅ |
| 点按钮 | `openi web click` | CDP → 合成事件 | ✅ |
| 截图 | `openi web shot out.png` | CDP → captureScreenshot | ✅ |
| 云端执行 | `openi cloud "cmd"` | 内核 WebSocket | ✅ |
| 读云端文件 | `openi cloud-read <path>` | JupyterLab REST API | ✅ |
| **本地→云端同步** | `openi sync --upload --install` | base64 分块上传 + 云端安装 | ✅ |
| 本地下载依赖 | 待做 | `scripts/download_wheels.sh` | ⬜ |
| 依赖对账 | 待做 | freeze 解析 | ⬜ |

## 四、关键设计决策

### 4.1 统一用「内核 WebSocket」而非 UI 自动化
云端执行曾尝试 5 种方式（见下），只有 WebSocket 稳定：

| 方式 | 结果 |
|------|------|
| `POST /api/kernels/<id>/execute` | ❌ 404，端点被禁用 |
| UI 点 Run 按钮 | ❌ 跑的是另一个 cell |
| 合成 `KeyboardEvent` | ❌ CodeMirror 6 不响应 |
| `Input.dispatchKeyEvent` rawKeyDown | ❌ cell 被清空 |
| Run 菜单 | ❌ 虚拟渲染，DOM 找不到 |
| **内核 WebSocket** | ✅ |

### 4.2 守护进程模式消灭弹窗
Chrome autoConnect 端点**每次建连接都弹窗授权**。守护进程只连一次并保持，
后续命令走本地 TCP 8765 → **零弹窗**。

### 4.3 断点续做靠 TASKS.md
单文件、可勾选、含"下一步"指引。任何 agent 打开即知进度。

## 五、已实现的整合功能

### 5.1 版本差异检测
`sync_wheels.py --dry-run` 对比本地与云端 `packages/` 的文件名与大小：

```
本地 comfyui: 28 个文件
云端 comfyui: 28 个文件
需要上传: 8 个          ← 云端缺的新版
云端多出（本地已删）: 8 个  ← 旧版 wheel
```

这个能力直接解决了实际问题：本地已做批次3升级（ComfyUI v0.42.0），
云端还是旧版，导致云端 `pip list` 与 requirements 不符。

### 5.2 分块上传
大文件（64.7 MB 的 comfy_kitchen）需 base64 编码后传输，
分块 1.5 MB 避免单条消息超限。上传后按大小校验。

### 5.3 装完即验
`--install` 会在云端跑 `install_offline.sh`，然后自动读
`comfyui-frontend-package` / `torch` / `numpy` 版本做对照。

## 六、遗留问题与处理

| 问题 | 影响 | 处理 |
|------|------|------|
| `install_offline.sh` 校验 bug | 云端安装直接失败 | 阶段 5 修复 |
| 云端 PortAudio 缺失 | sounddevice 无法 import | P1 待办 |
| ComfyUI 源码快照晚于清单 | 5 个包版本不符 | 阶段 4 同步解决 |
| `i_like_openi` 会话轮换 | 登录态失效 | 用 autoConnect 绕开 |

## 七、下一步路线

```
阶段 3 整合架构   ✅ 目录/CLI/文档/断点机制
阶段 4 同步升级   🔄 上传 8 个 wheel → 云端安装 → 验证
阶段 5 脚本修复   ⬜ 修校验 bug + sdist 支持
P1   云端补依赖   ⬜ libportaudio2
P2   下载集成     ⬜ download_wheels.sh 进 CLI
```

详见 `TASKS.md`。
