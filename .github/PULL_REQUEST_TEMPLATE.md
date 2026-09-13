## 变更说明

<!-- 用一两句话说明用户能看到什么变化，以及为什么需要它。 -->

## 验证

- [ ] `uv run pytest -q`
- [ ] `node --check web/civitai_inspiration.js`（如果修改前端）
- [ ] 在最新 ComfyUI 中完成最小 smoke test（如果修改节点或前端）

## 安全与兼容性

- [ ] 没有提交 API Key、Cookie、个人图片、缓存或本地绝对路径
- [ ] 没有扩大下载域名、文件写入范围或登录态权限
- [ ] 已更新 README/CHANGELOG/兼容性说明（如适用）
- [ ] 已考虑旧 workflow 的 `CivitaiInspirationLoader` 兼容别名

## 发布说明

<!-- 需要用户知道的限制、迁移步骤或外部服务变化。 -->
