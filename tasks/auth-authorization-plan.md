# 公共认证授权模块任务计划

## 范围

只实现认证上下文之上的公共功能权限和数据范围校验能力，不接入库存、批次、仓库或其他业务路由、服务、仓储和模型。

## 设计约束

- 权限来源只能是 `AuthContext.permission_codes`。
- 合作社范围来源只能是 `AuthContext.cooperative_id`。
- 仓库范围来源只能是 `AuthContext.warehouse_ids`。
- 请求中的 ID 只能作为待校验目标，不能作为授权依据。
- 功能权限不足返回 403 `PERMISSION_DENIED`。
- 数据范围不匹配返回 404 `RESOURCE_NOT_FOUND`。
- 公共模块不负责判断具体业务资源是否存在；资源查询由后续业务模块使用范围条件完成。

## 实施任务

### 任务1：认证上下文范围判断

- [x] 增加合作社范围判断。
- [x] 保留系统管理员的全局范围语义。

### 任务2：公共授权依赖

- [x] 实现 `require_permission(permission_code)`。
- [x] 实现合作社范围断言和 FastAPI 依赖。
- [x] 实现仓库范围断言和 FastAPI 依赖。
- [x] 提供统一的 403/404 异常构造函数。

### 任务3：测试与导出

- [x] 增加公共授权单元测试。
- [x] 验证 CamelCase 路径参数可以被依赖正确绑定。
- [x] 从 `app.core.auth` 统一导出公共接口。

## 验收标准

- [x] 有权限的上下文可以通过权限依赖。
- [x] 缺少功能权限时返回 403。
- [x] 合作社越权和仓库越权时返回 404。
- [x] 全局范围上下文可以通过合作社和仓库范围判断。
- [x] 空仓库范围不能访问任何仓库。
- [x] 公共模块没有引入业务模块依赖。

## 涉及文件

- `backend/app/core/auth/context.py`
- `backend/app/core/auth/authorization.py`
- `backend/app/core/auth/__init__.py`
- `backend/tests/unit/test_authorization.py`

## 明确不涉及

- 业务 API 路由及业务服务。
- 业务仓储的范围查询改造。
- 数据库模型、迁移和演示数据。
- 前端权限控制。
