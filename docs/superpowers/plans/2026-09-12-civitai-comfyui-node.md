# Civitai 灵感图加载器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个完全独立、可安装、可测试的 ComfyUI Civitai 灵感图画廊节点。当前产品是纯展示节点，没有 ComfyUI 输出端口；旧版输出端口和自动图片加载节点计划已废弃。

**Architecture:** 节点仓库自行实现 Civitai HTTP 客户端、metadata 归一化、缓存、安全下载和 ComfyUI 类型转换。模块通过数据类传递结构化结果，不依赖 `ty-civitai-gallery` 或本地 Web 服务；ComfyUI 只负责加载注册和执行节点。

**Tech Stack:** Python 3.10+、ComfyUI 节点 API、标准库 `urllib`/`json`/`sqlite3` 或轻量 JSON 缓存、Pillow、pytest、fake HTTP server。

**Spec:** `docs/superpowers/specs/2026-09-12-civitai-comfyui-node-development-design.md`

## Global Constraints

- 运行时不依赖主项目的 Python 包、Web 服务、数据库、缓存或目录。
- 只请求 `https://civitai.com/api/v1/` 和 `https://civitai.red/api/v1/` 的公开 HTTPS 资源。
- API Key 只从环境变量读取，不进入 workflow、输出、日志、缓存或 manifest。
- 不下载模型、不执行 workflow、不读取 Cookie、不写入 ComfyUI 的 models/workflows/input，也不使用 `F:\bddownload`；下载图片只写入 `output/ty-node/`。
- 查询读取量最多为 `count`（1–20），遇到重复 cursor 立即停止。
- 网络超时可返回陈旧缓存并写入 `stale=true`；无缓存时必须给出可读错误。
- 中文显示名称、标签和 tooltip；英文代码字段；节点分类 `Civitai/Inspiration`。
- 修改 Python 节点后需要重启 ComfyUI 后端才能验证。

---

### Task 1: 创建独立仓库骨架和测试入口

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_package.py`
- Create: `.gitignore`
- Create: `README.md`

**Interfaces:**
- Produces importable package root and pytest entry point.

- [ ] **Step 1: 写包加载失败测试**

```python
def test_package_import_exposes_node_mappings():
    import __init__ as package
    assert "CivitaiInspirationLoader" in package.NODE_CLASS_MAPPINGS
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_package.py -q`
Expected: FAIL because package files and mappings do not exist.

- [ ] **Step 3: 添加最小包结构**

在 `__init__.py` 导出 `NODE_CLASS_MAPPINGS`、`NODE_DISPLAY_NAME_MAPPINGS`，初始从 `nodes.py` 导入；在 `pyproject.toml` 固定 Python 版本和 pytest/Pillow 开发依赖。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_package.py -q`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .
git commit -m "chore: scaffold standalone ComfyUI node package"
```

### Task 2: 实现安全策略和站点配置

**Files:**
- Create: `security.py`
- Create: `tests/test_security.py`

**Interfaces:**
- Produces `SiteConfig`, `allowed_url(url: str, site: str) -> bool`, `redact_secrets(value) -> object`, `safe_cache_path(root, key, suffix) -> Path`。

- [ ] **Step 1: 写 URL、密钥和路径测试**

覆盖两个官方基址允许、其他域名/HTTP 拒绝、`api_key` 脱敏、路径穿越拒绝和临时文件后缀。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_security.py -q`
Expected: FAIL。

- [ ] **Step 3: 实现白名单和脱敏**

只允许精确站点域名及 HTTPS；递归处理字典、列表和字符串中的 key/token 字段；缓存路径使用 SHA-256 key，不使用用户输入作为文件名。

- [ ] **Step 4: 运行测试确认通过并提交**

Run: `python -m pytest tests/test_security.py -q`

```bash
git add security.py tests/test_security.py
git commit -m "feat: add URL and secret security helpers"
```

### Task 3: 实现 Civitai 客户端和分页

**Files:**
- Create: `civitai_client.py`
- Create: `tests/test_civitai_client.py`
- Create: `tests/fixtures/civitai_images_page.json`
- Create: `tests/fixtures/civitai_red_images_page.json`

**Interfaces:**
- Produces `QueryParams`、`CivitaiItem`、`CivitaiClient.search(params: QueryParams) -> SearchPage`。
- `SearchPage.items` 为按 API 顺序排列的条目，`next_cursor` 为下一页 cursor 或 `None`。

- [ ] **Step 1: 用 fake server 写分页和过滤测试**

测试站点基址选择、`count` 上限、重复 cursor 停止、图片/视频参数、429 Retry-After、403/404 映射。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_civitai_client.py -q`
Expected: FAIL。

- [ ] **Step 3: 实现请求、重试和响应解析**

使用标准库 HTTP 客户端，设置连接/读取超时；将 429、403、404 和超时转换为明确异常；最多按 `count` 累积条目，重复 cursor 立即停止。

- [ ] **Step 4: 运行测试确认通过并提交**

Run: `python -m pytest tests/test_civitai_client.py -q`

```bash
git add civitai_client.py tests/test_civitai_client.py tests/fixtures
git commit -m "feat: add standalone Civitai client"
```

### Task 4: 实现 metadata A/B/C 归一化

**Files:**
- Create: `metadata_parser.py`
- Create: `tests/test_metadata_parser.py`

**Interfaces:**
- Produces `normalize_item(item: CivitaiItem) -> NormalizedMetadata`。
- `NormalizedMetadata` 包含 `prompt`、`negative_prompt`、`classification`、`models`、`loras`、`parameters`、`workflow_summary`。

- [ ] **Step 1: 写 A/B/C fixture 测试**

A 类验证 workflow 摘要，B 类保留生成参数，C 类 prompt 和模型缺失时返回空字段且保留“只有参考图”分类。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_metadata_parser.py -q`
Expected: FAIL。

- [ ] **Step 3: 实现字段归一化和 workflow 静态摘要**

只读取公开 metadata；不伪造字段；workflow 仅生成节点/依赖摘要，不执行任何内容；所有输出通过脱敏函数。

- [ ] **Step 4: 运行测试确认通过并提交**

Run: `python -m pytest tests/test_metadata_parser.py -q`

```bash
git add metadata_parser.py tests/test_metadata_parser.py
git commit -m "feat: normalize Civitai metadata"
```

### Task 5: 实现缓存和图片预览加载

**Files:**
- Create: `cache.py`
- Create: `image_loader.py`
- Create: `tests/test_cache.py`
- Create: `tests/test_image_loader.py`

**Interfaces:**
- `Cache.get(key) -> CachedQuery | None`
- `Cache.put(key, value) -> None`
- `Cache.clear(key) -> None`
- `load_media(item, cache_dir) -> LoadedImage`
- `stack_images(images, target_size) -> ImageTensor`

- [ ] **Step 1: 写缓存命中、刷新、陈旧和安全下载测试**

测试缓存 key 包含所有筛选参数和版本；超时场景可读取 stale；图片使用临时文件和 SHA-256；视频输入明确拒绝或提示未支持。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_cache.py tests/test_image_loader.py -q`
Expected: FAIL。

- [ ] **Step 3: 实现缓存和媒体转换**

使用节点自有缓存目录；画廊使用官方图片 URL；不向 ComfyUI 输出图像 tensor。

- [ ] **Step 4: 运行测试确认通过并提交**

Run: `python -m pytest tests/test_cache.py tests/test_image_loader.py -q`

```bash
git add cache.py image_loader.py tests/test_cache.py tests/test_image_loader.py
git commit -m "feat: add cache and media loading"
```

### Task 6: 实现 ComfyUI 节点注册和纯展示执行

**Files:**
- Create: `nodes.py`
- Create: `tests/test_node.py`

**Interfaces:**
- `CivitaiInspirationLoader.INPUT_TYPES() -> dict`
- `CivitaiInspirationLoader.RETURN_TYPES == ()`
- `CivitaiInspirationLoader.FUNCTION == "load"`
- `load(...) -> {"ui": {"civitai": [...]}}`

- [ ] **Step 1: 写节点接口和 fake client 执行测试**

验证中文显示映射、输入默认值/范围、纯展示 UI 数据、空结果和 stale 状态。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_node.py -q`
Expected: FAIL。

- [ ] **Step 3: 实现节点执行函数**

规范化输入，生成缓存 key，调用 client 和 parser，生成画廊数据；将异常转换为 ComfyUI 可读的 `RuntimeError`；不生成 ComfyUI 输出端口。

- [ ] **Step 4: 运行测试确认通过并提交**

Run: `python -m pytest tests/test_node.py -q`

```bash
git add nodes.py tests/test_node.py __init__.py
git commit -m "feat: register Civitai inspiration loader node"
```

### Task 7: 完成集成测试、文档和本地接入

**Files:**
- Modify: `tests/test_integration.py`
- Modify: `README.md`
- Create: `scripts/link_to_comfyui.ps1`
- Create: `scripts/unlink_from_comfyui.ps1`

**Interfaces:**
- 集成测试通过 fake server 验证完整节点执行。
- PowerShell 脚本创建和移除指定 ComfyUI `custom_nodes` 下的 junction，不复制源码。

- [ ] **Step 1: 写端到端 fake server 测试**

覆盖站点切换、图片结果、缓存命中、空结果和网络错误；视频输入应明确提示未支持。

- [ ] **Step 2: 运行全量测试确认缺口**

Run: `python -m pytest -q`
Expected: 仅在集成功能尚未实现时失败。

- [ ] **Step 3: 完成 README 和 junction 脚本**

README 写明独立仓库、环境变量、安装方式、缓存目录、重启要求、节点输入输出和限制；脚本默认目标为 `E:\ComfyUI_windows_portable-G314\ComfyUI\custom_nodes`，但允许显式覆盖。

- [ ] **Step 4: 运行全量测试并做本地加载检查**

Run: `python -m pytest -q`

然后创建 junction，重启 ComfyUI，确认日志加载成功并在节点搜索中看到“Civitai 灵感图加载器”。

- [ ] **Step 5: 提交发布前版本**

```bash
git add README.md scripts tests/test_integration.py
git commit -m "test: document and verify ComfyUI integration"
```

### Task 8: 增加图片悬停操作（纯展示节点）

**Files:**
- Create: `download_api.py`
- Create: `web/civitai_inspiration.js`
- Create: `tests/test_download_api.py`

**Interfaces:**
- `download_to_output(url, item_id) -> str`：返回相对 `ty-node/` 的安全文件名。
- 前端扩展在画廊图片 hover 时显示“下载”按钮；当前版本不创建图片加载节点，也不提供输出端口。

- [ ] **Step 1: 写输出目录安全测试**
- [ ] **Step 2: 实现仅允许 output/ty-node 的安全下载**
- [ ] **Step 3: 写前端扩展测试或静态检查**
- [ ] **Step 4: 实现悬停下载按钮和状态提示**
- [ ] **Step 5: 运行全量测试并提交**

## 完成前验证

- `python -m pytest -q` 全部通过。
- 节点仓库脱离 `ty-civitai-gallery` 仍可安装和导入。
- junction 接入本地 ComfyUI 后，重启即可加载节点。
- fake server 测试不依赖实时 Civitai；只做少量官方只读 smoke test。
- 日志、metadata、source_url 和缓存中均不存在 API Key。
