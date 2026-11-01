# OpenI 工具集

一个完整闭环：**操作网页 → 本地下载依赖 → 上传云端 → 云端离线安装 → 验证**。

由两个项目整合而成 —— 网页操作（控制面）+ 依赖管理（数据面）。

## 快速开始

```bash
# 环境自检
python cli/openi.py doctor

# 项目状态（git + 页面 + 任务进度）
python cli/openi.py status

# 网页操作
python cli/openi.py web pages                    # 列出标签页
python cli/openi.py web read openi               # 读页面内容
python cli/openi.py web shot out.png             # 截图

# 云端容器
python cli/openi.py cloud "cd /tmp/code && ls"  # 执行 shell
python cli/openi.py cloud-read C500-Comfyui-Package/AGENTS.md

# 本地 → 云端同步
python cli/openi.py sync --dry-run               # 只看差异
python cli/openi.py sync --upload --install      # 上传并安装
```

## 目录结构

```
.
├── TASKS.md                  ★ 断点续做入口（先读这个）
├── cli/openi.py              ★ 统一 CLI
├── tools/
│   ├── web/                  网页操作
│   │   ├── cdp_daemon.py         常驻守护进程（一次授权，零弹窗）
│   │   ├── cdp_autoconnect.py    autoConnect 直连
│   │   ├── cdp.py                 独立实例模式
│   │   ├── jlab.py                执行 JS（避 shell 引号地狱 + 大 payload 分片）
│   │   ├── nb_exec.py             笔记本代码执行
│   │   └── watch_status.py        状态轮询
│   └── cloud/                云端容器
│       ├── cloud_shell.py        内核 WebSocket 执行 shell
│       ├── sync_wheels.py        本地→云端 wheel 同步
│       └── cloud_exec.py         笔记本 UI 方式执行（备用）
├── C500-Comfyui-Package/     ★ 数据面（嵌套独立 git，origin 指向 OpenI 远程）
│   ├── packages/                 离线 wheel 仓库（comfyui + batch2，约 981 MB）
│   ├── comfyui/                  ComfyUI v0.42.0 源码快照
│   ├── plans/                    清单与依赖档案（to-download.txt 为版本权威）
│   ├── scripts/                  下载/安装/探测脚本
│   ├── logs/                     操作日志
│   └── AGENTS.md                 硬性规则（torch 禁令等）
├── docs/
│   ├── INTEGRATION.md         整合设计
│   ├── BROWSER_CDP_GUIDE.md   网页操作方法论
│   ├── cloud_project/         云端项目文档存档
│   └── screenshots/
└── .workbuddy/memory/        agent 记忆区
```

数据面已整体并入本仓库（2026-11-01），嵌套保留独立 git
（`origin` → `openi.pcl.ac.cn/cybronya/C500-Comfyui-Package`，云端部署链路不变），
主仓库 `.gitignore` 忽略该子目录。

## 环境要求

| 组件 | 版本 | 位置 |
|------|------|------|
| Python | 3.12.10 | `F:\Program Files\Python3.12` |
| Node.js | 22.14.0 | `F:\Program Files\Nodejs`（用户级 PATH） |
| chrome-devtools-mcp | 1.12.0 | 全局 npm |
| Chrome | 156 | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Python 依赖 | websockets | `pip install websockets` |

## 前置条件（云端操作）

1. Chrome 开启远程调试：地址栏输入 `chrome://inspect/#remote-debugging` → 开启
2. 启动守护进程：`python -u tools/web/cdp_daemon.py --serve`（端口 8765）
3. JupyterLab 页面已打开（云端容器才有 shell）

## 关键限制

| 限制 | 说明 |
|------|------|
| Chrome 136+ 屏蔽默认 profile 调试端口 | autoConnect 走另一套通道，不受影响 |
| Chrome 156 app-bound 加密 | 登录态无法通过复制 profile 迁移，autoConnect 绕开 |
| 守护进程独占 Chrome 连接 | 同时只允许一个客户端，冲突时需重启守护进程 |
| 大 payload 传输 | 已实现分片，500KB JS / 64MB wheel 实测可用 |

## 详细文档

- `TASKS.md` —— 进度、待办、断点续做指引
- `docs/INTEGRATION.md` —— 整合设计与能力矩阵
- `docs/BROWSER_CDP_GUIDE.md` —— 网页操作完整方法论（含踩坑记录）
