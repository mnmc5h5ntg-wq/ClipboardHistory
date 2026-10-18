// 不覆盖管线：这一卷测的是**捕获闸门里那条放行谓词**（"这张空帧算这台机器画不出来，还是算产品缺陷"）。
// 它从产品入口到不了 —— 本机拍不出"高帧全空"那种形状（六张 `-1040-` 本机 `blank=0.0%`），
// 所以对照只能建在谓词自己身上：每一格都必须让它真的返回不同的值。
// 管线级的证人是 runner：它每一跑都打 `CAPTURE_GEOMETRY … requested=720x1040 content=720x1040 host=720x1040`
// 与 `BLANK_GAP_WOULD_RELEASE …`，而那六张帧报 95% 未画 —— 两边合起来才是这条出口的完整验收。
// 出口本身**还没接线放行**（判别轴没有读数之前红照旧红），所以这一卷钉的是"决定怎么做"，不是"放行已生效"。
import XCTest
@testable import ClipboardHistoryApp

/// R168 / BACKLOG 194：三种解释只剩一种最像时，把"该不该放行"抽成可单测的谓词。
/// R167 我犯过的错要在这里被堵住：那两格"正对照"是把**有对象的帧**强行塞进未画循环，
/// 于是两种实现都绿 —— 那是空对账。这里每一格都让谓词自己做决定。
///
/// `@MainActor` 不是偏好：谓词与 `codeOnly` / `functionBody` 都住在 `@MainActor` 的
/// `UICaptureTests` 里，测试类不加就会红成 `#ActorIsolatedCall`（本轮第一遍就是这么撞的）。
@MainActor
final class CaptureBlankFrameGapTests: XCTestCase {

    func testRegistersOnlyWhenGeometryEqualsTheRequest() {
        // runner 的真实形状：三边都等于 1040 ⇒ 会放行（记未运行）
        XCTAssertTrue(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "settings", requestedHeightPt: 1040, contentHeightPt: 1040, hostHeightPt: 1040))
        // 内容视图没铺满 ⇒ 那是布局问题，不许放行
        XCTAssertFalse(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "settings", requestedHeightPt: 1040, contentHeightPt: 681, hostHeightPt: 1040))
        // 窗口被收小 ⇒ 同上
        XCTAssertFalse(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "settings", requestedHeightPt: 1040, contentHeightPt: 1040, hostHeightPt: 681))
    }

    func testShortFixturesAreNeverReleased() {
        // 540 那一档在 runner 上画得出来 ⇒ 它没资格走这条出口（否则出口成了万能挡箭牌）
        XCTAssertFalse(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "settings", requestedHeightPt: 540, contentHeightPt: 540, hostHeightPt: 540))
        // 别的族（浮层、菜单栏、内容区）也不许走
        XCTAssertFalse(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "quickpick", requestedHeightPt: 1040, contentHeightPt: 1040, hostHeightPt: 1040))
    }

    func testMissingReadingIsNotEvidenceOfAMachineGap() {
        // 读不出"这张帧要的多高" ⇒ 不放行：缺证据不是"这台机器不行"的证据
        XCTAssertFalse(UICaptureTests.shouldRegisterBlankAsMachineGap(
            family: "settings", requestedHeightPt: nil, contentHeightPt: 1040, hostHeightPt: 1040))
    }

    /// 谓词不是纸上概念：未画帧的处置循环必须**真的**调用它，否则"抽出来了"等于"没接线"。
    /// 扫的是 `testCaptureKeyViews` 那一节的方法体，不是整份文件 —— 整文件 `contains`
    /// 会把我刚写在注释里的名字当成调用（R88 那一族）。
    func testBlankFrameLoopCallsThePredicate() throws {
        let harness = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let raw = try String(contentsOf: harness, encoding: .utf8)
        let body = UICaptureTests.functionBody(
            named: "func testCaptureKeyViews() throws {",
            in: UICaptureTests.codeOnly(raw))
        XCTAssertFalse(body.isEmpty,
                       "方法体取空了（签名变了或缩进前提不成立）⇒ 这条守卫无从判定，红给它")
        let needle = "shouldRegisterBlankAsMachineGap"
        let hits = body.components(separatedBy: "\n").filter { $0.contains(needle) }
        XCTAssertEqual(hits.count, 1,
                       "未画循环里对放行谓词的调用应该有 1 处，实到 \(hits.count) 处"
                       + " ⇒ 0 处等于谓词是死代码、2 处等于出口被复制成了两份实现")
    }

    /// 高帧的下界只准有一个来源：`render` 留读数与谓词判档必须同一颗常数。
    func testTallFixtureThresholdHasOneSource() throws {
        let harness = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let raw = UICaptureTests.codeOnly(try String(contentsOf: harness, encoding: .utf8))
        XCTAssertTrue(raw.contains("if size.height >= Self.tallFixtureHeightFloor"),
                      "render 里的高帧门槛不再引用 tallFixtureHeightFloor ⇒ 出口会跟着字面量悄悄换档")
        XCTAssertTrue(raw.contains("requested >= Self.tallFixtureHeightFloor"),
                      "CAPTURE_DRAW 那一圈不再用同一颗常数挑高帧 ⇒ 读数的覆盖面会与出口的判断面错位")
    }

    // MARK: - R168 的分辨轴：画到的包围盒（BACKLOG 194 剩下的两种解释靠它分开）

    /// 造一张纯手工的位图：只有 `inkedRows` 那些行的 alpha 是 `alpha`，其余像素全 0（没画）。
    /// 对照组全部建在这里 —— 本机拍不出"高帧全空"，那就**造得出**"第 0..680 行有墨、681 行起全空"，
    /// 而这一次每一格都让尺子真的给数（R167 那两格空对照的教训）。
    private func buffer(width: Int, height: Int, inkedRows: IndexSet, alpha: UInt8 = 255) -> [UInt8] {
        var bytes = [UInt8](repeating: 0, count: width * height * 4)
        let stride = width * 4
        for y in inkedRows {
            var x = 0
            while x < width {
                bytes[y * stride + x * 4 + 3] = alpha
                x += 1
            }
        }
        return bytes
    }

    private func box(_ bytes: [UInt8], width: Int, height: Int, scale: CGFloat)
            -> (topPt: Double, bottomPt: Double, heightPt: Double) {
        bytes.withUnsafeBufferPointer { handle in
            UICaptureTests.drawnBoundingBox(bytes: handle.baseAddress!, width: width, height: height,
                                            bytesPerRow: width * 4, backingScale: scale)
        }
    }

    func testBoundingBoxSeparatesNotRenderedFromClipped() {
        // 全空 ⇒ height=0、bottom=-1（"根本没渲染"那一格）
        let empty = buffer(width: 4, height: 1040, inkedRows: IndexSet())
        let measuredEmpty = box(empty, width: 4, height: 1040, scale: 1)
        XCTAssertEqual(measuredEmpty.heightPt, 0, accuracy: 0.001, "全空的帧必须报 0 高")
        XCTAssertEqual(measuredEmpty.bottomPt, -1, accuracy: 0.001, "没有有墨的行要报 -1，不许报 0")

        // 只画到 0..680 ⇒ 高 681 = 屏幕可视高那一侧（"渲染了但被裁"那一格）
        let clipped = buffer(width: 4, height: 1040, inkedRows: IndexSet(integersIn: 0..<681))
        let measuredClipped = box(clipped, width: 4, height: 1040, scale: 1)
        XCTAssertEqual(measuredClipped.heightPt, 681, accuracy: 0.001,
                       "被裁到可视高的形状必须量出 681，而不是 1040 或 0")
        XCTAssertGreaterThan(measuredClipped.heightPt, measuredEmpty.heightPt,
                             "两种解释在尺子上同高 ⇒ 这根轴分不开它们，194 还是没读数")

        // 画满 ⇒ 1040（本机高帧该有的样子，也是这把尺的标定另一侧）
        let full = buffer(width: 4, height: 1040, inkedRows: IndexSet(integersIn: 0..<1040))
        XCTAssertEqual(box(full, width: 4, height: 1040, scale: 1).heightPt, 1040, accuracy: 0.001)
    }

    func testBoundingBoxConvertsPixelsToPointsByBackingScale() {
        // 像素行 200..<400，2x ⇒ 点位 100..200，高 100pt。
        let bytes = buffer(width: 4, height: 800, inkedRows: IndexSet(integersIn: 200..<400))
        let measured = box(bytes, width: 4, height: 800, scale: 2)
        XCTAssertEqual(measured.topPt, 100, accuracy: 0.001)
        XCTAssertEqual(measured.heightPt, 100, accuracy: 0.001,
                       "包围盒必须换算成 pt —— 直接回像素数会把 2x 帧说成两倍高")
    }

    func testBoundingBoxUsesTheSameAlphaCeilingAsBlankness() {
        // 比 ceiling 低 1 ⇒ 按"没画"处理；恰好等于 ceiling ⇒ 算画过。
        // 这一格钉的是"这根轴与 `transparent` 用同一个常数"，两边一起变（R76 的按方向各一张名册同族）。
        let justBelow = buffer(width: 4, height: 40, inkedRows: IndexSet(integersIn: 0..<40),
                               alpha: UICaptureTests.transparentAlphaCeiling - 1)
        XCTAssertEqual(box(justBelow, width: 4, height: 40, scale: 1).heightPt, 0, accuracy: 0.001,
                       "alpha 低于 ceiling 的像素不该被算成墨")
        let exactlyCeiling = buffer(width: 4, height: 40, inkedRows: IndexSet(integersIn: 0..<40),
                                    alpha: UICaptureTests.transparentAlphaCeiling)
        XCTAssertEqual(box(exactlyCeiling, width: 4, height: 40, scale: 1).heightPt, 40, accuracy: 0.001,
                       "alpha 等于 ceiling 的像素必须被算成墨，否则这根轴比\"空\"那把尺更迟钝")
    }

    func testRequestedHeightComesFromTheFrameName() {
        XCTAssertEqual(UICaptureTests.requestedHeightPt(fromFile: "settings-privacy-tall-720x1040-light.png"),
                       1040, "高帧的需求高读不出来 ⇒ 出口与读数都会把它当\"没有尺寸\"")
        XCTAssertEqual(UICaptureTests.requestedHeightPt(fromFile: "quickpick-empty-420x300-dark.png"), 300)
        XCTAssertNil(UICaptureTests.requestedHeightPt(fromFile: "no-size-here.png"),
                     "没有尺寸的帧名必须返回 nil，不许返回 0（那会把\"读不到\"伪装成\"矮帧\"）")
    }
}
