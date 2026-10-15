import Foundation

/// 捕获卷读数的**第二条通道**（R64 / BACKLOG 96）。
///
/// 为什么要有这个文件：R63/R64 量到一个事实 —— `swift test` 的 stdout **会成块丢**，
/// 而且两台机器都丢。R64 把形状量清楚了（同一批代码本机两遍，逐行 `grep` 比对）：
/// 捕获卷那 488 行读数里 stdout 分别少了 **324 行**与 **238 行**，
/// 少的都是**连续大块**（第一遍 1 块、第二遍 3 块），切点落在**行中间**
/// —— stdout 停在 `…bottomI`，下一行直接是 `Test Case …`。
/// 五条判据自写的 marker 两遍**全丢**，而用例的 `passed` 结论行一条没少、作业 0 退出。
/// （R63 账本里"按条随机丢"那句是把机制说过头了，本轮更正，见 BACKLOG 96；
/// 结论不受影响：**丢掉的里面就是判据自己写的结论**，而 runner 上同样丢过。）
/// 动效卷在 R56 / BACKLOG 79 已经为同一件事付过学费并修好了（`MotionFilmstripTests.emit`）：
/// 那次是"测试全过、stderr 正常、胶片写出来了，而 print 的读数一行不剩" ——
/// **FileManager 那条路活着，stdout 那条死了**。捕获卷照抄同一个形状，不再重新发明。
///
/// 规矩由 `UICaptureTests.testCaptureReadingsUseTheFileChannel` 钉住：
/// `UICaptureHarness.swift` 里**一行 `print` 都不许有**，读数一律走 `emit`。
/// 之所以把通道实现单独放一个文件：那样这条守卫的规则可以是绝对的
/// （"这个文件里 `print` 的出现次数 = 0"），不需要给"emit 自己那一行"开白名单 ——
/// 而任何白名单都是下一次绕过去的入口（账本里 R55 的 M276 就是这个形状）。
enum CaptureReadings {
    /// 读数与帧住在同一个目录里（`CLIPBOARD_HISTORY_UI_SHOTS`），
    /// 这样"这一天的帧"与"这一天说过的话"是同一批证据，不会一份在 CI 产物里、另一份在别处。
    /// 环境变量没给时退回 `/tmp/capture-readings` —— **通道不能因为没设变量就不存在**，
    /// 否则守卫在自己的进程里就永远测不到真路径。
    static var readingsURL: URL {
        let configured = ProcessInfo.processInfo.environment["CLIPBOARD_HISTORY_UI_SHOTS"] ?? ""
        let base = configured.isEmpty ? "/tmp/capture-readings" : configured
        let url = URL(fileURLWithPath: base, isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url.appendingPathComponent("capture-readings.log")
    }

    /// 每个进程第一次写要**整份重写**：上一遍的读数冒充这一遍，比没有读数更坏
    /// （`SPARSE_EXEMPTION_OK` 会是从昨天带上来的）。这条与动效卷同一句话。
    nonisolated(unsafe) static var opened = false

    /// 通道自己坏了不许把判据变红（那是拿环境问题判产品），但必须**被看见**。
    /// 这一行为什么故意不叫 `CAPTURE_*`：它不是一条读数，而是"文件通道坏了"这件事本身，
    /// 且只能走 stdout；带上前缀就会被守卫的扫描判成"有条读数没进文件"。
    private static func channelBroken(_ error: Error) {
        FileHandle.standardError.write(("CAPTURE_READINGS_CHANNEL_BROKEN \(error.localizedDescription)\n").data(using: .utf8)!)
    }

    /// 打一行读数，**并且**把它记进文件通道。
    static func emit(_ line: String) {
        print(line)
        let payload = (line + "\n").data(using: .utf8) ?? Data()
        let url = readingsURL
        do {
            if !opened {
                opened = true
                try payload.write(to: url)
                return
            }
            let handle = try FileHandle(forWritingTo: url)
            handle.seekToEndOfFile()
            handle.write(payload)
            try? handle.close()
        } catch {
            channelBroken(error)
        }
    }
}
