# 时间剪史
<img width="862" height="592" alt="截屏2026-06-08 01 44 21" src="https://github.com/user-attachments/assets/78e060b3-101d-4a03-8db1-857a5885855f" />

时间剪史是一个 macOS 原生风格的剪贴板历史管理工具，面向日常写作、开发、整理资料和跨应用复制场景。

它会自动记录剪贴板中的文本、图片和文件引用，并提供搜索、预览、再次复制、删除、菜单栏入口等功能。项目采用 SwiftUI + AppKit 构建，目标是尽可能贴近 Apple 原生应用的使用体验。

![platform](https://img.shields.io/badge/platform-macOS%2012%2B-silver)
![swift](https://img.shields.io/badge/swift-6.0-orange)
![license](https://img.shields.io/badge/license-MIT-blue)
![version](https://img.shields.io/badge/version-v1.2.2beta-lightgrey)

## 功能特性

- 📋 剪贴板历史：自动记录最近复制的内容。
- 🔍 搜索：快速筛选文本、图片和文件记录。
- 🖼 图片预览：支持截图、Preview 复制图片内容、Finder 图片文件缩略图与大图预览。
- 🎬 视频预览：支持常见视频文件 QuickLook 预览。
- 🎞 视频缩略图：Finder 复制视频文件时显示首帧缩略图。
- 📄 文件预览：支持 PDF、Word、Excel、PowerPoint、Pages、Numbers、Keynote、代码文件等常见格式。
- 🏷 标签系统：保留条目语义分类，区分文本、图片内容和文件引用。
- 📌 菜单栏模式：顶部菜单栏可显示主窗口、刷新历史、清空历史和退出应用。
- ⌨️ 全局快捷键：关闭主窗口后，可按默认快捷键 `⌃⌥V` 呼出主窗口，并可在设置中自定义。
- 🧭 macOS 12+：兼容 macOS 12 及以上版本。
- 💻 Universal Binary：同时支持 Intel 与 Apple Silicon Mac。

## 安装方法

1. 打开 [GitHub Releases](https://github.com/mnmc5h5ntg-wq/ClipboardHistory/releases)。
2. 下载最新版本的 `.dmg` 文件。
3. 打开 DMG，将「时间剪史」拖入 `Applications` 文件夹。
4. 从启动台或 Finder 中打开「时间剪史」。

### 如果提示“Apple 无法验证”

当前公开测试包使用本地签名方式，未经过 Apple Developer ID 公证。首次打开时 macOS 可能提示“Apple 无法验证”。

可使用以下方式打开：

- 推荐：按住 `Control` 键点击「时间剪史.app」→ 选择「打开」→ 再次点击「打开」。
- 或：系统设置 → 隐私与安全性 → 找到拦截提示 → 点击「仍要打开」。
- 如果仍无法打开，可在终端执行：

```bash
xattr -cr /Applications/时间剪史.app
```

## 编译方法

```bash
git clone https://github.com/mnmc5h5ntg-wq/ClipboardHistory.git
cd ClipboardHistory
```

常用命令：

```bash
make build    # 编译 Intel + Apple Silicon Universal Binary
make bundle   # 生成本地 时间剪史.app
make run      # 编译并运行 App
make dmg      # 生成 DMG 安装包
make clean    # 清理构建产物
```

也可以直接使用 Swift Package Manager：

```bash
swift build --package-path ClipboardHistory
```

## 系统要求

- macOS 12 Monterey 或更高版本
- Intel Mac
- Apple Silicon Mac

## 使用说明

启动后，时间剪史会自动监听剪贴板变化：

| 操作 | 记录类型 | 说明 |
| --- | --- | --- |
| 复制文字 | 文本 | 可在详情区查看完整文本并再次复制 |
| 截图 / Preview 复制图片内容 | 图片 | 保存为图片内容，可直接预览 |
| Finder 中复制图片文件 | 文件 | 保留文件引用，同时显示图片缩略图和预览 |
| Finder 中复制视频文件 | 文件 | 保留文件引用，显示视频缩略图并支持预览 |
| Finder 中复制文档 | 文件 | 使用 QuickLook 预览常见文档格式 |

## 已知问题

- 当前 Release 包未进行 Apple 公证，首次打开可能需要手动允许。该事项短期内暂不处理，后续具备 Developer ID 条件后再补齐正式公证流程。
- 反复安装旧版和新版后，Launchpad 可能残留旧版入口；建议先删除旧版 App，再安装新版。
- 历史记录目前为内存存储，退出应用后不会持久保存。

## Roadmap

v1.3 计划：

- 收藏夹
- 历史持久化
- 开机启动
- 菜单栏快速粘贴
- 缩略图缓存系统
- 更完整的菜单本地化
- 正式 Developer ID 签名与 Apple notarization

## 技术栈

- Swift 6.0
- SwiftUI
- AppKit
- Quartz / QuickLook
- AVFoundation
- Swift Package Manager

## License

MIT © 王子懿
