# 前端问题分析与操作指引

> 工作树: `frontend-issues-guide` | 分支: `worktree-frontend-issues-guide`

基于对 `app/src/` 全部 25 个源文件的完整审查，按严重程度分级列出问题及修复指引。

---

## P0 — 运行时崩溃 / 严重逻辑错误

### P0-1. `data.settings` 不存在，多处引用导致运行时崩溃

**涉及文件:**
- `GachaPage.tsx:397` — `data.settings.theme.themeMode`
- `KnowledgePage.tsx:471` — `data.settings.mineru.apiUrl`

**问题:** `AppData` 类型 (`types.ts:163-175`) **没有 `settings` 字段**。访问 `data.settings` 返回 `undefined`，访问 `.theme.themeMode` 或 `.mineru.apiUrl` 会抛出 **TypeError: Cannot read properties of undefined**。

**指引:**
1. 在 `types.ts` 的 `AppData` 接口中补充 `settings` 字段类型定义
2. 在初始数据 `createInitialData()` 中为 `settings` 提供默认值
3. 访问时添加可选链 `data.settings?.theme?.themeMode ?? 'light'`
4. 或在单独的 context/hook 中管理设置状态

---

### P0-2. localStorage 数据初始加载失效

**涉及文件:** `store.tsx:282-289`

**问题:** `useReducer(reducer, null, createInitialData)` 使用的初始化函数 `createInitialData()` **返回空数据**，`loadData()` 从未被调用。每次刷新页面后所有数据丢失。`dispatch({type: 'LOAD'})` 虽然存在但从未被触发。

**指引:**
1. 方案 A: 将 `useReducer` 初始化函数改为 `loadData` → 最简单
2. 方案 B: 在 `useEffect` 中 `dispatch({type: 'LOAD'})` → 更灵活
3. 建议方案 A，最小改动

---

### P0-3. `ChoiceDialog.tsx:218` — 引用未定义的 `COSMIC` 常量

**涉及文件:** `ChoiceDialog.tsx:218, 223`

```tsx
color: COSMIC.textMuted,   // COSMIC 在第 484 行才定义
```

**问题:** 第 218 行和第 223 行引用了 `COSMIC`，但 `const COSMIC = {...}` 定义在第 484 行。`const` 不存在 hoisting，运行时抛出 **ReferenceError: Cannot access 'COSMIC' before initialization**。

**指引:**
1. 将 `COSMIC` 定义移动到文件顶部（第 1-5 行），在 `ChoiceDialog` 组件之前
2. 或将其抽到单独常量文件
3. 建议方案 1，因为该文件已经有一个重复的 COSMIC（第 484 行），需要同时删除重复定义

---

## P1 — 功能缺陷

### P1-1. 链式解锁功能未生效

**涉及文件:** `algorithms.ts:185-205`，`store.tsx:100-122`

**问题:** `chainUnlock()` 函数存在两个问题：
1. **直接修改入参对象**（第 197 行 `dep.isUnlocked = true`），违反不可变原则
2. **从未被调用** — `COMPLETE_TASK` action 中没有触发 chain unlock 逻辑

**指引:**
1. 修改 `chainUnlock` 返回不可变结果（返回更新后的 task 列表）
2. 在 `COMPLETE_TASK` action 中调用 chainUnlock 逻辑
3. 或改为在 `getAvailableTasks` 中动态计算解锁状态

---

### P1-2. 编辑任务时 `category` 字段丢失

**涉及文件:** `TasksPage.tsx:54-86`

**问题:** `handleAdd` 使用 `createDefaultTask()` 创建默认任务对象，其中 `category` 默认为 `daily`。编辑任务时 `formData` 不包含 `category` 字段，编辑后提交会将所有任务 category 重置为 `daily`。

**指引:**
1. 在 `TaskFormData` 接口和 `formData` 状态中添加 `category` 字段
2. 在 `TaskForm` 中添加 category 选择器
3. `handleEdit` 中正确读取并回填 category

---

### P1-3. 日/周任务自动重置无触发机制

**涉及文件:** `store.tsx:246-263`

**问题:** `RESET_PERIODIC` action 定义了重置逻辑（每日任务重置、每周任务重置），但 **没有任何地方 dispatch 这个 action**。没有定时器、没有页面加载检查，周期性任务永远不会自动恢复到抽牌堆。

**指引:**
1. 在 `StoreProvider` 中添加 `useEffect`，每分钟检查是否需要执行周期重置
2. 或在 `getAvailableTasks()` 中动态判断重置条件（推荐，更简单）

---

### P1-4. RECORD_DRAW 在用户确认前触发

**涉及文件:** `GachaPage.tsx:457`

```tsx
dispatch({ type: 'RECORD_DRAW', taskId: choices[0].id });  // 用户还没选择
```

**问题:** 单抽时在展示结果后就立即记录抽取，但用户可能点击"另寻天命"放弃选择。应仅在用户选择任务后再记录。

**指引:**
1. 将 `RECORD_DRAW` 移到 `handleSelectTask` 中
2. 在用户确认选择任务后才记录抽取

---

## P2 — 代码质量与可维护性

### P2-1. 力模拟算法重复

**涉及文件:** `KnowledgeGraph.tsx:19-82`，`KnowledgeGraph3D.tsx:9-57`

**问题:** 2D 和 3D 图谱组件各自实现了一套几乎完全相同的力导向图模拟算法（O(n²) 遍历、斥力/引力/阻尼/中心引力）。代码重复约 120 行。

**指引:**
1. 抽取公共力模拟模块到 `lib/forceSimulation.ts`
2. 2D 和 3D 版本共用算法逻辑，仅坐标维度不同

---

### P2-2. `mineruClient.ts` 模块级可变状态

**涉及文件:** `mineruClient.ts:9-10`

```ts
let serverUrl = 'http://127.0.0.1:8899';
let serverOnline = false;
```

**问题:** 在 React 应用中使用模块级可变变量管理状态。当多组件同时检查状态时可能不一致，且不支持响应式更新。

**指引:**
1. 改为使用 React Context 或 atom 状态管理
2. 或至少提供一个订阅机制，在状态变化时通知组件

---

### P2-3. `tsconfig.json` 启用了严格检查但代码不符

**涉及文件:** `tsconfig.json:18-21`

```json
"noUnusedLocals": true,
"noUnusedParameters": true
```

**问题:** 代码中存在多处未使用的变量，运行 `tsc` 会报错。例如 `KnowledgeGraph3D.tsx:170` 的 `timer` ref。

**指引:**
1. 运行 `npx tsc --noEmit` 查看所有错误
2. 逐项修复：删除未使用变量、用 `_` 前缀标记有意未使用的参数

---

### P2-4. 重复定义的 `COSMIC` 常量

**涉及文件:** `GachaPage.tsx:23-40`，`ChoiceDialog.tsx:484-491`

**问题:** GachaPage 定义了 `COSMIC` 常量，ChoiceDialog 重复定义了内容几乎相同的 `COSMIC`。一旦修改需要同步两处。

**指引:**
1. 抽取到共享常量文件 `lib/constants.ts` 或 `lib/theme.ts`
2. 两处统一引用

---

## P3 — 用户体验与细节

### P3-1. index.html 标题为默认值

**涉及文件:** `index.html:7`

```html
<title>Tauri + React + Typescript</title>
```

**指引:** 改为项目实际名称，如 `<title>学习工具</title>`。

---

### P3-2. README.md 为默认 Tauri 模版

**涉及文件:** `README.md`

**指引:** 更新为项目实际说明文档。

---

### P3-3. 缺少核心算法测试

**涉及文件:** `algorithms.ts`（0 个测试文件）

**问题:** 加权随机选择、卡池分配、循环检测等核心算法没有任何测试。

**指引:**
1. 为以下函数编写单元测试：
   - `calculateFullWeight` / `selectWeightedRandom`
   - `getPoolForTime` / `planMultiDraw`
   - `detectCycle`
   - `filterByPool`

---

### P3-4. 重置弃牌堆操作无确认

**涉及文件:** `DiscardPage.tsx:38-56`

**问题:** "重置全部"按钮直接执行 `RESET_DISCARD`，没有二次确认，可能误操作。

**指引:** 添加确认对话框，或使用 toast 撤销机制。

---

### P3-5. 日程周模板无法编辑

**涉及文件:** `SchedulePage.tsx`

**问题:** 周日程模板只能通过临时安排覆盖，无法直接编辑周模板。

**指引:** 添加周模板编辑功能，如长按设置周模板。

---

## 操作指引汇总

### 优先修复（P0 — 必须立即处理）

```
1. types.ts → 添加 settings 字段定义
2. store.tsx → 修复 localStorage 初始加载
3. ChoiceDialog.tsx → 移动 COSMIC 定义到文件顶部
```

预计影响：页面白屏、数据不持久、弹窗崩溃。

### 建议顺序

```
第一优先级 → P0 三个问题（运行时崩溃）
第二优先级 → P1 功能缺陷（链式解锁、category 丢失、周期重置）
第三优先级 → P2 代码质量（力模拟抽离、typescript 检查）
第四优先级 → P3 用户体验
```

### 验证方式

| 问题 | 验证方法 |
|------|---------|
| P0-1 settings | 打开 GachaPage，确认背景渲染不报错；打开 KnowledgePage 确认不报错 |
| P0-2 localStorage | 添加任务 → 刷新页面 → 确认任务仍在 |
| P0-3 COSMIC | 点击抽卡按钮，确认 ChoiceDialog 弹窗正常显示 |
| P1-1 chain unlock | 完成一个已锁任务的前置任务，确认后续任务自动解锁 |
| P1-2 category | 编辑一个 non-daily 任务，确认 category 保持原值 |
| P1-3 periodic | 设置每日任务 → 放入弃牌堆 → 确认次日自动回到抽牌堆 |
| P1-4 RECORD_DRAW | 抽卡后点"另寻天命"，确认抽取记录未被错误写入 |
| P2-3 tsc | 运行 `npx tsc --noEmit`，确认零错误 |
