import Foundation

/// R555 / BACKLOG 632：**受保护目录的读取计数器**。
///
/// 为什么要有它：「时间剪史想访问桌面文件夹」反复弹的根因是**有人在用户还没看到那一行之前就去拿字节**。
/// 这件事原来只能靠日志正则去猜，而日志是一条会坏的通道：没打印 ≠ 没发生
/// （账本里 R470/R536 同一族）。所以判据改读**数出来的次数**。
///
/// **隐私红线**：这里只存 `url.path` 的**整数哈希**与第几格，**永不存路径、文件名、URL 本身**，
/// 也永不落盘。判据要证明某个文件被碰过，就拿同一个 URL 现算哈希去对号 —— 反向是推不出路径的。
///
/// **有界**：事件环固定 1024 格，满了覆盖最旧的一条。产品可以一直预览文件而不长出一条内存尾巴
/// （无界字典就是泄漏）；判据只看刚发生的那几次。
///
/// **没有"归零"这一格**：判据并行跑（SwiftPM），任何全局 `reset()` 都会把别人正在数的东西抹掉，
/// 于是"0 次"这句话变成 races 的产物。每条判据数的是**自己那个文件的哈希**（夹具各占一个临时目录，
/// 哈希互不相同），天生互不串味 —— 不需要归零，也不许有人加一个归零来凑读数。
///
/// 计数点就是 632 实读出来的四格：
/// - `previewWholeFile`：`MediaLoader` 的图片预览 `Data(contentsOf:)` 整文件读；
/// - `previewTextSample`：`MediaLoader` 的文本预览 `FileHandle` 取样；
/// - `layoutTextSample`：`DetailView` **为了估高度**又开一次同一份文件；
/// - `layoutFileSizeStat`：`DetailView` 为了估高度再 `attributesOfItem` 探一次路径。
///
/// 采集路径（`ClipboardIntake`）本来一格都不该按到 —— 那是 632 的判据，也是刀 M1436 的位置。
enum ProtectedFileAccessLedger {
    enum Site: String, CaseIterable {
        case previewWholeFile
        case previewTextSample
        case layoutTextSample
        case layoutFileSizeStat
    }

    /// 一条事件：哪个文件的哪一格被碰了一次（文件只以哈希身份存在）。
    struct Event: Hashable { let fileDigest: Int; let site: Site }

    private static let capacity = 1_024
    private static let lock = NSLock()
    nonisolated(unsafe) private static var events: [Event] = []

    /// 在**真正读之前**记一格：读失败也要计数（"试图访问受保护目录"这件事与成败无关，
    /// 静默的 open 失败正是 632 要抓的形状）。
    static func note(_ site: Site, for url: URL) {
        let event = Event(fileDigest: url.path.hashValue, site: site)
        lock.lock()
        if events.count >= capacity { events.removeFirst() }
        events.append(event)
        lock.unlock()
    }

    static func count(_ site: Site, for url: URL) -> Int {
        let digest = url.path.hashValue
        lock.lock()
        defer { lock.unlock() }
        return events.filter { $0.fileDigest == digest && $0.site == site }.count
    }

    /// 这个文件在这一刻总共被碰了几次（四格求和）—— 「选中/预览之前不发生读取」判的就是它为 0。
    static func count(for url: URL) -> Int {
        let digest = url.path.hashValue
        lock.lock()
        defer { lock.unlock() }
        return events.reduce(0) { $0 + ($1.fileDigest == digest ? 1 : 0) }
    }

    /// 一行读数：**只有整数与格子名**，没有路径。走 XCTAttachment 通道进账。
    static func reading(_ prefix: String, for url: URL) -> String {
        let parts = Site.allCases.map { "\($0.rawValue)=\(count($0, for: url))" }
        return ([prefix, "total=\(count(for: url))"] + parts).joined(separator: " ")
    }
}
