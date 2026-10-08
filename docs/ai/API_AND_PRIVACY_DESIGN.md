# 用户自定义 API 与隐私设计

## 1. 设置界面模型

未来设置建议分为三块：

### 1.1 AI 总开关

- 关闭：不做任何模型请求。
- 仅本地：允许规则、Ollama、Apple 本地能力。
- 允许云端：允许向用户配置的云端 Provider 发送经裁剪的内容。

### 1.2 Provider 管理

字段：

- 显示名称
- Provider 类型
- Base URL
- API Key（Keychain）
- 默认聊天模型
- 默认 embedding 模型
- 能力开关：文本、embedding、视觉、流式
- 请求超时
- 每日预算 / 月度预算（可选）

### 1.3 数据发送策略

- 是否允许发送剪贴板全文
- 是否允许发送文件名
- 是否允许发送文件路径
- 是否允许发送图片 OCR/描述
- 是否允许发送当前窗口标题
- 是否自动排除疑似密码/验证码/API Key

## 2. API Key 存储

- 使用 Keychain，service 建议：`com.wangziyi.ClipboardHistory.ai-provider`
- account 使用 provider UUID
- 删除 Provider 时同步删除 Keychain 项
- 导出设置时不导出 API Key

## 3. 网络请求审计

每次模型请求应可记录本地审计摘要：

- 时间
- Provider
- 模型
- 任务类型
- 是否发送剪贴板全文
- token 用量
- 是否被隐私策略裁剪

不要默认保存完整 prompt。可提供调试模式，但需要明确提示。

## 4. 敏感内容检测

第一版用规则：

- 密码字段附近文本
- 6 位验证码
- JWT
- GitHub token / OpenAI key / Anthropic key 等常见 key pattern
- 私钥块
- 银行卡/身份证等疑似个人信息

命中后默认：

- 不发送云端
- 只允许本地模型处理
- 推荐结果中提示“因隐私策略已隐藏部分内容”

## 5. 自定义 OpenAI-compatible 服务

高级用户常用：

- DeepSeek
- OpenRouter
- Gemini OpenAI-compatible
- 本地 LiteLLM
- 公司内部代理
- Ollama `/v1`

因此不要把 base URL 写死，也不要假设模型列表一定可枚举。

最小配置：

```json
{
  "kind": "openAICompatible",
  "displayName": "DeepSeek",
  "baseURL": "https://api.deepseek.com/v1",
  "chatModel": "deepseek-chat",
  "embeddingModel": null,
  "capabilities": ["text"]
}
```

## 6. UX 建议

- 默认不要求用户配置 AI。
- 首次打开 AI 功能时展示“会发送什么 / 不会发送什么”。
- 每个 Provider 有“测试连接”按钮。
- 每个 AI 功能旁显示使用的 Provider。
- 推荐解释里避免过度技术化，例如：
  - “因为你正在 Safari 中编辑 GitHub 页面，且这条链接刚刚复制。”
  - “因为你最近常在微信中粘贴图片文件。”

## 7. 商业价值

可形成免费/付费分层：

免费：

- 本地历史
- 规则推荐
- 本地 Ollama 接入
- 手动 Provider 配置

Pro：

- 多 Provider 管理
- 语义搜索
- Predictive Paste
- 高级隐私规则
- 工作流模板
- iCloud 同步（如未来实现）

但早期不建议过早商业化，应先验证“预测粘贴是否真的帮用户省时间”。
