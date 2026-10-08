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
        }
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
    }

    @Published private(set) var isEnabled: Bool
    @Published private(set) var message: String?

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
        } catch {
            isEnabled = manager.isEnabled
            message = enabled ? "开机启动开启失败，请稍后重试。" : "开机启动关闭失败，请稍后重试。"
        }
    }

    func refresh() {
        isEnabled = manager.isEnabled
    }
}
