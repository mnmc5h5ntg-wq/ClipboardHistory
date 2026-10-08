# AI Clipboard 参考资料

以下资料用于校准 Provider、系统能力和上下文采集设计。它们不代表当前版本已经接入这些能力，只是长期架构规划的依据。

## Provider 与 API

- OpenAI Responses API：<https://platform.openai.com/docs/api-reference/responses>
  - 当前 OpenAI 主接口支持文本、图像、文件输入、结构化输出、工具调用和流式输出。
- Anthropic Messages API：<https://docs.anthropic.com/en/api/messages>
  - Anthropic 使用独立 Messages API，需要单独 Provider 适配。
- Gemini OpenAI compatibility：<https://ai.google.dev/gemini-api/docs/openai>
  - Gemini 提供 OpenAI 兼容路径，适合作为早期统一接入方案。
- Ollama OpenAI compatibility：<https://docs.ollama.com/api/openai-compatibility>
  - Ollama 支持本地 OpenAI-compatible 接口，适合作为隐私优先实验 Provider。
- OpenRouter Quickstart：<https://openrouter.ai/docs/quickstart>
  - OpenRouter 聚合多模型，适合走 OpenAI-compatible provider 分支。

## Apple 系统能力

- Foundation Models framework：<https://developer.apple.com/documentation/FoundationModels>
  - Apple Developer 文档说明其提供 Foundation Models 框架入口；页面内容需 JavaScript，但官方搜索摘要显示它用于访问 Apple Intelligence 相关模型。
- WWDC：Meet the Foundation Models framework：<https://developer.apple.com/videos/play/wwdc2025/286/>
  - 介绍 on-device 模型、结构化生成、流式响应、tool calling 和 session/context 管理。
- App Intents：<https://developer.apple.com/documentation/AppIntents>
  - App Intents 可让 App 内容和动作进入 Siri、Spotlight、Shortcuts、widgets 等系统体验。
- NSWorkspace `frontmostApplication`：<https://developer.apple.com/documentation/appkit/nsworkspace/frontmostapplication>
  - 可获取接收键盘事件的前台 App，适合作为低权限上下文信号。

## 规划结论

1. OpenAI-compatible 应作为第一条 Provider 主干。
2. Anthropic 保持独立适配，避免污染统一业务模型。
3. Ollama 是最适合早期本地隐私实验的 Provider。
4. Apple Foundation Models 和 App Intents 是长期机会，但必须以 capability/fallback 方式接入，不能影响 macOS 12 基线。
