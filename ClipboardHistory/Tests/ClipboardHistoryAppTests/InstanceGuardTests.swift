import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// M1×边界：同 bundle 的第二份进程必须认出来（它会把第一份写进存档的记录整片盖掉）。
final class InstanceGuardTests: XCTestCase {
    private let bundle = "com.clipboardhistory.app"

    private func instance(
        _ pid: pid_t,
        bundleID: String? = "com.clipboardhistory.app",
        alreadyTerminated: Bool = false
    ) -> InstanceGuard.RunningInstance {
        .init(bundleIdentifier: bundleID, processIdentifier: pid, isTerminated: alreadyTerminated)
    }

    func testFindsAnotherLiveInstanceWithSameBundle() {
        let found = InstanceGuard.conflictingPID(
            among: [instance(111), instance(222)], mine: 111, bundleIdentifier: bundle
        )
        XCTAssertEqual(found, 222)
    }

    func testSelfIsNeverTheConflict() {
        XCTAssertNil(InstanceGuard.conflictingPID(among: [instance(111)], mine: 111, bundleIdentifier: bundle))
    }

    func testOtherBundlesAreIgnored() {
        XCTAssertNil(InstanceGuard.conflictingPID(
            among: [instance(222, bundleID: "com.apple.Safari")], mine: 111, bundleIdentifier: bundle
        ))
    }

    func testInstanceThatAlreadyTerminatedIsIgnored() {
        // 换版本时旧进程刚退出但记录还在：这时拒绝新启动会让用户以为 App 打不开。
        XCTAssertNil(InstanceGuard.conflictingPID(
            among: [instance(222, alreadyTerminated: true)], mine: 111, bundleIdentifier: bundle
        ))
    }

    func testUnknownBundleIdentifierNeverConflicts() {
        // 裸可执行文件（swift run）没有 bundle id：宁可放行也不要误杀。
        XCTAssertNil(InstanceGuard.conflictingPID(
            among: [instance(222)], mine: 111, bundleIdentifier: nil
        ))
    }

    func testNoOtherInstancesAtAll() {
        XCTAssertNil(InstanceGuard.conflictingPID(among: [], mine: 111, bundleIdentifier: bundle))
    }
    /// 适配器那条路（读真实进程列表）也必须被跑过一次，否则测的只是纯函数。
    /// 这里拿本机一定存在的 Finder 当"同 bundle 的另一实例"喂给它。
    func testAdapterReadsTheRealProcessList() throws {
        let mine = ProcessInfo.processInfo.processIdentifier
        let finder = NSWorkspace.shared.runningApplications.first { $0.bundleIdentifier == "com.apple.finder" }
        try XCTSkipIf(finder == nil, "本机没有 Finder 进程，无法验证适配器")
        XCTAssertEqual(
            InstanceGuard.conflictingPID(excluding: mine, bundleIdentifier: "com.apple.finder"),
            finder?.processIdentifier,
            "适配器应能把系统里的真实进程认成冲突实例"
        )
    }

    /// 「排除自己」必须单独一条用例：xctest 进程不是 GUI App，本机 `NSWorkspace.runningApplications`
    /// 里根本没有它（实测 `ownPIDs=[]`），所以这条在本环境只能 skip。
    /// 放在同一条用例里会把上面 Finder 那个**阳性对照**一起染成 skipped，等于丢掉证据。
    ///
    /// 还有一层原因：这一条以前是拿产品的 bundle id 去问机器，于是用户开着
    /// `/Applications/时间剪史.app` 时它就是红的（本轮实测 pid 75412）—— 那是真冲突、不是缺陷，
    /// 测试的红绿不该由"用户开没开 App"决定。
    func testAdapterExcludesItselfWhenItIsTheOnlyInstance() throws {
        let mine = ProcessInfo.processInfo.processIdentifier
        let ownBundleID = Bundle.main.bundleIdentifier
        let ownPIDs = NSWorkspace.shared.runningApplications
            .filter { $0.bundleIdentifier == ownBundleID }
            .map(\.processIdentifier)
        guard let ownBundleID, ownPIDs == [mine] else {
            throw XCTSkip("测试进程的 bundle id 在本机不唯一或根本没被列出（ownPIDs=\(ownPIDs)，mine=\(mine)）；"
                + "「排除自己」由上面的纯函数用例覆盖")
        }
        XCTAssertNil(
            InstanceGuard.conflictingPID(excluding: mine, bundleIdentifier: ownBundleID),
            "测试进程自己不该被当成同 bundle 的另一实例"
        )
    }

}
