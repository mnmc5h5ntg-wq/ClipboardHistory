# 静默失败普查（R39 换装后做的，2026-10-14）

问题：**用户做了一个动作，它失败了，界面什么都没说。**
R39 就是顺着这个问题挖到 macOS 12 开机启动那条（D-098），R40 挖到复制失败这条（D-099）。
这份清单是同一问法下把 `Sources/ClipboardHistoryApp` 全过一遍的结果。

"复核"这一栏是**我自己读过代码**的，不是普查给的结论：
`已修` = 本轮改完并有判据；`已核` = 我逐行确认现象与位置；`未核` = 普查指出、我没逐行确认，
**未核的条目不许直接当缺陷修**（R34 的 U-56 就是拿没复核的推断去改，结果改错方向）。

| # | 位点 | 用户动作 | 失败时界面说什么 | 复核 |
|---|---|---|---|---|
| 1 | `HistoryStore.writeToClipboard` catch（:986）→ `clipboardWriteErrorMessage` | 双击行 / 浮层回车 / 菜单栏点一条 / ⌘R | 只有详情区那颗按钮会显示（`DetailView:123`）；其余三条入口**完全静默** | **已修**（R40 / D-099） |
| 2 | `ApplicationShell.copyAndPasteEntry`（:195） | 浮层回车、菜单栏点一条 | 第一步复制失败时**照样**切前台、照样注入 ⌘V ⇒ 目标应用粘出用户剪贴板里**原来**那条无关内容 | **已修**（R40，同一处：闸门 + 回执 + 一张新帧） |
| 3 | `HistoryStore` 保存失败（:1058-1064）与后台写盘（`HistoryPersistence:470-479`） | 任何改动（删除/收藏/清空/导入/每次复制入库） | 只有 debug 日志；条目照旧显示在列表里，重启后整片回滚 | 未核 |
| 4 | `HistoryPersistence:244-249` 只读模式 | 装过更高版本后再打开 | 只有**载入那一刻**的横幅；关掉之后再每次写盘被跳过 ⇒ 无任何提示 | 未核 |
| 5 | `AppDelegate:218` / `MenuBarController:160` 条目已被裁 | 点一条推荐 | 什么都不发生，菜单已关 | 未核 |
| 6 | `ApplicationShell:174` 按 id 找不到条目 | 菜单/命令面板复制 | 静默 | 未核 |
| 7 | `ApplicationShell.confirmAndClearHistory`（:184-193） | 菜单栏"清空未收藏" | 确认框之后**没有回执**（设置页同动作有 `clearReceipt`）⇒ 同一功能两套反馈语言 | 未核 |
| 8 | `SettingsView:147-155` + `HistoryStore:479` 导出 | 导出历史 | store 先把 `transferNotice` 设成"导出 N 条记录…"并弹主窗口横幅，设置页同时说"导出失败" ⇒ **两条互相矛盾** | 未核 |
| 9 | `DailyCopyLedger:207-215` 账本损坏 | 打开设置 → 统计 | 移去 .bak、返回空 ⇒ 热图显示"还没有可统计的记录"，两年计数静默清零而文案是**假的** | 未核 |
| 10 | `SystemContextCollector:158/204/235/261` 自动化未授权 | 打开隐私页那几个开关 | 开关仍显示"已开启"（`ContextPreferenceSettings` 只写 UserDefaults，不反映真实权限），相关推荐因子永远为 0 | 未核 |
| 11 | `LoginItemSettings:70/84/95` 的 `refresh()` | 启动 / 进设置页 | AppleScript 建不出、error 不读 ⇒ 开关显示"关"且无 message（R39 只修了 `setEnabled` 那一半） | 未核 |
| 12 | `RecommendationWeights:106` / `RecommendationFeedbackStore:140` / `HotKeyPreferences:39` encode 失败 | 拖权重滑块 / 采纳推荐 / 录快捷键 | 静默；本会话生效、重启回默认 | 未核 |
| 13 | `EntryDrag:60` plist 序列化失败 | 多文件拖进 Finder | 目标应用什么都不落地，无提示 | 未核 |
| 14 | `QuickPickController:210` `contentView` 为 nil | ⌃⇧V 呼出浮层 | 浮层不出现，热键像失灵 | 未核 |
| 15 | `HistoryStore:857` `intake.refresh()` 返回 nil | "刷新历史" | 无提示 —— 但 `AppCommand.refreshHistory` 既不在菜单栏也没有键位 ⇒ **不可达**，属"死代码"而不是缺陷 | 未核 |

## 这一族的共同形状（写下来是为了下次别再一样地漏）

1. 失败信息有地方放（`@Published var xxxErrorMessage`），但**只有某一个视图去读它** ⇒
   其余入口等于没有。R40 的 `clipboardWriteErrorMessage` 就是这个形状。
2. 更糟的是"失败之后**继续做下一步**"：复制失败还去注入 ⌘V（#2）、写盘失败还继续显示条目（#3）。
   判据要问的不是"有没有报错"，而是"**失败之后那一步有没有被挡住**"。
3. "只在此刻说一次"（#4）等于之后永远不说。
4. 状态显示与真实权限脱钩（#10）：开关说的是"用户许过什么愿"，不是"系统给了什么权"。
