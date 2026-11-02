# -*- coding: utf-8 -*-
"""R557 / 632：估高度的取样在同一个视图生命周期内只取一次（乘数 4→1）。"""
import io

p = 'Sources/ClipboardHistoryApp/Views/DetailView.swift'
s = io.open(p, encoding='utf-8').read()

# 1) 取样值类型 + 带缓存的入口
old_entry = r'''    static func preferredHeight(for url: URL, availableWidth: CGFloat) -> CGFloat {
        let fileExtension = url.pathExtension.lowercased()

        if FileTypeSupport.textExtensions.contains(fileExtension),
           let textHeight = preferredTextHeight(for: url, availableWidth: availableWidth) {
            return clamp(textHeight)
        }'''
assert s.count(old_entry) == 1, s.count(old_entry)
new_entry = r'''    /// 一次估高度所要的文本取样。**只带字节数与正文，不带路径**（与计数器同一口径）。
    /// `fileDigest` 是 `url.path` 的整数哈希：`ForEach(id: \.offset)` 让 `CollapsibleFilePreview`
    /// 的 `@State` 会在同一行的 URL 换掉后活下来，所以复用之前必须对得上号。
    struct TextSample {
        let fileDigest: Int
        let text: String
        let sampleBytes: Int
    }

    static func preferredHeight(for url: URL, availableWidth: CGFloat) -> CGFloat {
        var unused: TextSample? = nil
        return preferredHeight(for: url, availableWidth: availableWidth, textSample: &unused)
    }

    /// R557 / BACKLOG 632：`textSample` 是**视图作用域的一次性取样缓存**。
    /// 旧形状里每调用一次就重新 `FileHandle` 开一次同一份文件，而调用点是"宽度每变一次就来一趟"
    /// —— 现读旧值：展开一条文本 + 拖窗三次 = 同一份文件被开 **4** 次（加预览那一路共 5 次）。
    /// 现在同一次挂载里只开一次，后面几次宽度变化复用手里那份（算式逐字不变 ⇒ 高度不变）。
    static func preferredHeight(for url: URL,
                                availableWidth: CGFloat,
                                textSample: inout TextSample?) -> CGFloat {
        let fileExtension = url.pathExtension.lowercased()

        if FileTypeSupport.textExtensions.contains(fileExtension),
           let textHeight = preferredTextHeight(for: url, availableWidth: availableWidth,
                                                cached: &textSample) {
            return clamp(textHeight)
        }'''
s = s.replace(old_entry, new_entry, 1)

# 2) 估高度：命中缓存就不开文件
old_body = r'''    private static func preferredTextHeight(for url: URL, availableWidth: CGFloat) -> CGFloat? {
        ProtectedFileAccessLedger.note(.layoutTextSample, for: url)
        guard let handle = try? FileHandle(forReadingFrom: url) else { return nil }
        defer { try? handle.close() }

        guard let data = try? handle.read(upToCount: textSampleLimit),
              !data.isEmpty,
              let text = String(data: data, encoding: .utf8) else {
            return nil
        }
'''
assert s.count(old_body) == 1, s.count(old_body)
new_body = r'''    private static func preferredTextHeight(for url: URL,
                                            availableWidth: CGFloat,
                                            cached: inout TextSample?) -> CGFloat? {
        let digest = url.path.hashValue
        // 命中同一次挂载里的那份取样 ⇒ **一次文件都不开**。
        // 对不上号（换了行、换了文件）就重新取；取到之后写回，供后面每次宽度变化复用。
        let cachedText: String
        let cachedBytes: Int
        if let cached, cached.fileDigest == digest {
            cachedText = cached.text
            cachedBytes = cached.sampleBytes
        } else {
            ProtectedFileAccessLedger.note(.layoutTextSample, for: url)
            guard let handle = try? FileHandle(forReadingFrom: url) else { return nil }
            defer { try? handle.close() }

            guard let data = try? handle.read(upToCount: textSampleLimit),
                  !data.isEmpty,
                  let text = String(data: data, encoding: .utf8) else {
                return nil
            }
            cachedText = text
            cachedBytes = data.count
            cached = TextSample(fileDigest: digest, text: text, sampleBytes: data.count)
        }
        let text = cachedText
        let dataCount = cachedBytes
'''
s = s.replace(old_body, new_body, 1)

old_tail = r'''        let sampleCoverage: Double
        if data.count >= textSampleLimit {
            ProtectedFileAccessLedger.note(.layoutFileSizeStat, for: url)
            let fileSize = (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? NSNumber)?.doubleValue ?? Double(data.count)
            sampleCoverage = min(max(fileSize / Double(max(data.count, 1)), 1), 3)
        } else {
            sampleCoverage = 1
        }'''
assert s.count(old_tail) == 1, s.count(old_tail)
new_tail = r'''        let sampleCoverage: Double
        if dataCount >= textSampleLimit {
            ProtectedFileAccessLedger.note(.layoutFileSizeStat, for: url)
            let fileSize = (try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? NSNumber)?.doubleValue ?? Double(dataCount)
            sampleCoverage = min(max(fileSize / Double(max(dataCount, 1)), 1), 3)
        } else {
            sampleCoverage = 1
        }'''
s = s.replace(old_tail, new_tail, 1)

# 3) 视图作用域的 @State
old_state = r'''    @State private var targetHeight = MultiFilePreviewLayout.fallbackPreviewHeight'''
assert s.count(old_state) == 1
s = s.replace(old_state, r'''    @State private var targetHeight = MultiFilePreviewLayout.fallbackPreviewHeight
    /// R557 / 632：这一行本次挂载里取到的文本取样（宽度每变一次都复用同一份，不再重开文件）。
    @State private var previewTextSample: MultiFilePreviewLayout.TextSample?''', 1)

old_recalc = r'''        targetHeight = MultiFilePreviewLayout.preferredHeight(for: url, availableWidth: availableWidth)'''
assert s.count(old_recalc) == 1
s = s.replace(old_recalc, r'''        var sample = previewTextSample
        targetHeight = MultiFilePreviewLayout.preferredHeight(for: url,
                                                              availableWidth: availableWidth,
                                                              textSample: &sample)
        previewTextSample = sample''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('memo wired')
