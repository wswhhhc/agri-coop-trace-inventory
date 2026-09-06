# 质检业务模块专项计划书

## 1. 目标

仅完成农产品批次质检模块及其质检附件能力，形成“质检记录新增 → 项目明细保存 → 按批次查询 → 权限隔离 → 追溯/预警事件对接”的可测试后端闭环；不实现库存、公开追溯、预警规则、AI、报表等其他业务模块。

## 2. 当前基线

- 需求已定义质检项目、结果、结论和附件功能；P0 为文字质检，P1 为附件。
- `quality_inspections`、`quality_inspection_items`、`files`、`inspection_files` 已存在于 `schema.sql` 和初始 Alembic 迁移中，但目前只有数据库结构和演示数据，没有运行时 ORM、Schema、Repository、Service、API 或质检专用测试。
- 当前应用已注册批次路由，但没有 `/batches/{batchId}/quality-inspections` 路由。
- 现有公共约定必须沿用：Service 自持事务、Repository 不提交、范围越权 404、功能权限不足 403、错误响应包含请求 ID。

## 3. 范围边界

### 本次包含

1. 质检记录和质检项目明细。
2. 质检结论：`PENDING`、`PASSED`、`FAILED`。
3. 按批次查询质检历史。
4. 追加式保存和更正记录关联。
5. 合作社、批次、检验人员和附件权限校验。
6. 质检附件上传、元数据保存、下载/预览权限（P1）。
7. 向追溯和预警模块提供最小事件对接接口，不实现这两个模块自身的管理功能。
8. 质检后端测试；如需要全栈交付，再增加质检页面和 API 封装。

### 本次不包含

- 库存数量、入库/出库、库存流水和并发扣减。
- 追溯事件查询、二维码、公开追溯接口和 Redis 公开缓存。
- 预警规则扫描、预警处理工作台和 Celery 任务。
- AI 预测、报表、大屏和全局前端框架建设。

## 4. 实施阶段

### 阶段 0：冻结接口与数据契约

- [x] 确认质检请求不允许客户端伪造 `inspectorName`；检验人员从当前登录用户生成 `inspector_id`，名称只作为响应展示。
- [x] 确认 `inspection_no` 由服务端生成，避免数据库必填字段与请求体不一致。
- [x] 保留接口示例中的 `items[].unit`，给质检项目表新增 `unit` 字段。
- [x] 给 `quality_inspections` 增加可空的 `original_inspection_id` 自关联外键和索引，用于更正记录关联。
- [x] 明确存在不合格项目时不得提交 `PASSED`；允许 `PENDING` 作为未完成结论。
- [x] 同步接口文档、数据库设计文档、`schema.sql` 和迁移设计。

**阶段状态：** complete

**已冻结决策：**

| 决策 | 处理方式 | 理由 |
|---|---|---|
| 检验人 | 服务端从当前登录用户写入 `inspector_id`，响应返回其名称 | 防止客户端伪造检验人 |
| 检验编号 | 服务端生成，合作社内唯一 | 请求体不承担数据库内部编号 |
| 项目单位 | 持久化 `unit` 字段 | 与既有接口示例保持一致 |
| 更正关系 | `original_inspection_id` 自关联 | 保留不可覆盖的历史链路 |
| 结论规则 | 有不合格项目不得为 `PASSED`；允许 `PENDING` | 避免主结论与明细相互矛盾 |

**阶段产物：**冻结后的字段映射、状态规则、迁移清单和错误码清单。

### 阶段 1：ORM 与数据库一致性

- [x] 在 `backend/app/models/` 新增独立模型文件：质检主表、质检项目、文件、质检文件关联表。
- [x] 在 `backend/app/models/enums.py` 增加质检结论枚举。
- [x] 配置批次、合作社、检验用户、质检项目和附件的双向关系及删除策略。
- [x] 补齐唯一约束、检查约束、批次时间线索引和更正记录索引。
- [x] 在 `backend/app/models/__init__.py` 显式注册模型，保证进入 `Base.metadata`。
- [x] 新增 `unit` 和原记录关联字段的独立 Alembic 迁移，并同步 `schema.sql`。
- [x] 增加 ORM、迁移、SQL 结构一致性测试。

**阶段状态：** complete

**阶段验收：**真实 PostgreSQL 可升级/回退；模型字段、外键、索引和约束与 SQL 一致。

### 阶段 2：Schema、Repository、Service

- [x] 新增质检请求、项目明细、列表项、详情和附件摘要 Schema。
- [x] 实现 Repository：
  - 按批次和合作社范围查询；
  - 按 `inspected_at` 倒序返回质检时间线；
  - 新增主记录、项目明细和附件关联；
  - 禁止业务更新和删除历史质检记录；
  - 由数据库约束兜底检验编号和项目名称唯一性。
- [x] 实现 Service：
  - 校验批次存在、批次合作社归属和当前用户数据范围；
  - 校验检验人员状态和合作社归属；
  - 校验项目名称、标准值、结果值、排序号和重复项目；
  - 校验结论与项目合格状态；
  - 生成检验编号；
  - 使用 `transaction_scope(session)` 将主记录、明细、附件关联放入同一事务；
  - 将唯一键、外键和状态错误映射为既有统一错误响应。

**阶段状态：** complete

**阶段验收：**成功新增时全量数据一次提交；任一明细或附件失败时整体回滚；历史记录不可被覆盖。

### 阶段 3：API、权限与跨模块对接

- [x] 新增并注册：
  - `GET /api/v1/batches/{batchId}/quality-inspections`
  - `POST /api/v1/batches/{batchId}/quality-inspections`
- [x] 查询接口允许具备批次数据权限的用户访问。
- [x] 新增接口仅允许合作社管理员和仓库工作人员访问，并复用现有认证、合作社范围和仓库授权依赖。
- [x] 跨合作社、无授权批次统一返回 404；功能权限不足返回 403。
- [x] 新增质检成功后通过适配器/领域事件通知：追溯模块写入 `INSPECTION` 事件；`FAILED` 结论通知预警模块生成 `QUALITY_FAILED` 预警。
- [x] 对接失败的事务策略必须明确：若下游尚未实现，先使用可测试的端口接口，不引入库存、追溯或预警业务代码。
- [x] 写入创建、失败和越权审计信息，但不记录附件内容和敏感文件路径。

**阶段状态：** complete

**阶段验收：**OpenAPI 可发现两个质检接口；权限、数据隔离、事务和错误码符合公共契约。

### 阶段 4：质检附件（P1）

- [x] 新增 `POST /api/v1/files` 和 `GET /api/v1/files/{fileId}`。
- [x] 仅接受 `multipart/form-data`，字段名为 `file`。
- [x] 校验 PDF、PNG、JPEG 类型和 10MB 大小上限。
- [x] 服务端生成安全存储名，文件内容存放在受控目录，数据库只保存元数据。
- [x] 计算并保存 SHA-256、原始文件名、MIME 类型、大小和上传人。
- [x] 下载前校验合作社、质检关联和当前用户访问权限。
- [x] 验证非法类型、超限文件、空文件、路径穿越和无权限下载。

**阶段状态：** complete

**阶段验收：**附件可上传、关联、下载；不能通过文件 ID 访问其他合作社文件。

### 阶段 5：测试与文档验收

- [x] Schema 参数和状态规则单元测试。
- [x] Repository 范围过滤、排序、唯一约束和级联关系测试。
- [x] Service 事务提交、回滚、追加式更正和结论校验测试。
- [x] API 权限、404/403、请求 ID、响应结构和 OpenAPI 测试。
- [x] 附件上传安全和权限测试。
- [x] 质检事件/预警通知端口的调用测试，不测试下游模块内部实现。
- [x] PostgreSQL 集成测试通过；补充或更新演示数据计数测试。
- [x] 运行质检相关 Ruff、mypy、pytest 和全量回归。
- [x] 更新接口设计、数据库设计和测试记录，标明本阶段未实现的下游模块。

**阶段状态：** complete

**最终验收标准：**质检模块可独立完成“批次 → 新增质检 → 查询历史 → 附件访问”的闭环；无越权数据泄露；事务、审计、错误码和文档一致。

## 5. 预计文件清单

### 后端生产代码

- `backend/app/models/quality_inspection.py`
- `backend/app/models/quality_inspection_item.py`
- `backend/app/models/file.py`
- `backend/app/models/inspection_file.py`
- `backend/app/schemas/quality_inspection.py`
- `backend/app/schemas/file.py`
- `backend/app/repositories/quality_inspection.py`
- `backend/app/repositories/file.py`
- `backend/app/services/quality_inspection.py`
- `backend/app/services/file.py`
- `backend/app/api/quality_inspections.py`
- `backend/app/api/files.py`
- `backend/app/models/enums.py`、`backend/app/models/__init__.py`、`backend/app/main.py`

### 测试与数据库

- `backend/tests/unit/test_quality_inspection_models.py`
- `backend/tests/unit/test_quality_inspection_business.py`
- `backend/tests/unit/test_quality_inspection_api.py`
- `backend/tests/integration/test_quality_inspection.py`
- 必要时新增 Alembic 迁移，并同步 `backend/sql/schema.sql`、接口/数据库设计文档。

### 前端（若本次要求全栈）

- 仅新增质检 API 客户端、质检列表、质检录入/详情和附件上传组件；不建设其他模块页面。

## 6. 执行顺序与质量门禁

执行顺序固定为：

`契约冻结 → ORM/迁移 → Schema/Repository → Service → API/权限 → 附件 → 测试/文档`

每个阶段先写失败测试，再实现，再运行聚焦测试；阶段通过后才进入下一阶段。不得为了完成质检模块提前实现库存、追溯公开接口、预警规则或 AI 功能。

## 7. 关键风险

| 风险 | 处理方式 |
|---|---|
| 接口有 `unit`，表结构没有 | 阶段 0 统一契约，必要时先迁移再编码 |
| 要求更正记录关联原记录，但没有字段 | 增加自关联字段/迁移，或删除该要求，不能只靠备注字段假关联 |
| 仓库工作人员与批次没有直接仓库关系 | 质检阶段只复用现有批次合作社/授权门槛；真实仓库行级关联留给库存模块 |
| 下游追溯/预警尚未实现 | 只定义并测试适配器端口，不把下游业务混入本模块 |
| 文件路径和内容泄露 | 只返回安全下载地址，严格校验资源归属和文件类型 |

## 8. 当前状态

- **阶段 0：** complete
- **阶段 1：** complete
- **阶段 2：** complete
- **阶段 3：** complete
- **阶段 4：** complete
- **阶段 5：** complete（PostgreSQL/Redis 已连接，严格门禁全部通过）
