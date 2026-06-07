import AppKit
import Carbon

extension Notification.Name {
    static let showMainWindowHotKeyPressed = Notification.Name("ClipboardHistoryShowMainWindowHotKeyPressed")
}

private let globalHotKeySignature = fourCharacterCode("TJSJ")
private let globalHotKeyIdentifier: UInt32 = 1

@MainActor
final class GlobalHotKeyController {
    private(set) var shortcut = HotKeyShortcut.defaultShortcut

    private var hotKeyRef: EventHotKeyRef?
    private var eventHandlerRef: EventHandlerRef?

    @discardableResult
    func updateShortcut(_ newShortcut: HotKeyShortcut) -> Bool {
        let previousShortcut = shortcut
        if register(shortcut: newShortcut) {
            return true
        }

        _ = register(shortcut: previousShortcut)
        return false
    }

    @discardableResult
    func register(shortcut newShortcut: HotKeyShortcut) -> Bool {
        guard newShortcut.isValid else {
            LifecycleDebugLogger.log("GlobalHotKeyController invalid shortcut=\(newShortcut.displayString)")
            return false
        }

        stop()

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

        guard handlerStatus == noErr else {
            LifecycleDebugLogger.log("GlobalHotKeyController InstallEventHandler failed status=\(handlerStatus)")
            return false
        }

        let hotKeyID = EventHotKeyID(
            signature: globalHotKeySignature,
            id: globalHotKeyIdentifier
        )
        let registerStatus = RegisterEventHotKey(
            newShortcut.keyCode,
            newShortcut.modifiers,
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )

        guard registerStatus == noErr else {
            LifecycleDebugLogger.log("GlobalHotKeyController RegisterEventHotKey failed status=\(registerStatus)")
            removeEventHandler()
            return false
        }

        shortcut = newShortcut
        LifecycleDebugLogger.log("GlobalHotKeyController registered shortcut=\(shortcut.displayString)")
        return true
    }

    func stop() {
        if let hotKeyRef {
            UnregisterEventHotKey(hotKeyRef)
            self.hotKeyRef = nil
        }
        removeEventHandler()
    }

    private func removeEventHandler() {
        if let eventHandlerRef {
            RemoveEventHandler(eventHandlerRef)
            self.eventHandlerRef = nil
        }
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
          hotKeyID.id == globalHotKeyIdentifier else {
        return noErr
    }

    DispatchQueue.main.async {
        NotificationCenter.default.post(name: .showMainWindowHotKeyPressed, object: nil)
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
