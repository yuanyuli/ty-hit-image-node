# ComfyUI-Civitai-Inspiration

独立的 Civitai 灵感图 ComfyUI 节点。

## 安装

将本仓库放入 ComfyUI 的 `custom_nodes`，或开发时创建 junction：

```powershell
cmd /c mklink /J "E:\ComfyUI_windows_portable-G314\ComfyUI\custom_nodes\ComfyUI-Civitai-Inspiration" "D:\work_station\ty-comfyui-node\civitai-inspiration"
```

修改 Python 文件后必须重启 ComfyUI 后端。

## 使用

搜索“Civitai 灵感图加载器”，设置站点、关键词、数量和结果序号，点击执行队列。节点输出顺序为：

1. `image`：选中序号的图片
2. `prompt`
3. `negative_prompt`
4. `metadata`
5. `source_url`
6. `batch`：前 `count` 条可加载图片

`image` 和 `batch` 才能连接到图像预览节点；metadata、prompt 和 source_url 是文本输出。

执行完成后，节点内会显示批次画廊。鼠标悬停缩略图可下载到 ComfyUI 的 `output/ty-node/`，或自动创建“Civitai 图片加载器”节点。

## 网络和权限

默认使用匿名公开 Civitai API。如果站点返回 403，可在启动 ComfyUI 的同一终端设置：

```powershell
$env:CIVITAI_API_KEY = "你的 API Key"
```

API Key 只放入请求头，不保存到 workflow、缓存或日志。

## 开发

所有节点共用父目录的 uv 环境：

```powershell
cd D:\work_station\ty-comfyui-node
uv sync
uv run pytest
```

本节点不依赖 `ty-civitai-gallery` 的代码或服务。
