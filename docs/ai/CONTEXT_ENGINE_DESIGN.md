# Context Engine 设计方案

## 1. 为什么需要 Context Engine

Predictive Paste 的关键不是“历史里有什么”，而是“用户现在可能要做什么”。因此需要一个独立上下文引擎，把系统状态整理成可解释、可权限控制的 `ContextSnapshot`。

业务层不应到处直接读取 NSWorkspace、Accessibility、Spotlight 或 App Intents。所有上下文采集都应经过 Context Engine。

## 2. 上下文分层

### 2.1 Zero Permission Context

无需额外权限，风险低：

- 当前时间
- 最近剪贴板历史
- 当前 App bundle identifier（通常可从 NSWorkspace 获取）
- 当前 App 名称
- 应用内选择状态
- 收藏/最近使用反馈

### 2.2 User Granted Context

需要明确授权或系统权限：

- 当前窗口标题
- 当前选中文本
- 当前前台文档路径
- 浏览器 URL / 页面标题
- Finder 当前目录或选中文件
- Mail/Notes/Pages 等 App 的文档上下文

### 2.3 System Intelligence Context

未来能力：

- App Intents 暴露的实体
- Shortcuts 自动化输入
- Spotlight 搜索结果
- Apple Intelligence / Foundation Models 可访问的系统语义上下文

## 3. ContextSnapshot

推荐不可变快照结构：

```swift
struct ContextSnapshot {
    let capturedAt: Date
    let frontmostApplication: RunningApplicationContext?
    let activeWindow: WindowContext?
    let focusedDocument: DocumentContext?
    let recentEntries: [ClipboardEntrySummary]
    let selectedEntryID: UUID?
    let permissionState: ContextPermissionState
}
```

不要让推荐流程边推理边读取系统状态。这样可以：

- 降低竞态
- 方便测试
- 方便解释推荐原因
- 方便隐私审计

## 4. 上下文采集器

```swift
protocol ContextSignalCollector {
    var signalKind: ContextSignalKind { get }
    func collect() async -> ContextSignalResult
}
```

建议采集器：

- `FrontmostAppCollector`
- `WindowTitleCollector`
- `FinderSelectionCollector`
- `BrowserContextCollector`
- `RecentClipboardCollector`
- `UserFeedbackCollector`
- `AppIntentContextCollector`

## 5. 隐私预算

每个上下文信号应标记敏感级别：

- `.publicLike`：App 名称、文件扩展名
- `.personal`：窗口标题、文件名、URL
- `.sensitive`：选中文本、文档内容、剪贴板全文
- `.secret`：密码、验证码、密钥疑似内容

AI 请求构造时按用户设置裁剪上下文。例如用户只允许发送 App 名称，则 prompt 里不能包含窗口标题和剪贴板全文。

## 6. 推荐特征

第一版不需要模型也可以使用以下特征：

- recency：越近越高
- appAffinity：某条记录是否常在当前 App 粘贴
- contentTypeAffinity：当前 App 更常粘贴文本/图片/文件
- favoriteBoost：收藏加权
- exactSearchBoost：用户输入搜索词时关键词匹配
- reuseFrequency：历史复用频率
- negativeFeedback：用户忽略/撤销降权

## 7. Predictive Paste 可行性判断

### 可行

在低风险场景很可行：

- 最近复制了邮箱地址，当前焦点在邮件收件人输入框。
- 最近复制了验证码，当前 App 是浏览器登录页。
- 最近复制了文件，当前 App 是聊天窗口或上传框。
- 最近复制了 GitHub URL，当前 App 是浏览器、Markdown 编辑器、聊天 App。

### 难点

- macOS 普通 App 的输入框语义很难稳定获取。
- Accessibility 权限敏感，用户可能不愿开启。
- `⌘V` 是系统级肌肉记忆，错误一次会显著降低信任。
- 云端 AI 延迟不可控。

### 推荐策略

不要第一步拦截系统 `⌘V`。先做：

1. 专用快捷键打开“预测候选浮窗”。
2. 菜单栏显示 Top Candidates。
3. 记录用户选择反馈。
4. 命中率足够高后，再提供可选 Predictive Paste。

## 8. Apple 系统能力机会

### App Intents

可把「时间剪史」能力暴露给系统：

- 查询最近历史
- 查询收藏
- 再次复制某条
- 清空未收藏
- 开启/关闭隐私模式

未来 Shortcuts 和系统智能可以调用这些 Intent。

### Foundation Models / Apple Intelligence

机会：

- 本地摘要和分类
- 本地推荐解释
- 私密内容不出设备
- 与系统上下文整合

限制：

- 新系统才可用
- 设备支持不一致
- API 能力随系统变化
- 需要 fallback 到规则/Ollama/云端 provider

### Spotlight

机会：

- 文件记录丢失时尝试定位移动后的文件
- 结合用户最近文件推测粘贴意图

风险：

- 索引结果可能过多
- 文件名/路径隐私敏感

## 9. 性能策略

- 上下文采集有预算：例如 50ms 快速路径，慢信号后台补齐。
- 推荐排序必须先用本地规则快速返回。
- AI 请求只能异步更新候选，不阻塞 UI。
- embedding 和摘要生成走后台队列。
- 图片/文件内容默认不送模型，只送元数据，除非用户授权。
