# 审计日志查询接口记录书

## 2026-09-06

- 已创建执行书，范围仅限审计日志只读查询。
- 已核对接口与数据库文档：接口要求 `audit:read`；仓库工作人员仅本人；审计日志禁止写接口；`detail` 是已脱敏上下文。
- 已核对现有基础设施：可复用 `PageParams`、`ListResponse`、分页构造器、认证上下文与统一 403/404 异常语义。
- 已识别模型字段映射：文档 `resourceType/resourceId` 对应 ORM `object_type/object_id`。
- 下一步：先补 RED 契约测试，再实现查询链路。

## 2026-09-06（RED）

- 已新增 `backend/tests/unit/test_audit_log_query.py`。
- RED 验证：`uv run pytest backend/tests/unit/test_audit_log_query.py -q` 结果为 `3 failed`，均因 `/api/v1/audit-logs` 尚未注册而返回 404，符合预期。
- 已完成阶段 1，进入阶段 2。

## 2026-09-06（实现中）

- 已新增审计查询 Schema、Repository、Service、API 路由，并注册到应用。
- 已提取审计详情敏感键识别与脱敏工具，写入校验和查询响应共用同一规则；响应投影明确排除 IP 地址、User-Agent。
- 首轮 GREEN 发现测试夹具 `now` 初始化顺序错误及 3 项 Ruff 问题，未继续重试相同命令，已针对性修正后待复验。
- GREEN 验证：`uv run pytest backend/tests/unit/test_audit_log.py backend/tests/unit/test_audit_log_query.py -q` 为 `6 passed`；相关 Ruff、mypy 均通过。
- 已补齐过滤参数、响应脱敏规则至接口设计说明书；下一步进行阶段复查与首次提交。

## 2026-09-06（阶段复查）

- 复查结论：查询链路仅调用 Repository 的 `list_scoped/get_scoped`，没有审计写入、更新或删除入口；合作社过滤与仓库工作人员本人过滤均在 Repository 查询条件内生效。
- 安全复查：响应使用显式投影，IP 地址和 User-Agent 不出现；`detail` 按与写入校验共用的敏感键集合递归脱敏。
- 验证：聚焦测试 `6 passed`；新增及改动文件 Ruff、mypy 通过；`git diff --check` 通过。
- 阶段复查补充系统管理员全局读取、详情脱敏和非法时间范围 422 契约测试。
