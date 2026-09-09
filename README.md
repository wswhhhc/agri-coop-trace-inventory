# 农业合作社农产品批次追溯与智能库存预警系统

一个面向农业合作社的前后端分离管理系统，覆盖农产品批次全流程追溯、库存业务管理、质量检验、风险预警和需求预测。项目适合用于毕业设计、课程设计和本地业务流程演示；演示数据均为虚构合成数据，不代表真实经营情况。

## 项目特点

- 合作社、仓库、用户、角色和权限管理，支持按合作社及授权仓库进行数据隔离
- 产品、批次、生产日期、保质期和质量检验记录管理
- 入库、出库、调拨、盘点、报损及不可变库存流水
- 库存写操作使用 PostgreSQL 事务、行级锁和幂等键，避免重复提交和库存不一致
- 批次内部追溯时间线，以及面向消费者的脱敏公开追溯和二维码
- 低库存、临期、库存积压、质检不合格四类预警及处理记录
- 基于 XGBoost 的需求预测，支持移动平均基线对比和异步任务执行
- 数据大屏、库存与预警统计、Excel 报表导出和审计日志
- Redis 查询缓存、登录/公开接口限流、刷新令牌 HttpOnly Cookie 和请求追踪 ID

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 后端 | Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic |
| 数据库 | PostgreSQL 15+ |
| 缓存与异步任务 | Redis、Celery |
| 机器学习 | XGBoost、scikit-learn、pandas、NumPy |
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios |
| 工程化 | uv、pnpm、pytest、Vitest、mypy、Ruff |

## 运行环境

- Python 3.12+
- Node.js 与 pnpm
- PostgreSQL 15+
- Redis
- [uv](https://docs.astral.sh/uv/)

项目当前未提供 Docker Compose 配置，因此 PostgreSQL 和 Redis 需要提前在本机或服务器上启动。

## 快速开始

以下命令默认在项目根目录执行。

### 1. 安装依赖

```powershell
uv sync --dev

Set-Location frontend
pnpm install
Set-Location ..
```

### 2. 配置后端

复制配置模板：

```powershell
Copy-Item backend/.env.example backend/.env
```

编辑 `backend/.env`，至少确认以下配置：

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agri_trace
POSTGRES_USER=postgres
POSTGRES_PASSWORD=你的数据库密码

JWT_SECRET_KEY=请替换为至少32字节的随机密钥
JWT_ISSUER=agri-coop-trace-api
JWT_AUDIENCE=agri-coop-trace-web

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

不要提交 `backend/.env`，也不要在配置文件、SQL 文件或提交记录中写入真实密码、密钥和对象存储凭据。

### 3. 初始化数据库

先创建 PostgreSQL 数据库 `agri_trace`，再执行迁移：

```powershell
uv run alembic -c backend/alembic.ini upgrade head
```

如需导入演示数据：

```powershell
psql -h localhost -U postgres -d agri_trace -f backend/sql/demo_data.sql
```

演示账号密码统一为 `Demo@123456`，仅用于本地演示，不能用于生产环境。账号列表和数据范围见 [演示数据说明](docs/演示数据说明.md)。

如需重新生成一套可复现的虚构数据：

```powershell
uv run --directory backend python -m scripts.generate_demo_data --seed 20260904 --output sql/demo_data.sql
```

### 4. 启动后端

在一个终端执行：

```powershell
uv run --directory backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

- 健康检查：`http://localhost:8000/health`
- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

### 5. 启动前端

在另一个终端执行：

```powershell
Set-Location frontend
pnpm dev
```

前端地址：`http://localhost:5173`

本地开发环境会通过 Vite 将 `/api` 请求代理到 `http://localhost:8000`。如果前后端部署在不同域名，可在前端环境变量中设置 `VITE_API_BASE_URL`。

### 6. 启动异步任务服务（可选）

训练、预测、报表导出和定时预警扫描使用 Celery。需要执行异步任务时，分别启动 Worker 和 Beat：

```powershell
uv run --directory backend celery -A app.tasks.celery_app:celery_app worker --loglevel=INFO --pool=solo
uv run --directory backend celery -A app.tasks.celery_app:celery_app beat --loglevel=INFO
```

Windows 本地开发建议使用 `--pool=solo`；生产环境请根据部署方式选择合适的 Worker 并配置进程守护。

## 常用命令

### 后端

```powershell
uv run pytest -q
uv run mypy backend/app
uv run ruff check .
uv run python backend/scripts/test_gate.py
```

`backend/scripts/test_gate.py` 会执行带 PostgreSQL、Redis 和覆盖率门禁的完整检查，运行前请确保相关服务已经启动。

### 前端

```powershell
Set-Location frontend
pnpm test
pnpm type-check
pnpm build
```

## 项目结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # REST API 路由
│   │   ├── core/             # 配置、认证、安全、异常和日志
│   │   ├── infrastructure/   # PostgreSQL、Redis 和事务基础设施
│   │   ├── ml/               # 预测模型
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── repositories/     # 数据访问层
│   │   ├── schemas/          # Pydantic 数据契约
│   │   ├── services/         # 业务服务
│   │   └── tasks/            # Celery 异步任务
│   ├── alembic/              # 数据库迁移
│   ├── scripts/              # 演示数据和测试门禁脚本
│   ├── sql/                  # 数据库结构和演示数据 SQL
│   └── tests/                # 后端单元测试与集成测试
├── frontend/
│   ├── src/api/              # 前端 API 请求
│   ├── src/components/       # 通用组件
│   ├── src/stores/           # Pinia 状态
│   ├── src/views/            # 业务页面
│   └── src/router/           # 路由和访问控制
└── docs/                     # 需求、接口、数据库和演示数据说明
```

## API 文档

启动后端并开启 `DOCS_ENABLED=true` 后，可访问：

- Swagger UI：`http://localhost:8000/docs`
- OpenAPI JSON：`http://localhost:8000/api/v1/openapi.json`
- 接口设计说明：[docs/接口设计说明书.md](docs/接口设计说明书.md)

## 数据与安全说明

- `backend/sql/demo_data.sql` 中的数据全部为 `SYNTHETIC` 虚构合成数据。
- 生产环境必须更换 JWT 密钥、数据库密码和演示账号密码，并启用安全 Cookie。
- PostgreSQL 是业务数据的事实来源，Redis 仅用于会话、缓存、限流和 Celery 任务支撑。
- 公开追溯接口只返回脱敏信息，不返回库存数量、内部备注、用户标识和操作日志。
- 文件上传默认保存到 `backend/storage/uploads`，导出文件和模型产物属于运行时数据，不建议提交到仓库。

## 相关文档

- [软件需求规格说明书](docs/软件需求规格说明书.md)
- [接口设计说明书](docs/接口设计说明书.md)
- [数据库设计说明书](docs/数据库设计说明书.md)
- [演示数据说明](docs/演示数据说明.md)
- [前端开发说明](frontend/README.md)

## 贡献说明

欢迎通过 Issue 反馈问题或提交 Pull Request。提交代码前建议至少执行后端测试、Ruff 检查、前端类型检查和前端构建。

## 许可证

当前仓库未声明正式开源许可证。如果计划公开分发或允许他人修改使用，建议根据项目用途补充 `LICENSE` 文件。
