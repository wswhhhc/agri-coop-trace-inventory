# 前端开发说明

## 启动

在 `frontend/` 目录执行：

```bash
pnpm install
pnpm dev
```

默认访问地址：`http://localhost:5173`。

后端接口默认使用 `http://localhost:8000/api/v1`，如需修改，复制 `.env.example` 为 `.env` 后调整 `VITE_API_BASE_URL`。

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
