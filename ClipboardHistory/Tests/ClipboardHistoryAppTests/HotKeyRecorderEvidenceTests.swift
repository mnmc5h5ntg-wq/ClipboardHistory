import AppKit
import Carbon
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// R141 · 快捷键录制器「正在录制」那一圈的表达（BACKLOG 173 点的那一次真动效 / D-194）。
///
/// **这一条判据存在的全部理由**：那颗按钮在录制态会吃掉所有按键，而它当时唯一的说法
/// 是一句瞬间换掉的标题。标题不是形状 —— 屏幕上没有任何东西说「现在按下去会被记下来」。
/// 而 R141 之前**没有任何一张帧**画过录制态：它连夹具都没有，于是「这一格没做」与
/// 「这一格不需要」在账本上同形（BACKLOG 46 那一族）。
///
/// **尺的形状**（三条规矩都压在这里）：
/// ① 两态与参照块**同框渲染** ⇒ 所有比较都是同平台相对量，不是绝对像素（BACKLOG 42）；
/// ② 参照块 = 同一颗 `NSColor.controlAccentColor` 铺成的实心块。它自己读不到东西时
///    这条判据**直接红**，不许把「通道解析不了强调色」混进「产品没画」
///    （R102：能不能解析 accent 要按控件回答，不许由一次读数外推）；
/// ③ 静置态必须**一个像素都不画**（`strokeWidth = 0`）—— 这一条同时是旧帧
///    `CHANGED=0` 的原因，也是变异刀 M660 的靶。
///
/// **覆盖管线**：渲染的是产品自己的 `HotKeyRecorderRing`，底色是设置页的
/// `windowBackgroundColor`；尺寸按 `SettingsView:807` 那一框给 128×28pt —— 但**产品实际画的是 128×24**
/// （`.rounded` bezel 的固有高度把 representable 夹到 24pt；R143 实测宿主 frame=(16,18,128,24)），
/// 所以组件级那一格量的是 128×28 的**理想框**，真框那一半由产品入口那条用例量。亮暗两种外观都走；
/// 而「那一圈确实是录制器自己挂的」由 `testRecorderBodyRoutesThroughTheProductRing`
/// 这条源码守卫钉住（不是「我测了个替身」）。
/// **不覆盖**：**触发**那一半（真的点下去、真的进录制态）在离屏通道里做不到 ——
/// R14 实测三条合成通道全断。它由下面那两条行为用例判（回调**次数**与顺序），
/// 再加人工批次 90.1 的一眼。淡入的**时长**也量不到（中间态不在任何一张帧里，R11 那一族）。
@MainActor
final class HotKeyRecorderEvidenceTests: XCTestCase {

    // MARK: - 几何（点，与 SettingsView 给那一框同尺寸）

    private static let boxWidth: CGFloat = 128
    private static let boxHeight: CGFloat = 28
    private static let idleOrigin = CGPoint(x: 10, y: 10)
    private static let recordingOrigin = CGPoint(x: 10, y: 52)
    private static let referenceRect = CGRect(x: 150, y: 52, width: 40, height: 28)
    private static let canvasSize = CGSize(width: 200, height: 90)

    /// 一个像素算「有墨」的偏离量。这是**分档闸门**，不是判据（BACKLOG 42：
    /// 判过没过只能用比值），所以它允许是绝对数 —— 但它必须能被反方向证伪：
    /// 静置那一框要求恰好 0 个，所以这个数一旦调松，① 那条就跟着失效。
    static let inkDelta = 12

    /// 两条轴的容差带，**先量后判**。本机两档实测（2x，同框参照）：
    /// 强度轴（墨像素的平均偏离 / 实心参照块）亮 0.965、暗 0.976；
    /// 面积轴（录制态墨像素数 / 参照块墨像素数）亮 0.412、暗 0.406；@1x 录制态 600 个墨像素。
    /// 于是：强度带压成 `0.60…1.05`（这一圈必须就是那颗强调色本身，淡一档就红 ——
    /// 把 alpha 砍半的刀会把强度读到 ~0.5）；面积带 `0.10…0.60`（一圈描边的"响"要小于
    /// 一颗实心强调块，而"内部不许有墨"那条才是抓整块填充的那颗牙）。
    static let strengthLower = 0.60
    static let strengthUpper = 1.05
    static let areaLower = 0.10
    static let areaUpper = 0.60

    // MARK: - 判据

    /// ① + ② + ③：录制态那一圈必须在**两种外观**下都被这把尺看见，
    /// 静置态必须一个像素都不画，而描边不许比实心参照块更响。
    func testRecordingRingIsVisibleInBothAppearancesAndNeverLouderThanTheSwatch() throws {
        for appearance in [NSAppearance.Name.aqua, NSAppearance.Name.darkAqua] {
            let tag = appearance == .aqua ? "light" : "dark"
            let shot = try renderFrame(appearance: appearance, scale: 2)
            let bg = try backgroundOf(shot)

            let idle = try measure(shot, box: CGRect(origin: Self.idleOrigin,
                                                     size: CGSize(width: Self.boxWidth, height: Self.boxHeight)),
                                   bg: bg, label: "idle-\(tag)")
            let recording = try measure(shot, box: CGRect(origin: Self.recordingOrigin,
                                                          size: CGSize(width: Self.boxWidth, height: Self.boxHeight)),
                                        bg: bg, label: "recording-\(tag)")
            let reference = try measure(shot, box: Self.referenceRect, bg: bg, label: "reference-\(tag)")
            let interior = try measure(shot,
                                       box: CGRect(origin: Self.recordingOrigin,
                                                  size: CGSize(width: Self.boxWidth, height: Self.boxHeight))
                                            .insetBy(dx: 5, dy: 5),
                                       bg: bg, label: "recording-interior-\(tag)")

            let strength = recording.meanDev / max(reference.meanDev, 0.001)
            let area = Double(recording.inkPixels) / Double(max(reference.inkPixels, 1))
            CaptureReadings.emit("RECORDER_RING 外观=\(tag) 静置墨=\(idle.inkPixels) 录制墨=\(recording.inkPixels) "
                                 + "参照墨=\(reference.inkPixels) 内部墨=\(interior.inkPixels) "
                                 + "录制均值偏离=\(String(format: "%.1f", recording.meanDev)) "
                                 + "参照均值偏离=\(String(format: "%.1f", reference.meanDev)) "
                                 + "强度=\(String(format: "%.3f", strength)) 面积=\(String(format: "%.3f", area)) "
                                 + "录制色度峰=\(String(format: "%.0f", recording.peakChroma)) "
                                 + "参照色度峰=\(String(format: "%.0f", reference.peakChroma))")

            // ③ 静置 = 逐像素没有这一层。反过来就是「旧帧一张都不会变」的证明。
            XCTAssertEqual(idle.inkPixels, 0,
                "外观 \(tag)：静置态读到 \(idle.inkPixels) 个偏离背景的像素 ⇒ 那一圈在没在录制的时候也在画。"
                    + "这不是淡了一点，是每一张快捷键帧都会变，而帧基线会替你确认这件事")
            // ② 正对照：参照块自己读不到东西时，下面所有比较都是空的。
            XCTAssertGreaterThan(reference.inkPixels, 200,
                "外观 \(tag)：实心 accent 参照块只读到 \(reference.inkPixels) 个像素 ⇒ 是这条通道解析不了强调色，"
                    + "不是产品没画。此时录制态那条读数没有任何意义，先修通道（R102）")
            // ① 录制态必须被看见。
            XCTAssertGreaterThan(recording.inkPixels, 0,
                "外观 \(tag)：录制态那一圈一个像素都没读到，而同框的实心参照块读到了 \(reference.inkPixels) 个 "
                    + "⇒ 通道是通的，这一圈是没画的")
            // 强度轴：这一圈必须就是那颗强调色，不许是淡出来的一层灰。
            XCTAssertGreaterThanOrEqual(strength, Self.strengthLower,
                "外观 \(tag)：强度 = \(String(format: "%.3f", strength)) 低于 \(Self.strengthLower) ⇒ 这一圈淡到读不出来，"
                    + "「我在听」这件事在屏幕上没有形状 —— 正是本轮要修的那个缺陷")
            XCTAssertLessThanOrEqual(strength, Self.strengthUpper,
                "外观 \(tag)：强度 = \(String(format: "%.3f", strength)) 高于 \(Self.strengthUpper) ⇒ 描边比实心块还浓，"
                    + "它已经不是在「跟着状态」，是在抢这一屏")
            // 面积轴：一圈描边的"响"要小于一颗实心强调块。
            XCTAssertGreaterThanOrEqual(area, Self.areaLower,
                "外观 \(tag)：面积 = \(String(format: "%.3f", area)) 低于 \(Self.areaLower) ⇒ 这一圈细到等于没有")
            XCTAssertLessThanOrEqual(area, Self.areaUpper,
                "外观 \(tag)：面积 = \(String(format: "%.3f", area)) 高于 \(Self.areaUpper) ⇒ 录制态占的视觉面积快赶上实心块，"
                    + "不喧宾夺主那条被翻过去了")
            // 是**圈**不是填充：框内部（离边 5pt 以外）不许有墨。
            XCTAssertLessThanOrEqual(interior.inkPixels, 20,
                "外观 \(tag)：录制框内部读到 \(interior.inkPixels) 个像素 ⇒ 画的是整块填充而不是一圈。"
                    + "填充会把这颗按钮变成这一屏最重的东西，而它只是「在听键字」")
        }
    }

    /// @1x 是 CI runner 那一档（R29 实测 `scale=1.0`）。这里只要求「读得到」，
    /// 不要求比值 —— 1.5pt 的线在半分辨率下进不了同一档，那是尺的形状不是产品的形状。
    func testRecordingRingSurvivesTheCoarseSampling() throws {
        let shot = try renderFrame(appearance: .aqua, scale: 1)
        let bg = try backgroundOf(shot)
        let recording = try measure(shot, box: CGRect(origin: Self.recordingOrigin,
                                                      size: CGSize(width: Self.boxWidth, height: Self.boxHeight)),
                                    bg: bg, label: "recording@1x")
        CaptureReadings.emit("RECORDER_RING_1X 墨=\(recording.inkPixels) 均值偏离=\(String(format: "%.1f", recording.meanDev))")
        XCTAssertGreaterThan(recording.inkPixels, 0,
            "@1x 读不到录制态那一圈 ⇒ 这一格在 CI 上无从判定。不许记成通过，也不许记成产品没画")
    }

    // MARK: - 真值表（模型值，与动画无关）

    /// 状态押在模型值上，不押在动画上：减弱动态只是不淡入，描边照样在。
    func testEmphasisPresentationIsATruthTable() {
        XCTAssertEqual(HotKeyRecorderEmphasis.strokeWidth(isRecording: false), 0,
            "静置必须是 0pt —— 非零就会改每一张快捷键帧")
        XCTAssertEqual(HotKeyRecorderEmphasis.strokeWidth(isRecording: true), VisualStroke.highlight,
            "录制态必须落在 `VisualStroke.highlight` 这一档（与命中高亮同一档），不许另造一个数")
        XCTAssertTrue(HotKeyRecorderEmphasis.strokeColor(isRecording: false) == .clear,
            "静置的颜色必须是「没有」而不是「很淡」 —— 否则色度轴上会留下说不清的读数")
        XCTAssertTrue(HotKeyRecorderEmphasis.strokeColor(isRecording: true) == .controlAccentColor,
            "录制态要借用系统已有的那档「字段在接收输入」的颜色，而不是新造一档")
    }

    // MARK: - 触发那一半：回调**次数**与顺序

    /// 每一次真的转换恰好一次回调。判等放在 `setRecording` 里，所以
    /// 「已经在录制里再点一次」与「重复退出」都不许再报
    /// （R85：只数「出现过」的守卫会被另一条出口喂饱）。
    func testRecordingCallbacksFireExactlyOncePerTransition() throws {
        var seen: [Bool] = []
        let button = HotKeyRecorderButton()
        button.shortcut = .defaultShortcut
        button.onRecordingChange = { seen.append($0) }

        button.startRecording()
        XCTAssertEqual(seen, [true], "进入录制必须报一次 true")
        XCTAssertEqual(button.title, "请输入快捷键", "标题与状态要同时改")

        button.startRecording()
        XCTAssertEqual(seen, [true], "已经在录制里再点一次不许报第二次 —— 那会给同一次转换演两遍淡入")

        button.cancelViaFirstResponder()
        XCTAssertEqual(seen, [true, false], "退出录制必须报一次 false")
        button.cancelViaFirstResponder()
        XCTAssertEqual(seen, [true, false], "重复退出不许再报")

        button.startRecording()
        XCTAssertEqual(seen, [true, false, true], "第二次进入要重新报 true")
        button.keyDown(with: Self.keyEvent(UInt16(kVK_Escape)))
        XCTAssertEqual(seen, [true, false, true, false], "Esc 退出走的是同一个出口")
    }

    /// 提交一条新组合键 = 退出录制 ⇒ 那一圈必须跟着退。
    /// 只测标题会漏掉这条接线：标题改了而 `isRecording` 没改，那一圈就会永远留在屏幕上。
    func testCommittingAShortcutEndsTheRecordingState() throws {
        var seen: [Bool] = []
        var changed = 0
        let button = HotKeyRecorderButton()
        button.shortcut = .defaultShortcut
        button.onRecordingChange = { seen.append($0) }
        button.onShortcutChange = { _ in changed += 1 }

        button.startRecording()
        button.keyDown(with: Self.keyEvent(UInt16(kVK_ANSI_K), modifiers: [.control, .option]))
        XCTAssertEqual(changed, 1, "组合键要提交（否则这一条测的是非法路径）")
        XCTAssertEqual(seen, [true, false], "提交之后必须退出录制态")
        XCTAssertFalse(button.isRecording, "私有状态也要对得上：那一圈跟的就是它")
    }

    // MARK: - 接线（不许我测了个替身）

    /// 录制器自己挂的就是那一圈，且**驱动在**（R42 那一族：声明了过渡而没有驱动等于零。
    /// 这里用的是 `.animation(..., value: isRecording)`，也就是 `MotionDriverTests` 认得的这一族）。
    func testRecorderBodyRoutesThroughTheProductRing() throws {
        // 产品源码在包根的另一侧：这个文件在 Tests/ClipboardHistoryAppTests/，
        // 而被读的两个视图在 Sources/ClipboardHistoryApp/Views/ —— 少退一层就会
        // 报「文件不存在」（第一版正是这样：它红在夹具路径上，不是红在产品上）。
        let viewsDir = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // ClipboardHistoryAppTests
            .deletingLastPathComponent()   // Tests
            .deletingLastPathComponent()   // 包根
            .appendingPathComponent("Sources/ClipboardHistoryApp/Views", isDirectory: true)
        let source = try String(contentsOf: viewsDir.appendingPathComponent("HotKeyRecorderView.swift"),
                                encoding: .utf8)
        let outer = try XCTUnwrap(source.components(separatedBy: "struct HotKeyRecorderView: View").last)
            .components(separatedBy: "struct HotKeyRecorderField").first ?? ""
        XCTAssertFalse(outer.isEmpty, "取不到外层 body ⇒ 结构被改了，这条守卫无从判定")
        XCTAssertTrue(outer.contains("HotKeyRecorderRing(isRecording: isRecording)"),
            "外层没挂那一圈 ⇒ 上面的像素判据测的是一个没人用的替身")
        XCTAssertTrue(outer.contains(".animation(MotionCatalog.animation(for: .emphasis), value: isRecording)"),
            "那一圈没有驱动 ⇒ 它是瞬间出现、瞬间消失的，动效只剩一个名字（BACKLOG 53 的原始形状）")
        XCTAssertTrue(outer.contains(".overlay("),
            "描边必须挂在 representable 外面：representable 的 body 就是那颗 NSButton")

        let settings = try String(contentsOf: viewsDir
            .appendingPathComponent("SettingsView.swift"), encoding: .utf8)
        XCTAssertGreaterThanOrEqual(settings.components(separatedBy: "HotKeyRecorderView(").count - 1, 1,
            "调用点不再构造 `HotKeyRecorderView` ⇒ 这一圈在产品里根本不会被挂上（今天三行快捷键都走它）")
        XCTAssertFalse(settings.contains("HotKeyRecorderField("),
            "调用点绕过外层直接用内层 ⇒ 那一圈被跳过，而像素判据仍然会绿")
    }

    // MARK: - 从产品入口进：真的点一下那颗按钮

    /// 这一条走完整链条：真的 `NSWindow` + 真的 `NSHostingView` 里放产品那个 `HotKeyRecorderView`，
    /// 在视图树里找到那颗真的 `NSButton`，`performClick` 它，再比两帧 —— 判的是**那一圈本身**。
    ///
    /// **这一条是 R143 审查轮改回来的，改的是一条我自己写错的结论。**
    /// R141 那天它红着（"点过才有、静置没有"的墨像素 = 0），我据此写下 U-470 / BACKLOG 179：
    /// "`cacheDisplay` 不合成挂在 `NSViewRepresentable` 外面的 SwiftUI overlay"，并把那一圈的判据搬去真机通道。
    /// 审查轮用同样的结构逐字重跑同一条通道，读到 **2924 个高色度像素** ⇒ 通道一直是好的，坏的是我的量法：
    /// `backgroundLuma` 取整幅中位数，而控件之外全是**透明像素（luma=0）** ⇒ bg≈0 ⇒
    /// `inkPixels` 数的其实是"整个控件矩形"（52800 = 440×120，两态当然一样），
    /// 于是 `after 有墨 && before 无墨` **在构造上恒为 0**。
    /// ⇒ U-470 撤回；真正的教训是 U-479：**两条读数矛盾时，先证明两边量的是同一个对象** ——
    /// 我拿一把坏尺给的 0，去推翻一条真通道给的 1548，方向反了，还把它写进了四处台账。
    func testClickingTheRealControlDrawsTheRingThroughTheProductEntry() throws {
        let idle = try Self.renderRealControl(clicked: false)
        let clicked = try Self.renderRealControl(clicked: true)
        let differing = Self.differingPixels(idle, clicked)
        let idleChroma = Self.highChromaPixels(idle)
        let clickedChroma = Self.highChromaPixels(clicked)
        let edges = Self.chromaByEdge(clicked)
        CaptureReadings.emit("RECORDER_ENTRY 通道=cacheDisplay 不同像素=\(differing) "
                             + "静置高色度=\(idleChroma) 点击后高色度=\(clickedChroma) "
                             + "四边高色度=上\(edges.top)/下\(edges.bottom)/左\(edges.left)/右\(edges.right)")
        XCTAssertGreaterThan(differing, 200,
            "点下去之后这条视图树一个像素都没变（不同像素=\(differing)）⇒ 点击没走到状态、或者状态没走到视图")
        XCTAssertEqual(idleChroma, 0,
            "静置态读到 \(idleChroma) 个高色度像素 ⇒ 那一圈在没在录制的时候也在画（每一张快捷键帧都会变）")
        XCTAssertGreaterThanOrEqual(clickedChroma, 200,
            "从产品入口点下去之后屏幕上没有出现强调色描边（高色度像素=\(clickedChroma)）⇒ 那一圈没画上，"
                + "或者按钮→状态→overlay 这条边断了（这一条就是这个断点的证人）")
        for (name, count) in [("上", edges.top), ("下", edges.bottom), ("左", edges.left), ("右", edges.right)] {
            XCTAssertGreaterThanOrEqual(count, Int(Double(clickedChroma) * 0.05),
                "高色度像素里" + name + "边只占 \(count)/\(clickedChroma) ⇒ 画出来的不是一圈"
                    + "（贴边的横带、单边裁切都会红在这里）")
        }
    }

    /// 「我在听」那一圈是一个**承诺**：按下去的键会被这里吃掉。响应者链没接上时不许亮。
    /// R143 审查轮（F7）指出：`makeFirstResponder` 的返回值原来被丢掉，于是"窗口在、链没接上"
    /// 这一格会画出一圈假的承诺。这一条用例就是那个断点的证人（变异 M668 拆掉守卫，它必须红）。
    func testRingDoesNotPromiseListeningWhenTheResponderChainRefuses() throws {
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 220, height: 60),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let blocker = RefusingFirstResponder()
        blocker.frame = NSRect(x: 0, y: 0, width: 100, height: 20)
        window.contentView?.addSubview(blocker)
        let host = NSHostingView(rootView: HotKeyRecorderView(
            shortcut: .constant(HotKeyShortcut.defaultShortcut), onInvalidShortcut: {}))
        host.frame = NSRect(x: 0, y: 0, width: 220, height: 60)
        window.contentView?.addSubview(host)
        window.setFrameTopLeftPoint(NSPoint(x: -4000, y: -4000))
        window.orderFront(nil)
        host.layoutSubtreeIfNeeded()
        Self.spin(0.05)
        window.makeFirstResponder(blocker)
        guard let button = Self.firstButton(in: host) else {
            window.orderOut(nil)
            XCTFail("视图树里找不到那颗 NSButton ⇒ 无从判定")
            return
        }
        button.performClick(nil)
        Self.spin(0.45)
        let shot = try Self.grab(host, scale: 2)
        let chroma = Self.highChromaPixels(shot)
        window.orderOut(nil)
        CaptureReadings.emit("RECORDER_REFUSING_CHAIN 高色度=\(chroma) 录制中=\(button.isRecording)")
        XCTAssertEqual(chroma, 0,
            "响应者链拒绝交接时仍然亮出那一圈（高色度=\(chroma)）⇒ 屏幕在说「按下去会被记下来」，"
                + "而实际按键不会到这里 —— 这是假承诺，比没有反馈更坏")
        XCTAssertFalse(button.isRecording, "同一件事的模型值侧：拿不到链就不该进入录制态")
    }

    /// 一个"占着响应者且不肯让"的视图：用来造出 `makeFirstResponder` 返回 false 的那一格。
    private final class RefusingFirstResponder: NSView {
        override var acceptsFirstResponder: Bool { true }
        override func resignFirstResponder() -> Bool { false }
    }

    /// 真的 `NSWindow` + 真的 `NSHostingView` 里放产品那个 `HotKeyRecorderView`，
    /// 在视图树里找到那颗真的 `NSButton`，`performClick` 它 —— 于是被测的是
    /// "用户点下去之后屏幕上多了什么"，不是我搭的替身（AGENTS.md 的硬规矩）。
    private static func renderRealControl(clicked: Bool) throws -> NSBitmapImageRep {
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 220, height: 60),
                              styleMask: [.titled], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: HotKeyRecorderView(
            shortcut: .constant(HotKeyShortcut.defaultShortcut),
            onInvalidShortcut: {}))
        host.frame = NSRect(x: 0, y: 0, width: 220, height: 60)
        window.contentView?.addSubview(host)
        // 摆到屏幕外但真的 orderFront：不 orderFront 的话 AppKit 不会给这条视图树走完布局，
        // 而"帧是空的"与"这一格没画"必须分得开（R19 那条通道）。
        window.setFrameTopLeftPoint(NSPoint(x: -4000, y: -4000))
        window.orderFront(nil)
        host.layoutSubtreeIfNeeded()
        spin(0.05)
        if clicked {
            guard let button = firstButton(in: host) else {
                window.orderOut(nil)
                XCTFail("视图树里找不到那颗 NSButton ⇒ 产品入口变了，这条判据无从判定（不许读成通过）")
                throw XCTSkip("找不到录制按钮")
            }
            button.performClick(nil)
            XCTAssertEqual(button.title, "请输入快捷键", "点下去必须真的进入录制态（否则比的是两个静置态）")
            // 0.16s 的淡入要落定，否则量到的是中间态（中间态不是判据，R11 那一族）。
            spin(0.45)
            host.layoutSubtreeIfNeeded()
        }
        let rep = try grab(host, scale: 2)
        window.orderOut(nil)
        return rep
    }

    /// **一次性 spike（默认 skip，不进 CI）**：这条通道（`cacheDisplay`）看不见挂在
    /// `NSViewRepresentable` 外面的 SwiftUI overlay，于是"屏幕上到底有没有那一圈"只能问真机。
    /// 开法：`CLIPBOARD_HISTORY_SPIKE_ONSCREEN=1 swift test --filter ...SpikeOnScreen...`，
    /// 同时在另一个进程里 `screencapture -x -R$(cat /tmp/spike_ring_rect.txt) /tmp/spike_ring.png`。
    func testSpikeOnScreenRingCapture() throws {
        try XCTSkipIf(ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_SPIKE_ONSCREEN"] == nil,
                      "只在手动 spike 时跑（会把窗口摆到屏幕上）")
        let clicked = try renderRealControlOnScreen(clicked: true)
        let idle = try renderRealControlOnScreen(clicked: false)
        guard let screen = NSScreen.main else {
            try? "NO_SCREEN".write(toFile: "/tmp/spike_ring_rect.txt", atomically: true, encoding: .utf8)
            XCTFail("没有主屏 ⇒ 这一格是没跑（锁屏/休眠），不许由 python 那边猜坐标")
            return
        }
        // 两扇窗的矩形**都由被测物自己印**（R143 审查轮 #33：python 那边手抄了一个 320pt 的
        // 横向偏移，Swift 一改布局它就会截到错的那一态，而错法长得像"产品没画"）。
        let screenH = screen.frame.height
        func box(_ window: NSWindow) -> String {
            let r = window.frame
            return "\(Int(r.minX)),\(Int(screenH - r.maxY)),\(Int(r.width)),\(Int(r.height))"
        }
        let text = box(clicked) + ";" + box(idle)
        try text.write(toFile: "/tmp/spike_ring_rect.txt", atomically: true, encoding: .utf8)
        CaptureReadings.emit("SPIKE_RING rect=\(text) 两窗都在屏上，等待外部截图")
        RunLoop.current.run(until: Date().addingTimeInterval(12))
        idle.orderOut(nil)
        clicked.orderOut(nil)
    }

    private func renderRealControlOnScreen(clicked: Bool) throws -> NSWindow {
        // 两扇窗必须**并排**，不能同一格重叠：后 orderFront 的那扇会把前一扇整个盖住，
        // 于是"截到的是哪一态"就不由我说得算了。
        let window = NSWindow(contentRect: NSRect(x: clicked ? 240 : 560, y: 300, width: 260, height: 80),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        let host = NSHostingView(rootView: HotKeyRecorderView(
            shortcut: .constant(HotKeyShortcut.defaultShortcut), onInvalidShortcut: {}))
        host.frame = NSRect(x: 0, y: 0, width: 260, height: 80)
        window.contentView?.addSubview(host)
        window.title = "spike"
        window.orderFront(nil)
        host.layoutSubtreeIfNeeded()
        RunLoop.current.run(until: Date().addingTimeInterval(0.2))
        if clicked, let button = Self.firstButton(in: host) {
            button.performClick(nil)
            RunLoop.current.run(until: Date().addingTimeInterval(0.6))
        }
        return window
    }

    // MARK: - 渲染与量尺

    /// 把宿主视图（含那颗真的 NSButton 与 SwiftUI 那一层 overlay）画进位图。
    private static func grab(_ view: NSView, scale: Int) throws -> NSBitmapImageRep {
        let size = view.bounds.size
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil,
                                   pixelsWide: Int(size.width) * scale,
                                   pixelsHigh: Int(size.height) * scale,
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 0, bitsPerPixel: 0)
        let bitmap = try XCTUnwrap(rep)
        bitmap.size = size
        view.cacheDisplay(in: view.bounds, to: bitmap)
        return bitmap
    }

    /// 在视图树里找那颗录制按钮（按类找，不按标题找 —— 标题会随状态变）。
    private static func firstButton(in view: NSView) -> HotKeyRecorderButton? {
        if let match = view as? HotKeyRecorderButton { return match }
        for sub in view.subviews {
            if let found = firstButton(in: sub) { return found }
        }
        return nil
    }

    private static func spin(_ seconds: TimeInterval) {
        RunLoop.current.run(until: Date().addingTimeInterval(seconds))
    }

    /// 两帧里**任何一个通道**不同的像素数。用来把"没重画"与"重画了但那一圈读不到"分开：
    /// 标题从 4 个字符换成 6 个，如果这个数还是 0，那就是通道没重画，产品结论无从谈起。
    private static func differingPixels(_ a: NSBitmapImageRep, _ b: NSBitmapImageRep) -> Int {
        guard a.pixelsWide == b.pixelsWide, a.pixelsHigh == b.pixelsHigh else { return -1 }
        var n = 0
        for py in 0..<a.pixelsHigh {
            for px in 0..<a.pixelsWide {
                let x = rgb(of: a, px: px, py: py)
                let y = rgb(of: b, px: px, py: py)
                if x.r != y.r || x.g != y.g || x.b != y.b { n += 1 }
            }
        }
        return n
    }

    /// 背景 = **不透明像素**的中位亮度。
    ///
    /// 原来把透明像素也算进去了：内存里的 `NSBitmapImageRep` 带 alpha（与落盘 PNG 不是一回事），
    /// 控件之外全是透明 ⇒ 中位数被拉到 0 ⇒ `isInk` 变成"这个像素不是全黑"，
    /// 于是 `inkPixels` 数到的是整个控件矩形，两态恒等 —— R143 的审查轮就是这么揪出这把坏尺的。
    private static func backgroundLuma(_ rep: NSBitmapImageRep) -> Int {
        var values: [Int] = []
        for py in stride(from: 0, to: rep.pixelsHigh, by: 3) {
            for px in stride(from: 0, to: rep.pixelsWide, by: 3) {
                guard let color = rep.colorAt(x: px, y: py), color.alphaComponent > 0.5,
                      let rgbColor = color.usingColorSpace(.deviceRGB) else { continue }
                values.append(luma(RGB(r: Int(rgbColor.redComponent * 255),
                                       g: Int(rgbColor.greenComponent * 255),
                                       b: Int(rgbColor.blueComponent * 255))))
            }
        }
        values.sort()
        XCTAssertFalse(values.isEmpty, "整幅没有一个不透明像素 ⇒ 这条通道没量到任何画面，读数不算数")
        return values.isEmpty ? 0 : values[values.count / 2]
    }

    /// 高色度像素：`max-min` 通道差超过 60。灰 bezel 与底色到不了这一档，
    /// 所以这一格量的正是"那一圈强调色"，而不是"有没有画东西"。
    static let chromaMin = 60

    private static func highChromaPixels(_ rep: NSBitmapImageRep) -> Int {
        var n = 0
        for py in 0..<rep.pixelsHigh {
            for px in 0..<rep.pixelsWide where chroma(of: rep, px: px, py: py) > chromaMin {
                n += 1
            }
        }
        return n
    }

    private static func chroma(of rep: NSBitmapImageRep, px: Int, py: Int) -> Int {
        guard let color = rep.colorAt(x: px, y: py)?.usingColorSpace(.deviceRGB) else { return 0 }
        let r = color.redComponent, g = color.greenComponent, b = color.blueComponent
        return Int((max(r, max(g, b)) - min(r, min(g, b))) * 255)
    }

    /// 把高色度像素按"离哪条边最近"分成四堆 —— 这是"一圈 vs 一条带"的形状判据。
    private static func chromaByEdge(_ rep: NSBitmapImageRep) -> (top: Int, bottom: Int, left: Int, right: Int) {
        guard let box = opaqueBoundingBox(rep), box.width > 4, box.height > 4 else { return (0, 0, 0, 0) }
        var top = 0, bottom = 0, left = 0, right = 0
        let band = max(3, Int(min(box.width, box.height) * 0.18))
        for py in Int(box.minY)..<Int(box.maxY) {
            for px in Int(box.minX)..<Int(box.maxX) where chroma(of: rep, px: px, py: py) > chromaMin {
                if py - Int(box.minY) < band { top += 1 }
                if Int(box.maxY) - 1 - py < band { bottom += 1 }
                if px - Int(box.minX) < band { left += 1 }
                if Int(box.maxX) - 1 - px < band { right += 1 }
            }
        }
        return (top, bottom, left, right)
    }

    /// 不透明像素的包围盒 = 那颗按钮（含 overlay）实际占的矩形。
    private static func opaqueBoundingBox(_ rep: NSBitmapImageRep) -> CGRect? {
        var minX = rep.pixelsWide, minY = rep.pixelsHigh, maxX = -1, maxY = -1
        for py in 0..<rep.pixelsHigh {
            for px in 0..<rep.pixelsWide {
                guard let color = rep.colorAt(x: px, y: py), color.alphaComponent > 0.5 else { continue }
                minX = min(minX, px); maxX = max(maxX, px)
                minY = min(minY, py); maxY = max(maxY, py)
            }
        }
        guard maxX >= minX, maxY >= minY else { return nil }
        return CGRect(x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1)
    }



    private func renderFrame(appearance: NSAppearance.Name, scale: Int) throws -> NSBitmapImageRep {
        let app = NSApplication.shared
        let previous = app.appearance
        app.appearance = NSAppearance(named: appearance)
        defer { app.appearance = previous }

        let root = AnyView(ZStack(alignment: .topLeading) {
            Color(nsColor: .windowBackgroundColor)
            HotKeyRecorderRing(isRecording: false)
                .frame(width: Self.boxWidth, height: Self.boxHeight)
                .position(x: Self.idleOrigin.x + Self.boxWidth / 2,
                          y: Self.idleOrigin.y + Self.boxHeight / 2)
            HotKeyRecorderRing(isRecording: true)
                .frame(width: Self.boxWidth, height: Self.boxHeight)
                .position(x: Self.recordingOrigin.x + Self.boxWidth / 2,
                          y: Self.recordingOrigin.y + Self.boxHeight / 2)
            Rectangle()
                .fill(Color(nsColor: .controlAccentColor))
                .frame(width: Self.referenceRect.width, height: Self.referenceRect.height)
                .position(x: Self.referenceRect.midX, y: Self.referenceRect.midY)
        }.frame(width: Self.canvasSize.width, height: Self.canvasSize.height, alignment: .topLeading))

        let rep = NSBitmapImageRep(bitmapDataPlanes: nil,
                                   pixelsWide: Int(Self.canvasSize.width) * scale,
                                   pixelsHigh: Int(Self.canvasSize.height) * scale,
                                   bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                   isPlanar: false, colorSpaceName: .deviceRGB,
                                   bytesPerRow: 0, bitsPerPixel: 0)
        let bitmap = try XCTUnwrap(rep)
        bitmap.size = Self.canvasSize
        let host = NSHostingView(rootView: root)
        host.frame = NSRect(origin: .zero, size: Self.canvasSize)
        host.appearance = NSAppearance(named: appearance)
        host.cacheDisplay(in: NSRect(origin: .zero, size: Self.canvasSize), to: bitmap)
        return bitmap
    }

    private struct Reading {
        var inkPixels = 0
        var meanDev = 0.0
        var peakChroma = 0.0
    }

    /// 背景 = 画布顶边那一条（离三个框都远）的中位亮度。
    /// 参照点必须问自己：这里不取角点，因为角上正好可能压着描边。
    private func backgroundOf(_ rep: NSBitmapImageRep) throws -> Int {
        let scale = Double(rep.pixelsWide) / Double(Self.canvasSize.width)
        var values: [Int] = []
        let py = Int(2 * scale)
        for px in stride(from: 0, to: rep.pixelsWide, by: 2) {
            values.append(Self.luma(of: rep, px: px, py: py))
        }
        XCTAssertFalse(values.isEmpty, "背景采样一条都没有 ⇒ 这把尺的分母是 0")
        values.sort()
        return values[values.count / 2]
    }

    private func measure(_ rep: NSBitmapImageRep, box: CGRect, bg: Int, label: String) throws -> Reading {
        let scale = Double(rep.pixelsWide) / Double(Self.canvasSize.width)
        let x0 = Int(box.minX * scale)
        let x1 = Int(box.maxX * scale)
        let y0 = Int(box.minY * scale)
        let y1 = Int(box.maxY * scale)
        guard x0 >= 0, y0 >= 0, x1 <= rep.pixelsWide, y1 <= rep.pixelsHigh, x1 > x0, y1 > y0 else {
            XCTFail("框 \(label) 落在画布外：x=\(x0)..\(x1) y=\(y0)..\(y1) 帧=\(rep.pixelsWide)x\(rep.pixelsHigh)")
            return Reading()
        }
        var reading = Reading()
        var devSum = 0.0
        var scanned = 0
        for py in y0..<y1 {
            for px in x0..<x1 {
                let color = Self.rgb(of: rep, px: px, py: py)
                let dev = abs(Self.luma(color) - bg)
                reading.peakChroma = max(reading.peakChroma,
                                         Double(max(color.r, max(color.g, color.b))
                                                - min(color.r, min(color.g, color.b))))
                scanned += 1
                if dev > Self.inkDelta {
                    reading.inkPixels += 1
                    devSum += Double(dev)
                }
            }
        }
        XCTAssertGreaterThan(scanned, 0, "框 \(label) 一个像素都没扫到 ⇒ 尺没量到东西，读数不算数")
        reading.meanDev = reading.inkPixels > 0 ? devSum / Double(reading.inkPixels) : 0
        return reading
    }

    private struct RGB {
        var r = 0
        var g = 0
        var b = 0

        /// 与 `inkDelta` 同一条分档闸门（不是判据）：偏离背景超过它才算"有墨"。
        /// 阈值由调用方传进来：这个结构体不是 main-actor 隔离的，直接读类上的静态量编译不过。
        func isInk(against bg: Int, delta: Int) -> Bool {
            abs(Int(0.299 * Double(r) + 0.587 * Double(g) + 0.114 * Double(b)) - bg) > delta
        }
    }

    private static func rgb(of rep: NSBitmapImageRep, px: Int, py: Int) -> RGB {
        guard let color = rep.colorAt(x: px, y: py)?.usingColorSpace(.deviceRGB) else { return RGB() }
        return RGB(r: Int(color.redComponent * 255),
                   g: Int(color.greenComponent * 255),
                   b: Int(color.blueComponent * 255))
    }

    private static func luma(of rep: NSBitmapImageRep, px: Int, py: Int) -> Int {
        luma(rgb(of: rep, px: px, py: py))
    }

    private static func luma(_ c: RGB) -> Int {
        Int(0.299 * Double(c.r) + 0.587 * Double(c.g) + 0.114 * Double(c.b))
    }

    private static func keyEvent(_ keyCode: UInt16, modifiers: NSEvent.ModifierFlags = []) -> NSEvent {
        NSEvent.keyEvent(with: .keyDown, location: .zero,
                         modifierFlags: modifiers.intersection(.deviceIndependentFlagsMask),
                         timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: 0,
                         context: nil, characters: "", charactersIgnoringModifiers: "",
                         isARepeat: false, keyCode: keyCode) ?? NSEvent()
    }
}

private extension HotKeyRecorderButton {
    /// 退出录制的测试入口。产品侧的退出只有两条路（提交 / 失焦），而 `resignFirstResponder`
    /// 需要真的窗口与真的响应者链 —— 这里要数的是**出口次数**，响应者链本身由
    /// `HotKeyRecorderButtonTests` 用真窗口测（那条不重复）。
    func cancelViaFirstResponder() {
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 200, height: 100),
                              styleMask: [.titled], backing: .buffered, defer: false)
        window.contentView?.addSubview(self)
        window.makeFirstResponder(self)
        window.makeFirstResponder(nil)
    }
}
