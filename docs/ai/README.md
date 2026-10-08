# AI 剪贴板规划文档索引

这组文档用于规划「时间剪史」从传统 Clipboard Manager 演进为 AI Clipboard 的长期方向。当前阶段不接入任何具体模型，不改变现有用户体验，只建立清晰架构边界。

## 文档列表

1. [AI 剪贴板长期愿景](AI_CLIPBOARD_VISION.md)
   - 产品北极星
   - 体验层级
   - 成功指标

2. [技术路线图](AI_TECHNICAL_ROADMAP.md)
   - 当前工程基线
   - 技术债风险
   - 分阶段路线
   - macOS 12 兼容策略

3. [系统架构草图](AI_ARCHITECTURE_OVERVIEW.md)
   - Fact Layer
   - Intelligence Layer
   - Context Engine
   - Recommendation Engine
   - Provider Layer
   - Privacy Gate

4. [Provider 设计方案](AI_PROVIDER_DESIGN.md)
   - OpenAI-compatible 主干
   - DeepSeek / OpenRouter / Ollama / Gemini 兼容策略
   - Anthropic 单独适配
   - Apple Foundation Models 机会

5. [Context Engine 设计方案](CONTEXT_ENGINE_DESIGN.md)
   - 上下文采集分层
   - `ContextSnapshot`
   - Predictive Paste 可行性判断
   - App Intents / Spotlight / Apple Intelligence 机会

6. [用户自定义 API 与隐私设计](API_AND_PRIVACY_DESIGN.md)
   - Provider 设置
   - Keychain
   - 数据发送策略
   - 审计与敏感内容检测

7. [风险分析](RISK_ANALYSIS.md)
   - 工程风险
   - 隐私风险
   - 用户体验风险
   - 性能风险
   - 可行性结论

## 已加入的基础设施代码

新增纯 Swift 类型，不接网络、不改变 UI：

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

这些类型只是未来 AI 能力的接口地基：

- Provider 配置
- AI 请求/响应模型
- 隐私策略决策
- 上下文快照
- 推荐候选与反馈

## 下一步建议

本地 `RuleBasedRecommendationEngine` 的第一版内核已经加入，但还没有接入任何用户可见入口。下一步应做的是：

- 从现有历史生成 `ClipboardEntrySummary`
- 在开发态或隐藏入口中跑推荐候选
- 记录用户接受/忽略反馈
- 观察候选命中率，再决定是否进入菜单栏或快捷键面板

这可以验证 Predictive Paste 的基础假设，同时不引入隐私风险。
