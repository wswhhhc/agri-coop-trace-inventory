# 测试底座补齐任务书

## 1. 任务目标

建立统一、可复用、分层的数据库测试底座，让测试在功能开发过程中持续提供反馈，并覆盖以下真实行为：

- 所有数据库测试复用公共 `backend/tests/conftest.py`，不再在测试文件内重复创建数据库引擎和会话 Fixture。
- 所有数据库测试直接使用真实 PostgreSQL；未配置测试数据库时自动跳过，不阻塞不需要数据库的纯逻辑测试。
- 通过测试数据工厂构造合作社、角色、用户、仓库、产品分类、产品和批次等关联数据。
- 通过真实 SQLAlchemy ORM 会话验证实体的增删改查及关联加载。
- 通过真实数据库提交验证唯一键、外键和检查约束，而不是只检查模型声明。
- 通过 Alembic 实际执行 `upgrade head → downgrade base`，并验证数据库对象确实创建和清理。

## 2. 当前问题

- `backend/tests/unit/` 中有多处重复的 SQLite 引擎、建表、UUID 默认值处理和会话 Fixture。
- 现有 ORM 测试主要验证模型可建表和少量创建/查询，缺少系统化 CRUD 与约束冲突测试。
- 现有 Alembic 测试主要验证 metadata/check 结果，没有完成完整迁移往返。
- 当前项目只注册了部分业务 ORM 模型；迁移测试必须以 Alembic 脚本实际管理的完整数据库结构为准，不能用 `Base.metadata.create_all()` 替代迁移。

## 3. 实施范围

### 阶段一：公共 PostgreSQL 数据库底座

- 新增 `backend/tests/conftest.py`。
- 提供 PostgreSQL 异步引擎、异步会话和事务隔离 Fixture，连接地址由 `TEST_POSTGRES_DATABASE_URL`（兼容 `TEST_DATABASE_URL`）提供。
- 每个测试使用独立临时 schema，避免测试间相互污染，也避免清理时误删测试库中的其他对象。
- 添加 `postgres` 标记及未配置时的明确跳过原因。

### 阶段二：测试数据工厂

- 新增 `backend/tests/factories.py`。
- 工厂保持显式、可读，支持构造最小有效对象和带关系的完整场景。
- 工厂不替代被测 ORM 行为，不在工厂内偷偷提交会话。

### 阶段三：真实 ORM 与约束测试

- 将现有测试改用公共 Fixture，并删除重复的本地数据库 Fixture。
- 增加合作社、用户、仓库、产品分类、产品、批次及关联表的真实 ORM CRUD 测试。
- 增加唯一键冲突、外键冲突、检查约束冲突测试，断言提交时抛出真实 `IntegrityError`。
- 所有约束测试均在 PostgreSQL 中真实提交并验证数据库异常。

### 阶段四：Alembic 往返测试

- 新增迁移集成测试，使用临时 PostgreSQL 数据库执行 `upgrade head`。
- 验证 `alembic_version` 到达 head，关键表和关键约束存在。
- 执行 `downgrade base`，验证业务表和版本表被清理。
- 迁移测试不通过 `metadata.create_all()` 预先造表，以保证测试的是迁移脚本本身。

## 4. 验收标准

- 测试文件中不再重复定义数据库引擎/会话 Fixture；公共 Fixture 可直接按名称注入。
- 至少一个唯一键冲突测试真实触发 `sqlalchemy.exc.IntegrityError`。
- 至少一个外键冲突测试真实触发 `IntegrityError`。
- 至少覆盖产品和批次的日期/数值/状态检查约束，并真实触发冲突。
- ORM CRUD 测试通过真实异步 SQLAlchemy 会话完成，不使用仓储 Mock 代替数据库。
- Alembic 测试实际完成 `upgrade head → downgrade base`，并在结束时确认数据库已回到 base。
- 未配置 PostgreSQL 时，纯逻辑测试仍可独立通过；配置后所有数据库测试可执行。
- `uv run pytest -q` 通过；新增测试文件通过 Ruff 检查。

## 5. 预估变更量

预计新增/修改约 900～1,300 行，删除重复 Fixture 约 100～180 行；最终净增约 750～1,150 行。若本阶段只覆盖当前已注册 ORM 模型，按约 1,100 行控制规模。

## 6. 执行顺序

1. 公共 PostgreSQL Fixture 与工厂最小闭环。
2. 将现有数据库测试迁移到公共 Fixture，删除重复代码。
3. 增加 ORM CRUD 和真实约束测试。
4. 增加 PostgreSQL 标记集成测试。
5. 增加 Alembic upgrade/downgrade 往返测试。
6. 分阶段运行聚焦测试，再运行全量测试、Ruff 和最终审查。

## 7. 非目标

- 本任务不新增业务模型或业务 API。
- 本任务不把所有业务表强行补成 ORM 模型；迁移脚本已有的未注册业务表只由 Alembic 往返测试验证。
- 本任务不修改现有文档中的业务定义，不处理与测试底座无关的既有 Ruff 问题。

## 8. 实施状态

- [x] 公共 PostgreSQL 异步 Fixture：独立 schema、会话工厂、会话回滚和自动清理。
- [x] 测试数据工厂：合作社、角色、权限、用户、仓库、分类、产品、批次及用户仓库关联。
- [x] 现有认证、审计、产品批次测试迁移到公共 Fixture，删除重复数据库初始化代码。
- [x] 真实 ORM CRUD、唯一键、外键、检查约束和并发唯一键测试。
- [x] Alembic 真实 `upgrade head → downgrade base` 往返测试。
- [x] 全量 PostgreSQL 回归和 Ruff 验证。

验证结果：`131 passed, 2 warnings`；PostgreSQL 测试库为本机专用 `agri_trace_test`，测试使用临时 schema 隔离。
