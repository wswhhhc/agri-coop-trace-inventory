# 前端样式拆分任务清单

> 独立于现有后端/业务计划，执行时按阶段逐项勾选。

## 阶段 0：基线

- [ ] 建立 `components.css` 选择器归属清单
- [ ] 记录主题、断点、表格、弹窗和表单的视觉基线
- [ ] 确认页面/组件之间没有隐式依赖内部 class

## 阶段 1：全局基础层

- [x] 新增 `frontend/src/styles/primitives.css`
- [x] 仅保留 tokens、base 和复用 primitives 为全局样式
- [x] 收敛 `[class$='__filters']`、`.muted` 等泛化选择器
- [x] 更新 `frontend/src/main.ts` 的样式入口

## 阶段 2：公共与布局组件

- [x] 迁移 AppShell、AppLayout、AppSidebar、AppHeader（AppShell 当前无专属样式）
- [x] 迁移 Breadcrumb、Container、Header、Context
- [x] 迁移 PageHeader、PageState、PageContext、StatusBadge、ConfirmDialog
- [x] 迁移 PageState、StatusBadge、Toast、Confirm、TaskProgress、ThemeSwitcher

## 阶段 3：业务组件

- [x] 迁移仪表盘组件
- [x] 迁移批次/质检组件
- [x] 迁移预测图表组件

## 阶段 4：页面样式

- [x] 迁移登录、错误页、公开追溯（错误页无专属样式）
- [x] 迁移合作社、仓库、用户、角色
- [x] 迁移产品、分类、批次
- [x] 迁移库存和库存流水
- [x] 迁移告警、预测、导出、审计
- [x] 迁移首页/仪表盘页面编排

## 阶段 5：清理与防回归

- [x] 删除已无引用的 `components.css`
- [x] 删除已无职责的 `layout.css`
- [x] 增加全局 CSS 选择器和 `<style scoped>` 结构检查
- [x] 补充样式维护约定

## 阶段 6：验证

- [x] `pnpm test`
- [x] `pnpm type-check`（已由 `pnpm build` 中的 `vue-tsc --noEmit` 覆盖）
- [x] `pnpm build`
- [ ] 关键页面、移动端和主题切换人工复核（未接入浏览器调试工具）
- [x] `git diff --check`
