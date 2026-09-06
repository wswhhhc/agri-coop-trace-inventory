# forecasting 模块任务执行书

目标：按现有接口/数据库设计，实现模型版本、异步任务、需求预测结果查询与本地可复现预测流程，遵守“Schema → Service → Repository → API → 权限 → 测试 → 文档”的纵向闭环；预测粒度固定为“仓库＋产品”，周期支持 7 天和 30 天，结果明确标注合成数据限制。

## 执行顺序与记录

- [completed] F0：现状盘点、契约冻结、测试计划和执行记录书
- [completed] F1：forecasting ORM（模型版本、预测结果、预测明细）与数据库结构一致性
- [pending] F2：预测输入校验、特征处理、移动平均基线和 XGBoost 适配
- [pending] F3：任务记录与模型版本 Repository/Service/API（查询、训练提交、激活）
- [pending] F4：预测任务、结果落库、异步 Celery 状态流转和幂等处理
- [pending] F5：预测结果分页/详情 API、范围权限和接口文档
- [pending] F6：模块专项测试、全量回归、最终全面复查

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
