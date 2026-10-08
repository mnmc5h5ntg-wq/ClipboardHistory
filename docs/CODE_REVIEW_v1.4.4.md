> **历史快照**：本文里的行数、测试数、文件清单与结论都是**写下它那天**的状态，不代表当前代码（当前基线请看 `AGENT_STATE.md` 与 `swift test` 的实际输出）。保留原文是为了留痕，不要照它行事。

# ClipboardHistory 五维度同行评审报告

**日期**：2026-06-11 | **版本**：v1.4.4 | **审查模式**：5 Subagent 并行审查

---

## 审查维度与代理

| 代号 | 维度 | 发现数 |
|------|------|--------|
| 🔒 Hubble | 安全性 | 2 高 · 3 中 |
| 📋 Arendt | 代码质量 | 5 项 |
| 🐛 Lagrange | 缺陷猎手 | 1 Bug · 7 维通过 |
| ⚡ Pauli | 并发与性能 | 2 高 · 4 中 |
| 🏗️ Ampere | 架构评估 | 4 优化 · 7 维通过 |

---

## 🔴 高优先级（建议近期修复）

### 1. 明文存储全部剪贴板内容
**代理**：Hubble (Security)  
**文件**：`Managers/HistoryStore.swift`  
**描述**：`history.json` 文本字段和 `images/` 目录中图片**以明文存储**。目录权限 `0o700`/`0o600` 正确，但 FileVault 未启用或物理访问时数据暴露。  
**建议**：AES-GCM 加密 + Keychain 密钥，或存储前调用 `sensitivity()` 过滤 `.secret` 级别。

### 2. 反馈导出无文件权限保护 + 强制解包
**代理**：Hubble (Security) + Arendt (Quality)  
**文件**：`Intelligence/RecommendationFeedbackStore.swift:55-56`  
**描述**：`exportToFile()` 导出 JSONL 文件未设 `0o600` 权限，含用户文件路径。另 `dir!` 两处强制解包（来自 `.first?` 可选链），`userDomainMask` 不可用时崩溃。  
**建议**：`guard let dir` 安全解包；目录设 `0o700`，文件设 `0o600`。

### 3. 主线程 AppleScript 同步阻塞
**代理**：Pauli (Concurrency)  
**文件**：`Intelligence/SystemContextCollector.swift`  
**描述**：`currentBrowserContext()` 使用 `CGWindowListCopyWindowInfo`（10-50ms）+ `NSAppleScript`（可能阻塞数秒），在主线程同步执行。触发于用户点击推荐/切换推荐面板时。  
**建议**：改为 `async` + `Task.detached`。

### 4. 非 Sendable 类型跨越 Task.detached
**代理**：Pauli (Concurrency)  
**文件**：`Managers/HistoryStore.swift:134-144`  
**描述**：`ClipboardEntry`（含 `NSImage`）被传入 `Task.detached` 闭包。Swift 6 严格检查下直接报错。  
**建议**：Task 前提取纯文本摘要数组 `[ClipboardEntrySummary]` + `[UUID: EntryIntelligence]` 传递。

---

## 🟡 中优先级

### 5. `togglePredictionSuggestions` 重复 if/else 块 (Bug)
**代理**：Lagrange (Bug Hunter)  
**文件**：`Managers/HistoryStore.swift:400-410`  
**描述**：完全相同的 `if/else` 块执行两次，每次切换触发两次 `refreshPredictions()`。  
**修复**：删除重复块。

### 6. 隐私过滤器覆盖不足
**代理**：Hubble (Security)  
**文件**：`Intelligence/RuleBasedRecommendationEngine.swift`  
**描述**：`containsSensitiveContent()` 仅检查 `preview` 前 160 字符，缺 AWS/Slack/JWT/私钥等模式，仅推荐引擎中使用。  
**建议**：扩展检测模式（`AKIA`、`xoxb-`、`eyJ`、`-----BEGIN`、数据库连接串），检测完整文本，在存储入口调用。

### 7. 剪贴板入口无敏感过滤
**代理**：Hubble (Security)  
**文件**：`Managers/ClipboardIntake.swift`  
**描述**：`readEntry(from:)` 直接存储密码/API key/验证码等敏感文本，不做拦截。  
**建议**：存储前调用 `ClipboardEntryIntelligenceAdapter` 的检测器。

### 8. `copySequence` 死代码
**代理**：Arendt (Quality)  
**文件**：`Managers/HistoryStore.swift:301`  
**描述**：被持续写入和裁剪，从未被任何代码读取。  
**建议**：删除或实现序列识别逻辑。

### 9. 过长函数
**代理**：Arendt (Quality)  
| 函数 | 文件 | 行数 |
|------|------|------|
| `refreshPredictions()` | HistoryStore.swift | 192 |
| `settingsContent` | SettingsView.swift | 236 |
| `body` (HistorySidebarView) | HistorySidebarView.swift | 141 |
| `perform(_:)` | HistoryStore.swift | 78 |

### 10. HistoryStore God Object 倾向
**代理**：Ampere (Architecture)  
**描述**：852 行承担 6 项职责（轮询/增删改查/多选/去重/OCR/推荐）。  
**建议**：提取 `PredictionCoordinator`(~250行)和 `OCRScheduler`(~80行)。

### 11. Timer 持续运行影响电池
**代理**：Pauli (Concurrency)  
**描述**：0.5s 轮询 + 1s App 切换 Timer 在后台不暂停。  
**建议**：后台时暂停，用 `NSWorkspace` 通知替代轮询。

---

## 🟢 低优先级 / 优化建议

- `scheduleOCRIfNeeded` 中 CGImage 提取回退模式重复 → 提取为 `NSImage` 扩展
- `SystemContextCollector` 硬编码实例化 → 走构造注入
- `osascript` ⌘V 模拟 → 抽象为 `PasteSimulationService` 协议
- `RecommendationFeedbackStore.exportToFile()` try? 静默吞错 → 区分无数据/导出失败

---

## 📊 综合评级

| 维度 | 评级 |
|------|------|
| 安全性 | 🟡 |
| 代码质量 | 🟢 |
| 缺陷控制 | 🟢 |
| 并发与性能 | 🟡 |
| 架构设计 | 🟢 |
| **综合** | **🟢 良好** |

项目整体处于同类个人工具的良好水平。架构分层清晰，兼容方案优雅，核心引擎可独立单测。
