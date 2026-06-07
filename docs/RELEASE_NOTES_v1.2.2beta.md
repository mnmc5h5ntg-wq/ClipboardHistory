# 时间剪史 v1.2.2beta

这是 v1.2.2 的 beta 测试版本，重点是完成一轮较大的架构重构，并补上可配置的全局快捷键设置。这个版本已经完成基础构建校验和手动冒烟测试，适合继续作为公开测试包验证。

## 功能亮点

- 新增设置窗口：可从应用菜单打开设置。
- 支持修改呼出主窗口的全局快捷键。
- 支持一键恢复默认快捷键 `Control + Option + V`。
- 保留菜单栏入口，可显示主窗口、刷新历史、清空历史和退出应用。
- 继续支持文本、图片、Finder 文件引用和 QuickLook 文件预览。

## 架构改进

- `ClipboardIntake`：集中处理剪贴板轮询、内容解析、缩略图生成、来源 UTI 和相邻去重。
- `FilePreview`：集中处理文件类型判断、文本读取、QuickLook 和 fallback 预览。
- `ApplicationShell`：集中应用生命周期意图，让 `AppDelegate` 回到 macOS 生命周期适配角色。
- `HotKeySettings` / `GlobalHotKeyController`：集中快捷键保存、注册、失败回滚和错误提示。
- `EntryPresentation`：集中条目预览文案、文件名、大小和显示文本格式化。

## 验证结果

- 构建通过：`swift build --package-path ClipboardHistory`
- DMG 校验通过，可正常挂载。
- DMG 内 App 版本号：`1.2.2beta`
- Bundle ID：`com.clipboardhistory.app`
- 最低系统：macOS 12.0
- 架构：Intel + Apple Silicon
- ad-hoc 签名校验通过。
- 手动冒烟测试通过：
  - 文本复制与重新复制
  - 图片复制与预览
  - 文件复制与 QuickLook 预览
  - 快捷键修改与恢复
  - 菜单栏显示窗口、刷新历史、清空历史、退出

## 下载文件

- `时间剪史_v1.2.2beta.dmg`
- SHA256：`10b92c3da54b84d7164b1bdb9334c2fbbcf873197286089257a4ef0d92f58a05`

## 兼容性说明

- 最低系统：macOS 12 Monterey
- 支持架构：Intel + Apple Silicon
- 构建方式：Swift Package Manager + Makefile

## 已知问题

- 当前测试包未进行 Apple Developer ID 公证，首次打开可能出现“Apple 无法验证”的提示。请按住 Control 点击 App 并选择“打开”，或在系统设置的隐私与安全性中允许打开。
- 历史记录尚未持久化，退出应用后记录不会保留。
- 多版本反复安装后，Launchpad 可能残留旧版入口；建议先删除旧版 App，再安装新版。

## 后续计划

- 历史持久化
- 收藏夹
- 开机启动
- 菜单栏快速粘贴
- 缩略图缓存系统
- Release / DMG 自动校验
- Developer ID 签名与 Apple notarization
