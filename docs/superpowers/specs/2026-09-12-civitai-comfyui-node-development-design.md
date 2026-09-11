# Civitai 灵感图加载器 ComfyUI 独立节点开发规格

## 1. 项目定位

本项目是一个完全独立的 ComfyUI 自定义节点仓库。它参考 `ty-civitai-gallery` 已验证的产品能力和行为，但运行时不依赖该项目的 Python 包、Web 服务、数据库、缓存、目录或本地 API。

节点可以单独克隆、安装、升级、测试和发布。原项目与本节点之间不存在运行时通信和代码依赖。

## 2. 首版目标

提供一个名为“Civitai 灵感图加载器”的节点：用户输入站点、关键词和筛选条件后，节点读取公开 Civitai 内容，按序号选择一条结果，并输出图片、提示词、脱敏 metadata、来源信息和可选图片批次。

支持 `civitai.com` 和 `civitai.red`。支持图片和视频查询；视频结果输出可用预览图或首帧，metadata 必须明确标记原始媒体类型和视频来源。

## 3. 非目标

首版不生成图片、不执行外部 workflow、不导入 workflow、不自动下载模型、不绕过登录、NSFW、403 或付费权限、不读取浏览器 Cookie、不修改 `ComfyUI\models`、`workflows`、`input`、`output` 目录，也不使用 `F:\bddownload`。

## 4. 节点接口

节点内部类名为 `CivitaiInspirationLoader`，注册名为 `CivitaiInspirationLoader`，显示名为“Civitai 灵感图加载器”。

输入控件按以下顺序排列：

| 输入 | 类型 | 默认值与约束 |
|---|---|---|
| site | COMBO | `civitai.com`、`civitai.red`；默认 `civitai.com` |
| prompt_query | STRING | 可为空，最多 256 个字符 |
| period | COMBO | `Day`、`Week`、`Month`、`AllTime`；默认 `Day` |
| media_type | COMBO | `image`、`video`；默认 `image` |
| count | INT | 1–20；默认 10；代表本次读取上限 |
| result_index | INT | 1–20；默认 1；选择结果序号 |
| model | STRING | 可为空；精确或关键词筛选 |
| family | STRING | 可为空 |
| base_model | STRING | 可为空 |
| lora | STRING | 可为空 |
| sfw | BOOLEAN | 默认 true；不能绕过站点限制 |
| refresh | BOOLEAN | 默认 false；只清除本查询缓存 |

输出顺序：

| 输出 | ComfyUI 类型 | 语义 |
|---|---|---|
| image | IMAGE | `result_index` 对应的单张图；加载失败时明确报错 |
| prompt | STRING | 正向提示词；缺失时为空字符串 |
| negative_prompt | STRING | negative prompt；缺失时为空字符串 |
| metadata | STRING | 脱敏 JSON，包含 ID、作者、时间、模型、LoRA、参数、A/B/C 分类及 stale 标记 |
| source_url | STRING | 图片 URL、页面 URL、站点和查询摘要 |
| batch | IMAGE | 前 `count` 张图片组成的批次；统一到首张图尺寸后按 ComfyUI 图像批次语义返回 |

A 类结果可在 metadata 中包含通过静态检查的 workflow 摘要，但绝不执行。B 类标记为“只有生成参数”，C 类标记为“只有参考图”。不伪造缺失字段。

## 5. 用户体验

节点使用中文显示名称、标签和 tooltip，代码字段保留英文。节点分类为 `Civitai/Inspiration`。错误信息必须告诉用户原因、站点、请求条件和可执行的处理方式。

结果序号越界必须直接报错并说明实际结果数量。单张图片加载失败不得静默替换为其他序号。视频结果优先使用站点提供的预览图或缩略图；没有可用预览图时明确报错，不在首版引入本地视频解码依赖。视频结果在输出中标注“视频预览图”，并保留原始视频 URL。

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

- `nodes.py`：ComfyUI 输入输出和执行函数适配。
- `civitai_client.py`：官方 HTTPS 请求、分页、超时、重试和状态码映射。
- `metadata_parser.py`：A/B/C 分类、字段归一化和脱敏前结构化处理。
- `cache.py`：查询结果和允许缓存的图片路径。
- `image_loader.py`：图片读取、视频预览图读取和 `IMAGE` tensor 转换。
- `security.py`：URL 白名单、大小限制、SHA-256、临时文件和密钥脱敏。

模块之间使用明确的数据类或 TypedDict 传递数据，不导入主项目模块。

批次图片以首张成功图片的宽高为目标尺寸，使用保持比例的缩放和边缘填充统一尺寸，避免不同尺寸图片无法堆叠为 ComfyUI `IMAGE`。

## 7. 数据和网络策略

站点基址固定为：

- `https://civitai.com/api/v1/`
- `https://civitai.red/api/v1/`

只请求公开 HTTPS 资源。API Key 仅从环境变量读取，不能进入 workflow、输出、日志、缓存或 manifest。分页遇到重复 cursor 立即停止，读取量不得超过 `count` 配置上限。

429 必须尊重 `Retry-After`；403 表示需要授权或内容不可见；404 表示资源不存在；超时可返回陈旧缓存并在 metadata 写入 `stale=true`；无缓存时返回可读错误。

## 8. 缓存和文件安全

缓存键至少包含站点、查询、周期、媒介、模型筛选、SFW、数量和节点版本。`refresh=true` 只删除当前查询缓存，不删除其他缓存和用户文件。

图片下载采用临时文件、白名单 URL、最大文件大小、SHA-256 校验、拒绝覆盖和安全文件名。缓存目录位于节点自有缓存目录或用户配置目录，不写入 ComfyUI 模型、工作流和输入素材目录。

## 9. 测试策略

测试不依赖实时热榜：

- 固定 fixture：普通站和 Red 站兼容响应。
- 过滤测试：图片/视频、SFW、模型字段。
- 分页测试：上限和重复 cursor。
- 输出测试：序号边界、B 类 prompt、C 类缺失 metadata、A 类 workflow 摘要。
- 错误测试：429、403、404、超时和无缓存。
- 缓存测试：命中、刷新、陈旧缓存和站点切换。
- 安全测试：密钥脱敏、URL 白名单、大小限制、临时文件和路径穿越。
- ComfyUI 集成测试：最小 fake server，验证节点注册、执行和 `IMAGE` 输出。

## 10. 本地开发与安装

节点仓库与 ComfyUI 分离。开发时使用 Windows junction 接入：

```powershell
cmd /c mklink /J "E:\ComfyUI_windows_portable-G314\ComfyUI\custom_nodes\ComfyUI-Civitai-Inspiration" "<节点仓库路径>"
```

修改 Python 节点代码后重启 ComfyUI 后端；修改前端资源后刷新浏览器。节点不依赖复制到 ComfyUI 目录，junction 只提供扫描入口。

## 11. 验收标准

给定站点、关键词和数量后，节点能够稳定返回对应序号的图片或视频预览图、提示词、来源 URL 和脱敏 JSON。缺失字段、权限限制、网络错误和序号越界都必须明确显示。测试使用 fake server 可重复运行，且节点仓库可以脱离原项目独立安装和运行。

## 12. 图片预览交互

节点提供 ComfyUI 前端扩展，在批次图片预览上支持悬停操作：

- “下载”：通过节点后端安全接口把指定原图保存到 `ComfyUI/output/ty-node/`。
- “加载”：自动创建一个 `Civitai Image Loader` 节点，并填入该文件的安全相对路径。

`Civitai Image Loader` 只允许读取 `output/ty-node/` 下的文件，不使用绝对路径，不复制到 `input/`。扩展和后端接口必须校验路径归属、文件名和请求来源；下载失败要在前端显示可读错误。
