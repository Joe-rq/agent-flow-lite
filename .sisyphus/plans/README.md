# Plans 目录索引

**说明**: 本目录存放所有工作计划的 Markdown 文件

---

## 📊 统计

- **总计**: 24 个计划

---

## 📋 计划列表

### 🔧 CI/CD 和质量改进

- `anti-oom-scheduling-guardrails.md` - 防止 OOM 的调度护栏
- `fix-quality-gate-double-failure.md` - 修复 Quality Gate 双重失败
- `global-claude-test-resource-constraints.md` - Claude 测试资源约束
- `post-gate-stability-quick-pass.md` - Post-Gate 稳定性快速修复
- `week1-quality-baseline.md` - Week 1 质量基线

### 🎨 UI/UX 改进

- `chat-composer-desktop-scale.md` - 聊天编辑器桌面缩放
- `frontend-ui-refresh.md` - 前端 UI 刷新
- `frontend-ui-style-unification.md` - 前端 UI 样式统一
- `login-page-cleanup.md` - 登录页面清理
- `login-ui-register.md` - 登录 UI 注册
- `remove-info-panel.md` - 移除信息面板
- `skill-menu-home.md` - Skill 菜单主页
- `ui-refactor.md` - UI 重构
- `workflow-editor-toolbar-drawer.md` - 工作流编辑器工具栏抽屉

### 🔐 认证和授权

- `auth-refresh-logout-fix.md` - 认证刷新登出修复
- `user-management-email-zep.md` - 用户管理邮箱 Zep

### 🧪 测试和验证

- `coze-demo.md` - Coze 演示
- `prd-compliance-review.md` - PRD 合规性审查

### 🗑️ 清理和移除

- `remove-skill-model-field.md` - 移除 Skill 模型字段
- `remove-skill-model-field-completed.md` - 移除 Skill 模型字段（已完成）
- `remove-zep.md` - 移除 Zep
- `zep-session-memory.md` - Zep 会话内存

### 🔧 其他

- `skill-run-401.md` - Skill 运行 401 错误
- `skill-save-422.md` - Skill 保存 422 错误

---

## 🔍 快速查找

### 按状态

查看 `boulder.json` 获取当前活跃的计划。

### 按类型

- **CI/CD**: anti-oom*, fix-quality*, global*, post-gate*, week1*
- **UI/UX**: chat*, frontend*, login*, remove-info*, skill-menu*, ui*, workflow*
- **Auth**: auth*, user*
- **Test**: coze*, prd*
- **Cleanup**: remove*, zep*

---

## 📝 使用说明

1. **查找计划**: 使用文件名或 `ls` 命令
2. **查看详情**: `cat .sisyphus/plans/<plan-name>.md`
3. **当前计划**: 查看 `.sisyphus/boulder.json`

---

**更新**: 2026-02-08
