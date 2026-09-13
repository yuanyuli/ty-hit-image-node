# 更新日志

本文件记录 `ty-hit-image-node` 的用户可见变化。日期使用 `YYYY-MM-DD`。

## [Unreleased]

- 继续验证最新 ComfyUI 前端生命周期和 Civitai API 变化。
- 收集公开 Beta 用户反馈，优先修复分页、提示词识别和下载兼容问题。

## [0.1.0] - 2026-09-13

### 新增

- 纯展示版 `ty-hit-image-node`，支持 Civitai 图片查询、网格预览和 cursor 分页。
- 支持 `civitai.com`、`civitai.red`、关键词、周期、数量、SFW 和排序筛选。
- 支持提示词状态角标、正向/负面提示词复制、完整 metadata 查看和原帖打开。
- 支持单张下载和当前页下载到 `output/ty-node/`。
- 支持查询缓存、陈旧缓存提示、静态离线数据源和 `only_with_prompt` 过滤。
- 支持 Civitai API metadata、详情页状态数据和图片内嵌 metadata 的分层读取。
- 增加独立测试、安全 URL 校验、大小限制、临时文件和路径安全策略。

### 兼容性

- 节点内部类型为 `TyHitImageNode`。
- 保留 `CivitaiInspirationLoader` 注册别名，避免早期本地 workflow 无法加载。
- 当前版本按最新稳定 ComfyUI 验证；旧版 ComfyUI 不在兼容承诺范围内。

### 已知限制

- 只支持图片；视频和视频 metadata 不属于当前版本范围。
- Civitai API、详情页和 CDN 是外部依赖，服务端限流、403、改版或网络故障可能影响结果。
- prompt 是否可用取决于作者公开 metadata；“无提示词”不代表图片一定没有生成信息。
- 本节点没有输出端口，不能直接把图片或 prompt 接到下游工作流。
