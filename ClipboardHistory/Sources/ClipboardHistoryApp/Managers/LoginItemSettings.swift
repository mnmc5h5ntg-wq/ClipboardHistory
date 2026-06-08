import Combine
import Foundation
import ServiceManagement

@MainActor
protocol LoginItemManaging {
    var isSupported: Bool { get }
    var isEnabled: Bool { get }
    func setEnabled(_ enabled: Bool) throws
}

@MainActor
struct SystemLoginItemManager: LoginItemManaging {
    var isSupported: Bool {
        if #available(macOS 13, *) {
            return true
        }
        return false
    }

    var isEnabled: Bool {
        if #available(macOS 13, *) {
            return SMAppService.mainApp.status == .enabled
        }
        return false
    }

    func setEnabled(_ enabled: Bool) throws {
        guard #available(macOS 13, *) else {
            throw LoginItemSettings.Error.unsupportedSystem
        }

        if enabled {
            try SMAppService.mainApp.register()
        } else {
            try SMAppService.mainApp.unregister()
        }
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
