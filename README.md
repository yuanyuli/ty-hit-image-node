# ComfyUI-Civitai-Inspiration

一个独立的 ComfyUI Civitai 灵感图画廊节点。节点负责查询公开的 Civitai 图片、分页展示缩略图、标记提示词可用性、复制提示词和下载原图。

节点是纯展示节点，没有 ComfyUI 输出端口，也不会驱动下游工作流。它不依赖 `ty-civitai-gallery` 的代码、服务、数据库或缓存。

## 产品边界

当前版本只承诺图片画廊能力：

- 查询 `civitai.com` 或 `civitai.red` 的公开图片。
- 按关键词、时间范围、数量和 SFW 选项查询。
- 在节点内展示当前页结果，点击“下一页（执行）”获取下一页。
- 图片角标显示是否检测到正向提示词；点击有提示词角标可复制文本。
- 鼠标悬停图片可将原图下载到 ComfyUI 的 `output/ty-node/`。

以下能力不属于当前版本：视频播放或视频解码、输出 `IMAGE`/`STRING` 端口、下游节点连接、自动创建图片加载节点、模型下载、工作流导入或执行。`source=static` 仅用于开发和离线验收，不是生产数据源。

## 兼容性

- ComfyUI：使用 ComfyUI 自定义节点 API 和前端扩展 API；建议使用近期稳定版。
- Python：3.10 或更高版本。ComfyUI 环境必须已提供与其版本匹配的 PyTorch；节点不会修改 ComfyUI 的 Python 环境。
- 依赖：`Pillow`、`numpy`；开发测试额外需要 `pytest`。安装清单见 `requirements.txt`。
- 已在 Windows portable ComfyUI、Python 3.14 环境中进行加载和离线测试。

## 安装

在 ComfyUI 的 `custom_nodes` 目录克隆仓库，然后重启 ComfyUI 后端：

```powershell
cd E:\ComfyUI_windows_portable-G314\ComfyUI\custom_nodes
git clone <你的 GitHub 仓库地址> ComfyUI-Civitai-Inspiration
E:\ComfyUI_windows_portable-G314\python_embeded\python.exe -m pip install -r ComfyUI-Civitai-Inspiration\requirements.txt
```

开发时可以使用 junction 接入源码，不复制文件：

```powershell
cmd /c mklink /J "E:\ComfyUI_windows_portable-G314\ComfyUI\custom_nodes\ComfyUI-Civitai-Inspiration" "D:\work_station\ty-comfyui-node\civitai-inspiration"
```

修改 Python 文件后重启 ComfyUI 后端；修改 `web/` 下的 JavaScript 后刷新浏览器。节点加载失败时应先查看 ComfyUI 启动日志。

## 使用

在节点搜索中找到“Civitai 灵感图加载器”，选择 `source=civitai` 后设置站点、关键词、周期、数量和 SFW 选项，执行节点即可显示画廊。`count` 表示请求的结果数量，当前画廊最多显示 9 张。

点击“下一页（执行）”会请求下一页；切换工作流标签不会触发网络请求。勾选 `only_with_prompt` 可只在画廊中显示已检测到提示词的图片。若没有结果，节点会显示空状态。

提示词来自 Civitai API 或图片内嵌 metadata；Civitai 未提供提示词时，角标会显示“无提示词”。这不是对图片内容的判断。

## 网络和权限

默认使用匿名公开 API。若 Civitai 返回 403，可在启动 ComfyUI 的同一终端设置：

```powershell
$env:CIVITAI_API_KEY = "你的 API Key"
```

API Key 只用于请求头，不写入 workflow、输出、日志、缓存或仓库。节点不会绕过登录、付费权限或站点内容限制。

## 缓存和文件

查询缓存位于节点目录下的 `.cache/`，可以安全删除以清理缓存。下载文件位于 ComfyUI `output/ty-node/`。节点不会写入 `models`、`workflows` 或 `input` 目录，也不会使用其他项目的缓存。

## 开发与验证

所有节点共用工作区的 uv 环境：

```powershell
cd D:\work_station\ty-comfyui-node
uv sync
uv run pytest
```

测试使用固定 fixture 和离线静态数据，不依赖实时热榜。发布前还应在目标 ComfyUI 中检查节点注册、前端扩展加载、分页、空结果、下载失败和工作流标签切换。
