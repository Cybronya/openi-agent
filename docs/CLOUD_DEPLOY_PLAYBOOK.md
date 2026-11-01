# 云端离线依赖部署 Playbook

> **场景**：把本地 `C500-Comfyui-Package` 仓库（含离线 wheel）部署到启智平台
> `openi.pcl.ac.cn` 的 C500 容器里，升级 ComfyUI 依赖到 v0.42.0 对应版本。
>
> **最后验证**：2026-11-01 18:55 全流程跑通，28/28 包版本对齐，torch 栈未受损。

---

## 0. 全链路一览

```
本地 packages/ 下的 wheel 变更
        │  git add + commit + push（唯一必需的一次提交）
        ▼
远程仓库 cybronya/C500-Comfyui-Package（master）
        │  平台创建调试任务，选仓库 + 分支
        │  → 平台自动 clone 整个仓库到 /tmp/code/<repo-name>/
        ▼
云端容器 /tmp/code/C500-Comfyui-Package/packages/**
        │  bash scripts/install_offline.sh
        │  （--no-index --find-links --no-deps --no-build-isolation）
        ▼
云端 site-packages 升级到钉死版本 → 版本核对 → 完成
```

### ★ 最重要的一条结论

**平台会把仓库连同 616 MB 的 wheel 一起完整 clone 下来。**

不需要任何「本地上传到云端」的自建通道（早期设想的 base64 + 内核 WebSocket 传文件
方案可以退休）。只要 wheel 已被 git 跟踪且 push 到远程，平台任务起来就自带。

> 顺带澄清两个曾经误判的点：
> - `code_size_limit: 50` 是 **容器内项目存储配额 50 GiB**，不是「代码 50 MB 上限」；
>   1.1 GiB 的仓库远未超限。
> - 平台 clone 后**仓库在 `/tmp/code/<repo-name>/`，不是 `/tmp/code/` 本身**。
>   `code_path` 字段写的是 `/tmp/code`，容易踩坑。

---

## 1. 阶段 A：本地仓库准备（控制面 → 数据面）

依赖项目已并入本仓库：`F:\openi\C500-Comfyui-Package`（嵌套独立 git）。

```bash
cd "/f/openi/C500-Comfyui-Package"
git add -A
git commit -m "chore: update comfyui wheels to v0.42.0 pins"
git push origin master
git log -1 --oneline      # 记下 commit id，平台会按它 clone
```

约束（来自仓库 `AGENTS.md`，必须遵守）：
1. **严禁**从 PyPI 下载/安装 `torch`、`torchvision`、`numpy`、`scipy`、`pillow`
   —— 云端 torch 来自沐曦 MACA 适配仓库，混入 CUDA 版会破坏 GPU 加速栈。
2. 交叉下载必须指定
   `--platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --abi cp312`。
3. 版本钉死以 `plans/to-download.txt` 为准；云端环境变化先更新 `plans/cloud-env.md`。
4. 安装动作**只**通过 `scripts/` 下的脚本执行，日志归档到 `logs/`。

---

## 2. 阶段 B：清理任务槽位（必做，且必须真删）

平台**调试任务上限 5 个**，且「关闭/停止」任务**不释放槽位**——必须真正删除。

列表页只提供 `新建计算任务 / 批量删除 / 关闭` 三个按钮，没有单条「更多→删除」。
正确做法：勾选表格行 checkbox → 点「批量删除」→ 确认弹窗。

真实删除接口（netwatch 抓到的，**不存在** `/api/v1/ai_task/delete`，那是 404）：

```
POST https://openi.pcl.ac.cn/api/v1/ai_task/batch_del?_csrf=<token>
body: {"id":[920072,913141,...],"_csrf":"<token>"}
→ 200
```

> 排查任务状态/停任务时用：
> `GET /api/v1/ai_task/my_list`、`GET /api/v1/ai_task?id=X&_csrf=`、
> `POST /api/v1/ai_task/stop?id=X&_csrf=`、
> `GET /api/v1/ai_task/creation/required`（看 `can_create_more` / `not_stop_task_count`）。

---

## 3. 阶段 C：创建调试任务（Element UI 表单真实路径）

入口：`https://openi.pcl.ac.cn/cloudbrains/create`

表单顺序（从上到下 y≈462→1139）：

| # | 字段 | 控件类型 | 操作要点 |
|---|------|---------|---------|
| 1 | **计算资源** | `<a class="item">` **卡片**（不是 el-radio！） | 默认选中「昇腾NPU」。**必须先点「沐曦GPGPU」**，规格下拉才会出现 C500 |
| 2 | **资源规格** | `.spec-sel` el-select | 选 `METAX-GPGPU: 1*C500(显存: 64GB)` → `spec_id=333` |
| 3 | 任务名称 | input | 自动生成 `cybro2026MMDDHHMMSS` |
| 4 | **镜像** | el-select + Dialog | 「平台推荐镜像」**没有**目标镜像 → 切「我的镜像」tab → 搜 C500 → 对 `C500-py3.12-torch2.10-git-unzip-proxy-comfyui` 那一行点 **「使用」** 按钮（点外层容器无效） |
| 5 | 数据集 / 预训练模型 | — | 留空 |
| 6 | **项目** | 「选择项目」按钮 → Dialog(el-tree) | 点**右侧** `btn-select` 按钮（不是左边的 `model-item-placeholder` 占位符）→ 在树里选 `cybronya/C500-Comfyui-Package` → 点「确定」 |
| 7 | **代码分支** | el-select | 选完项目后**自动联动**填充，选 `master`（即目标 commit） |
| 8 | 访问 Internet | el-radio | 否/是 |
| 9 | 新建任务 | button | 提交 |

提交后平台调用：

```
POST https://openi.pcl.ac.cn/api/v1/repos/cybronya/C500-Comfyui-Package/ai_task/create
```

关键参数（netwatch 实测）：

```json
{
  "repoName": "C500-Comfyui-Package",
  "branch_name": "master",
  "compute_source": "METAX-GPGPU",
  "spec_id": "333",
  "image_id": "0b0ac7785b434ee68886d6f60b2a2e62",
  "display_job_name": "cybro202611011828252"
}
```

> `image_id` 对应镜像 `C500-py3.12-torch2.10-git-unzip-proxy-comfyui`；
> 选错「沐曦」卡片 → 规格列表里只有 NPU/Ascend，没有 C500。

---

## 4. 阶段 D：任务状态 → 拿到容器入口

状态流转：`PREPARING`（拉镜像/分配资源，约 10 min）→ `WAITING` → `RUNNING`。

```bash
# 轮询（每 15 s 一次）
GET /api/v1/ai_task?id=920100&_csrf=<token>
```

**`end_point` / `port` 字段在点「调试」之前一直是空的**，别指望从详情接口直接拿地址。

真正入口来自列表行操作栏的 **「调试」** 按钮（`<a href="javascript:;">`，Vue 绑定）：

```
GET https://openi.pcl.ac.cn/api/v1/ai_task/debug_url?id=920100&_csrf=<token>
→ 平台随即跳转到：
https://mlunotebook.openi.org.cn/notebook_<hash>_task0/lab
```

`notebook_<hash>_task0` 就是容器上下文前缀，`/lab` 是 JupyterLab 前端。

---

## 5. 阶段 E：进容器执行命令（内核 WebSocket 通道）

唯一可靠路径是**内核 WebSocket**：

```
wss://mlunotebook.openi.org.cn/notebook_<hash>_task0/api/kernels/<kernel-id>/channels
```

发 `execute_request` 消息，直接收 `stream` / `execute_reply`。

### 为什么不用别的

| 方式 | 结果 |
|------|------|
| `POST /api/kernels/<id>/execute` | **404**，端点被禁用 |
| UI 点 Run / 合成 KeyboardEvent / `Input.dispatchKeyEvent` | 不可靠（CodeMirror 6 事件体系特殊，Shift+Enter 被吞） |
| **内核 WebSocket** | ✅ 稳定，能拿到 stdout/stderr/退出码 |

### 前置：必须先有 kernel

JupyterLab 首页**不会**自动起内核，`GET /api/kernels` 返回空 → `cloud_shell` 报 `NO_KERNEL`。
手动建一个（**必须带 XSRF 头，否则 403**）：

```javascript
const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
const xsrf = decodeURIComponent((document.cookie.split(';').map(s=>s.trim())
                    .find(s=>s.startsWith('_xsrf='))||['='])[1].split('=')[1]);
await fetch(base + '/api/kernels', {
  method: 'POST', credentials: 'include',
  headers: {'Content-Type':'application/json', 'X-XSRFToken': xsrf},
  body: JSON.stringify({name: 'python3'})
});
```

### 用法

```bash
# 单条命令
python tools/cloud/cloud_shell.py "cd /tmp/code/C500-Comfyui-Package && ls" 120

# 多行脚本（推荐，避免引号地狱）
python tools/cloud/cloud_shell.py --file /f/openi/xxx.sh 300
```

---

## 6. 阶段 F：离线安装与验证

```bash
cd /tmp/code/C500-Comfyui-Package
bash scripts/install_offline.sh          # core：packages/comfyui（28 包）
bash scripts/install_offline.sh check    # 只校验齐全性，不安装
bash scripts/install_offline.sh all      # core + batch2（含 sdist，耗时更长）
```

脚本内部等价于：

```bash
python -m pip install --no-index \
  --find-links packages/comfyui \
  --no-deps \
  --no-build-isolation \
  -r plans/to-download.txt
```

- `--no-deps`：不让 pip 去解析依赖（否则离线环境会失败）。
- `--no-build-isolation`：sdist（fairscale、antlr4-python3-runtime）构建时
  隔离环境要联网下 setuptools，离线必失败。

### 本次实际升级的 8 个包

| 包 | 旧版本 | 新版本 |
|----|--------|--------|
| comfyui-frontend-package | 1.53.6 | **1.57.1** |
| comfyui-embedded-docs | 0.5.12 | 0.5.14 |
| comfy-kitchen | 0.2.35 | 0.2.40 |
| comfy-aimdo | 0.5.5 | 0.6.0 |
| comfyui-workflow-templates | 旧 | 0.11.96 |
| comfyui-workflow-templates-core | 旧 | 0.3.387 |
| comfyui-workflow-templates-json | 旧 | 0.1.122 |
| comfyui-workflow-templates-media-assets-02 | 旧 | 0.1.23 |

### 验证清单

```bash
python -c "import comfyui_frontend_package as f; print(f.__version__)"   # 期望 1.57.1
python -c "import torch; print(torch.__version__)"                        # 必须仍是 2.10.0+metax3.8.1.0
python -c "import numpy, scipy, PIL; print(numpy.__version__, scipy.__version__, PIL.__version__)"
pip list --format=freeze | grep -iE "^(comfyui|comfy|torch|numpy|scipy|pillow|...)"
```

---

## 7. 坑位速查表

| # | 现象 | 根因 | 解法 |
|---|------|------|------|
| 1 | 任务一直 `PREPARING` 10 分钟 | 正常，拉 C500 镜像 + 排资源 | 耐心等，轮询 |
| 2 | 「调试任务数量已达上限」 | 上限 5，**停止不释放槽位** | 必须 `batch_del` 真删 |
| 3 | `/api/v1/ai_task/delete` → 404 | 该接口不存在 | 用 UI 批量删除，netwatch 抓 `batch_del` |
| 4 | `end_point` 永远为空 | 没点「调试」 | 点「调试」，走 `debug_url` |
| 5 | 规格下拉只有 NPU/Ascend | 计算资源卡片还停在「昇腾NPU」 | 先点「沐曦GPGPU」卡片 |
| 6 | 点「选择项目」没反应 | 点到的是占位符 `model-item-placeholder` | 点右侧 `btn-select` 按钮 |
| 7 | 项目选完分支下拉仍为空 | 没点 Dialog 的「确定」 | 勾选树节点 → 点确定 |
| 8 | 点镜像项无效 | 点的是外层容器 | 点该行「使用」按钮 |
| 9 | 镜像列表里找不到目标镜像 | 在「平台推荐镜像」tab | 切「我的镜像」tab |
| 10 | `cloud_shell` 报 `NO_KERNEL` | lab 没自动起内核 | POST `/api/kernels` + `X-XSRFToken` |
| 11 | POST `/api/kernels` → 403 | 缺 XSRF 头 | 带 `X-XSRFToken`（取 `_xsrf` cookie） |
| 12 | `cloud_shell` 返回 `eval 返回 None` | `JS_TEMPLATE` 里 `wsUrl` 重复声明导致语法错 | 已修（`tools/cloud/cloud_shell.py`） |
| 13 | 云端 `ls packages/comfyui` 为空 | 实际仓库在 `/tmp/code/<repo-name>/` | `cd /tmp/code/C500-Comfyui-Package` |
| 14 | 验证脚本卡死 | `torch.cuda.get_device_name(0)` 会初始化 CUDA context，很慢 | 只用 `torch.cuda.is_available()` |
| 15 | 多行脚本里 heredoc 行为异常 | `subprocess(shell=True)` 走 `/bin/sh`（dash） | 改用 `cloud_shell.run_python`（base64 传码） |
| 16 | 云端 shell 不支持 `<(...)` 进程替换 | `/bin/sh` 而非 bash | 先落地临时清单文件 |

---

## 8. 工具与命令速查

### 本地（控制面 `F:\openi`）

```bash
# 守护进程（必须用 run_in_background 启动，勿用 `&`）
python tools/web/cdp_daemon.py --serve

# 发命令给守护进程
python tools/web/cdp_daemon.py --client '{"cmd":"pages"}'
python tools/web/cdp_daemon.py --client '{"cmd":"read","match":"openi"}'
python tools/web/cdp_daemon.py --client '{"cmd":"eval","expr":"..."}'

# 在 openi 页面执行 JS（脚本化，避免引号地狱）
python tools/web/jlab.py tools/cloud/xxx.js openi      # match=openi
python tools/web/jlab.py tools/cloud/xxx.js            # match=mlunotebook（默认）

# netwatch：执行 JS 的同时抓网络请求/响应
python tools/cloud/run_netwatch.py tools/cloud/xxx.js 40 [url_filter]

# 云端容器执行 shell
python tools/cloud/cloud_shell.py "cmd" 120
python tools/cloud/cloud_shell.py --file script.sh 300
```

### 云端（数据面 `F:\openi\C500-Comfyui-Package`）

```bash
scripts/download_wheels.sh      # 交叉下载 wheel 到 packages/
scripts/install_offline.sh      # 离线安装
scripts/resolve_missing.py      # 依赖缺口解析
plans/to-download.txt           # 版本钉死唯一权威
plans/cloud-env.md              # 云端环境事实唯一权威
```

---

## 9. 一次完整执行的实际命令序列

```bash
# 1) 本地提交推送
cd "/f/openi/C500-Comfyui-Package"
git add -A && git commit -m "..." && git push origin master

# 2) 清任务槽位（若有旧任务）
#    浏览器：/cloudbrains → 勾选 → 批量删除

# 3) 建任务（浏览器 UI，见阶段 C）
#    提交后记下 task id（如 920100）

# 4) 轮询状态到 RUNNING
python tools/cloud/poll_task_920100.py

# 5) 点「调试」→ 拿到 mlunotebook URL

# 6) 建内核（403 则补 X-XSRFToken）
python tools/web/jlab.py tools/cloud/js_create_kernel2.js

# 7) 验证 clone 结果
python tools/cloud/cloud_shell.py --file /f/openi/tools/cloud/verify_cloud.sh 300

# 8) 离线安装
python tools/cloud/cloud_shell.py --file /f/openi/tools/cloud/install_core.sh 600

# 9) 验证
python tools/cloud/cloud_shell.py --file /f/openi/tools/cloud/verify_cloud.sh 300
```

> 现成的云端脚本（本地已归档）：
> `tools/cloud/verify_cloud.sh`（版本核对）、
> `tools/cloud/install_core.sh`（装 core 批次）。
