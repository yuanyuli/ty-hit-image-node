# 兼容性与支持范围

## 支持目标

项目以当前最新稳定版 ComfyUI 为唯一主要验证目标。节点使用 ComfyUI 的自定义节点注册机制、`OUTPUT_NODE` 纯展示执行协议和前端扩展 API。

每次发布前需要在最新 ComfyUI 中验证：

- 节点能注册并显示为 `ty-hit-image-node`。
- 默认输入可以直接执行。
- 前端画廊可以创建、更新、销毁和恢复。
- 切换工作流标签后再次显示节点时，画廊状态不会破坏工作流。
- 下载路由、分页、空结果和错误状态可用。
- 画廊按钮通过 `partialExecutionTargets` 局部执行，只运行本节点及必要依赖。

## 平台

- Windows portable：主要开发和验收环境。
- Windows 源码安装：支持，路径由 ComfyUI 自己决定。
- Linux/macOS：代码使用标准 Python 和 ComfyUI API，理论上支持；发布前应在目标平台运行本仓库测试和一次真实 ComfyUI smoke test。

## Python 和依赖

节点要求 Python 3.10 或更高版本，并依赖：

- Pillow >= 10.0
- NumPy >= 1.26

开发测试额外使用 pytest。依赖应安装到 ComfyUI 自己的 Python 环境，或者由 ComfyUI Manager 按仓库清单处理；不要为了本节点修改系统 Python 或另一套 ComfyUI 环境。

## 版本策略

节点注册名 `TyHitImageNode` 是当前内部类型。`CivitaiInspirationLoader` 作为兼容别名保留，直到另行发布迁移说明。

ComfyUI 旧版如果缺少当前前端扩展 API，不保证画廊正常工作。遇到问题时请先升级 ComfyUI，并在 issue 中同时提供 ComfyUI commit/tag 和浏览器版本。

## 外部服务兼容性

Civitai API、详情页状态数据、图片 CDN 和访问策略由 Civitai 控制。节点会对官方域名、响应类型、重定向和大小做校验，但无法保证第三方服务永久保持同样的字段和 URL 结构。外部接口变化属于需要升级节点或调整适配器的兼容性事件。
