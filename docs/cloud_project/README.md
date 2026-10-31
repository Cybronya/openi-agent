# C500-Comfyui-Package

本仓库用于集中管理 Linux 云 GPU（沐曦 MetaX C500）ComfyUI 部署所需的依赖包与源码快照，
本机预下载后经 git 分发，云端克隆即可离线安装，不依赖云端网速。

> **本目录即项目根目录**：项目记忆与工作约定见 [AGENTS.md](AGENTS.md)，
> 上层目录（Git Bash 宿主环境）不参与项目管理，请勿在外层做任何修改。

## 用途

- 存放需要在 Linux 环境中安装的依赖包（.deb / .rpm / .tar.gz 等）
- 记录依赖的来源、版本与安装方式，便于追溯和复现

## 目录约定

| 路径 | 说明 |
| --- | --- |
| `packages/` | 下载或构建好的依赖包文件 |
| `comfyui/` | ComfyUI 源码快照（v0.42.0，upstream commit 067f853，2026-10-24） |
| `scripts/` | 安装脚本与依赖解析脚本 |
| `logs/` | 安装过程的日志输出 |

## 管理规则

1. 新增依赖包时，同时在 `packages/` 下保留原始文件，并在此 README 中登记名称、版本与用途。
2. 安装动作一律通过 `scripts/` 下的脚本执行，避免手工零散操作。
3. 安装完成后将日志归档到 `logs/`，文件名带日期，例如 `install-2026-09-30.log`。
4. 为 Linux 云 GPU 离线装依赖时，用 `scripts/download_wheels.sh` 在本机通过国内镜像交叉下载 manylinux wheel 到 `packages/`，云端用 `pip install --no-index --find-links=...` 离线安装，不走云端网络。

## 已登记的依赖批次

| 批次 | 目录 | 清单 | 内容 |
| --- | --- | --- | --- |
| 1 ComfyUI | `packages/comfyui/` | `plans/to-download.txt` | 28 wheel，616MB |
| 2 视觉/评测栈 | `packages/batch2/` | `plans/to-download-batch2.txt` | 29 wheel + 2 sdist（fairscale、antlr4-python3-runtime），317MB；根需求见 `plans/install-reqs-batch2.txt` |

第二批关键钉定：opencv 4.11.0.86（5.x 需 numpy>=2）、mediapipe 1.0.1（0.10.x 需 protobuf<5 与云端 7.35.1 冲突）、contourpy 1.3.3、tifffile 2025.5.10 —— 全部为保云端 numpy 1.26.4 不被升级。

## ComfyUI 源码快照（comfyui/）

- 版本: **v0.42.0**，upstream commit `067f853305e74a051dd17f15964d5b0e7887abf5`（2026-10-24）
- 来源: https://gitcode.com/GitHub_Trending/co/ComfyUI.git （浅克隆 `--depth 1`，仅保留最新一层代码，已移除其内嵌 `.git`）
- 用途: 云端克隆本仓库即同时获得 ComfyUI 代码与全部离线依赖，进入 `comfyui/` 按常规方式 `pip install -r comfyui/requirements.txt --no-index --find-links=../packages/...`（或直接用 `python main.py` 启动，视云端已装包情况）
