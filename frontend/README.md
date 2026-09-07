# 前端开发说明

## 启动

在 `frontend/` 目录执行：

```bash
pnpm install
pnpm dev
```

默认访问地址：`http://localhost:5173`。

开发环境默认通过 Vite 代理使用 `/api/v1` 访问 `http://localhost:8000`，可避免本地联调时的跨域问题。部署到独立前端域名时，复制 `.env.example` 为 `.env` 并填写完整的 `VITE_API_BASE_URL`。

如果要用微信在手机上扫描批次二维码，手机和电脑需连接同一局域网，并将后端 `.env` 中的 `PUBLIC_TRACE_URL` 设置为电脑局域网 IP（例如 `http://192.168.1.100:5173/trace`），然后重启前后端服务。

## 当前功能

- 登录、退出登录
- 访问令牌仅保存在内存
- 刷新令牌由后端通过 HttpOnly Cookie 管理
- 登录后加载当前用户、角色、权限和合作社范围
- 未登录访问业务页面自动跳转登录页

## 常用命令

```bash
pnpm test
pnpm type-check
pnpm build
```
