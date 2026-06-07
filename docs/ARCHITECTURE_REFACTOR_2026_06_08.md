# 时间剪史架构重构总结

日期：2026-06-08

本轮重构基于 `improve-codebase-architecture` 生成的五个候选改进点展开，目标是在不改变用户可见行为的前提下，把浅模块加深，让核心流程拥有更清晰的 interface、更好的 locality，以及后续测试和功能扩展的 leverage。

## 改动概览

### 1. 剪贴板摄取模块

新增 `ClipboardIntake`，替代原来的 `ClipboardReader` 扩展。

现在 `ClipboardIntake` 负责：

- 记录和判断 `NSPasteboard.changeCount`
- 按既有顺序读取剪贴板：文件 URL -> PNG -> TIFF -> 文本
- 生成文件、图片和视频缩略图
- 收集来源 UTI
- 将读取结果转换为 `ClipboardEntry`
- 阻止相邻重复条目进入历史列表

`ClipboardManager` 现在主要负责历史列表、选中项、搜索、复制、删除和清空。

### 2. 文件预览模块

新增 `FilePreview` 和 `FilePreviewLoader`。

现在文件预览选择集中在一个模块里：

- 图片文件加载为图片预览
- 文本文件加载为文本预览
- 文档和视频走 QuickLook
- 其他文件走 fallback 预览

`DetailFileView` 不再直接判断文件类型，也不再在 `body` 中做磁盘读取；它只渲染 `FilePreview` 的结果。

### 3. 应用外壳模块

新增 `ApplicationShell`。

现在应用级意图集中在一个 module：

- 配置剪贴板管理器
- 显示主窗口
- Dock 重开后恢复窗口
- 激活后延迟恢复主窗口
- 显示设置窗口
- 刷新历史
- 清空历史
- 退出应用

`AppDelegate` 现在更像 macOS 生命周期 adapter，负责接收系统事件、注册 Apple Event、监听全局快捷键按下通知，再把意图转发给 `ApplicationShell`。

### 4. 快捷键配置模块

新增 `HotKeySettings`。

现在快捷键配置集中处理：

- 当前快捷键状态
- 启动时注册 Carbon 全局快捷键
- 保存新快捷键
- 注册失败时回滚到旧快捷键
- 重置默认快捷键
- 向设置界面暴露错误消息

`SettingsView` 不再通过“保存偏好 -> 发通知 -> AppDelegate 注册 -> 失败通知 -> View 回滚”的链路处理快捷键，而是直接调用 `HotKeySettings`。

### 5. 展示格式化模块

新增 `EntryPresentation`。

现在条目展示文案集中处理：

- 边栏 preview 文案
- 详情尺寸文案
- 文件名 base name 和扩展名拆分

`EntryContent.preview` 和 `EntryContent.sizeDescription` 保留原有调用方式，但实现已委托给 `EntryPresentation`，减少模型与展示文案之间的耦合。

## 行为保持

本轮重构刻意保持以下行为不变：

- 剪贴板读取优先级仍然是：文件 URL -> PNG -> TIFF -> 文本
- 文本复制和重新复制行为不变
- 图片复制和预览行为不变
- 文件 QuickLook 预览行为不变
- 菜单栏显示窗口、刷新历史、清空历史、退出行为不变
- 快捷键修改、失败回滚和恢复默认行为不变

## 验证

自动验证：

```bash
swift build --package-path ClipboardHistory
```

结果：通过。

人工冒烟测试：

- 文本复制与重新复制：通过
- 图片复制与预览：通过
- 文件复制与 QuickLook 预览：通过
- 快捷键修改与恢复：通过
- 菜单栏显示窗口、刷新历史、清空历史、退出：通过

## 后续建议

- 为 `ClipboardIntake` 增加单元测试，覆盖读取顺序、空文本过滤、相邻重复过滤和 source UTI 保留。
- 为 `FilePreviewLoader` 增加轻量测试，覆盖图片、文本、QuickLook 和 fallback 分支。
- 后续做历史持久化时，把持久化 adapter 接到 `ClipboardManager` 外侧，避免重新扩大 manager interface。
- 后续做缩略图缓存时，优先放在 `ClipboardIntake` 或其内部 adapter 里，避免缓存逻辑泄漏到 View。
