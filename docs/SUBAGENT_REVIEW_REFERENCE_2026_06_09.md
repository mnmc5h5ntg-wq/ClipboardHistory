> **历史快照**：本文里的行数、测试数、文件清单与结论都是**写下它那天**的状态，不代表当前代码（当前基线请看 `AGENT_STATE.md` 与 `swift test` 的实际输出）。保留原文是为了留痕，不要照它行事。

# Subagent Review Reference 2026-06-09

项目：时间剪史 / ClipboardHistory
用途：把本轮 5 维度子代理同行评审、重复审查原因、已确认问题、已完成修复和后续改进路线整理成一个后续会话可直接读取的参考文档。
状态：参考文档，不代表已经提交或发布。

## 1. 快速结论

本轮审查的总体判断是：项目方向正确，v1.3 正在从“临时剪贴板工具”升级为“长期可依赖的剪贴板历史管理器”。核心架构已经形成：

- `HistoryStore`：历史状态中心。
- `MediaLoader`：文件、图片、文本、视频预览加载边界。
- `ClipboardWriter`：系统剪贴板写入边界。
- `ApplicationShell`：菜单、快捷键、状态栏等系统命令入口。
- `EntryPresentation`：历史条目展示文案和隐私标题。

审查中发现的主要风险集中在三类：

- 可靠性：系统剪贴板写入、快捷键注册、文件缺失、窗口识别等失败路径不能被当成成功。
- 性能与并发：大图、大视频、全量持久化、AppKit 对象跨线程会影响长期稳定性。
- 隐私与发布：剪贴板内容天然敏感，菜单栏、文件路径、明文持久化和安装说明需要谨慎处理。

截至本文件最新更新时，审查报告中的 20 个问题已经全部修复、完成收口，或按本轮约束明确暂缓。继续接手时请先读 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md` 的最终审计。

## 2. 关于“两轮 Subagent 审查”

本轮确实发生了两轮 5-subagent 审查：

1. 第一轮发生在自动上下文压缩之前。
2. 当时已经启动 5 个独立子代理，并且主 Agent 同步做了本地测试和关键文件抽查。
3. 自动上下文压缩之后，为避免遗漏，主 Agent 又重新调度了第二轮 5 个子代理。
4. 两轮均为只读审查，没有因为审查本身修改代码。
5. 两轮结论高度重合，说明核心问题可信度较高。

后续类似情况的处理原则：

- 优先读取本文件、`docs/SUBAGENT_CODE_REVIEW_2026_06_08.md` 和 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md`。
- 如果已有结果完整，不再重复启动子代理。
- 只有在缺少某个维度、结果明显不完整、或用户明确要求重新审查时，才重新调度。

## 3. 五个审查维度结论

### Security Agent

结论：

- 没有发现明显传统网络安全攻击面。
- 最大风险是剪贴板工具天然会接触密码、验证码、token、截图、聊天缓存路径和项目路径。
- 明文持久化、菜单栏摘要、完整文件路径展示都可能泄露隐私。

已处理：

- 历史目录和图片目录权限收紧为 `700`。
- `history.json` 和图片文件权限收紧为 `600`。
- 菜单栏快速复制条目改为隐私标题，不再直接显示文本摘要或文件名。
- UI 中的文件路径默认脱敏为文件名。

暂缓：

- 首次启动隐私说明。
- 暂停记录 / 隐私模式。
- 历史内容加密。
- 退出时清除或敏感内容自动清理。

### Quality Agent

结论：

- 一些系统边界失败路径原先不够明确。
- 快捷键、剪贴板写入、文件预览、文档一致性需要更严格的结果表达。

已处理：

- `ClipboardWriter.write` 改为失败时抛错。
- `HistoryStore` 只有在写入成功后才置顶、选中和持久化。
- `GlobalHotKeyController` 增加明确的快捷键更新结果。
- 启动快捷键失败时尝试恢复默认快捷键，并暴露最终状态。
- 增加多组负路径测试。

后续：

- 发布前继续同步 README、CHANGELOG、许可证、安装说明和架构文档。

### Bug Hunter Agent

结论：

- 重点缺陷是“看起来成功但实际失败”：再次复制失败仍置顶、快捷键注册失败回滚不可靠、文件丢失后预览或复制继续走旧路径。
- 图片去重曾依赖对象身份，不稳定。
- 主窗口识别依赖不稳定 identifier。

已处理：

- 再次复制失败不再置顶、不更新 changeCount、不持久化。
- 文件缺失时 `MediaLoader` 返回明确失败状态。
- 缺失文件再次复制前检查存在性，失败时不清空系统剪贴板。
- `StoredImage` 改为基于 PNG 数据 SHA256 去重。
- 主窗口由 `WindowConfigurator` 设置稳定 identifier，`WindowManager` 精确匹配。

### Concurrency & Performance Agent

结论：

- 大图片、大视频、外接盘文件、iCloud 文件会放大主线程压力。
- 视频缩略图生成、图片预览、全量持久化写盘是主要性能点。
- `@unchecked Sendable` 掩盖了 AppKit 对象跨线程风险。

已处理：

- `ClipboardIntake` 不再同步生成视频缩略图。
- `FileHistoryPersistence` 改为后台串行队列写盘，并提供 `flushPendingSaves()`。
- 应用退出时等待待保存历史落盘。
- `MediaLoader` 后台任务只返回 `Data`、`String`、URL、视频比例等安全 payload。
- `NSImage` 和 `FilePreview` 在 MainActor 创建。
- `FilePreview` 移除 `@unchecked Sendable`。
- 视频播放器停止、切换、视图拆卸时释放旧 `AVPlayerItem` 和 player layer。

### Architecture Agent

结论：

- v1.3 的主模块方向正确。
- 仍需收口几个维护边界：macOS 13+ 菜单栏快速复制、`DetailPreviewViews.swift` 文件过重、`ClipboardIntake` 仍承担部分媒体处理。

当前状态：

- macOS 13+ `MenuBarExtra` 快速复制已统一到 `ApplicationShell`。
- 视频预览、播放控制器、播放参数和时间格式化已经从 `DetailPreviewViews.swift` 拆到同目录 `VideoPreview.swift`。
- `ClipboardIntake` 已移除视频缩略图生成，也不再为文件 URL 同步读取源图片文件缩略图；图片文件内容读取留给 `MediaLoader` 预览阶段。

## 4. 去重后问题清单与状态

| 编号 | 优先级 | 问题 | 当前状态 |
| --- | --- | --- | --- |
| 1 | P0 | 剪贴板写回失败被当成成功 | 已完成 |
| 2 | P0 | 快捷键注册失败回滚不可靠 | 已完成 |
| 3 | P0 | 主窗口识别依赖不稳定 identifier | 已完成 |
| 4 | P0 | 图片去重按对象身份判断 | 已完成 |
| 5 | P0 | 文件丢失或移动后仍进入预览/复制流程 | 已完成 |
| 6 | P1 | 视频缩略图生成阻塞主线程 | 已完成 |
| 7 | P1 | 持久化在 MainActor 同步全量写盘 | 已完成 |
| 8 | P1 | AppKit 对象跨线程传递 | 已完成 |
| 9 | P1 | 视频播放器资源释放不完整 | 已完成 |
| 10 | P2 | 明文持久化剪贴板内容 | 已做权限硬化，产品功能暂缓 |
| 11 | P2 | 收藏绕过保留策略 | 已评估，保持现有产品决策 |
| 12 | P2 | 菜单栏直接暴露最近内容 | 已完成 |
| 13 | P2 | 文件路径在 UI 和 JSON 中暴露 | UI 已脱敏，JSON 保留真实 URL |
| 14 | P2 | macOS 13+ 菜单栏快速复制绕过 `ApplicationShell` | 已完成 |
| 15 | P3 | `DetailPreviewViews.swift` 过重 | 已完成 |
| 16 | P3 | `ClipboardIntake` 仍承担媒体处理 | 已完成 |
| 17 | P3 | 发布脚本失败回滚不完整 | 已完成 |
| 18 | P3 | 发布/安装说明鼓励绕过 Gatekeeper | 已完成 |
| 19 | P3 | GitHub Issue 脚本与本地 `.scratch/` 工作流冲突 | 已完成 |
| 20 | P3 | 文档与实现不一致 | 已完成 |

## 5. 已完成修复摘要

### 历史与剪贴板

- `ClipboardWriter` 成为系统剪贴板写入边界。
- 写入失败会被显式抛出。
- `HistoryStore` 只有在写入成功后才改变历史状态。
- 缺失文件不会先清空系统剪贴板。
- 图片历史去重改为基于内容指纹。

### 快捷键

- 快捷键更新采用 probe 机制，先验证新快捷键可注册，再切换真实快捷键。
- 新快捷键失败时明确区分旧快捷键是否恢复成功。
- 启动时保存快捷键不可用，会尝试回退默认快捷键。

### 窗口与菜单

- 主窗口设置稳定 identifier。
- 菜单栏内容标题改为隐私标题。
- macOS 12 状态栏菜单使用基于条目 id 的查找路径。
- macOS 13+ 菜单栏快速复制也统一到 `ApplicationShell`，并按 entry id 重新解析当前条目。

### 媒体预览

- 视频文件进入历史时不再同步生成缩略图。
- 缺失文件预览返回明确失败状态。
- 媒体后台加载只返回安全 payload，避免跨线程传递 AppKit 对象。
- 视频播放器在停止、切换 URL、视图拆卸时释放资源。

### 持久化与隐私

- 默认磁盘写入移到后台串行队列。
- 退出时 flush 待保存历史。
- 历史目录和文件权限已收紧。
- UI 默认不展示完整文件路径。
- JSON 仍保留真实文件 URL，以保证文件再次复制功能。

## 6. 后续推荐路线

本轮审查报告范围内的问题已经处理完。后续建议转入人工冒烟和提交前筛选：

- 按 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md` 的人工冒烟清单测试真实 App。
- 提交前排除 agent 工作流配置：`.agents/`、`AGENTS.md`、`docs/agents/`、`skills-lock.json`。
- 若要继续做隐私模式、历史加密、清空收藏、Developer ID 公证等，应作为下一轮独立产品需求规划。

## 7. 后续会话接手步骤

新会话建议先读取：

1. `docs/SUBAGENT_REVIEW_REFERENCE_2026_06_09.md`
2. `docs/REVIEW_FIX_PROGRESS_2026_06_08.md`
3. `docs/SUBAGENT_CODE_REVIEW_2026_06_08.md`

建议先检查当前状态：

```bash
cd /Users/wangziyi/Documents/Codex_Project0
git status --short
swift test --package-path ClipboardHistory
python3 -m unittest discover -s scripts/tests
```

人工测试启动命令：

```bash
cd /Users/wangziyi/Documents/Codex_Project0
osascript -e 'quit app "时间剪史"' 2>/dev/null || true
make run
```

## 8. 当前约束与注意事项

- 不要 commit 或 push，除非用户明确确认。
- 不要改动 agent 工作流配置：`.agents/`、`AGENTS.md`、`docs/agents/`、`skills-lock.json`。
- 不要为了审查建议做大规模目录重排。
- 保留 v1.2.1 及以前的边栏设计偏好：红绿灯在边栏左上角，边栏左侧圆角与窗口圆角同心。
- 用户更关心实际功能可用性，架构优化应服务功能，不应反过来扩大风险。

## 9. 最近验证记录

来自 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md` 的最近记录：

- 2026-06-09 02:03：`python3 -m unittest discover -s scripts/tests` 通过，11 个测试，0 失败。
- 2026-06-09 02:03：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。

本文档汇总的是既有审查和修复进度；最终证据以 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md` 为准。
