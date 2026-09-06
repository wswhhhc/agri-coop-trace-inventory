# forecasting 模块任务执行书

目标：按现有接口/数据库设计，实现模型版本、异步任务、需求预测结果查询与本地可复现预测流程，遵守“Schema → Service → Repository → API → 权限 → 测试 → 文档”的纵向闭环；预测粒度固定为“仓库＋产品”，周期支持 7 天和 30 天，结果明确标注合成数据限制。

## 执行顺序与记录

- [completed] F0：现状盘点、契约冻结、测试计划和执行记录书
- [completed] F1：forecasting ORM（模型版本、预测结果、预测明细）与数据库结构一致性
- [completed] F2：预测输入校验、特征处理、移动平均基线和 XGBoost 适配
- [completed] F3：任务记录与模型版本 Repository/Service/API（查询、训练提交、激活）
- [completed] F4：预测任务、结果落库、异步 Celery 状态流转和幂等处理
- [completed] F5：预测结果分页/详情 API、范围权限和接口文档
- [completed] F6：模块专项测试、全量回归、最终全面复查

## 每阶段验收

1. 每完成一个功能先运行聚焦测试并在本文件记录结果。
2. 每完成一个大功能先复查代码、测试和敏感信息，再使用中文提交一次 Git。
3. 最终阶段需运行 forecasting 专项测试、全量测试、Ruff、mypy，并检查工作区和迁移/schema/文档一致性。

## 错误记录

| 错误 | 尝试次数 | 解决方案 |
|---|---:|---|
| 旧规划文件内容包含此前模块历史，不能直接覆盖 | 1 | 新建 forecasting 专项执行记录书，并只向既有计划追加本模块阶段 |

## F1 完成记录

- 新增 `ModelVersion`、`ForecastResult`、`ForecastPoint` 独立 ORM 文件，补齐枚举、关系、外键、唯一约束、检查约束和索引。
- 扩展 `ModelType`、`DataType` 枚举并注册到 `app.models`。
- 新增模型结构/默认值测试：`uv run pytest backend/tests/unit/test_forecasting_models.py -q`，2 passed。
- 复查：本次模型文件、测试文件 Ruff 通过；已确认 `ModelVersion` 活跃范围部分唯一索引与迁移定义一致。

## F2 完成记录

- 新增 `app/ml/forecasting.py`：出库日聚合、日历/滞后/滚动特征、移动平均基线、MAE/RMSE、XGBoost 训练与非负预测。
- 预测特征列固定为 `day_of_week/day_of_month/month/day_of_year/lag_1/lag_7/rolling_7`，避免训练和推理漂移。
- 聚焦测试：`uv run pytest backend/tests/unit/test_forecasting_ml.py -q`，5 passed；相关 Ruff 通过。
- 复查：XGBoost 只接受白名单参数，推理结果统一截断为非负值；无历史出库时基线返回 0。

## F3 完成记录

- 新增 forecasting Schema、权限策略、Repository、Service 和 API；接入模型版本列表/详情、模型激活、训练任务提交、预测任务提交、任务查询和预测结果查询路由。
- 所有查询在 Repository 追加合作社/仓库范围条件；越权资源返回 404，功能权限不足返回 403。
- Celery 任务名固定为 `app.tasks.forecasting_tasks.train_model_task` 与 `forecast_demand_task`，为 F4 Worker 实现预留稳定入口。
- 聚焦测试：Schema/策略/API 合计 6 passed；相关 Ruff 和 mypy 通过；应用导入检查通过（路由对象检查命令本身误将 `_IncludedRouter` 当 APIRoute，未影响应用导入）。

## F4-F5 完成记录

- Worker 已实现真实训练和预测流程：读取出库流水、生成日特征、训练 XGBoost、保存 joblib 模型、计算 MAE/RMSE 与移动平均基线、写入模型版本/预测结果/每日明细，并回写任务成功或失败状态。
- 预测结果按未来 7/30 天生成，补货建议按预测总量、当前库存和产品安全库存计算，所有结果标注 `SYNTHETIC` 与限制说明。
- Repository 增加出库历史和当前库存聚合查询；API 文档已补充实现说明。
- F4/F5 聚焦回归：forecasting 相关 13 项测试通过；Worker/Repository Ruff 和 mypy 通过；全量回归已通过 248 项。

## F6 最终复查记录

- 专项测试：forecasting 13 passed。
- 全量测试：`uv run pytest -q` 248 passed、2 warnings。
- 严格门禁：`uv run python backend/scripts/test_gate.py` 通过，覆盖率 81.39%，关键模块覆盖率 95%，mypy 129 files 通过，Ruff 全仓通过。
- 代码复查结论：权限、范围过滤、输入校验、任务失败回写、模型/结果约束和合成数据限制均符合契约；未提交 `.env`、`.idea` 或覆盖既有用户修改。
