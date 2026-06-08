# 时间剪史架构重构总结

日期：2026-06-08

本轮重构基于最新架构体检报告继续推进，先把历史状态、媒体加载、菜单命令、发布流程和核心测试收进更清晰的模块；随后 v1.3 在该结构上加入历史持久化、收藏、开机启动和菜单栏快速复制。完成后又运行了一轮 `improve-codebase-architecture` 复查：唯一仍值得立即处理的菜单栏快速复制重复定义已抽成 `QuickCopyMenu`，剩余建议已经偏可选或理论优化，可以进入收尾和人工冒烟阶段。

## 1. 历史状态模块集中化

### 修改说明

- 新增 `HistoryStore`，作为历史记录的单一状态入口。
- 移除浅转发层 `ClipboardManager`，界面和应用外壳直接面向 `HistoryStore`。
- `HistoryStore` 统一处理：
  - 定时检查剪贴板
  - 历史记录新增、相邻去重、倒序排列、数量限制
  - 选择、复制、复制并置顶、删除、清空、搜索
  - 状态广播
- 新增 `ClipboardWriting` / `SystemClipboardWriter`，把“写入系统剪贴板”收成可替换的适配口。
- `HistorySidebarView` 和 `DetailView` 不再直接改历史状态，只发送行为事件。

### 测试结果摘要

- `HistoryStoreTests` 覆盖新增排序、相邻去重、数量限制、搜索、选择、删除、清空、复制、复制并置顶。
- 自动测试通过。

### 风险/兼容性说明

- v1.3 已接入 `FileHistoryPersistence`；历史记录会保存到 `~/Library/Application Support/时间剪史/`。
- 文件类记录保存的是原文件路径；如果原文件被移动或删除，历史记录仍在，但预览可能无法打开。
- 写系统剪贴板的真实行为仍由 `SystemClipboardWriter` 完成，用户可见复制行为保持一致。

### 建议下一个优化步骤

- 后续如果加入多版本迁移或加密，再继续深化 `HistoryPersistence` 内部结构。

## 2. 后台媒体加载模块

### 修改说明

- 新增 `MediaLoader` 和 `MediaLoadHandle`。
- `MediaLoader` 统一处理文件、图片、视频、文本预览加载。
- 新增加载状态：`loading`、`success`、`failure`。
- 支持取消已经发起的预览加载。
- `FilePreview` 只保留“预览结果”模型，不再承担加载流程。
- `DetailFileView` 改为异步加载预览，不再在初始化时同步读取文件。

### 测试结果摘要

- `MediaLoaderTests` 覆盖：
  - 文本预览
  - 图片预览
  - 文档 QuickLook 路径
  - 视频内置播放器路径
  - 未知类型 fallback
  - 异步加载成功
  - 取消加载
- 自动测试通过。

### 风险/兼容性说明

- `MediaLoader` 后台任务只返回 `Data`、`String`、URL、视频比例等可安全跨线程的数据；`NSImage` 和 `FilePreview` 在 MainActor 创建。
- QuickLook 真实渲染仍依赖系统能力；自动测试覆盖“选择 QuickLook 路径”，人工测试仍建议打开 App 看一次真实预览。

### 建议下一个优化步骤

- 做缩略图缓存时优先放到 `MediaLoader` 或独立缓存适配口中，避免缓存逻辑回流到 View。

## 3. 统一菜单命令清单

### 修改说明

- 新增 `AppCommand` 和 `AppCommandCatalog`，集中定义：
  - 显示主窗口
  - 设置
  - 刷新历史
  - 清空历史
  - 退出
- macOS 13+ `MenuBarExtra` 使用同一命令清单生成菜单。
- macOS 12 `NSStatusItem` 菜单也使用同一命令清单。
- 复查后继续收口：`MenuBarController` 现在只展示菜单并发送命令，实际行为统一交给 `ApplicationShell.perform(_:)`。
- v1.3 继续新增 `QuickCopyMenu`，统一 macOS 12/13 两条菜单栏入口的最近记录和收藏记录展示数据。

### 测试结果摘要

- `AppCommandTests` 覆盖命令顺序、标题、快捷键。
- `QuickCopyMenuTests` 覆盖最近记录和收藏记录分组、数量限制和空状态。
- 构建通过，确认 macOS 12/13 两条菜单路径都能编译。

### 风险/兼容性说明

- AppKit 菜单仍需要 selector 作为桥接，这是 macOS 12 状态栏菜单的系统要求。
- 清空历史的确认弹窗仍保留在 `ApplicationShell`，没有改变用户操作流程。

### 建议下一个优化步骤

- 如果未来菜单项继续增加，可以把主菜单构建也拆成纯数据描述；目前还不是必须项。

## 4. 打包与发布自动化工具

### 修改说明

- 新增 `scripts/prepare_release.py`。
- 支持输入版本号。
- 写入 `Makefile` 的 `VERSION`，由现有 `make dmg` 流程写入 App 的 `Info.plist`。
- 构建 App 和 DMG。
- 复制 DMG 到 `releases/`。
- 生成 SHA256 校验文件。
- 生成发布说明草稿。
- 更新 `CHANGELOG.md`。
- 如果同名 DMG 已存在，会先移入 `releases/archive/`。
- 支持 `--dry-run` 预演和 `--skip-build` 测试模式，避免误发布。
- v1.3 增加默认自动测试、`--skip-tests` 调试选项，以及构建后 `Info.plist` 版本号校验。

### 测试结果摘要

- `scripts/tests/test_prepare_release.py` 覆盖：
  - 版本号规范化
  - Makefile 版本写入
  - CHANGELOG 插入新版本块
  - 复制新 DMG
  - 生成 SHA256
  - 生成发布说明
  - 归档同名旧 DMG
  - 默认测试、构建和 `Info.plist` 校验流程
- `python3 scripts/prepare_release.py 9.9.9test --dry-run --skip-build` 预演通过。

### 风险/兼容性说明

- 正式发布仍不会自动上传 GitHub Release，也不会自动打 tag；脚本只准备本地发布材料。
- 正式执行不加 `--skip-build` 时会运行现有 `make dmg`，因此仍依赖本机 Swift、lipo、codesign、hdiutil 等 macOS 工具。

### 建议下一个优化步骤

- 下一次真正发版时，用脚本准备本地材料，再人工确认 DMG 后打 tag 和上传 Release。

## 5. 自动化测试

### 修改说明

- 在 Swift Package 中新增 `ClipboardHistoryAppTests` 测试目标。
- 新增核心测试文件：
  - `HistoryStoreTests`
  - `MediaLoaderTests`
  - `AppCommandTests`
  - `HotKeyShortcutTests`
  - `HotKeySettingsTests`
  - `HistoryPersistenceTests`
  - `ClipboardIntakeTests`
  - `LoginItemSettingsTests`
  - `QuickCopyMenuTests`
  - `EntryPresentationTests`
- 新增发布脚本测试：
  - `scripts/tests/test_prepare_release.py`

### 测试结果摘要

- Swift XCTest：89 个测试，0 失败。
- Python 脚本测试：11 个测试，0 失败。
- Swift 构建通过。
- 发布脚本预演通过。

### 风险/兼容性说明

- 自动测试覆盖核心逻辑和分支选择；真实 macOS UI 行为仍建议在提交前做一次人工冒烟：
  - 文本复制与重新复制
  - 图片复制与预览
  - 文件复制与 QuickLook 预览
  - 视频复制与内置播放器预览
  - 快捷键修改与恢复
  - 收藏、收藏筛选、菜单栏最近记录/收藏记录快速复制
  - 菜单栏显示窗口、刷新历史、清空历史、退出

### 建议下一个优化步骤

- 进入人工冒烟测试；如果通过，再按提交策略整理待提交文件。

## 复查结论

第二轮 `improve-codebase-architecture` 复查后，继续推进了三个实际有收益的点：

- 菜单控制器从“展示并执行”改为“只展示并发送命令”。
- `ClipboardManager` 作为浅转发层被删除，历史状态真正集中到 `HistoryStore`。
- `MediaLoader` 从 `FilePreview` 文件中拆出，媒体加载流程和预览结果模型分离。
- 菜单栏快速复制内容抽成 `QuickCopyMenu`，macOS 12/13 两条入口共享同一份菜单数据。

剩余建议主要是可选整理：

- 主菜单构建可以进一步数据化，但当前规模下收益有限。
- `EntryPresentation` 可以继续拆分更多展示文案，但现在已有足够集中度。
- AppKit / SwiftUI 的窗口生命周期还可以继续抽象，但会增加接口，不一定提升实际可维护性。

结论：本轮结构优化已经趋近合理，可以停止继续重构，进入人工冒烟测试和提交前检查。
