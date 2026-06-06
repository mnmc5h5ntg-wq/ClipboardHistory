# 时间剪史 v1.2.1

这是 v1.2 系列的发布收尾版本，重点是稳定性、macOS 12 兼容、文件/视频预览、菜单栏模式和项目架构整理。

## 功能亮点

- 新增菜单栏模式：可从 macOS 顶部菜单栏显示主窗口、刷新历史、清空历史和退出应用。
- 支持视频文件预览：复制 Finder 中的视频文件后，可在详情区通过 QuickLook 预览。
- 支持视频缩略图：复制视频文件时，边栏显示首帧缩略图。
- 支持常见文件预览：PDF、Word、Excel、PowerPoint、Pages、Numbers、Keynote、代码文件等。
- 完善 macOS 12 支持：保留 macOS 13+ `MenuBarExtra`，macOS 12 使用 `NSStatusItem` 回退。
- 支持 Universal Binary：Intel 与 Apple Silicon Mac 均可运行。

## 修复内容

- 修复搜索无结果时状态提示错误。
- 修复边栏时间每秒刷新导致的跳动。
- 修复边栏标题偶尔换行。
- 修复 macOS 12 关闭窗口后 Dock 图标无法重新打开窗口。
- 修复 macOS 12 菜单栏图标透明问题。
- 优化 Hover 动效和 glass 按钮视觉一致性。
- 统一图片、视频、文件缩略图样式。
- 补充关于窗口信息。
- 改进打包流程，清理 quarantine / xattr 并进行签名验证。

## 兼容性说明

- 最低系统：macOS 12 Monterey
- 架构：Intel + Apple Silicon
- 构建方式：Swift Package Manager + Makefile

## 已知问题

- 当前 Release 包未进行 Apple Developer ID 公证，首次打开可能出现“Apple 无法验证”的提示。请按住 Control 点击 App 并选择“打开”，或在系统设置的隐私与安全性中允许打开。
- 原生全屏暂时禁用：macOS 15 下曾出现详情区顶部白条问题，后续版本会继续修复。
- 历史记录尚未持久化，退出应用后记录不会保留。

## 后续计划

v1.3 计划方向：

- 收藏夹
- 历史持久化
- 全局快捷键
- 开机启动
- 菜单栏快速粘贴
- 缩略图缓存系统
- 更完整的菜单本地化
- Developer ID 签名与 Apple notarization
