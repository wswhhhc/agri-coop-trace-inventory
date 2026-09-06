# 前端全局与局部样式拆分实施计划

## 目标

将当前集中在全局 CSS 中的页面、业务组件和公共基础样式分层，减少样式污染和文件体积，让样式能够在所属组件附近维护，同时保持现有页面视觉效果、响应式行为和主题切换行为不变。

## 当前基线

- `frontend/src/main.ts` 全局加载 `tokens.css`、`base.css`、`layout.css`、`components.css`。
- 前端共有 44 个 `.vue` 文件，目前没有任何 `<style>` 块。
- `components.css` 约 2108 行，混合了公共组件、布局、仪表盘、库存、批次、质检、预测、用户、登录等样式。
- `base.css` 中的通用元素选择器（如 `button`、`input`、`table`）属于合理的全局基础样式，但 `.muted`、`[class$='__filters']` 等规则需要收敛作用范围。
- 当前 `pnpm build` 已通过，说明本次重构应以行为保持和结构改善为主，不夹带视觉改版。

## 最终目录与职责

```text
frontend/src/
├─ styles/
│  ├─ tokens.css       # 颜色、间距、字号、阴影、动效变量
│  ├─ base.css         # reset、html/body、基础元素和主题基础行为
│  └─ primitives.css   # 少量跨页面复用的布局/表格/筛选/分页工具类
├─ components/
│  └─ **/*.vue         # 组件自身模板 + <style scoped>
└─ views/
   └─ **/*.vue         # 页面自身模板 + <style scoped>
```

最终不再保留承载业务页面样式的 `components.css`；`layout.css` 中的布局样式迁移到对应布局组件，避免“布局文件”和组件实现分离。

## 样式归属规则

| 样式类型 | 归属位置 | 示例 |
|---|---|---|
| 设计变量 | `styles/tokens.css` | `--color-brand`、`--space-4` |
| 全局基础行为 | `styles/base.css` | `html`、`body`、表单默认字体、focus-visible |
| 跨页面且确实复用的原子/结构样式 | `styles/primitives.css` | `.data-table-wrap`、`.pagination`、`.filter-bar` |
| 公共组件外观 | 对应公共组件 `.vue` 的 `<style scoped>` | `PageHeader`、`PageState`、`ConfirmDialog` |
| 布局组件外观 | 对应布局组件 `.vue` 的 `<style scoped>` | `AppSidebar`、`AppHeader`、`AppLayout` |
| 业务组件外观 | 对应业务组件 `.vue` 的 `<style scoped>` | `MetricCard`、`ForecastRangeChart` |
| 页面编排和页面特有样式 | 对应页面 `.vue` 的 `<style scoped>` | `DashboardView`、`InventoryListView` |

规则：默认使用 `scoped`；只有真正跨组件复用的样式才进入 `primitives.css`。禁止用宽泛的属性选择器推断组件身份，例如 `[class$='__filters']`；页面和组件之间需要联动时优先使用明确的父级类名和组件根节点类名，必要时才使用有注释的 `:deep()`。

## 实施阶段

### 阶段 0：冻结基线和迁移清单

1. 建立 `components.css` 选择器到目标组件/页面的映射表。
2. 标记每条规则属于“全局基础、跨页面复用、公共组件、业务组件、页面专属”哪一类。
3. 记录当前主题、移动端断点、表格最小宽度、弹窗层级和表单间距等不可回归行为。
4. 确认没有通过字符串拼接或第三方 DOM 直接依赖这些 class。

验收：每个现有选择器都有唯一归属；没有开始改动运行时代码。

### 阶段 1：收缩全局样式层

1. 保留 `tokens.css` 和 `base.css` 的必要内容。
2. 从 `components.css` 提取确实被多个页面复用的基础结构样式，新增 `styles/primitives.css`。
3. 删除或改写 `[class$='__filters']`、`.muted` 等泛化选择器，改为显式的工具类或组件根类。
4. 更新 `main.ts`，只全局加载 `tokens.css`、`base.css`、`primitives.css`。

验收：全局 CSS 不再包含任何具体业务页面选择器；构建通过，页面仍能显示基本结构。

### 阶段 2：迁移公共组件和布局组件

按小批次迁移以下组件，每批迁移后立即构建：

- 布局：`AppShell.vue`、`AppLayout.vue`、`AppSidebar.vue`、`AppHeader.vue`。
- 公共导航：`AppBreadcrumb.vue`、`PageContainer.vue`、`PageHeader.vue`、`PageContext.vue`。
- 公共状态与交互：`PageState.vue`、`StatusBadge.vue`、`ToastNotice.vue`、`ConfirmDialog.vue`、`TaskProgress.vue`、`ThemeSwitcher.vue`。

将对应 CSS 移入组件自身的 `<style scoped>`，同时处理跨组件的根节点和响应式规则。组件共用的表格、分页、筛选容器只保留在 `primitives.css`。

验收：公共组件不依赖 `components.css`；任意公共组件单独复用时不会携带页面业务样式。

### 阶段 3：迁移业务组件

按领域迁移，避免一次修改整个大文件：

1. 仪表盘：`MetricCard`、`DashboardSummary`、`DashboardFilters`、`AlertDistributionPanel`、`InventoryTrendPanel`、`ProductRankingPanel`。
2. 批次和质检：`TraceEventTimeline`、`QualityInspectionPanel`。
3. 预测：`ForecastRangeChart`。

仪表盘页面网格属于 `DashboardView.vue` 的页面编排；图表、指标卡和面板内部布局属于各自组件。若父组件需要影响子组件根节点，只允许使用明确的根节点类名，不把子组件内部结构暴露成全局选择器。

验收：业务组件样式在组件文件内可定位；跨组件样式依赖数量明确且有理由。

### 阶段 4：迁移页面专属样式

按页面领域拆分 `components.css` 剩余规则，每次只处理一个领域：

1. 登录、错误页、公开追溯。
2. 合作社、仓库、用户、角色。
3. 产品、产品分类、批次、批次详情。
4. 库存和库存流水。
5. 告警、预测、导出、审计日志。
6. 首页/仪表盘页面。

页面根类继续保留（如 `.inventory-list-page`、`.dashboard-page`），但只在对应页面的 `scoped` 样式中定义。重复的表单字段、详情列表和表格容器样式回收到 `primitives.css`，不复制到多个页面。

验收：每个页面可独立阅读模板和样式；页面 A 的选择器不会因为 class 同名影响页面 B。

### 阶段 5：清理旧文件与建立防回归检查

1. 删除 `components.css` 中已迁移内容，确认无剩余引用后删除文件。
2. 删除 `layout.css` 中已迁移内容；若只剩全局结构规则，再决定是否并入 `base.css`。
3. 增加轻量检查：全局样式文件不得出现页面领域前缀，`.vue` 的局部样式默认必须带 `scoped`。
4. 补充样式维护约定，说明何时使用 `primitives.css`、何时使用局部 `<style scoped>`。

验收：全局样式文件职责单一；新页面不会再默认把样式追加到巨型 CSS 文件。

### 阶段 6：完整验证和视觉复核

- `pnpm test`
- `pnpm type-check`
- `pnpm build`
- 登录、首页、仪表盘、库存、批次详情、预测、公开追溯、移动端侧栏和深浅主题人工检查。
- 对比重构前后的关键页面截图，重点检查表单、表格、弹窗、响应式断点和主题色。
- 执行 `git diff --check`，确认没有无关文件被修改。

## 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 全局选择器迁移后优先级变化 | 页面间距或颜色改变 | 每批迁移后构建并检查关键页面，必要时保持原选择器顺序 |
| 父页面依赖子组件内部 class | scoped 后样式失效 | 只保留根节点编排，内部样式归子组件；必要时使用注释明确的 `:deep()` |
| 公共样式被误判为页面样式 | 产生重复 CSS | 以实际引用次数和语义判断，重复三次以上且无业务含义才进入 primitives |
| 移动端规则散落 | 响应式回归 | 每个组件的媒体查询和本组件规则放在一起，阶段 6 专门检查 48rem/64rem 断点 |
| 旧工作区已有未提交修改 | 误覆盖用户内容 | 只新增本计划文件；实际实施前先确认当前 diff，并按领域小提交 |

## 建议提交顺序（中文提交说明）

1. `整理前端样式分层基线`
2. `提取全局基础与复用样式`
3. `迁移公共组件和布局组件样式`
4. `迁移仪表盘与业务组件样式`
5. `迁移页面专属样式并清理旧样式`
6. `补充前端样式结构检查与回归验证`

每个提交都应保持可构建，避免把“样式迁移”和功能修改混在同一个提交中。

## 暂不处理

- 不改变颜色、字体、间距等视觉设计值。
- 不引入新的 UI 框架或 CSS 预处理器。
- 不在本次重构中修改后端接口、业务逻辑或权限逻辑。
- 不为了追求文件数量而拆分只使用一次的样式；局部样式应优先靠近组件维护。
