# 云 GPU 环境档案（供依赖规划用）

> 2026-10-01 更新：ComfyUI 首批 28 包已安装完成；第二批需求（视觉/评测栈）
> 已解析并下载，见文末「第二批」一节。

## 硬件/软件栈

| 项目 | 值 | 来源 |
| --- | --- | --- |
| OS | Linux x86_64 | 推断（GPU 云主机） |
| Python | 3.12.11 | 用户提供 |
| PyTorch | 2.10.0+metax3.8.1.0 | 用户提供（pip freeze） |
| torchvision | 0.25.0+metax3.8.1.0 | 用户提供（pip freeze） |

## ⚠️ 关键注意事项

1. **MetaX 特供 torch**：`+metax` 本地版本号说明 PyTorch 来自沐曦（MetaX）MACA
   适配仓库，而非 PyPI。**严禁**从 PyPI 下载/安装 `torch`、`torchvision`，
   任何把官方 CUDA 版 torch 装进环境的行为都会破坏 GPU 加速栈。
2. **依赖 torch 的包**（torchsde / kornia / spandrel）：
   - torchsde、kornia 纯 Python + numpy 实现，不直接依赖 torch 二进制 → 可下载
   - spandrel 声明依赖 torch → `--no-deps` 单包下载，包本体是纯 Python
3. 下载时必须指定 `--platform manylinux2014_x86_64 --python-version 3.12
   --implementation cp --abi cp312`，与本机 Windows/Python3.12 环境隔离。
4. 已装列表来自云端 `pip freeze` 解析，版本钉死以清单为准。

## 已满足依赖（18 个，云端已有，禁止重复下载安装）

torch, torchvision, numpy, einops, transformers, tokenizers, sentencepiece,
safetensors, aiohttp, yarl, pyyaml, Pillow, scipy, tqdm, psutil, filelock,
requests, pydantic

## ComfyUI requirements.txt 中直接缺失（16 个）

comfyui-frontend-package, comfyui-workflow-templates, comfyui-embedded-docs,
torchsde, alembic, SQLAlchemy, av, comfy-kitchen, comfy-aimdo, simpleeval,
blake3, kornia, spandrel, pydantic-settings, PyOpenGL, comfy-angle

> 注意：上表只是「直接缺失」，其中 alembic / av / comfy-kitchen / blake3 /
> pydantic-settings 等自身还有传递依赖（如 Mako、sqlalchemy 已有但 mako 没有），
> 需要用 resolve_missing.py 算出完整闭包后统一下载，否则云端离线安装仍会缺包。

## 版本钉定决策（依据云端已装版本）

| 包 | 钉定版本 | 原因 |
| --- | --- | --- |
| numpy 系依赖（如 blake3/kornia/scipy 关联） | 兼容 numpy 1.26.4 | 云端 numpy=1.26.4，不能被 numpy>=2 的包连带升级 |
| pydantic 系（pydantic-settings） | pydantic-settings ~=2.0 | 与云端 pydantic 2.13.4 同代兼容 |
| transformers 系 | 已装 5.12.0 | 不动 |
| torch 系（torchsde/kornia/spandrel） | 最新版即可 | 纯 Python 包，对 torch 2.x 均兼容 |

## 最终结果（2026-09-30 已完成下载，全量 freeze 复核后修订）

- 云端完整环境见 `plans/cloud-full-freeze.txt`（275 个包，含大量 MetaX 特供轮子：apex/flash_attn/sglang/triton 等，均不可动）
- 最终清单: `plans/to-download.txt`（**28 个包** = 16 直接缺失 + 12 传递依赖），与云端已有版本零冲突
- 相比初版 32 包剔除 4 个（云端已有且版本满足约束）: typing-extensions 4.16.0、typing-inspection 0.4.2、MarkupSafe 3.0.2、packaging 26.2（镜像最新 26.3 不必要，遵循最小侵入不升级）
- 安装包已下载到: `packages/comfyui/`（616MB，大头是 workflow-templates-media-* 系列约 520MB，内含工作流模板媒体资源）
- 全部为 Linux x86_64 wheel，无 sdist、无 aarch64 误包；kornia 取稳定版 0.8.3、PyOpenGL 取稳定版 3.1.10
- 云端安装: 上传本仓库整个目录（或直接 git clone 远程仓库）后执行 `bash scripts/install_offline.sh`（--no-index 离线安装，自动校验文件齐全）
- 注意: packages/comfyui/ 内严禁混入 torch/torchvision/numpy/scipy/pillow 等云端已有包（曾有 pip 自动解析拉入，已删除；download_wheels.sh 已加 --no-deps 防复发）

## OpenI 镜像仓库（云 GPU 获取入口）

- 仓库: https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package （公开仓库，云端克隆无需鉴权；2026-10-26 由 c500-linux-deps 迁移，并新增 comfyui/ 源码快照）
- 2026-10-02 曾推送 4 个提交: 文档/脚本/清单 + 3 批 wheel，共 28 个 wheel（616MB），API 校验 28/28 包名版本一致
- 云端获取与安装（仓库根即项目根，不再有 linux-deps/ 前缀）:
  ```bash
  git clone https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package.git
  cd C500-Comfyui-Package
  pip install --no-index --find-links=packages/comfyui -r plans/to-download.txt
  pip install --no-index --find-links=packages/batch2 -r plans/install-reqs-batch2.txt
  ```
- 注意: .gitattributes 已保证 .sh 为 LF 行尾；install_offline.sh 建议显式传两个参数，避免相对路径歧义

## 第二批（2026-10-01）：视觉/评测栈 31 包

### 需求来源与去重

用户提供 requirements（timm / transformers / fairscale / pycocoevalcap / opencv-python /
qrcode[pil] / pytorch_lightning / kornia / pydantic / segment_anything / omegaconf / boto3 /
transformers>=4.49 / accelerate / safetensors / sentencepiece / Pillow / imageio-ffmpeg>=0.6.0 /
opencv-python(重复) / scipy / scikit-image / matplotlib / mediapipe>=0.10.20 / dlib-bin>=19.24.6）。

**云端已装、直接跳过（9 个去重后）**：accelerate 1.14.0、transformers 5.12.0（满足 >=4.49）、
safetensors 0.8.0、sentencepiece 0.2.2、Pillow 11.2.1、scipy 1.16.0、kornia 0.8.3、
pydantic 2.13.4、imageio-ffmpeg 0.6.0（满足 >=0.6.0）。

### numpy 1.26.4 兼容性钉定（本批关键决策）

| 包 | 钉定 | 原因 |
| --- | --- | --- |
| opencv-python / opencv-contrib-python | ==4.11.0.86 | 5.x 要求 numpy>=2；4.11 在 py3.12 只要求 numpy>=1.26.0 |
| mediapipe | ==1.0.1 | 0.10.x 要求 protobuf<5，与云端 protobuf 7.35.1 冲突（sglang/MetaX 栈在用，不可降级）；1.0.1 无 protobuf 约束 |
| contourpy | ==1.3.3 | 最新 1.4.0 要求 numpy>=2.0 |
| tifffile | ==2025.5.10 | 2026.x 要求 numpy>=2.1 |

注：mediapipe 依赖 opencv-contrib-python，与 opencv-python 同装会互相覆盖 cv2；
cv2 模块缺失时重装一次 opencv-contrib-python 即可（见 install-reqs-batch2.txt 注释）。

### 下载结果

- 清单: `plans/to-download-batch2.txt`（**32 包** = 13 根包 + 19 传递依赖，与云端零冲突）
- 其中 30 个 wheel + 2 个纯 Python sdist（fairscale 0.4.13、antlr4-python3-runtime 4.9.3，
  PyPI 上从未发 wheel，云端直接从 sdist 构建即可，sha256 已校验）
- 安装包在 `packages/batch2/`（317MB，大头 pycocoevalcap 104MB、opencv-contrib 69MB、opencv 63MB）
- 全部为 Linux x86_64 wheel / 纯 py3 包，无 aarch64 误包

### 云端安装

```bash
# wheels + 2 个 sdist（sdist 云端构建需 setuptools，云端已有）
pip install --no-index --find-links=packages/batch2 -r plans/install-reqs-batch2.txt
# 若 cv2 缺 contrib 模块:
pip install --no-index --find-links=packages/batch2 --force-reinstall --no-deps opencv-contrib-python==4.11.0.86
```
