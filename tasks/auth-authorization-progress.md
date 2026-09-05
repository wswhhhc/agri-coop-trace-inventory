# 公共认证授权模块进度

## 2026-09-05

### 已完成

- 完成公共授权接口设计，权限和数据范围均从 `AuthContext` 推导。
- 增加合作社范围判断、合作社/仓库范围断言。
- 增加 `require_permission`、`require_cooperative_scope` 和 `require_warehouse_scope`。
- 增加统一的 `PERMISSION_DENIED`（403）和 `RESOURCE_NOT_FOUND`（404）异常构造。
- 增加 11 个公共授权测试，包含 FastAPI CamelCase 路径参数绑定验证。
- 完成 Ruff 和 mypy 检查。

### 当前验证

- 聚焦测试：11 passed。
- 全量测试：110 passed，2 个第三方弃用警告。
- Ruff：通过。
- mypy：通过。

### 范围说明

本任务只完成公共授权能力。具体资源是否存在，以及业务查询是否附加合作社/仓库范围条件，留给后续业务模块实现。
