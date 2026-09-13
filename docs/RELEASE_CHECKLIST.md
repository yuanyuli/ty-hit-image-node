# ty-hit-image-node 发布检查清单

这份清单用于每次公开发布或打 tag 前的验收。没有证据的项目不要标记为完成。

## 代码和仓库

- [ ] 版本号已同步到 `pyproject.toml`、发布说明和 Git tag。
- [ ] `git status` 只包含本次发布明确需要的文件。
- [ ] 没有 `.cache/`、虚拟环境、个人 workflow、下载图片、API Key、Cookie 或本地绝对路径被提交。
- [ ] `LICENSE`、`README.md`、`CHANGELOG.md` 和贡献说明已更新。
- [ ] 兼容别名和迁移说明经过确认。

## 自动化验证

```powershell
cd D:\work_station\ty-comfyui-node\civitai-inspiration
uv run pytest -q
node --check web\civitai_inspiration.js
```

- [ ] 测试全部通过。
- [ ] Python 文件能被目标 ComfyUI Python 编译。
- [ ] 失败测试没有被跳过或静默忽略。

## 最新 ComfyUI 验证

- [ ] 在最新稳定 ComfyUI 中全新加载节点。
- [ ] 节点显示为 `ty-hit-image-node`，默认值可直接执行。
- [ ] 加载、刷新、下一页、搜索条件重置和空结果均已验证。
- [ ] 画廊不会重复叠加，节点尺寸变化不会越界。
- [ ] 切换工作流标签后返回，节点和画廊仍能恢复。
- [ ] prompt 角标、详情面板、复制和原帖链接已验证。
- [ ] 单张下载和当前页下载成功；非法 URL、非图片和超限响应被拒绝。
- [ ] 403、429、5xx、超时和无网络时显示可读状态。

## 安全与隐私

- [ ] 下载 URL 只允许 Civitai 官方站点/CDN，跨域重定向会被拒绝。
- [ ] 文件名、输出路径和临时文件经过安全校验。
- [ ] API Key 不会出现在日志、缓存、UI、workflow 或发布产物。
- [ ] 仅请求公开图片资源，不读取浏览器 Cookie，不绕过权限或验证码。
- [ ] README 已说明图片版权、Civitai 服务条款和第三方服务边界。

## 发布产物

- [ ] GitHub README 的安装命令、节点名称和当前输入契约与代码一致。
- [ ] CHANGELOG 说明本版本新增、修复和已知限制。
- [ ] issue 模板可正常创建 Bug 和功能请求。
- [ ] Release 页面包含版本号、发布日期、验证环境和已知限制。
- [ ] 发布后用干净目录 clone 一次，按 README 完成安装和最小 smoke test。
