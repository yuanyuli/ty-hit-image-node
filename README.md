# ty-hit-image-node

`ty-hit-image-node` 是一个 **ComfyUI 自定义节点**，用于在 ComfyUI 画布中浏览 Civitai 公开图片。

它把 Civitai 的图片搜索、分页浏览、提示词识别、详情查看、提示词复制和安全下载集中到一个节点里。安装到 `ComfyUI/custom_nodes/` 并重启 ComfyUI 后，就可以在节点搜索中找到 `ty-hit-image-node`。

> 当前版本是纯展示节点：它没有任何 ComfyUI 输出端口，也不会把图片、提示词或 metadata 传给下游节点。

## 能做什么

- 从 `civitai.com` 或 `civitai.red` 查询公开图片。
- 从“从本地获取”读取曾下载到 `output/ty-node/` 的历史图片，按修改时间倒序浏览。
- 按关键词、时间范围、SFW 和排序条件筛选。
- 在节点内以网格浏览当前页，使用“下一页（执行）”继续读取结果。
- 用角标区分“有提示词”和“无提示词”。
- 点击图片查看大图和详情；复制正向提示词、负面提示词、workflow 或完整 metadata，并查看已识别的模型与 LoRA。
- 将单张图片或当前页图片下载到 ComfyUI 的 `output/ty-node/`。
- 使用本地缓存减少重复请求；网络暂时不可用时尽可能保留陈旧结果并标记状态。

节点的定位是“Civitai 灵感浏览器”。它不生成图片，不执行外部 workflow，也不替代 ComfyUI 的 `Load Image`、提示词编码或模型节点。

## 产品边界

当前公开版只支持图片查询和预览。以下能力明确不在范围内：

- 视频查询、视频播放、视频解码和视频下载。
- `IMAGE`、`STRING`、`JSON` 或文件路径输出端口。
- 自动创建下游图片加载节点或自动把 prompt 接入工作流。
- 模型、LoRA、工作流和其他 Civitai 资源下载。
- 绕过登录、付费权限、NSFW 限制、验证码或站点访问策略。
- 读取浏览器 Cookie，或调用 `ty-civitai-gallery` 的服务、数据库和缓存。

仓库中的 `source=static` 是开发和离线验收用的数据源，默认隐藏，不是生产数据源。

## 兼容性

| 项目 | 支持范围 |
| --- | --- |
| ComfyUI | 当前最新稳定版；使用 ComfyUI 自定义节点 API 和前端扩展 API |
| 操作系统 | Windows portable、Windows 源码安装；Linux/macOS 应遵循同样的 ComfyUI 目录结构 |
| Python | 3.10 或更高版本，以当前 ComfyUI 要求为准 |
| 运行时依赖 | Pillow、NumPy；节点不会替换或升级 ComfyUI 的 PyTorch |
| 浏览器 | ComfyUI 当前支持的 Chromium/Firefox 浏览器 |

项目只承诺跟随最新 ComfyUI 版本验证。旧版 ComfyUI 的前端生命周期 API 可能不同，遇到兼容问题请先升级 ComfyUI，再提交 issue 时附上版本信息。

## 安装

### 手动安装

在 ComfyUI 的 `custom_nodes` 目录执行：

```powershell
$ComfyRoot = "你的 ComfyUI 路径"
cd "$ComfyRoot\custom_nodes"
git clone <你的 GitHub 仓库地址> ComfyUI-TyHitImageNode
& "$ComfyRoot\python_embeded\python.exe" -m pip install -r ComfyUI-TyHitImageNode\requirements.txt
```

Linux/macOS 示例：

```bash
cd /path/to/ComfyUI/custom_nodes
git clone <你的 GitHub 仓库地址> ComfyUI-TyHitImageNode
python3 -m pip install -r ComfyUI-TyHitImageNode/requirements.txt
```

安装依赖后完全重启 ComfyUI 后端，再刷新浏览器页面。修改 Python 文件需要重启后端；只修改 `web/` 下的 JavaScript 时，刷新浏览器即可。

### 开发者接入

开发时可以使用 junction/symlink 指向源码，避免复制仓库：

```powershell
$ComfyRoot = "你的 ComfyUI 路径"
$NodeRoot = "你的节点仓库路径"
cmd /c mklink /J "$ComfyRoot\custom_nodes\ComfyUI-TyHitImageNode" "$NodeRoot"
```

仓库中的 `scripts/restart_comfyui.ps1` 仅服务于本地开发。公开用户不需要运行它，也不需要安装仓库的开发依赖。

## 第一次使用

1. 在 ComfyUI 节点搜索中输入 `ty-hit-image-node`，添加节点。
2. 保持默认值，点击节点内的“加载灵感图”。默认查询公开图片，数量为 9，SFW 开启。
3. 修改关键词、周期、数量、排序或 SFW 后，再点击“加载灵感图”。搜索条件变化会从第 1 页开始。
4. 需要绕过缓存重新查询时，点击“刷新结果”。“下一页（执行）”会继续当前查询的 cursor 分页。
5. 鼠标悬停图片可下载；点击图片可查看详情。提示词角标可以复制相应文本。
6. `site`、`周期` 和 `排序` 等下拉参数支持右键循环选择；右键会切换到下一个选项，循环到末尾后回到第一个选项。

### 控件说明

| 控件 | 说明 |
| --- | --- |
| 站点 | `civitai.com`、`civitai.red` 或“从本地获取” |
| 关键词 | Civitai 图片搜索关键词，可为空 |
| 周期 | Day、Week、Month、AllTime |
| 数量 | 每页请求和显示的上限，范围 1–9 |
| SFW | 将查询限制为站点允许的安全内容；不会绕过站点限制 |
| 排序 | Most Reactions、Most Comments、Most Downloaded、Newest、Oldest |
| 仅显示有提示词 | 只展示已检测到正向提示词的结果；如果当前页不足，节点会继续读取后续页 |

选择“从本地获取”后，节点只读取 `<ComfyUI>/output/ty-node/` 目录中的历史图片，不访问 Civitai。结果按文件修改时间倒序分页；关键词可匹配文件名或图片内嵌 prompt。本地图片已经在输出目录中，因此不会显示重复下载按钮。

提示词来源可能是 Civitai API metadata、公开详情页状态数据或图片内嵌 metadata。详情中的模型和 LoRA 来自公开 metadata 的 `models`、`loras` 或 `resources` 字段；未公开或无法识别时显示“未检测到”。工作流 JSON、模型信息或任意非提示词字段不会被冒充为正向提示词。角标表示“检测到正向提示词”，不代表提示词质量，也不保证负面提示词存在。

## API Key（可选）

匿名公开接口通常可以直接使用。如果 Civitai 返回 403，说明当前内容或接口需要授权，可以在启动 ComfyUI 的同一个终端设置：

```powershell
$env:CIVITAI_API_KEY = "你的 API Key"
```

然后从该终端启动或重启 ComfyUI。Linux/macOS：

```bash
export CIVITAI_API_KEY="你的 API Key"
```

节点只从进程环境读取 API Key，不把它写入 workflow、节点 UI、缓存、下载文件名、日志或仓库。不要把 API Key 写进 README、工作流或截图中。

## 下载、缓存和隐私

- 下载目标固定为 `<ComfyUI>/output/ty-node/`，不会写入 `models`、`workflows` 或 `input`。
- 下载地址必须属于 Civitai 官方站点或其官方 CDN；跨到其他域名会被拒绝。
- 下载使用临时文件、大小限制、图片类型校验和安全文件名，避免路径穿越和覆盖任意文件。
- 查询缓存位于本仓库的 `.cache/`。删除该目录即可清理本地查询缓存；缓存不包含 API Key。
- 节点会向 Civitai 请求公开 API 和图片资源。搜索关键词、请求时间、站点和网络地址可能被 Civitai 记录，具体以 Civitai 的隐私政策和服务条款为准。
- 图片版权、作者许可和再利用条件由原作者与 Civitai 规则决定。下载按钮只代表用户主动保存，不授予再发布权利。

## 故障排查

**节点搜索不到**

确认仓库位于 `ComfyUI/custom_nodes/` 的一级目录中，检查 ComfyUI 启动日志，然后完全重启后端。节点注册名为 `TyHitImageNode`，显示名为 `ty-hit-image-node`。

**点击后提示 403**

这通常表示内容不可见或需要授权。设置 `CIVITAI_API_KEY` 后重启 ComfyUI；节点不会绕过账号权限或验证码。

**提示 429、5xx、超时或“使用陈旧缓存”**

先检查网络和 Civitai 状态。节点会对可重试状态进行有限重试，并尽量展示已有缓存。点击“刷新结果”可以在服务恢复后重新请求当前页。

**图片能打开但没有提示词**

该图片可能确实没有公开正向提示词，或者作者只上传了工作流/模型信息。角标只在检测到正向提示词时显示“有提示词”，不会把 workflow JSON 当作 prompt。

**下载失败或提示不允许重定向**

确认使用的是最新版本。Civitai 图片可能跳转到官方 CDN；节点只允许 Civitai 官方域名之间的跳转。其他域名、非图片响应或超出大小限制都会被拒绝。

**修改代码后界面没有变化**

Python 修改需要重启 ComfyUI 后端；前端 JavaScript 修改需要浏览器硬刷新。若使用 junction，确认链接目标仍指向当前仓库。

## 开发与验证

所有节点共用工作区的 uv 环境：

```powershell
$WorkspaceRoot = "你的节点工作区路径"
cd $WorkspaceRoot
uv sync
uv run pytest -q
```

测试使用固定 fixture、fake server 和静态数据，不依赖实时热点。提交前至少运行：

```powershell
uv run pytest -q
node --check civitai-inspiration\web\civitai_inspiration.js
```

真实 ComfyUI 验证应检查节点注册、默认输入、前端扩展、空结果、分页、缓存、下载失败、工作流标签切换和 API 403/5xx 错误提示。详见 [发布检查清单](docs/RELEASE_CHECKLIST.md)。

## 贡献和反馈

请先搜索已有 issue，再使用仓库的 issue 模板提交问题。Bug 报告请附：ComfyUI 版本、操作系统、Python 版本、节点版本、复现步骤、ComfyUI 日志和是否使用 API Key。提交日志和截图前请删除 API Key、Cookie、本地路径中的敏感信息。

欢迎提交只涉及文档、测试和兼容性修复的 PR。新增网络来源、改变下载范围或引入登录态之前，请先开 issue 讨论产品边界和服务条款。

## 许可证与第三方服务

本节点代码使用仓库中的 [MIT License](LICENSE)。Civitai 是独立的第三方服务，节点不代表 Civitai，也不改变 Civitai 对图片、metadata、API 和内容的授权规则。使用本节点即表示你仍需遵守 Civitai 的服务条款、API 限制和当地法律。

## 版本状态

当前版本定位为公开 Beta。核心功能已在最新 ComfyUI 环境验证，但 Civitai API、详情页结构和 CDN 行为属于外部依赖，可能在无通知的情况下变化。版本变化见 [CHANGELOG](CHANGELOG.md)。
