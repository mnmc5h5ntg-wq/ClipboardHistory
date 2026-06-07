# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic-style version naming for public releases.

## [v1.2.2beta] - 2026-06-08

### Added

- 新增设置窗口，可修改和恢复呼出主窗口的全局快捷键。
- 新增快捷键录制控件，支持在设置中直接录入组合快捷键。
- 新增本轮架构重构总结文档，记录五个模块深化点和验证结果。

### Changed

- 深化剪贴板输入模块，将轮询、解析、缩略图生成、来源 UTI 和相邻去重集中到 `ClipboardIntake`。
- 深化文件预览模块，将文件类型判断、文本读取、QuickLook 与 fallback 预览集中到 `FilePreview`。
- 深化应用外壳模块，将应用生命周期意图、主菜单、菜单栏、设置窗口和窗口恢复逻辑从 `AppDelegate` 中拆分。
- 深化快捷键配置模块，将偏好保存、Carbon 注册、失败回滚和错误提示集中管理。
- 将条目展示文案、文件名、大小和预览文本集中到 `EntryPresentation`，减少视图中的格式化逻辑。
- 更新 Release / 仓库整理文档，继续保持 DMG、App bundle 和分析产物不进入源码提交。

### Fixed

- 改善文件、图片和文本预览路径的一致性，减少视图层直接做磁盘读取的情况。
- 改善关闭窗口后的快捷键呼出路径，快捷键注册失败时会回滚到上一个可用配置。

## [v1.2.1] - 2026-06-06

### Added

- 菜单栏模式，支持显示主窗口、刷新历史、清空历史和退出应用。
- 视频文件预览，常见视频文件可通过 QuickLook 在详情区查看。
- 视频缩略图，Finder 复制视频文件时显示首帧缩略图。
- 标签/语义分类基础，区分文本、图片内容和文件引用。
- macOS 12 支持完善，补齐 `NavigationView` 与 `NSStatusItem` 兼容路径。

### Fixed

- 修复搜索无结果时错误显示“暂无剪贴板历史”的问题。
- 修复边栏时间精确到秒导致列表频繁跳动的问题。
- 修复边栏标题“时间剪史”在窄宽度下换行的问题。
- 完善关于窗口内容，补充版本、作者、GitHub、License 和项目简介。
- 优化按钮 Hover 动效，减少不一致和溢出感。
- 统一图片、视频、文件缩略图样式。
- 修复 macOS 12 关闭窗口后 Dock 图标无法重新打开主窗口的问题。
- 修复 macOS 12 菜单栏图标透明问题。
- 修复打包流程中的签名与扩展属性问题，降低“损坏无法打开”的概率。

### Changed

- 项目架构整理，将源码按 `Managers`、`Models`、`Utilities`、`Views` 分组。
- 拆分 `ContentView`、`ClipboardManager` 等核心文件，降低单文件职责复杂度。
- 生命周期管理优化，集中主窗口显示和恢复逻辑。
- 启动性能优化，默认关闭生命周期日志并延迟启动剪贴板监听。
- 打包流程优化，生成 Intel + Apple Silicon 通用 App。

## [v1.1] - 2026-06-06

### Added

- macOS 12+ 兼容构建。
- 常见文件格式预览。

### Fixed

- 移除调试绿框。
- 修正 Dock 图标尺寸。

## [v1.0] - 2026-06-05

### Added

- 初始版本。
- 剪贴板文本、图片和文件历史记录。
- SwiftUI 主窗口界面。
- DMG 打包流程。
