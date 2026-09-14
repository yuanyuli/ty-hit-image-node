# Civitai 灵感图加载器 ComfyUI 独立节点开发规格

## 1. 项目定位

本项目是一个完全独立的 ComfyUI 自定义节点仓库。它参考 `ty-civitai-gallery` 已验证的产品能力和行为，但运行时不依赖该项目的 Python 包、Web 服务、数据库、缓存、目录或本地 API。

节点可以单独克隆、安装、升级、测试和发布。原项目与本节点之间不存在运行时通信和代码依赖。

## 2. 首版目标

提供一个名为“Civitai 灵感图画廊”的纯展示节点：用户输入站点、关键词和筛选条件后，节点读取公开 Civitai 图片并在节点内分页展示。节点没有 ComfyUI 输出端口，不参与下游工作流执行。

当前版本支持 `civitai.com` 和 `civitai.red` 的图片查询，并支持“从本地获取”浏览节点下载历史。视频播放、视频解码和视频输出不在当前版本范围内。

## 3. 非目标

首版不生成图片、不执行外部 workflow、不导入 workflow、不输出图像或文本端口、不自动下载模型、不绕过登录、NSFW、403 或付费权限、不读取浏览器 Cookie。不修改 `ComfyUI\models`、`workflows` 或 `input` 目录；下载按钮只允许写入 `ComfyUI/output/ty-node/`，不使用 `F:\bddownload`。`source=static` 仅用于开发和离线验收。

## 4. 节点接口

节点内部类名为 `CivitaiInspirationLoader`，注册名为 `CivitaiInspirationLoader`，显示名为 `ty-hit-image-node`。保留类名和注册名是为了兼容已经保存的本地 workflow。

输入控件按以下顺序排列：

| 输入 | 类型 | 默认值与约束 |
|---|---|---|
| site | COMBO | `civitai.com`、`civitai.red`、`从本地获取`；默认 `civitai.com` |
| prompt_query | STRING | 可为空，最多 256 个字符 |
| period | COMBO | `Day`、`Week`、`Month`、`AllTime`；默认 `Day` |
| media_type | COMBO | `image`、`video`；默认 `image` |
| count | INT | 1–20；默认 9；代表本次读取上限；画廊最多展示 9 张 |
| sfw | BOOLEAN | 默认 true；不能绕过站点限制 |
| refresh | BOOLEAN | 默认 false；只刷新当前查询缓存 |

可选控件为隐藏字符串 `source`（`static`/`civitai`，默认 `civitai`；仅开发用途）、`page`（从 0 开始的页码）和 `only_with_prompt`（仅显示已检测到提示词的图片）。`source` 对未知旧值（包括历史工作流保存的数字索引）回退为 `civitai`，以保持工作流升级兼容。选择“从本地获取”时只读取 `output/ty-node` 直接子目录中的图片，按修改时间倒序分页，并通过 `/view` URL 展示。当前版本没有任何 ComfyUI 输出端口；提示词、metadata 和来源信息通过画廊交互查看。

内部 metadata 解析仍可区分 A/B/C 类，但当前版本只用于提示词状态和后续扩展，不在节点输出端口暴露，也绝不执行任何 workflow。不伪造缺失字段。

## 5. 用户体验

节点使用中文显示名称、标签和 tooltip，代码字段保留英文。节点分类为 `Civitai/Inspiration`。错误信息必须告诉用户原因、站点、请求条件和可执行的处理方式。

查询失败、权限限制和空结果必须显示可读状态。图片加载失败不得静默替换为其他图片。提示词角标只表示 API 或内嵌 metadata 是否提供了正向提示词，不代表模型或内容质量。

## 6. 独立模块

```text
ComfyUI-Civitai-Inspiration/
├─ __init__.py
├─ nodes.py
├─ civitai_client.py
├─ metadata_parser.py
├─ cache.py
├─ image_loader.py
├─ security.py
├─ tests/
├─ README.md
├─ pyproject.toml
└─ requirements.txt
```

- `nodes.py`：ComfyUI 输入、执行和纯展示 UI 数据适配。
- `civitai_client.py`：官方 HTTPS 请求、分页、超时、重试和状态码映射。
- `metadata_parser.py`：A/B/C 分类、字段归一化和脱敏前结构化处理。
- `cache.py`：查询结果和允许缓存的图片路径。
- `image_loader.py`：图片读取和 metadata 读取。
- `security.py`：URL 白名单、大小限制、SHA-256、临时文件和密钥脱敏。

模块之间使用明确的数据类或 TypedDict 传递数据，不导入主项目模块。

节点不向 ComfyUI 输出图片批次；画廊缩略图由前端直接加载并限制数量。

## 7. 数据和网络策略

站点基址固定为：

- `https://civitai.com/api/v1/`
- `https://civitai.red/api/v1/`

只请求公开 HTTPS 资源。当前版本只请求图片结果。API Key 仅从环境变量读取，不能进入 workflow、输出、日志、缓存或 manifest。分页遇到重复 cursor 立即停止，读取量不得超过 `count` 配置上限。

429 必须尊重 `Retry-After`；403 表示需要授权或内容不可见；404 表示资源不存在；超时可继续使用陈旧画廊并明确标记；无缓存时返回可读错误。

## 8. 缓存和文件安全

缓存键至少包含站点、查询、周期、媒介、SFW、数量、页码和节点版本。`refresh=true` 只刷新当前查询缓存，不删除其他缓存和用户文件。公开版本必须提供可控的过期或清理策略。

图片下载采用临时文件、白名单 URL、最大文件大小、SHA-256 校验、拒绝覆盖和安全文件名。缓存目录位于节点自有缓存目录或用户配置目录，不写入 ComfyUI 模型、工作流和输入素材目录。

## 9. 测试策略

测试不依赖实时热榜：

- 固定 fixture：普通站和 Red 站兼容响应。
- 过滤测试：图片、SFW 和数量上限；视频输入应明确拒绝或提示未支持。
- 分页测试：上限、空页和重复 cursor。
- 展示数据测试：B 类 prompt、C 类缺失 metadata、内嵌 EXIF prompt、only_with_prompt 过滤。
- 错误测试：429、403、404、超时和无缓存。
- 缓存测试：命中、刷新、陈旧缓存和站点切换。
- 安全测试：密钥脱敏、URL 白名单、重定向、大小限制、临时文件和路径穿越。
- ComfyUI 集成测试：最小 fake server，验证节点注册、纯展示 UI 返回、前端扩展加载和路由注册。

## 10. 本地开发与安装

节点仓库与 ComfyUI 分离。开发时使用 Windows junction 接入：

```powershell
$ComfyRoot = "你的 ComfyUI 路径"
$NodeRoot = "你的节点仓库路径"
cmd /c mklink /J "$ComfyRoot\custom_nodes\ComfyUI-Civitai-Inspiration" "$NodeRoot"
```

修改 Python 节点代码后重启 ComfyUI 后端；修改前端资源后刷新浏览器。节点不依赖复制到 ComfyUI 目录，junction 只提供扫描入口。

## 11. 验收标准

给定站点、关键词和数量后，节点能够稳定展示对应页的图片、提示词可用性和下载操作；点击下一页后替换为新页，不叠加旧结果。缺失字段、权限限制、网络错误和空结果都必须明确显示。测试使用 fake server 可重复运行，且节点仓库可以脱离原项目独立安装和运行。

## 12. 图片预览交互

节点提供 ComfyUI 前端扩展，在画廊图片上支持悬停操作：

- “下载”：通过节点后端安全接口把指定原图保存到 `ComfyUI/output/ty-node/`。
扩展和后端接口必须校验 URL、路径归属和文件名；下载失败要在前端显示可读错误。当前版本不自动创建图片加载节点，也不向下游输出文件路径。
