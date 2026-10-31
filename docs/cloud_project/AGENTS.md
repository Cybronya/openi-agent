# AGENTS.md — C500-Comfyui-Package 项目记忆

> 本文件是本项目（`C500-Comfyui-Package`）给 Codebuff（Buffy）的记忆 / 工作说明。
> 项目实际根目录就是本文件所在目录，所有工作都应以此目录为准，
> 外层的 Git Bash 安装目录只是宿主环境，不需要也不要去修改。

## 项目定位

集中管理 Linux 云 GPU（沐曦 MetaX C500）环境的依赖包下载、离线安装与追溯。
当前主线任务：为云端 ComfyUI 离线补齐 pip 依赖。

## 目录约定

| 路径 | 说明 |
| --- | --- |
| `packages/` | 下载好的 manylinux wheel（当前 `packages/comfyui/` 共 28 个，616MB；`packages/batch2/` 31 个，317MB） |
| `comfyui/` | ComfyUI 源码快照（v0.42.0，upstream commit 067f853，2026-10-24，GitCode 镜像浅克隆，已去内嵌 .git） |
| `scripts/` | `download_wheels.sh`（本机交叉下载）、`install_offline.sh`（云端离线安装）、`resolve_missing.py`（依赖闭包解析） |
| `plans/` | 云端环境档案、下载清单、依赖报告（`cloud-env.md` 是环境事实的唯一权威来源） |
| `logs/` | 操作日志，文件名带日期 |

## 硬性规则（务必遵守）

1. **严禁从 PyPI 下载/安装 `torch`、`torchvision`、`numpy`、`scipy`、`pillow`**：
   云端 torch 2.10.0+metax3.8.1.0 来自沐曦 MACA 适配仓库，任何 CUDA 版 torch
   混入都会破坏 GPU 加速栈。云端已有的 275 个包一律不重复下载，
   权威清单见 `plans/cloud-full-freeze.txt`。
2. **交叉下载参数**：必须指定
   `--platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --abi cp312`
   （或按 wheel 兼容性放宽为 abi3），与本机 Windows 环境隔离；`download_wheels.sh`
   已内置 `--no-deps`，防止 pip 自动解析拉入云端已有包。
3. **版本钉死以 `plans/to-download.txt` 为准**；如云端环境变化，
   先更新 `plans/cloud-env.md` 再动清单。
4. **安装动作只通过 `scripts/` 下的脚本执行**，日志归档到 `logs/`。
5. 新增依赖包时，在 `README.md` 登记名称、版本与用途。

## 版本钉定决策（依据云端已装版本）

| 包 | 钉定 | 原因 |
| --- | --- | --- |
| numpy 系关联 | 兼容 numpy 1.26.4 | 云端 numpy=1.26.4，禁止被连带升级到 2.x |
| pydantic-settings | ~=2.0 | 与云端 pydantic 2.13.4 同代 |
| transformers | 5.12.0 已装 | 不动 |
| torchsde / kornia / spandrel | 最新稳定版 | 纯 Python，对 torch 2.x 均兼容 |

## 对外分发（OpenI 镜像仓库）

- 仓库: https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package （公开，云端克隆无需鉴权）
- 2026-10-26 起远程地址由 c500-linux-deps 迁移至 C500-Comfyui-Package，仓库根即项目根，
  并新增 `comfyui/` 源码快照（v0.42.0，upstream commit 067f853）
- 云端获取与安装:
  ```bash
  git clone https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package.git
  cd C500-Comfyui-Package
  pip install --no-index --find-links=packages/comfyui -r plans/to-download.txt
  pip install --no-index --find-links=packages/batch2 -r plans/install-reqs-batch2.txt
  ```
- 注意: `.gitattributes` 保证 `.sh` 为 LF 行尾。

## 历史背景

- 之前的工作区根（Git Bash 安装目录）曾被当作 git 项目管理，已于 2026-10-01 弃用：
  本目录改为自包含的项目根，记忆内容以本文件与 `plans/` 为准。
- 2026-10-26: 远程仓库由 c500-linux-deps 迁移至 C500-Comfyui-Package，git 历史重建为
  全新 orphan 链（旧历史因服务器单次 push 体积限制与 push 协商异常无法完整迁移，
  按体积分 8 批推送完成，单批 ≤140MB）。原完整历史仅保留在本地分支 `backup-full`
  （63102a4，含 linux-deps/ 前缀时代与中间重组态），未推送远程。
- 环境事实（硬件、Python/PyTorch 版本、已装包）详见 `plans/cloud-env.md`。
