import AppKit
import Vision

@MainActor
struct SystemContextCollector {
    var preferences: ContextPreferenceSettings
    private var eventLog: [ContextEvent] = []

    init(preferences: ContextPreferenceSettings = ContextPreferenceSettings()) {
        self.preferences = preferences
    }

    mutating func recordCopy(entryID: UUID) -> ContextEvent {
        let app = currentApp()
        let event = ContextEvent(
            kind: .copy,
            frontmostApplication: app,
            entryID: entryID
        )
        eventLog.append(event)
        trimEventLog()
        return event
    }

    mutating func recordAppSwitch() -> ContextEvent {
        let app = currentApp()
        let event = ContextEvent(
            kind: .switchToApp,
            frontmostApplication: app
        )
        eventLog.append(event)
        trimEventLog()
        return event
    }

    func currentContext(
        recentEntries: [ClipboardEntrySummary],
        selectedEntryID: UUID?,
        capturedAt: Date = Date(),
        skipAppleScript: Bool = false
    ) -> ContextSnapshot {
        let permissionState = preferences.permissionState
        let app = currentApp()

        var snapshot = ContextSnapshot.minimal(
            recentEntries: recentEntries,
            selectedEntryID: selectedEntryID,
            capturedAt: capturedAt
        )
        snapshot.frontmostApplication = app
        snapshot.recentEvents = recentEvents(since: capturedAt)
        snapshot.permissionState = permissionState

        // AppleScript 调用可能阻塞主线程数百毫秒（尤其在目标应用无响应时）。
        // 性能敏感路径（推荐刷新、反馈记录）传入 skipAppleScript: true 跳过。
        if skipAppleScript { return snapshot }

        if permissionState.canReadWindowTitle {
            snapshot.activeWindow = WindowContext(
                title: currentWindowTitle(),
                sensitivity: .personal
            )
        }

        if permissionState.canReadBrowserDomain {
            snapshot.browser = currentBrowserContext()
        }

        if permissionState.canReadFinderDirectory {
            snapshot.finderDirectory = currentFinderDirectory()
        }

        if permissionState.canReadFinderSelection {
            snapshot.finderSelection = currentFinderSelection()
        }

        return snapshot
    }

    func currentApp() -> RunningApplicationContext? {
        guard let app = NSWorkspace.shared.frontmostApplication else { return nil }
        return RunningApplicationContext(
            localizedName: app.localizedName,
            bundleIdentifier: app.bundleIdentifier,
            processIdentifier: app.processIdentifier
        )
    }

    func currentWindowTitle() -> String? {
        guard let app = NSWorkspace.shared.frontmostApplication else { return nil }

        return app.localizedName.flatMap { name in
            let windows = CGWindowListCopyWindowInfo(
                [.optionOnScreenOnly, .excludeDesktopElements],
                kCGNullWindowID
            ) as? [[String: Any]]

            return windows?.first { info in
                guard let owner = info[kCGWindowOwnerName as String] as? String,
                      owner == name,
                      let layer = info[kCGWindowLayer as String] as? Int,
                      layer == 0 else { return false }
                return true
            }?[kCGWindowName as String] as? String
        }
    }

    func currentBrowserContext() -> BrowserContext? {
        guard let app = NSWorkspace.shared.frontmostApplication,
              let bundleID = app.bundleIdentifier else { return nil }

        let browserIDs: Set<String> = [
            "com.apple.Safari", "com.google.Chrome",
            "org.chromium.Chromium", "company.thebrowser.Browser",
            "com.microsoft.edgemac", "com.operasoftware.Opera",
            "com.vivaldi.Vivaldi", "org.mozilla.firefox",
            "com.brave.Browser"
        ]

        guard browserIDs.contains(bundleID) else { return nil }

        let script: String
        if bundleID == "com.apple.Safari" {
            script = """
            tell application "Safari"
                if (count of windows) > 0 then
                    set w to front window
                    set u to URL of current tab of w
                    set t to name of current tab of w
                    return u & "|||" & t
                end if
            end tell
            """
        } else if bundleID == "com.google.Chrome" || bundleID == "org.chromium.Chromium" {
            script = """
            tell application "\(app.localizedName ?? "Google Chrome")"
                if (count of windows) > 0 then
                    set w to front window
                    set u to URL of active tab of w
                    set t to title of active tab of w
                    return u & "|||" & t
                end if
            end tell
            """
        } else {
            script = """
            tell application "\(app.localizedName ?? "")"
                if (count of windows) > 0 then
                    set w to front window
                    set u to URL of active tab of w
                    set t to title of active tab of w
                    return u & "|||" & t
                end if
            end tell
            """
        }

        guard let appleScript = NSAppleScript(source: script) else { return nil }
        var error: NSDictionary?
        let result: NSAppleEventDescriptor
        if Thread.isMainThread {
            result = appleScript.executeAndReturnError(&error)
        } else {
            result = DispatchQueue.main.sync {
                appleScript.executeAndReturnError(&error)
            }
        }

        guard error == nil,
              let text = result.stringValue,
              !text.isEmpty else { return nil }

        let parts = text.components(separatedBy: "|||")
        let urlString = parts.first?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let title = parts.count > 1 ? parts[1].trimmingCharacters(in: .whitespacesAndNewlines) : nil

        let domain: String?
        if let url = URL(string: urlString), let host = url.host {
            domain = host
        } else {
            domain = nil
        }

        return BrowserContext(
            urlString: urlString.isEmpty ? nil : urlString,
            domain: domain,
            title: title,
            sensitivity: .personal
        )
    }

    func currentFinderDirectory() -> FinderDirectoryContext? {
        guard let app = NSWorkspace.shared.frontmostApplication,
              app.bundleIdentifier == "com.apple.finder" else { return nil }

        let script = """
        tell application "Finder"
            if (count of windows) > 0 then
                set targetPath to POSIX path of (target of front window as alias)
                return targetPath
            end if
        end tell
        """
        guard let appleScript = NSAppleScript(source: script) else { return nil }
        var error: NSDictionary?
        let result = appleScript.executeAndReturnError(&error)
        guard error == nil, let path = result.stringValue, !path.isEmpty else { return nil }

        return FinderDirectoryContext(path: path, sensitivity: .personal)
    }

    func currentFinderSelection() -> FinderSelectionContext? {
        guard let app = NSWorkspace.shared.frontmostApplication,
              app.bundleIdentifier == "com.apple.finder" else { return nil }

        let script = """
        tell application "Finder"
            if (count of windows) > 0 then
                set selectedItems to selection
                if (count of selectedItems) = 0 then return ""
                set extList to {}
                repeat with itemRef in selectedItems
                    try
                        set ext to name extension of itemRef
                        if ext is not "" then
                            set end of extList to ext
                        end if
                    end try
                end repeat
                set AppleScript's text item delimiters to ","
                return (count of selectedItems) & "||" & (extList as text)
            end if
        end tell
        """
        guard let appleScript = NSAppleScript(source: script) else { return nil }
        var error: NSDictionary?
        let result = appleScript.executeAndReturnError(&error)
        guard error == nil, let text = result.stringValue, !text.isEmpty else { return nil }

        let parts = text.components(separatedBy: "||")
        let count = Int(parts.first ?? "0") ?? 0
        let exts = parts.count > 1
            ? parts[1].components(separatedBy: ",").map { $0.trimmingCharacters(in: .whitespaces).lowercased() }.filter { !$0.isEmpty }
            : []

        guard count > 0 else { return nil }

        return FinderSelectionContext(fileExtensions: exts, count: count, sensitivity: .personal)
    }

    /// 对图片条目执行 OCR，返回识别文字（供搜索索引使用，不参与推荐排序）
    nonisolated static func recognizeText(in cgImage: CGImage) -> String? {
        let request = VNRecognizeTextRequest()
        request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en"]
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        do {
            try handler.perform([request])
        } catch {
            return nil
        }

        let texts = request.results?
            .compactMap { $0.topCandidates(1).first?.string }
            .filter { !$0.isEmpty } ?? []

        return texts.isEmpty ? nil : texts.joined(separator: " ")
    }

    private mutating func trimEventLog(maxEvents: Int = 200) {
        if eventLog.count > maxEvents {
            eventLog.removeFirst(eventLog.count - maxEvents)
        }
    }

    private func recentEvents(since anchor: Date, within interval: TimeInterval = 600) -> [ContextEvent] {
        let start = max(anchor.addingTimeInterval(-interval), Date(timeIntervalSince1970: 0))
        return eventLog.filter { $0.timestamp >= start && $0.timestamp <= anchor }
    }
}
