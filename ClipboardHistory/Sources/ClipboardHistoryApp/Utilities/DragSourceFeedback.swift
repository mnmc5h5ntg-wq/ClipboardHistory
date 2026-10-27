import AppKit
import SwiftUI

/// 拖拽源反馈的纯状态：正在拖的那一条是谁；鼠标松开即清。
struct DragSourceFeedbackState: Equatable {
    private(set) var entryID: UUID?

    mutating func begin(_ id: UUID) {
        entryID = id
    }

    mutating func end() {
        entryID = nil
    }

    mutating func tick(mouseButtons: Int) {
        if mouseButtons == 0 { entryID = nil }
    }

    func isDragging(_ id: UUID) -> Bool {
        entryID == id
    }
}

/// 产品侧唯一的拖拽源状态。`.onDrag` 只负责在拖起来时登记；结束靠 `.common` runloop 里
/// 的 50ms 轮询 `NSEvent.pressedMouseButtons`（拖拽期间主 runloop 在 tracking 模式，
/// 普通 Timer 会停，`.common` 不会）。
@MainActor
final class DragSourceFeedback: ObservableObject {
    static let shared = DragSourceFeedback()

    /// 行内容的降幅：0.55 是"读得出还是它，但明显退到背景里"的档；不是像素地板。
    static let dimOpacity: Double = 0.55

    @Published private(set) var state = DragSourceFeedbackState()

    private var pollTimer: Timer?
    private var beginTimer: Timer?

    init() {}

    /// 拖起来之后延迟 50ms 再变暗：系统的拖拽预览在 onDrag 返回时就抓图，
    /// 同一 tick 变暗会把预览也拍成暗的。
    func beginAfterDelay(_ entryID: UUID) {
        beginTimer?.invalidate()
        let timer = Timer(timeInterval: 0.05, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated {
                self?.begin(entryID)
            }
        }
        RunLoop.main.add(timer, forMode: .common)
        beginTimer = timer
    }

    func begin(_ entryID: UUID) {
        beginTimer?.invalidate()
        beginTimer = nil
        state.begin(entryID)
        startPolling()
    }

    func end() {
        beginTimer?.invalidate()
        beginTimer = nil
        pollTimer?.invalidate()
        pollTimer = nil
        state.end()
    }

    private func startPolling() {
        pollTimer?.invalidate()
        let timer = Timer(timeInterval: 0.05, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.state.tick(mouseButtons: Int(NSEvent.pressedMouseButtons))
                if self.state.entryID == nil {
                    self.pollTimer?.invalidate()
                    self.pollTimer = nil
                }
            }
        }
        RunLoop.main.add(timer, forMode: .common)
        pollTimer = timer
    }
}

/// 取证通道（R427）：只有夹具会写正在拖的条目 ID；产品路径永远是 nil。
struct DraggingEntryIDForCaptureKey: EnvironmentKey {
    static let defaultValue: UUID? = nil
}

extension EnvironmentValues {
    var draggingEntryIDForCapture: UUID? {
        get { self[DraggingEntryIDForCaptureKey.self] }
        set { self[DraggingEntryIDForCaptureKey.self] = newValue }
    }
}
