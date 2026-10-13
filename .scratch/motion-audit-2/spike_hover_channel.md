# R14 spike：能不能让"悬停"变成机器量得到的东西 —— 结论：三条路都不通（含复现命令）

## 为什么值得花这一轮去试

清单里约 15 处位点的**唯一**反馈是悬停（行底色、清除钮、44pt 圆按钮、多文件行、热图描边、
筛选胶囊底色、R13 那三颗…）。仓库里没有任何一条判据能证明"悬停时那层东西真的画出来了"，
于是这 15 处全部停在"源码已接、产物未量"。做成 ⇒ 一次解锁一片；做不成 ⇒ 它们永远只能靠人眼批次。
**两种结局都是有价值的结论，但必须是量出来的结论，不是猜的。**

## 三条路，逐条实测

### ① 合成真指针：`CGWarpMouseCursorPosition` + `CGEvent(mouseMoved:).post(tap: .cghidEventTap)`
复现：`swift /tmp/hover_spike.swift`（一个 `.regular` 策略的裸进程，开窗 + `activate(ignoringOtherApps:)`，
窗口里放一个自建 `NSTrackingArea`（`.activeAlways | .mouseEnteredAndExited | .inVisibleRect`）的 `NSView`）。

结果：`RESULT appkit_enters=0`，SwiftUI 的 `.onHover` 一次都没回调。
把光标移到窗口正中、先 warp 再 post、只 post 不 warp 三种组合都试过。

判读：**连 AppKit 自己的 tracking area 都没收到 `mouseEntered:`** —— 也就是事件根本没进这个 App。
最可能的原因是这个进程没有辅助功能/输入监控授权，`event.post()` 被窗口服务器丢弃
（`post` 的返回值不报错，这是它最阴的地方）。走授权路线意味着要求 CI runner 与本人都给
一个测试进程开输入权限 —— 不划算，而且会把用户的真实光标挪走。

### ② 直接调 AppKit 的入口：对 `NSHostingView` 调 `mouseEntered(with:)` / `mouseMoved(with:)`
复现：`swift /tmp/hover_spike2.swift`。先遍历视图树找持有 tracking area 的视图：

```
TRACKING_VIEWS 1 NSHostingView<HoverBox>x1
TARGET NSHostingView<HoverBox> mask=643
RESULT=after-mouseEntered        ← 没有 SWIFTUI_ONHOVER 这一行
```

`mask=643` = `mouseEnteredAndExited(1) | mouseMoved(2) | assumeInside(128) | cursorUpdate(512)`，
owner 就是 hosting view 本身 —— 也就是说 SwiftUI 把整棵树的悬停收在一个 tracking area 上，
按坐标自己分发。但对 `-mouseEntered:` / `-mouseMoved:` 两个入口直接调用，
`.onHover` 的闭包**一次都没执行**：它不走这两个方法。

### ③ 让窗口自己收事件：`window.sendEvent(合成的 mouseMoved / mouseEntered)`
复现：`swift /tmp/hover_spike3.swift`（`window.acceptsMouseMovedEvents = true`）。

```
STEP1
STEP2 after window.sendEvent(mouseMoved)     ← 到这里为止，没有 SWIFTUI_ONHOVER
（进程死在下一步：构造 .mouseEntered 类型的 NSEvent 时 AppKit 抛 ObjC 异常）
```

`mouseMoved` 那条走通了没反应；`mouseEntered` 那条直接崩。

## 结论与改道

**"把指针动起来"这件事在没有输入权限的进程里做不到**，而加权限不是这一轮该付的代价
（它要求 CI 与每台开发机给测试进程开辅助功能，且会抢走用户的光标）。

于是本轮把"悬停"这句话**拆成两半分开记账**：

* **触发**（指针进了控件的包围盒 ⇒ `onHover` 被调）—— 只能人眼验，批次 23。
* **表达**（那一档底色画在 22pt 的控件上看不看得出来、与相邻档差多少）—— **可以量**，
  做成 `testFillLaddersAreVisibleOnBothControlClasses`：用 `NSHostingView` + `cacheDisplay`
  画产品自己那一层（`VisualShape.rounded(...).fill(Color.primary.opacity(level))`），
  按**均值通道差**而不是"变化像素占比"判（均匀底色会把每个像素都改一点点，
  占比那条轴在这里恒等于 1，没有判别力）。

这条新判据上线的**第一件事就是抓到 R13 自己引入的回归**：
`controlHover 0.10 → pressed 0.12` 在 22pt 上只差 `3.7/255`，低于地板 4 ——
也就是"为了让小控件悬停看得出来而抬的那一档，恰好把按压缩成了和悬停同一档"。
改成 0.08 之后：`idle→hover 15.9/14.0`、`hover→pressed 8.4/7.5`（亮/暗），两边都过。

## 如果以后还要再试（BACKLOG 24 的新形态）

没试过的路只剩两条，都不便宜：
① 给测试进程申请输入监控/辅助功能授权（CI 上不可复现，且会动用户光标）；
② 用 XCUITest（`XCUIApplication` + `typeText`/`press` 那一族有真事件通道）——
但仓库现在整套是 SwiftPM 测试，没有 .xcodeproj 的 UI 测试 target，那是另一个量级的工程。
