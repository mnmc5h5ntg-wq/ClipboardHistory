import AppKit
import XCTest
@testable import ClipboardHistoryApp

/// 审计第二轮 R2-06（1.7）：菜单栏那条清空历史的 `NSAlert` 以前把"清空"放在第一位，
/// 于是 Return 直接触发破坏性动作，违反 HIG"默认按钮 = 最安全动作"。
/// 弹窗本身要真机点，测不了；但它的全部可判定内容（按钮顺序、角色、快捷键、返回值映射）
/// 都在 `DestructiveAlertLayout` 里，这里逐条钉住。
final class DestructiveAlertLayoutTests: XCTestCase {
    func testCancelButtonComesFirstAndOwnsTheReturnKey() {
        let buttons = DestructiveAlertLayout.buttons(confirmTitle: "清空历史", cancelTitle: "取消")
        XCTAssertEqual(buttons.count, 2)
        XCTAssertEqual(buttons[0].title, "取消", "第一个按钮 = NSAlert 的默认按钮，必须是最安全的动作")
        XCTAssertFalse(buttons[0].isDestructive)
        XCTAssertEqual(buttons[0].keyEquivalent, "\r", "Return 只能落在取消上")
        XCTAssertEqual(buttons[1].title, "清空历史")
        XCTAssertTrue(buttons[1].isDestructive, "破坏性按钮要标出来，系统才会给警示样式且不把它当默认")
        XCTAssertEqual(buttons[1].keyEquivalent, "", "破坏性按钮不许有快捷键，必须显式点击")
    }

    func testModalResponseMappingFollowsTheNewButtonOrder() {
        // 这条是"改按钮顺序"最容易翻车的地方：映射判反了会把"取消"当成"清空历史"。
        XCTAssertTrue(DestructiveAlertLayout.isConfirmed(.alertSecondButtonReturn))
        XCTAssertFalse(DestructiveAlertLayout.isConfirmed(.alertFirstButtonReturn),
                       "第一个按钮现在是取消，绝不能被当成确认")
        XCTAssertFalse(DestructiveAlertLayout.isConfirmed(.alertThirdButtonReturn))
        XCTAssertFalse(DestructiveAlertLayout.isConfirmed(.cancel), "取消/中止一类的返回值都不算确认")
        XCTAssertFalse(DestructiveAlertLayout.isConfirmed(.abort))
    }
}
