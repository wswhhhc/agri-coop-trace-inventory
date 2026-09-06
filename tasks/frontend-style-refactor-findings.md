# 前端样式拆分发现记录

## 2026-09-06：现状盘点

- 前端共有 44 个 `.vue` 文件。
- 当前没有任何 `.vue` 文件包含 `<style>` 块。
- `main.ts` 全局加载四个 CSS 文件。
- `components.css` 约 2108 行，包含公共组件样式和多个业务页面样式。
- `base.css` 中的元素选择器属于全局基础层，不能简单全部迁移到组件内。
- `components.css` 中的 `[class$='__filters']` 是泛化属性选择器，可能匹配未来新增的任意同后缀 class，应改成显式类名或局部选择器。
- 当前 BEM 风格命名降低了冲突概率，但不能替代 Vue `scoped` 样式隔离。
- `pnpm build` 已通过；本次仅做规划，没有修改前端源代码。

## 规划决策

- 不直接把所有 CSS 粗暴拆成“一组件一文件”；先识别真正复用的 primitives，避免重复样式。
- 布局样式最终靠近 `AppLayout`、`AppSidebar`、`AppHeader` 等布局组件，而不是继续集中在 `layout.css`。
- 页面编排样式归页面，组件内部结构样式归组件，跨层样式只在有明确理由时使用 `:deep()`。
- 现有设计变量和基础 reset 保持全局，不在样式重构中改变视觉设计。

## 2026-09-06：第一批迁移

- `PageHeader`、`PageState`、`StatusBadge`、`PageContext`、`ConfirmDialog`、`PageContainer` 已改为组件内 `<style scoped>`。
- 新增 `styles/primitives.css`，承载 `.filter-bar`、`.data-table`、`.detail-panel`、`.pagination` 等复用结构样式。
- 库存流水筛选表单显式增加 `.filter-bar`，不再依赖 `[class$='__filters']`。
- 已从 `components.css` 移除上述公共组件和基础结构样式；业务页面专属规则暂留，等待后续领域切片迁移。
- 验证结果：`pnpm test` 为 24 个测试文件、78 项测试通过；`pnpm build` 通过；`git diff --check` 无内容错误，仅报告既有换行符提示。

## 2026-09-06：迁移完成

- 布局、公共组件、仪表盘、批次、预测、认证、公开追溯及全部管理页面均已使用 `<style scoped>` 承载专属样式。
- `styles/primitives.css` 只保留 `.data-card`、`.filter-bar`、`.data-table`、`.detail-panel`、`.pagination` 等明确复用的结构样式。
- 已移除 `components.css` 和 `layout.css`，避免全局业务选择器继续扩大影响范围。
- 迁移过程中保持原有 CSS 规则和断点，不主动改变页面视觉设计；仅调整归属位置和重复的全局入口。
- 构建产物已按页面拆出独立 CSS chunk，说明 scoped 页面样式已进入对应页面模块。
