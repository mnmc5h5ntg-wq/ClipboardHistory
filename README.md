# 时间剪史

一个 macOS 原生风格的剪贴板历史管理工具。

![platform](https://img.shields.io/badge/platform-macOS%2012%2B-silver)
![swift](https://img.shields.io/badge/swift-6.0-orange)
![license](https://img.shields.io/badge/license-MIT-blue)

## 功能

- 📋 自动记录剪贴板文本、图片、文件
- 🔍 搜索历史记录
- 🖼 图片 & 文档预览（支持 PNG / PDF / Word / Excel / 代码文件等）
- 📁 区分「图片内容」与「文件引用」，Finder 复制文件不丢语义
- 💎 Liquid Glass 风格界面，类原生 macOS 体验

## 安装

```bash
git clone https://github.com/你的用户名/时间剪史.git
cd 时间剪史
make run
```

`make run` 会自动编译并生成 `时间剪史.app`。也可分步操作：

```bash
make build    # 仅编译
make bundle   # 编译 + 打包 .app
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

## 技术栈

- Swift 6.0 + SwiftUI
- AppKit (NSWindow 定制)
- Quartz (QuickLook 文档预览)

## License

MIT
