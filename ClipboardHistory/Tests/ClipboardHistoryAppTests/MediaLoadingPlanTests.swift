import XCTest
@testable import ClipboardHistoryApp

// 不覆盖管线（AGENTS.md 的规矩，写在文件开头）：这一支判的是**决定与默认值**，
// 不是"屏幕上真的出现了骨架"。管线级证人是帧基线里的
// `detail-loading-composed-720x520-{dark,light}`（R211 / BACKLOG 233）：
// 那张组合帧只有当 `freezeLoadingForCapture=true` 真的让 `.task` 不去加载时才会画成骨架，
// 而"默认值 ⇒ 会加载"这句话由下面 `testDefaultsStartTheLoad` 从视图结构体上**读字段**钉住。
//
// 为什么值得单独钉（BACKLOG 236）：R211 我在注释里写过"默认值由某支测试钉住"，而那支测试当时不存在
// —— 不执行的声明比没有更坏。今天它存在了，而且下面这两格都是**会红的**：
// 把 `= false` 翻成 `= true`，`testDefaultsStartTheLoad` 红（刀 M748 就是干这个的）；
// 在产品代码里硬写 `freezeLoadingForCapture: true`，`testProductCodeNeverFreezesTheLoad` 红。
@MainActor
final class MediaLoadingPlanTests: XCTestCase {

    // MARK: 真值表

    func testStartsLoadTruthTable() {
        XCTAssertTrue(MediaLoadingPlan.startsLoad(freezeLoadingForCapture: false),
                      "默认（不冻结）必须真去加载，否则详情区永远停在骨架")
        XCTAssertFalse(MediaLoadingPlan.startsLoad(freezeLoadingForCapture: true),
                       "夹具显式要求冻结时必须不加载，否则组合帧会静默变成成功帧")
        XCTAssertEqual(MediaLoadingPlan.stageWhenLoadNotStarted(), 0,
                       "没开始加载时停在阶段 0（骨架）—— 这个数同时是 DetailView 按值动画的键档位")
    }

    // MARK: 默认值（读字段，不读注释）

    func testDefaultsStartTheLoad() {
        let url = URL(fileURLWithPath: "/Users/tester/Desktop/合同 终版 v3.pdf")
        let view = DetailFileView(url: url, thumbnail: nil)
        XCTAssertFalse(view.freezeLoadingForCapture,
                       "`DetailFileView` 的默认值被翻动了 ⇒ 产品路径会永远停在加载骨架")
    }

    func testProductCodeNeverFreezesTheLoad() {
        // 冻结只允许出现在**测试夹具**里。产品代码里出现 `freezeLoadingForCapture: true`
        // 就等于把详情区永久冻在骨架 —— 这一格要能在有人这么写的时候红。
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()   // Tests/ClipboardHistoryAppTests
            .deletingLastPathComponent()   // Tests
            .deletingLastPathComponent()   // ClipboardHistory
            .appendingPathComponent("Sources", isDirectory: true)
        let offenders = swiftFilesUnder(root).filter {
            strippedLines(in: $0).contains { $0.contains("freezeLoadingForCapture: true") }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "产品代码里不许把加载冻住：\(offenders.map { $0.lastPathComponent })")
    }

    func testHarnessIsTheOnlyPlaceThatFreezes() {
        // 反向证人：夹具那一格**必须**还在传 true。它要是被删了，
        // `detail-loading-composed` 会退化成成功帧，而帧基线只会报"像素变了"、说不出原因。
        let harness = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .appendingPathComponent("UICaptureHarness.swift")
        let hits = strippedLines(in: harness).filter { $0.contains("freezeLoadingForCapture: true") }
        XCTAssertEqual(hits.count, 1,
                       "夹具里应当恰好一处显式冻结（组合帧）；实得 \(hits.count) 次 ⇒ 组合帧的身份要重看")
    }

    // MARK: 取行的小工具

    private func swiftFilesUnder(_ dir: URL) -> [URL] {
        let fm = FileManager.default
        guard let en = fm.enumerator(at: dir, includingPropertiesForKeys: nil) else { return [] }
        return en.compactMap { $0 as? URL }.filter { $0.pathExtension == "swift" }
    }

    /// 剥掉行注释再比对：否则**注释里提到**这个键的散文会把守卫喂饱（R76 那一族）。
    private func strippedLines(in url: URL) -> [String] {
        guard let raw = try? String(contentsOf: url, encoding: .utf8) else { return [] }
        return raw.split(separator: "\n").map { line in
            if let r = line.range(of: "//") { return String(line[..<r.lowerBound]) }
            return String(line)
        }
    }
}
