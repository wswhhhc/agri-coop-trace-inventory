# backend/app/utils 公共方法整理建议

## 1. 文档状态

- 日期：2026-09-06
- 状态：已完成第一阶段公共方法和局部领域策略重构；其余高风险建议暂未实施
- 检查范围：`backend/app/api`、`backend/app/services`、`backend/app/repositories`、`backend/app/core`
- 本次操作：已新增/修改公共辅助方法及调用方，并同步更新本文件

## 2. 总体结论

当前 `backend/app/utils` 只有 `.gitkeep`。项目中确实存在重复代码，但重复主要集中在以下三类：

1. API 列表接口重复构造分页元数据。
2. Service 重复校验更新请求不能为空。
3. Service 重复计算认证用户的角色和仓库数据范围。

其中，前两类适合抽取为低耦合公共方法；第三类虽然重复最多，但属于认证和数据权限逻辑，建议优先复用或扩展 `backend/app/core/auth`、领域策略模块，不建议无条件搬到普通 `utils`，避免安全规则失去明确归属。

复查补充：并非所有“公共方法”都应放进 `utils`。返回 `PaginationMeta` 的方法依赖 API 响应 Schema，关键词模式服务于 SQL 查询，二者都有更清晰的分层归属；若项目仍统一使用 `utils` 目录，至少应在模块说明中明确其依赖边界，避免把它误当作纯标准库式工具箱。

## 3. 建议优先抽取的公共方法

### 3.1 分页元数据构造：最高收益

当前多个 API 列表接口都重复以下结构：

```python
PaginationMeta(
    page=params.page,
    page_size=params.page_size,
    total_items=total,
    total_pages=ceil(total / params.page_size) if total else 0,
)
```

涉及位置：

- `backend/app/api/cooperatives.py:39`
- `backend/app/api/batches.py:42`
- `backend/app/api/products.py:59`、`102`
- `backend/app/api/inventory.py:50`、`71`
- `backend/app/api/quality_inspections.py:92`
- `backend/app/api/traceability.py:115`
- `backend/app/api/users.py:60`
- `backend/app/api/warehouses.py:39`

建议新增（优先位置）：

```text
backend/app/api/_pagination.py
└── build_pagination_meta(total, page, page_size) -> PaginationMeta
```

建议职责：统一计算 `total_pages`，并返回现有的 `schemas.common.PaginationMeta`。API 层只负责传入查询结果和分页参数。

如果团队明确要求所有跨模块纯辅助函数均置于 `utils`，可以使用 `backend/app/utils/pagination.py`；但它会依赖 `schemas.common.PaginationMeta`，因此不应被描述为无业务依赖的通用工具。另一种等价方案是在 `PaginationMeta` 上提供具名构造方法。

预期收益：约 10 个调用点可以删除重复的 `ceil` 计算和 `PaginationMeta` 字段拼装，预计减少约 50～70 行重复代码，并避免未来某个接口单独修改分页计算规则。

注意：`PaginationMeta` 模型仍应保留在 `backend/app/schemas/common.py`，`utils` 只提供构造方法，不要把 API 响应模型整体搬过去。

### 3.2 空更新字段校验：高收益

以下 6 个位置使用完全相同的错误码、错误信息和状态码：

- `backend/app/services/cooperative.py:84-90`
- `backend/app/services/batch.py:157-163`
- `backend/app/services/product.py:92-98`
- `backend/app/services/product.py:205-211`
- `backend/app/services/user.py:158-163`
- `backend/app/services/warehouse.py:95-101`

建议新增（优先位置）：

```text
backend/app/core/validation.py
└── require_non_empty_update(values) -> values
```

建议职责：接收 `model_dump(exclude_unset=True)` 的结果；为空时统一抛出当前已有的 `BAD_REQUEST` 异常，不为空时原样返回，方便在 Service 中继续使用。

预期收益：删除 6 处重复异常构造，减少约 30 行代码，同时统一所有更新接口的错误行为。

注意：该方法只处理“是否为空”，不要把批次日期校验、用户角色校验等业务规则混入其中。

若仍放入 `utils/validation.py`，该模块将依赖 `core.exceptions.AppException`；这是可接受但并非纯工具函数。不要为了抽取而让该方法接收 `BaseModel` 并在内部调用 `model_dump`，否则会把 Pydantic 更新语义和 Service 的输入边界隐藏起来。

### 3.3 SHA-256 字符串摘要：中低收益

当前存在多处相同的字符串 SHA-256 计算：

- `backend/app/core/auth/session.py:232-233`：刷新令牌摘要
- `backend/app/core/auth/rate_limit.py:94`
- `backend/app/core/auth/public_rate_limit.py:63`
- `backend/app/services/inventory_idempotency.py:82-86`：请求幂等摘要

可以考虑新增：

```text
backend/app/utils/crypto.py
└── sha256_hex(value: str | bytes) -> str
```

预期收益：减少少量重复代码，并统一编码处理方式。

注意：这是安全相关公共方法，必须明确字符串统一使用 UTF-8；不能改变现有摘要输入、排序和序列化规则。`request_hash_for` 的 JSON 规范化仍应保留在幂等业务模块中，不能简单替换成对 Python 对象直接求哈希。

### 3.4 关键词模糊查询模式：低到中收益

以下 Repository 都重复使用 `f"%{keyword.strip()}%"`：

- `backend/app/repositories/cooperative.py:48`
- `backend/app/repositories/batch.py:47`
- `backend/app/repositories/inventory.py:52`
- `backend/app/repositories/product.py:45`
- `backend/app/repositories/product_category.py:43`
- `backend/app/repositories/user.py:79`
- `backend/app/repositories/warehouse.py:63`

可以考虑新增（更合适的位置）：

```text
backend/app/repositories/_query_helpers.py
└── contains_pattern(keyword: str) -> str
```

建议只负责去除首尾空格并添加 `%`，保持当前 SQL `LIKE` 通配符行为不变。该方法只能减少少量重复代码，优先级低于分页和空更新校验；如果将来要增加 SQL 通配符转义，应作为单独的行为变更处理，不能在抽取时悄悄改变查询结果。

原因：该模式只在 Repository 的 SQL `ILIKE` 条件中使用，放在 Repository 私有辅助模块比 `utils/text.py` 更能表达其 SQL 语义。若团队坚持放在 `utils`，函数名应明确为 `sql_like_contains_pattern`，避免被误用于非 SQL 场景。

## 4. 重复明显，但不建议直接放入普通 utils 的逻辑

### 4.1 用户角色和权限校验

重复位置包括：

- `backend/app/services/product.py:40-42`、`109-114`、`229-234`
- `backend/app/services/batch.py:191-205`
- `backend/app/services/quality_inspection.py:195-209`
- `backend/app/services/warehouse.py:113-124`
- `backend/app/services/user.py:285-291`
- `backend/app/services/traceability.py:277-280`

这些代码都围绕角色、功能权限和数据范围，但规则并不完全相同。例如：

- 产品分类和产品要求合作社管理员且具备 `product:manage`。
- 批次和质检允许合作社管理员、仓库工作人员，并检查 `batch:manage`。
- 追溯只检查 `trace:read`。
- 用户管理只允许系统管理员和合作社管理员。

建议方案：

1. 保留权限规则的归属模块。
2. 将通用的角色常量、权限常量和底层断言能力集中到 `backend/app/core/auth`。
3. Service 只调用统一的权限函数，不在每个文件中重新写角色集合。

不建议把带有具体业务权限含义的函数全部放进 `backend/app/utils`，否则 `utils` 会反向承载业务授权策略，后续很难判断某个权限规则属于哪个模块。

### 4.2 仓库和数据范围计算

重复位置包括：

- `backend/app/services/batch.py:226-232`
- `backend/app/services/product.py:127-133`、`247-253`
- `backend/app/services/quality_inspection.py:212-218`
- `backend/app/services/traceability.py:283-288`
- `backend/app/services/warehouse.py:127-135`

这些实现大体都是：系统管理员或合作社管理员返回全范围，仓库工作人员返回自己的仓库集合。

复查结论：此处不能直接笼统替换。以下实现的分支逐字一致，适合统一为一项认证范围能力：

- `backend/app/services/batch.py:226-232`
- `backend/app/services/product.py:127-133`、`247-253`
- `backend/app/services/quality_inspection.py:212-218`
- `backend/app/services/warehouse.py:127-135`
- `backend/app/services/inventory_policy.py:42-45`

其中 `product.py` 的 `ProductCategoryService` 与 `ProductService` 在同一文件内就有三段逐字重复的方法：`_require_manage`、`_require_cooperative`、`_warehouse_ids_for_query`（分别见 `109-133` 与 `229-253`）。这是本次复查遗漏的高确定性重复；应先提为该文件的模块级私有函数，或提到“产品访问策略”模块，**不应**新增一套 `utils` 方法。

`BatchService` 与 `QualityInspectionService` 的 `_require_read_role`、`_require_manage` 和 `_warehouse_ids_for_query` 也几乎逐字一致（`batch.py:191-232`、`quality_inspection.py:195-218`），且两者都使用 `batch:manage`。后续如实施，优先建立 `batch` 领域的访问策略模块，而不是复制到普通 `utils`。

`TraceabilityService._warehouse_ids_for_query`（`traceability.py:283-288`）例外：除仓库工作人员外，它对其他角色均返回全范围；它与上述实现不等价。现有角色集合下可能符合预期，但在将来新增拥有 `trace:read` 的角色时可能扩大仓库数据范围。实施复用前必须先确认该授权策略，并为“非系统管理员、非仓库工作人员且拥有 `trace:read`”的上下文补测试。

但项目中已经存在相近的公共实现：

- `backend/app/services/inventory_policy.py:42-46` 的 `warehouse_ids`
- `backend/app/core/auth/context.py:30-42` 的范围判断属性和方法
- `backend/app/core/auth/authorization.py:34-49` 的合作社、仓库范围断言

建议后续将上述“逐字一致”的规则提升到 `core/auth`（或抽成专属领域策略模块）后再删除私有副本。`inventory_policy.warehouse_ids` 目前虽可作为实现参考，但其模块名和库存读写权限同属库存领域，不宜让批次、产品、仓库、质检反向依赖它；更不能直接替换 `TraceabilityService`。不要先在 `utils` 新增第二套近似方法，否则会形成新的公共方法分裂。

角色字面量也存在分散：`COOPERATIVE_ADMIN` 在认证、库存、批次、产品、质检、用户、仓库等模块重复定义或直接书写，`WAREHOUSE_STAFF` 同样多处直接书写。可以将角色代码常量集中为 `core/auth/roles.py`（或现有模型常量的唯一归属处），但权限代码如 `batch:manage`、`product:manage` 仍应跟随各自领域策略，不建议统一堆进 `utils/constants.py`。

### 4.3 Repository 的 `_scope_conditions`

以下 Repository 都有同名的范围条件构造方法：

- `backend/app/repositories/cooperative.py:95-102`
- `backend/app/repositories/batch.py:99-106`
- `backend/app/repositories/product.py:95-104`
- `backend/app/repositories/product_category.py:92-101`
- `backend/app/repositories/inventory.py:244-280`
- `backend/app/repositories/quality_inspection.py:84` 附近
- `backend/app/repositories/traceability.py:66` 附近
- `backend/app/repositories/warehouse.py:108-117`

它们名称相同，但操作的 SQLAlchemy 模型列不同，库存 Repository 还额外区分库存、交易和仓库三种范围条件。整段查询逻辑不适合直接抽成通用 CRUD 工具。

如果后续确实要减少重复，可以只抽取非常小的 SQL 条件方法，例如“给定列和仓库 ID 集合生成范围条件”，并为 `None`、空集合分别编写测试。该项优先级低于分页和空更新校验，且必须先确认不会改变数据越权防护。

## 5. 已经是公共实现，不要重复创建

以下能力已有较合适的归属：

- 当前 UTC 时间：`backend/app/models/_common.py:4-8` 的 `utc_now`
- 权限不足、资源不可见：`backend/app/core/auth/authorization.py:16-31`
- 合作社和仓库范围断言：`backend/app/core/auth/authorization.py:34-49`
- 库存权限策略：`backend/app/services/inventory_policy.py:26-55`
- 事务上下文：`backend/app/infrastructure/transaction.py:10`
- 库存响应转换：`backend/app/services/inventory_presenter.py`
- 文件类型和文件路径安全校验：`backend/app/services/file.py:32-46`、`126-156`

这些代码不应为了“填充 utils 目录”而再复制一份。应优先让调用方复用已有实现。

### 5.1 时间方法的复查结论

项目已经有 `backend/app/models/_common.py:4-8` 的 `utc_now()`，并且被模型、认证流程、审计和幂等逻辑复用。以下位置仍直接调用 `datetime.now(UTC)`：

- `backend/app/services/inventory_presenter.py:45`
- `backend/app/repositories/inventory.py:286`
- `backend/app/core/audit/service.py:65`
- `backend/app/core/security.py:59`
- `backend/app/core/auth/session.py:226`

这属于“已有公共方法未完全复用”，不是应该新增第二个 `utils/time.py` 的理由。后续如重构，应统一评估是否改为调用现有 `utc_now()`，并注意测试中的时间注入和时区语义。

## 6. 不建议抽取的代码

- `BatchService._new_trace_code`、`QualityInspectionService._new_inspection_no`、库存操作号生成：都有业务前缀和领域语义，应留在所属 Service。
- `PublicTraceabilityService._project`、`_public_event_description`：属于公开追溯数据投影，不是通用工具。
- 各 API 的 `_user_data`、`_quality_inspection_data` 等响应转换：字段结构不同，强行统一会增加间接层。
- Repository 的完整列表查询：每个模型的筛选字段、排序字段和关联加载不同，泛化后可读性和类型安全会下降。
- 文件上传校验和安全路径处理：只服务于附件模块，继续留在 `FileService` 附近更容易审计。
- 各 Repository 的 `self.session.add(...)`、逐字段 `setattr(...)` 和 `flush()`：虽然 `add` 在约 9 个 Repository、`update` 在多个 Repository 中重复，但这是持久化层行为，不应下沉到无业务边界的 `utils`；如确有需要，应设计带类型约束的 Repository 基类或混入类。
- 各 API 的 `get_xxx_service` 依赖提供函数：形式相似，但构造参数和 FastAPI 依赖不同，抽成工具方法会降低类型可读性，收益很小。
- 各 Service 的 `async with transaction_scope(self.session)`：这是已有事务边界工具的正常使用，不要再包一层装饰器或通用执行器，以免隐藏事务范围。
- Repository 返回 `list(result), int(total or 0)` 的分页收尾：虽然约 10 处相似，但它紧邻 SQLAlchemy 查询和实体类型；抽成工具函数只能减少两行，不能明显降低复杂度。

## 7. 建议的后续实施顺序

本次已完成分页、空更新校验、SHA-256 摘要、SQL 关键词模式，以及产品/批次/质检的重复访问策略重构。剩余建议按以下顺序继续评估：

1. 先为分页方法和空更新方法补充单元测试，覆盖 `total=0`、`total` 非整页、空字典和非空字典。
2. 已完成：新增 `backend/app/api/_pagination.py`、`backend/app/core/validation.py`，并替换所有分页 API 和更新 Service。
3. 已完成：新增 `backend/app/utils/crypto.py`、`backend/app/repositories/_query_helpers.py`，并保留流式文件哈希和幂等 JSON 规范化边界。
4. 已完成：消除 `product.py` 文件内的逐字重复，并为批次/质检建立 `batch_policy.py`；追溯的例外范围规则仍未合并。
5. 后续再评估角色常量集中、已有 `utc_now()` 的全面复用，以及 SQLAlchemy 范围条件是否值得抽取。
6. 本次已运行聚焦测试、全量测试、类型检查和 Ruff；后续每个小步骤仍需确认权限边界、分页结果和异常响应没有变化。

## 8. 本次检查结论

项目存在重复代码，但最大收益并不是建立一个“大杂烩式的 utils”，而是：

- 用 `api/_pagination.py`（或 Schema 的具名构造方法）统一分页元数据构造；
- 用 `core/validation.py` 统一空更新字段校验；
- 优先消除 `product.py` 内部的精确重复，并把批次/质检的访问策略放回所属领域；
- 在确认追溯范围例外后，再决定哪些规则提升到 `core/auth`；
- 仅将 SHA-256 摘要这类无领域依赖的能力放入 `utils/crypto.py`；
- 保留领域专属的编号生成、响应投影和 Repository 查询逻辑。

这样既能减少大量重复代码，也不会把业务规则隐藏在无边界的工具目录中。
