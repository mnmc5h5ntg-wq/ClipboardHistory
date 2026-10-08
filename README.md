# 时间剪史

时间剪史是一个 macOS 原生风格的剪贴板历史管理工具，面向日常写作、开发、整理资料和跨应用复制场景。

它会自动记录剪贴板中的文本、图片和文件引用，并提供搜索、预览、收藏、再次复制、删除、菜单栏入口等功能。项目采用 SwiftUI + AppKit 构建，目标是尽可能贴近 Apple 原生应用的使用体验。

![platform](https://img.shields.io/badge/platform-macOS%2012%2B-silver)
![swift](https://img.shields.io/badge/swift-6.0-orange)
![license](https://img.shields.io/badge/license-WTFPL-blue)
![version](https://img.shields.io/badge/version-v1.4.5-lightgrey)

## 功能特性

- 📋 剪贴板历史：自动记录最近复制的内容。
- 💾 历史持久化：重启后保留历史记录，普通记录默认保留 500 条 / 30 天。
- ⭐ 收藏夹：重要记录可收藏保存，收藏项不受自动清理策略影响。
- 🧹 批量管理：侧边栏支持按住 `Shift` / `Command` 多选，也支持拖动滑选后批量收藏、取消收藏或删除。
- 🔍 搜索：快速筛选文本、图片和文件记录。
- 🪄 猜你要粘贴：菜单栏顶部列出本地规则算出的 Top 3 候选，**点击即复制并自动粘贴到前台应用**（详见下方"猜你要粘贴"）。
- 🖼 图片预览：支持截图、Preview 复制图片内容和 Finder 图片文件大图预览。
- 🎬 视频预览：支持常见视频文件内置播放器预览，默认静音自动播放。
- 📄 文件预览：支持 PDF、Word、Excel、PowerPoint、Pages、Numbers、Keynote、代码文件等常见格式。
- 🏷 本地内容分类：规则引擎区分文本、图片、文件、链接、验证码等语义类别，用于搜索匹配与推荐排序；不上传任何内容。
- 📌 菜单栏模式：顶部菜单栏可显示主窗口、打开设置、清空未收藏记录、退出应用；有候选时还会显示"猜你要粘贴"与"都不是我想要的"。
- ⌨️ 全局快捷键：默认 `⌃⌥V` 呼出主窗口，默认 `⌃⌥C` 再次复制当前选中记录，均可在设置中自定义。
- 🚀 开机启动：可在设置中开启或关闭登录后自动启动。
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
- 如果仍无法打开，建议先删除已安装的 App，重新从 DMG 拖入 `Applications` 后再按上述方式打开。

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
make dmg      # 生成 DMG 安装包，并生成可校验的 .sha256
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
| Finder 中复制图片文件 | 文件 | 保留文件引用，在详情区加载图片预览 |
| Finder 中复制视频文件 | 文件 | 保留文件引用，使用内置播放器预览 |
| Finder 中复制文档 | 文件 | 使用 QuickLook 预览常见文档格式 |
| Finder 中多选并复制文件 | 多文件 | 作为一条多文件历史保存，再次复制时会把整组文件放回剪贴板 |
| 点击星标 | 收藏 | 收藏项会出现在收藏筛选中 |
| 多选侧边栏记录 | 批量管理 | 可批量收藏、取消收藏或删除所选记录 |

历史数据默认保存在当前用户的应用支持目录中：`~/Library/Application Support/时间剪史/`。

### 猜你要粘贴

⚠️ **点击推荐条目会立刻把内容粘贴到当前前台应用**，不是"只选中"。这是这个功能存在的目的，
但也意味着：在错误的输入框上点击，内容就会进入那个输入框。

- 推荐只使用本地 `RuleBasedRecommendationEngine`，不接入云端模型，不上传任何内容。
- 自动粘贴通过向「系统事件」发送一次 `⌘V` 完成，需要在「系统设置 → 隐私与安全性 → 自动化」里
  首次授权；未授权时记录仍会复制到剪贴板，窗口顶部会给出提示，可手动粘贴。
- 默认开启"推荐过滤"：疑似密钥、令牌、密码一类的敏感内容不会进入推荐列表（可在设置的"隐私"页调整）。
- 不拦截系统 `⌘V`，也不会替你按除 `⌘V` 以外的任何键。

### 历史与隐私

- 时间剪史会在本机保存剪贴板历史，用于重启后恢复记录。
- 保存内容包括文本、图片、文件引用和预览缩略图；文件记录会保存原文件路径，用于再次复制。
- 普通历史默认保留 500 条 / 30 天，收藏项会长期保留，不受自动清理影响。
- 设置中的“清空未收藏记录”只会删除未收藏记录；如需移除收藏内容，请先取消收藏或删除对应条目。
- 剪贴板可能包含密码、验证码、截图或聊天内容。复制敏感内容后，建议及时删除对应历史。

## 已知问题

- 当前 Release 包未进行 Apple 公证，首次打开可能需要手动允许。该事项短期内暂不处理，后续具备 Developer ID 条件后再补齐正式公证流程。
- 反复安装旧版和新版后，Launchpad 可能残留旧版入口；建议先删除旧版 App，再安装新版。
- 文件类历史记录保存的是原文件路径；如果原文件被移动或删除，预览可能无法打开。

## Roadmap

后续计划：

- 缩略图缓存系统
- 暂停记录 / 隐私模式
- 正式 Developer ID 签名与 Apple notarization

## 技术栈

- Swift 6.0
- SwiftUI
- AppKit
- Quartz / QuickLook
- AVFoundation
- Swift Package Manager

## License

WTFPL © 王子懿
