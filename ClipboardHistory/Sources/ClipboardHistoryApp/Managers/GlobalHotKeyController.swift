import AppKit
import Carbon

extension Notification.Name {
    static let showMainWindowHotKeyPressed = Notification.Name("ClipboardHistoryShowMainWindowHotKeyPressed")
    static let repeatCopyHotKeyPressed = Notification.Name("ClipboardHistoryRepeatCopyHotKeyPressed")
}

private let globalHotKeySignature = fourCharacterCode("TJSJ")

@MainActor
enum HotKeyUpdateResult: Equatable {
    case updated
    case newShortcutUnavailable(restoredPrevious: Bool)
}

@MainActor
protocol HotKeyControlling {
    var shortcut: HotKeyShortcut { get }

    @discardableResult
    func updateShortcut(_ newShortcut: HotKeyShortcut) -> HotKeyUpdateResult

    @discardableResult
    func register(shortcut newShortcut: HotKeyShortcut) -> Bool

    func stop()
}

@MainActor
final class GlobalHotKeyController: HotKeyControlling {
    private let action: HotKeyAction
    private(set) var shortcut: HotKeyShortcut

    private var hotKeyRef: EventHotKeyRef?
    private static var eventHandlerRef: EventHandlerRef?

    init(action: HotKeyAction = .showMainWindow) {
        self.action = action
        self.shortcut = action.defaultShortcut
    }

    @discardableResult
    func updateShortcut(_ newShortcut: HotKeyShortcut) -> HotKeyUpdateResult {
        let previousShortcut = shortcut
        guard newShortcut != previousShortcut else { return .updated }

        guard let probeHotKeyRef = registerHotKeyRef(
            for: newShortcut,
            hotKeyIdentifier: action.probeHotKeyIdentifier
        ) else {
            let restoredPrevious = hotKeyRef != nil || register(shortcut: previousShortcut)
            return .newShortcutUnavailable(restoredPrevious: restoredPrevious)
        }

        UnregisterEventHotKey(probeHotKeyRef)
        stop()

        if register(shortcut: newShortcut) {
            return .updated
        }

        let restoredPrevious = register(shortcut: previousShortcut)
        return .newShortcutUnavailable(restoredPrevious: restoredPrevious)
    }

    @discardableResult
    func register(shortcut newShortcut: HotKeyShortcut) -> Bool {
        guard newShortcut.isValid else {
            LifecycleDebugLogger.log("GlobalHotKeyController invalid shortcut=\(newShortcut.displayString)")
            return false
        }

        stop()

        if let newHotKeyRef = registerHotKeyRef(for: newShortcut, hotKeyIdentifier: action.hotKeyIdentifier) {
            hotKeyRef = newHotKeyRef
            shortcut = newShortcut
            LifecycleDebugLogger.log("GlobalHotKeyController registered \(action.title) shortcut=\(shortcut.displayString)")
            return true
        }

        return false
    }

    func stop() {
        if let hotKeyRef {
            UnregisterEventHotKey(hotKeyRef)
            self.hotKeyRef = nil
        }
    }

    private static func installSharedEventHandler() -> Bool {
        if eventHandlerRef != nil {
            return true
        }

        var eventType = EventTypeSpec(
            eventClass: OSType(kEventClassKeyboard),
            eventKind: UInt32(kEventHotKeyPressed)
        )

        let handlerStatus = InstallEventHandler(
            GetApplicationEventTarget(),
            globalHotKeyEventHandler,
            1,
            &eventType,
            nil,
            &eventHandlerRef
        )

        if handlerStatus != noErr {
            LifecycleDebugLogger.log("GlobalHotKeyController InstallEventHandler failed status=\(handlerStatus)")
            return false
        }

        return true
    }

    private func registerHotKeyRef(
        for newShortcut: HotKeyShortcut,
        hotKeyIdentifier: UInt32
    ) -> EventHotKeyRef? {
        guard Self.installSharedEventHandler() else {
            return nil
        }

        var newHotKeyRef: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(
            signature: globalHotKeySignature,
            id: hotKeyIdentifier
        )
        let registerStatus = RegisterEventHotKey(
            newShortcut.keyCode,
            newShortcut.modifiers,
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &newHotKeyRef
        )

        guard registerStatus == noErr, let newHotKeyRef else {
            LifecycleDebugLogger.log("GlobalHotKeyController RegisterEventHotKey failed status=\(registerStatus)")
            return nil
        }

        return newHotKeyRef
    }
}

private func globalHotKeyEventHandler(
    _ nextHandler: EventHandlerCallRef?,
    _ event: EventRef?,
    _ userData: UnsafeMutableRawPointer?
) -> OSStatus {
    guard let event else { return noErr }

    var hotKeyID = EventHotKeyID()
    let status = GetEventParameter(
        event,
        EventParamName(kEventParamDirectObject),
        EventParamType(typeEventHotKeyID),
        nil,
        MemoryLayout<EventHotKeyID>.size,
        nil,
        &hotKeyID
    )

    guard status == noErr,
          hotKeyID.signature == globalHotKeySignature,
          let action = HotKeyAction(hotKeyIdentifier: hotKeyID.id) else {
        return noErr
    }

    DispatchQueue.main.async {
        NotificationCenter.default.post(name: action.notificationName, object: nil)
    }

    return noErr
}

private func fourCharacterCode(_ string: String) -> OSType {
    var result: OSType = 0
    for scalar in string.utf8.prefix(4) {
        result = (result << 8) + OSType(scalar)
    }
    return result
}
