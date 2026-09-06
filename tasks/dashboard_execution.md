# dashboard 模块任务执行书

## 目标

完成后端 `dashboard` 数据大屏模块：在当前登录用户的数据范围内，提供汇总、库存趋势、预警分布、产品排行和预测对比查询；复用已有认证、数据范围、库存、预警和预测能力，不重复实现业务规则；补齐测试、文档和最终质量复查。

## 范围

- `GET /dashboard/summary`
- `GET /dashboard/inventory-trends`
- `GET /dashboard/alert-distribution`
- `GET /dashboard/product-ranking`
- `GET /dashboard/forecast-comparison`
- 查询参数校验、分页/数量上限、时间范围、仓库范围和权限隔离
- dashboard 查询仓储/服务/API、必要的缓存降级
- 单元/集成测试、接口文档同步、质量门禁

## 不在本次范围

- 前端页面（当前 `frontend/` 无实现）
- Excel 报表导出和导出任务
- 审计查询
- 新增库存、预警、预测领域业务能力
- 修改既有数据库密码或提交 `.env`

## 执行阶段

- [completed] D0 现状盘点与契约冻结
- [completed] D1 查询契约、聚合模型与权限边界
- [completed] D2 汇总与库存趋势查询
- [completed] D3 预警分布与产品排行查询
- [completed] D4 预测对比查询与缓存策略
- [in_progress] D5 路由注册、文档同步与接口回归
- [pending] D6 全面复查、质量门禁与最终提交

## 每阶段执行规则

1. 先写行为测试，确认 RED；再实现最小闭环，确认 GREEN。
2. 每完成一个阶段，在本文件和 `progress.md` 记录修改文件、测试和遗留问题。
3. 每完成一个大功能，复查暂存差异、敏感信息和测试后，使用中文提交说明提交一次 Git。
4. 全部功能完成后执行一次全面代码复查，修复问题后再次运行完整门禁并作最终提交。
5. 测试数据库连接优先读取 `backend/.env`，不得把密码写入代码、日志或提交内容。

## 验收标准

- 五个接口可访问，响应模型稳定，错误遵循现有统一错误契约。
- 所有结果按合作社/角色/授权仓库进行数据范围隔离；预测对比额外校验预测读取权限。
- 时间范围、仓库筛选和数量参数有边界校验；聚合查询不出现无界读取或 N+1 查询。
- Redis 可用时使用短 TTL 缓存，缓存不可用时大屏查询可回源 PostgreSQL；缓存键包含数据范围和筛选条件。
- 相关测试、mypy、Ruff 和项目严格门禁通过；既有工作区修改和 `.idea/workspace.xml` 不被纳入提交。

## 已冻结的响应契约

- `summary`：产品数、批次数、按单位库存汇总、待处理预警数、即将到期批次数、低库存产品数、统计时间。
- `inventory-trends`：按自然日返回入库量、出库量、期末库存量；库存量按单位拆分，避免跨单位相加。
- `alert-distribution`：按预警类型和等级返回数量，附总数。
- `product-ranking`：按产品返回出库数量和出库次数，按出库数量降序并以产品 ID 稳定排序，支持 `limit` 上限。
- `forecast-comparison`：按预测结果返回预测区间、预测需求、测试集实际出库量、误差指标和模型版本；只允许具备 `model:read` 的用户访问。
- 日期参数使用 `startDate`/`endDate`，均为日期且 `startDate <= endDate`；未传时由服务端使用最近 30 个自然日，预测对比未传时同样使用最近 30 日。

## 错误记录

| 错误 | 次数 | 解决方案 |
|---|---:|---|
| 技能路径初次拼接错误 | 1 | 按实际目录改为 `agent-skills/skills/<skill>/SKILL.md` |

## 阶段记录

### D1 查询契约、聚合模型与权限边界

- 新增 `backend/app/schemas/dashboard.py`：冻结五类接口的筛选参数和响应模型，日期范围最多 366 个自然日。
- 新增 `backend/app/services/dashboard_policy.py`：复用现有内部角色、库存读取权限、模型读取权限和仓库范围语义。
- 新增 `backend/app/services/dashboard_cache.py`：缓存键包含合作社、可见仓库集合和筛选条件；Redis 故障自动降级为未命中。
- 新增 `backend/tests/unit/test_dashboard_contract.py`：覆盖 camelCase 参数、时间范围、数量上限、权限和缓存键隔离。
- 验证：`uv run pytest backend/tests/unit/test_dashboard_contract.py -q`，5 passed。

### D2 汇总与库存趋势查询

- 新增 `backend/app/repositories/dashboard.py`：通过聚合 SQL 查询产品/批次、按单位库存、待处理预警、到期批次、低库存产品和按日库存流水趋势。
- 新增 `backend/app/services/dashboard.py`：建立只读事务边界，复用认证范围，补齐默认最近 30 日日期。
- 新增 `backend/tests/unit/test_dashboard_business.py`：真实 PostgreSQL 验证单位分组、库存结余、日期范围、预警/到期/低库存统计。
- 验证：`uv run pytest backend/tests/unit/test_dashboard_business.py backend/tests/unit/test_dashboard_contract.py -q`，6 passed；相关 Ruff、mypy 通过。

### D3 预警分布与产品排行查询

- `DashboardRepository` 新增按类型/等级聚合预警和按产品聚合出库排行查询，所有查询复用合作社/仓库范围条件。
- `DashboardService` 新增预警分布和产品排行用例，排行数量受 Schema 上限约束，出库量按出库流水的绝对变动量统计。
- 扩展 `backend/tests/unit/test_dashboard_business.py`，验证预警分布、出库排行结果。
- 验证：`uv run pytest backend/tests/unit/test_dashboard_business.py backend/tests/unit/test_dashboard_contract.py -q`，6 passed；相关 Ruff、mypy 通过。

### D4 预测对比查询与缓存策略

- `DashboardRepository` 新增预测结果与预测区间内实际出库量的聚合查询，复用模型版本和数据范围过滤。
- `DashboardService` 新增预测对比用例，并将 `DashboardCache` 接入五个查询用例；缓存 JSON 反序列化失败按未命中处理，Redis 异常回源数据库。
- 扩展合同测试覆盖缓存 JSON 往返，业务测试覆盖预测值、实际值和绝对误差。
- 验证：`uv run pytest backend/tests/unit/test_dashboard_business.py backend/tests/unit/test_dashboard_contract.py -q`，7 passed；相关 Ruff、mypy 通过。
