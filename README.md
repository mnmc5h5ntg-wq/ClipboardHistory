# 时间剪史

一个 macOS 原生风格的剪贴板历史管理工具。

![platform](https://img.shields.io/badge/platform-macOS%2012%2B-silver)
![swift](https://img.shields.io/badge/swift-6.0-orange)
![license](https://img.shields.io/badge/license-MIT-blue)
![version](https://img.shields.io/badge/version-v1.1-lightgrey)

## 功能

- 📋 自动记录剪贴板文本、图片、文件
- 🔍 搜索历史记录
- 🖼 图片 & 文档预览（支持 PNG / PDF / Word / Excel / 代码文件等）
- 📁 区分「图片内容」与「文件引用」，Finder 复制文件不丢语义
- 💎 Liquid Glass 风格界面，类原生 macOS 体验
- 🖥 支持 macOS 12 及以上，兼容 Intel & Apple Silicon

## 安装

### 直接下载

从 [Releases](https://github.com/mnmc5h5ntg-wq/ClipboardHistory/releases) 下载最新 `.dmg`，打开后将「时间剪史」拖入 `Applications` 文件夹即可。

> ⚠️ 首次打开可能提示「无法验证」，请参考下方 [常见问题](#常见问题)。

### 从源码编译

```bash
git clone https://github.com/mnmc5h5ntg-wq/ClipboardHistory.git
cd ClipboardHistory
make run
```

`make run` 会自动编译并生成 `时间剪史.app`。也可分步操作：

```bash
make build    # 仅编译
make bundle   # 编译 + 打包 .app
make dmg      # 生成 DMG 安装包
make clean    # 清理
```

## 使用

启动后，App 会在后台自动监听剪贴板变化：

| 操作 | 记录类型 |
|------|----------|
| 复制文字 | 文本 |
| 截图 / Preview 复制 | 图片 |
| Finder Cmd+C 文件 | 文件引用 |

点击左侧条目查看详情，点击右下角胶囊按钮可再次复制或删除。

## 常见问题

### 打开时提示「无法验证」或「已损坏」

本软件未经过 Apple 付费开发者公证，macOS Gatekeeper 默认拦截。任选一种方式解决：

| 方法 | 操作 |
|------|------|
| **A（推荐）** | 按住 `Control` 键 → 点击 App 图标 → 选「打开」→ 再点「打开」 |
| **B** | 系统设置 → 隐私与安全性 → 页面底部点「仍要打开」 |
| **C** | 终端执行：`xattr -cr /Applications/时间剪史.app` |

> 方法 A 只需做一次，之后正常双击即可启动。

## 技术栈

- Swift 6.0 + SwiftUI
- AppKit (NSWindow 定制)
- Quartz (QuickLook 文档预览)
- Universal Binary (Intel + Apple Silicon)

## License

MIT © 王子懿
