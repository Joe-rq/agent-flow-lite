# C4 前端工具函数 / 类型集中化 - 完成记录

## 任务概述
创建前端共享工具文件并集中类型定义，确保 Vue 组件从共享工具导入。

## 已创建/确认的文件

### 1. `frontend/src/utils/format.ts`
**功能**: 日期和文件大小格式化函数
- `formatDate(dateStr: string, includeTime = false): string` - 格式化日期为中文格式
- `formatFileSize(bytes: number): string` - 格式化文件大小（B/KB/MB/GB）

### 2. `frontend/src/utils/constants.ts`
**功能**: API 常量定义
- `API_BASE = '/api/v1'` - API 基础路径

### 3. `frontend/src/utils/fetch-auth.ts`
**功能**: 带认证的 fetch 工具
- `createAuthenticatedHeaders(contentType?: string): Record<string, string>` - 创建带认证头的 headers
- `authenticatedFetch(url: string, options?: RequestInit): Promise<Response>` - 带自动认证头的 fetch 封装

### 4. `frontend/src/types/index.ts`
**功能**: 共享 TypeScript 接口定义
- `User` - 用户数据接口
- `SkillInput` - Skill 输入参数接口
- `Skill` - Skill 数据接口
- `SkillApiItem` - API 返回的 Skill 格式
- `KnowledgeBase` - 知识库接口
- `Document` - 文档接口
- `UploadTask` - 上传任务接口
- `SearchResult` - 搜索结果接口

## 已更新的 Vue 组件

以下组件已在使用共享工具：

1. **KnowledgeView.vue**
   - 导入: `formatDate`, `formatFileSize` from `@/utils/format`
   - 导入: `API_BASE` from `@/utils/constants`
   - 导入: `KnowledgeBase`, `Document`, `UploadTask`, `SearchResult` from `@/types`

2. **SkillsView.vue**
   - 导入: `formatDate` from `@/utils/format`
   - 导入: `API_BASE` from `@/utils/constants`
   - 导入: `Skill`, `SkillApiItem` from `@/types`

3. **AdminUsersView.vue**
   - 导入: `formatDate` from `@/utils/format`
   - 导入: `API_BASE` from `@/utils/constants`
   - 导入: `User` from `@/types`

4. **SkillEditor.vue**
   - 导入: `API_BASE` from `@/utils/constants`
   - 导入: `SkillInput` from `@/types`

5. **WorkflowEditor.vue**
   - 导入: `formatDate` from `@/utils/format`
   - 导入: `API_BASE` from `@/utils/constants`

## 验证结果

- **TypeScript 检查**: ✅ 通过 (`npx tsc --noEmit`)
- **测试运行**: ⚠️ 132 通过，26 失败（失败为既有问题，与本重构无关）

## 重构模式总结

1. **工具函数集中化**: 将重复的格式化逻辑集中到 `format.ts`
2. **API 路径统一**: 通过 `constants.ts` 统一管理 API 前缀
3. **认证逻辑封装**: `fetch-auth.ts` 提供统一的认证头处理
4. **类型定义共享**: `types/index.ts` 作为单一类型来源，避免重复定义

## 向后兼容性

- 所有类型定义与原有使用方式兼容
- 组件功能无变化，仅导入路径调整
- API 合约保持不变

## 注意事项

- ChatTerminal.vue 中的 `formatTime` 保持独立实现，因其使用 timestamp 数字格式而非日期字符串
- SkillsView.vue 中的 `runSkill` 函数内联了认证头创建逻辑，可考虑未来使用 `fetch-auth.ts` 中的 `createAuthenticatedHeaders`

---
记录时间: 2026-02-09
