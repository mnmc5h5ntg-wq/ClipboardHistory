import Combine
import Foundation
import ServiceManagement
import AppKit

@MainActor
protocol LoginItemManaging {
    var isSupported: Bool { get }
    var isEnabled: Bool { get }
    func setEnabled(_ enabled: Bool) throws
}

@MainActor
struct SystemLoginItemManager: LoginItemManaging {
    private static let loginItemName = "时间剪史"

    var isSupported: Bool { true }

    var isEnabled: Bool {
        if #available(macOS 13, *) {
            return SMAppService.mainApp.status == .enabled
        }
        return Self.checkLoginItemExistsViaAppleScript()
    }

    func setEnabled(_ enabled: Bool) throws {
        if #available(macOS 13, *) {
            if enabled {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
        } else {
            guard let appPath = Bundle.main.bundlePath as String? else {
                throw LoginItemSettings.Error.unsupportedSystem
            }
            if enabled {
                Self.addLoginItemViaAppleScript(appPath: appPath)
            } else {
                Self.removeLoginItemViaAppleScript(appPath: appPath)
            }
            // macOS 12 这条路上，"什么都没发生"是**常态而不是异常**：
            // 自动化权限被拒时 `tell application "System Events"` 常常不抛错，只是脚本没生效
            // （`executeAndReturnError` 的 error 字典被丢在这里第 71 行那个位置，历史上没人读它）。
            // 于是用户看到的是：开关自己弹回去，一句话都没有。
            // 所以**事后读回一次**，不一致就抛 —— 让 `LoginItemSettings` 那层去说那句话。
            try Self.verifyApplied(enabled: enabled, readBack: Self.checkLoginItemExistsViaAppleScript)
        }
    }

    /// 把"写完读回"这一步单独拆出来，有两个理由：
    /// ① 它是唯一能证明"这条路上成功是真的成功"的手段（AppleScript 的返回不可信）；
    /// ② 这台开发机是 macOS 14+，`#available` 那一支**永远走不到** ——
    ///    不拆成纯函数的话，这段逻辑就只能等一台 12 的机器来发现它错了（见账本里的"打桩成真值"规矩）。
    static func verifyApplied(enabled: Bool, readBack: () -> Bool) throws {
        let applied = readBack()
        guard applied == enabled else { throw LoginItemSettings.Error.loginItemNotApplied }
    }

    private static func checkLoginItemExistsViaAppleScript() -> Bool {
        let script = """
        tell application "System Events"
            set itemNames to name of every login item
            if itemNames contains "\(loginItemName)" then
                return "1"
            end if
            return "0"
        end tell
        """
        guard let appleScript = NSAppleScript(source: script) else { return false }
        var error: NSDictionary?
        let result = appleScript.executeAndReturnError(&error)
        return result.stringValue == "1"
    }

    private static func addLoginItemViaAppleScript(appPath: String) {
        let script = """
        tell application "System Events"
            if not (exists login item "\(loginItemName)") then
                make new login item at end with properties {path:"\(appPath)", name:"\(loginItemName)", hidden:false}
            end if
        end tell
        """
        guard let appleScript = NSAppleScript(source: script) else { return }
        var error: NSDictionary?
        appleScript.executeAndReturnError(&error)
    }

    private static func removeLoginItemViaAppleScript(appPath: String) {
        let script = """
        tell application "System Events"
            delete every login item whose path is "\(appPath)"
        end tell
        """
        guard let appleScript = NSAppleScript(source: script) else { return }
        var error: NSDictionary?
        appleScript.executeAndReturnError(&error)
    }
}

@MainActor
final class LoginItemSettings: ObservableObject {
    enum Error: Swift.Error {
        case unsupportedSystem
        /// macOS 12 的 AppleScript 路径：脚本没报错，但登录项**事后不在**（要嘛权限被拒，
        /// 要嘛 System Events 根本没执行）。以前这种失败是**静默**的 —— 开关弹回去，没有回执。
        case loginItemNotApplied
    }

    @Published private(set) var isEnabled: Bool
    @Published private(set) var message: String?
    /// R384：这条 message 是**做失败了**，还是「本机不支持」的静态说明？
    /// 两者的视觉语言不能一样 —— 失败是当下要重试的事，说明是这一屏的能力边界。
    @Published private(set) var lastActionFailed = false

    private let manager: LoginItemManaging

    var isSupported: Bool {
        manager.isSupported
    }

    init(manager: LoginItemManaging = SystemLoginItemManager()) {
        self.manager = manager
        self.isEnabled = manager.isEnabled
        self.message = manager.isSupported ? nil : "当前系统不支持从应用内设置开机启动。"
    }

    func setEnabled(_ enabled: Bool) {
        do {
            try manager.setEnabled(enabled)
            isEnabled = manager.isEnabled
            message = nil
            lastActionFailed = false
        } catch {
            isEnabled = manager.isEnabled
            message = enabled ? "开机启动开启失败，请稍后重试。" : "开机启动关闭失败，请稍后重试。"
            lastActionFailed = true
        }
    }

    func refresh() {
        isEnabled = manager.isEnabled
    }
}
