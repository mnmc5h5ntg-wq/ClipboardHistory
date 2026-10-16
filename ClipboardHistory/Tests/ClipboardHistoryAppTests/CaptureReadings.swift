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

    /// 每个进程对**每一份**读数文件第一次写要整份重写：上一遍的读数冒充这一遍，比没有读数更坏
    /// （`SPARSE_EXEMPTION_OK` 会是从昨天带上来的）。这条与动效卷同一句话。
    /// **按 URL 记**而不是记一个布尔：并发判据要拿一份临时文件去锤同一段代码，
    /// 共享布尔会让"临时文件的第一行"以为已经开过卷，于是去 open 一份不存在的文件。
    /// **只能在 `lock` 里读写**（R81 / BACKLOG 112）：它原来没有锁，两个线程可以同时看到"没开过"，
    /// 于是两边都做整份重写 —— 后写的那一份把前一份**整卷抹掉**。
    nonisolated(unsafe) private static var openedURLs = Set<URL>()

    /// 一把进程内的锁。为什么必须它：SwiftPM 从 Swift 6 起**并行**跑用例，
    /// 而 R79 的 CI 日志里抓到过实锤 —— 我的 `QUICKPICK_FOCUS 暗 …` 那一行被**缝进了另一条判据的行**：
    /// `MENUBAR_FITTING 声明宽=320 hosting.fittingSize=0.08px 宽=87.0pt(聚焦 12…98) …`
    /// 前半是别人的、后半是我的，而 MENUBAR_FITTING 自己的结论被吃掉。
    /// 坏在两个地方：`print(line)` 把"内容"与"换行"分两次 write（两个线程可以在两次之间插进来），
    /// 文件通道的 `seekToEndOfFile()` + `write()` 也不是一个原子动作（两个线程可以 seek 到同一个偏移）。
    /// ⇒ 现在**一整行一次 write**，两条腿都在锁里。
    private static let lock = NSLock()

    /// 一条读数写两遍：stdout（给人看现场）与文件（给闸门兜底）。**两条腿都必须整行原子。**
    static func emit(_ line: String) {
        writeStdoutLine(line)
        let url = readingsURL
        lock.lock()
        defer { lock.unlock() }
        do {
            try appendLocked(line, to: url)
        } catch {
            channelBroken(error)
        }
    }

    /// 同一套两条腿，但写到**指定**文件。
    ///
    /// 为什么要这个重载而不是让调用方共用 `emit(_:)`：`readingsURL` 是按
    /// `CLIPBOARD_HISTORY_UI_SHOTS` 推导的，而 CI 的捕获卷与在屏卷用的是同一个目录 ——
    /// 在屏卷第一次写会按"整份重写"的规矩把**捕获卷那份读数**抹掉（那条规矩本身是对的：
    /// 上一遍的读数冒充这一遍，比没有读数更坏）。
    /// 为什么要复用这一套而不是另写一份：锁、整行一次 write、第一次整份重写这三件事
    /// 每一份读数通道都需要，抄一遍就会漏一条（R79 那两条读数缝在一起就是这么来的）。
    static func emit(_ line: String, to url: URL) {
        writeStdoutLine(line)
        lock.lock()
        defer { lock.unlock() }
        do {
            try appendLocked(line, to: url)
        } catch {
            channelBroken(error)
        }
    }

    /// stdout 那一条腿：一次 `write` 一整行（含换行）。
    /// 为什么不再用 `print`：`print` 走 stdio，会把它拆成"串"与"换行"两次写 ——
    /// 那正是 R79 那两条读数缝在一起的缝。
    private static func writeStdoutLine(_ line: String) {
        guard let payload = (line + "\n").data(using: .utf8) else { return }
        FileHandle.standardOutput.write(payload)
    }

    /// 文件那一条腿的**实现**（调用方必须已经持锁）。单独抽出来是为了并发判据能拿一个
    /// **临时文件**去锤它 —— 否则锤击测试自己会往真正的读数卷里灌上千行垃圾，
    /// 而那条卷正是闸门要读的东西（"测试把被测对象弄脏了"那一族）。
    static func appendLocked(_ line: String, to url: URL) throws {
        let payload = (line + "\n").data(using: .utf8) ?? Data()
        if !openedURLs.contains(url) {
            openedURLs.insert(url)
            try payload.write(to: url)
            return
        }
        let handle = try FileHandle(forWritingTo: url)
        defer { try? handle.close() }
        handle.seekToEndOfFile()
        handle.write(payload)
    }

    /// 并发锤击判据用的入口：**带锁**写一行到指定文件（与 `emit` 的文件那一条腿同一段代码）。
    static func appendForced(_ line: String, to url: URL) {
        lock.lock()
        defer { lock.unlock() }
        do {
            try appendLocked(line, to: url)
        } catch {
            channelBroken(error)
        }
    }

    /// 通道自己坏了不许把判据变红（那是拿环境问题判产品），但必须**被看见**。
    /// 这一行为什么故意不叫 `CAPTURE_*`：它不是一条读数，而是"文件通道坏了"这件事本身，
    /// 且只能走 stderr；带上前缀就会被守卫的扫描判成"有条读数没进文件"。
    private static func channelBroken(_ error: Error) {
        FileHandle.standardError.write(("CAPTURE_READINGS_CHANNEL_BROKEN \(error.localizedDescription)\n").data(using: .utf8)!)
    }
}
