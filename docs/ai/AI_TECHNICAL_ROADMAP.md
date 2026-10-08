# AI 剪贴板技术路线图

## 1. 当前工程基线

当前代码已经拆出若干重要边界：

- `ClipboardEntry`：历史条目主模型。
- `ClipboardEntryContent`：文本、图片、文件、多文件的内容枚举。
- `HistoryStore`：历史集合、收藏、清理、选择等状态管理。
- `HistoryPersistence`：本地持久化。
- `ClipboardIntake`：剪贴板读取与条目生成。
- `ClipboardWriter`：再次复制。
- `EntryPresentation`：展示文案。
- `MenuBarController` / `WindowManager` / `GlobalHotKeyController`：系统入口。

这些边界适合继续演化，但 AI 化后有几个风险点必须提前控制。

## 2. 最容易变成技术债的位置

### 2.1 `ClipboardEntry` 语义过薄

当前条目主要描述“内容是什么”。AI 需要的是“内容意味着什么”：

- 摘要
- 语言
- 来源 App
- 内容类型标签
- 敏感性判断
- embedding 状态
- 最近使用反馈
- 推荐特征

如果直接把所有 AI 字段塞进 `ClipboardEntry`，模型会迅速膨胀。建议保留 `ClipboardEntry` 作为事实层，新增派生层：`EntryIntelligence`。

### 2.2 `HistoryStore` 容易变成万能状态桶

AI 推荐需要排序、反馈、候选召回、上下文匹配。如果都塞进 `HistoryStore`，会把 UI 状态、历史管理和智能排序耦合在一起。

建议新增：

- `IntelligenceStore`：保存 AI 派生数据和本地索引。
- `RecommendationEngine`：根据上下文生成候选。
- `UserFeedbackStore`：记录用户选择、忽略、撤销等反馈。

### 2.3 `HistoryPersistence` 需要版本化迁移

未来会保存更多结构化数据。需要避免单个 JSON 无限膨胀：

- 历史事实数据
- 缩略图 / 图片 blob
- AI 元数据
- embedding 向量
- 用户反馈

建议分文件或 SQLite，而不是继续扩大单个 Codable 文件。

### 2.4 UI 与推荐排序不能混在一起

AI 推荐不是“换一种排序方式”这么简单。UI 只应该消费 `RecommendationResult`，不要知道 provider、prompt、embedding、上下文采集细节。

### 2.5 Provider 不能泄漏到业务层

OpenAI、DeepSeek、Anthropic、Gemini、OpenRouter、Ollama 的请求格式不同。业务层只应依赖统一协议：

```swift
protocol AIProvider {
    func complete(_ request: AICompletionRequest) async throws -> AICompletionResponse
    func embed(_ request: AIEmbeddingRequest) async throws -> AIEmbeddingResponse
}
```

## 3. 必须预留的扩展点

1. **条目智能元数据**：每条历史可关联一份独立 AI 分析结果。
2. **上下文快照**：推荐时使用不可变 `ContextSnapshot`，避免到处实时读取系统状态。
3. **Provider Registry**：用户可配置多个模型服务。
4. **隐私策略**：每次 AI 请求都要经过 `PrivacyPolicy` 判定。
5. **异步任务队列**：摘要、分类、embedding 后台执行，不能阻塞复制。
6. **推荐解释**：推荐结果必须包含 reason / features。
7. **反馈闭环**：记录用户选择哪条、忽略哪条、撤销哪条。
8. **能力探测**：不同 Provider 支持的 text、vision、embedding、tool use、local only 不同。

## 4. 分阶段路线

### Phase 0：架构准备（当前阶段）

- 写清 AI 愿景和边界。
- 增加 provider / context / recommendation 的基础类型。
- 不接模型，不改体验。

### Phase 1：本地规则推荐

不接 AI，只用规则建立可测试闭环：

- 前台 App 匹配
- 最近复制时间
- 收藏加权
- 文本类型识别
- 文件类型识别
- 用户最近选择反馈

当前已完成第一块基础内核：`EntryIntelligence` 和 `RuleBasedRecommendationEngine` 已加入 `Intelligence/`，可基于最近复制、收藏、当前 App、复用反馈和敏感内容标签生成本地候选，不调用任何模型、不改变现有 UI。

下一步交付：把该引擎接入一个隐藏或开发态候选入口，验证菜单栏/快捷键候选排序是否更聪明，但暂不宣传 AI。

### Phase 2：智能元数据离线生成

- 摘要
- 类型标签
- 敏感内容检测
- 语言检测
- 本地 embedding 预留接口

默认本地规则，可选 Ollama。

### Phase 3：语义搜索

- 语义查询入口
- embedding 索引
- OpenAI-compatible / Ollama provider
- 明确隐私提示

### Phase 4：上下文推荐

- 前台 App / 窗口标题 / 当前文件上下文
- `ContextSnapshot` 权限管理
- 推荐解释
- 反馈学习

### Phase 5：Predictive Paste Beta

- 专用快捷键，不拦截系统 `⌘V`
- 高置信度候选置顶
- 低置信度弹出候选面板
- 一键撤销与纠错反馈

### Phase 6：系统级能力融合

- App Intents 暴露历史查询和粘贴动作
- Shortcuts 自动化
- Spotlight / 文件上下文
- Apple Foundation Models 本地推理（系统支持时）

## 5. macOS 12 兼容策略

- 核心 AI 架构必须纯 Swift/Foundation，兼容 macOS 12。
- Apple Intelligence / Foundation Models / 新 App Intents 能力必须用 `if #available` 包裹。
- Provider 和 Context Engine 不能依赖 macOS 15+ API。
- 新能力以 capability 形式注册：旧系统没有能力但不崩溃。

## 6. 验收标准

每个阶段都必须保持：

- 不破坏传统剪贴板历史。
- 用户能关闭 AI。
- AI 失败不影响复制/粘贴。
- 敏感内容不会未经授权发送到网络。
- `swift build` 和现有测试通过。
