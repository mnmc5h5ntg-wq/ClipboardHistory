# AI 剪贴板规划交付对照表

## 本轮目标边界

本轮不实现最终 AI 功能，不接入任何模型，不改变现有用户体验。已完成的是长期架构规划、风险拆解和一组不会影响现有功能的基础类型。

## 需求对照

| 原始要求 | 已交付位置 | 结论 |
| --- | --- | --- |
| 未来接入 AI 哪些地方容易成为技术债 | `AI_TECHNICAL_ROADMAP.md` | `ClipboardEntry` 语义过薄、`HistoryStore` 可能膨胀、持久化需版本化、Provider 不能泄漏到业务层。 |
| 哪些模块未来必须重构 | `AI_TECHNICAL_ROADMAP.md` | 建议新增 `IntelligenceStore`、`RecommendationEngine`、`UserFeedbackStore`，并让 `HistoryPersistence` 分层。 |
| 现在应预留哪些扩展点 | `AI_TECHNICAL_ROADMAP.md`、`AI_ARCHITECTURE_OVERVIEW.md` | 预留智能元数据、上下文快照、Provider Registry、Privacy Gate、反馈闭环。 |
| 用户自定义 API 接入如何设计 | `AI_PROVIDER_DESIGN.md`、`API_AND_PRIVACY_DESIGN.md` | 简单/高级两层配置，API Key 进 Keychain，OpenAI-compatible 为主干。 |
| 兼容 DeepSeek / OpenAI / Anthropic / Gemini / OpenRouter / Ollama / 第三方服务 | `AI_PROVIDER_DESIGN.md`、`AIProviderModels.swift` | Provider kind 已建模，OpenAI-compatible 覆盖 DeepSeek/OpenRouter/Ollama/Gemini-compatible/第三方服务，Anthropic 单独适配。 |
| Apple Intelligence / Foundation Models / App Intents 机会 | `CONTEXT_ENGINE_DESIGN.md`、`REFERENCES.md` | 作为长期系统 Provider 和系统动作入口，必须 capability 检测，不能影响 macOS 12。 |
| 当前项目未来如何获取上下文 | `CONTEXT_ENGINE_DESIGN.md`、`ContextSnapshot.swift` | 分成低权限、用户授权、系统智能三层；统一输出 `ContextSnapshot`。 |
| Predictive Paste 是否可行 | `CONTEXT_ENGINE_DESIGN.md`、`RISK_ANALYSIS.md` | 可行但必须渐进：先候选面板和规则推荐，再语义搜索，最后才考虑拦截或增强粘贴。 |
| 从工程、性能、隐私、用户体验、商业价值分析 | `RISK_ANALYSIS.md`、`API_AND_PRIVACY_DESIGN.md`、`AI_CLIPBOARD_VISION.md` | 已分别拆解，并给出本地优先、异步推理、隐私分层、Pro 价值路径。 |

## 新增文档

```text
docs/ai/
    README.md
    AI_CLIPBOARD_VISION.md
    AI_TECHNICAL_ROADMAP.md
    AI_ARCHITECTURE_OVERVIEW.md
    AI_PROVIDER_DESIGN.md
    CONTEXT_ENGINE_DESIGN.md
    API_AND_PRIVACY_DESIGN.md
    RISK_ANALYSIS.md
    REFERENCES.md
    DELIVERY_MAP.md
```

## 新增基础设施代码

```text
ClipboardHistory/Sources/ClipboardHistoryApp/Intelligence/
    AIProviderModels.swift
    AIPrivacyPolicy.swift
    ContextSnapshot.swift
    RecommendationModels.swift
    EntryIntelligence.swift
    ClipboardEntryIntelligenceAdapter.swift
    RuleBasedRecommendationEngine.swift
    LocalRecommendationService.swift
```

这些代码目前只定义数据结构和隐私决策，不发网络请求，不读取系统上下文，不接入 UI。

## 新增测试

```text
ClipboardHistory/Tests/ClipboardHistoryAppTests/IntelligenceModelsTests.swift
```

覆盖：

- 云端 Provider 遇到 `secret` 内容时阻止发送。
- 本地 Provider 可以在本机处理敏感内容。
- Ollama / Apple Foundation Models 被识别为本地优先。
- 最小上下文快照默认不读取窗口标题、选中文本和文件上下文。

## 后续开发建议

### Step 1：规则推荐引擎

已新增 `RuleBasedRecommendationEngine` 和 `LocalRecommendationService`，只用本地特征：最近时间、收藏、内容类型、当前 App、用户选择反馈。

当前验收：不接模型也能产生可解释 Top Candidates；尚未接入用户可见 UI。

### Step 2：反馈存储

下一步记录用户接受、忽略、手动复制、撤销等反馈。先只本地保存，不上云。

### Step 3：上下文采集 MVP

先实现 `FrontmostAppCollector`，只采集前台 App 名称和 bundle id，不申请 Accessibility 权限。

### Step 4：Ollama 本地 Provider

先接本地 Ollama，验证摘要/分类和隐私策略。

### Step 5：OpenAI-compatible Provider

支持 OpenAI、DeepSeek、OpenRouter、自定义 base URL，但默认关闭云端发送。

### Step 6：语义搜索

在用户明确开启后，对文本和文件名生成 embedding；图片和文件内容后置。

### Step 7：Predictive Paste Beta

使用专用快捷键弹出候选，不直接替换系统 `⌘V`。

## 新增 Phase 1 内核

本轮继续推进后，新增了纯本地规则推荐内核：

- `EntryIntelligence`：未来 AI 派生元数据的独立承载层。
- `RuleBasedRecommendationEngine`：根据 recency、favorite、content type affinity、reuse feedback、negative feedback、sensitive tags 生成候选。
- `ClipboardEntryIntelligenceAdapter`：从现有 `ClipboardEntry` 生成 `ClipboardEntrySummary` 和 `EntryIntelligence`，识别 URL、邮箱、代码、shell 命令、验证码、API Key、图片/视频/文档/压缩包等标签。
- `LocalRecommendationService`：串联 adapter 和 rule engine，提供未来开发态入口可直接调用的本地推荐门面。
- `RuleBasedRecommendationEngineTests`：验证最近内容、收藏、反馈、浏览器 URL 上下文、敏感标签降权。
- `ClipboardEntryIntelligenceAdapterTests` 和 `LocalRecommendationServiceTests`：验证现有历史条目可以进入推荐链路。

该内核目前没有接入 UI，也不会改变用户体验。


## Magic 推荐入口 MVP

当前已将本地推荐链路接入一个轻量用户可见入口：

- 侧边栏顶部原「时间剪史」标题在普通单选状态下改为 `Magic` 按钮。
- 点击后展开「猜你要粘贴」。
- 只展示 `RuleBasedRecommendationEngine` 生成的 Top 3。
- 不接模型，不改剪贴板内容，不拦截 `⌘V`。
- 点击推荐条目复用普通历史选择逻辑。

这一步的目的不是宣称 AI 已完成，而是用真实 UI 逐步观察规则推荐是否有价值。

## 当前不建议立刻做的事

- 不建议直接接云端大模型。
- 不建议拦截系统 `⌘V`。
- 不建议读取当前选中文本或窗口标题，除非先完成权限说明和隐私策略 UI。
- 不建议把 AI 字段直接塞进 `ClipboardEntry` 主模型。
