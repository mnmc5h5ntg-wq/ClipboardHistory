# AI Provider 设计方案

## 1. 目标

未来「时间剪史」需要同时支持：

- OpenAI
- DeepSeek
- Anthropic
- Gemini
- OpenRouter
- Ollama
- 兼容 OpenAI API 的第三方服务
- Apple Intelligence / Foundation Models（可用时）

Provider 层目标不是“每个厂商写一套业务逻辑”，而是把差异压在边界内，让业务层只关心：摘要、分类、embedding、推荐解释。

## 2. Provider 类型

```swift
enum AIProviderKind {
    case openAI
    case openAICompatible
    case deepSeek
    case anthropic
    case gemini
    case openRouter
    case ollama
    case appleFoundationModels
}
```

### 2.1 OpenAI-compatible 主干

DeepSeek、OpenRouter、Ollama、许多第三方服务都提供 OpenAI-compatible Chat Completions 或相近接口。建议把它们统一走 `OpenAICompatibleProvider`，差异通过配置表达：

- `baseURL`
- `apiKey`
- `model`
- `supportsStreaming`
- `supportsEmbeddings`
- `supportsVision`
- `customHeaders`

### 2.2 Anthropic 单独适配

Anthropic Messages API 与 OpenAI Chat/Responses API 结构不同，建议单独 `AnthropicProvider`。业务层不要直接依赖 Anthropic message schema。

### 2.3 Gemini 双路径

Gemini 既有原生 API，也提供 OpenAI compatibility 入口。为了降低初期复杂度：

- Phase 1 使用 OpenAI-compatible 路径。
- 后续如需多模态或更细能力，再增加 `GeminiProvider`。

### 2.4 Ollama 本地优先

Ollama 是隐私友好的默认实验对象：

- base URL 默认 `http://localhost:11434/v1`
- 不需要云端 API Key
- 可作为语义搜索和摘要的第一块试验田

### 2.5 Apple Foundation Models

Apple 本地模型能力应作为系统 Provider：

- 不需要用户 API Key
- 隐私优势明显
- 但系统版本、设备和区域可用性不稳定
- 必须做 capability 检测和 fallback

## 3. 统一请求模型

### 3.1 Completion

```swift
struct AICompletionRequest {
    var task: AITask
    var messages: [AIMessage]
    var temperature: Double
    var maxTokens: Int?
    var privacy: AIPrivacyScope
}
```

### 3.2 Embedding

```swift
struct AIEmbeddingRequest {
    var input: [String]
    var model: String
    var privacy: AIPrivacyScope
}
```

### 3.3 Response

```swift
struct AICompletionResponse {
    var text: String
    var usage: AITokenUsage?
    var providerMetadata: [String: String]
}
```

## 4. Provider 配置

用户自定义 API 接入应支持两层：

### 4.1 简单模式

- 服务商：OpenAI / DeepSeek / Anthropic / Gemini / OpenRouter / Ollama
- API Key
- 模型名
- 是否允许发送剪贴板内容

### 4.2 高级模式

- Base URL
- 自定义 Header
- Chat endpoint
- Embedding endpoint
- 模型能力开关
- 超时
- 最大上下文长度
- 是否走代理

## 5. Keychain 与隐私

- API Key 必须保存在 Keychain，不写入 JSON 偏好文件。
- Provider 配置文件只保存非敏感字段。
- 每次联网请求前经过 `AIPrivacyPolicy`。
- 默认禁止发送疑似密码、验证码、密钥、私密文件路径。

## 6. 能力矩阵

| Provider | 云端/本地 | Text | Embedding | Vision | Tool Use | macOS 12 |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI | 云端 | 是 | 是 | 是 | 是 | 是 |
| DeepSeek | 云端 | 是 | 视模型 | 否/视模型 | 视模型 | 是 |
| Anthropic | 云端 | 是 | 否/外部 | 是 | 是 | 是 |
| Gemini | 云端 | 是 | 是 | 是 | 是 | 是 |
| OpenRouter | 云端 | 是 | 视路由模型 | 视模型 | 视模型 | 是 |
| Ollama | 本地 | 是 | 视本地模型 | 视模型 | 否/有限 | 是 |
| Apple Foundation Models | 本机/私有云视系统 | 是 | 待定 | 待定 | App Intents 联动 | 需新系统 |

## 7. 错误处理

Provider 错误要分层：

- 配置错误：缺 API Key、Base URL 不合法。
- 网络错误：超时、离线、TLS。
- 鉴权错误：401/403。
- 限流错误：429。
- 内容策略错误：provider 拒绝。
- 隐私策略阻止：本地策略不允许发送。
- 模型能力不支持：例如请求 embedding 但 provider 无 embedding。

UI 不应展示原始技术错误，而应给用户可行动的提示。

## 8. 推荐默认方案

首个可落地组合：

1. `RuleBasedRecommendationEngine`：不接模型，先验证推荐闭环。
2. `OllamaProvider`：本地摘要/分类实验。
3. `OpenAICompatibleProvider`：支持 OpenAI、DeepSeek、OpenRouter、Gemini compatible、自定义服务。
4. `AnthropicProvider`：第二批加入。
5. Apple Foundation Models：等系统 API 和可用性稳定后加入。
