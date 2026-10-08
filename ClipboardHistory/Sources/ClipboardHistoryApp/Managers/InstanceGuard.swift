import AppKit

/// 单实例守卫。
///
/// 为什么需要：本应用没有任何"已经有一份在跑"的检查，而两个实例会各自轮询剪贴板、
/// 各自把**整库**写回 `history.json` —— 后写的那一次会把先写的记录整片盖掉。
/// 这与审计 P-06 是同一类数据丢失，只是触发方式从"存档损坏"换成"再开一次"。
/// 而且这条路对本项目作者是日常路径：`make run` 用的就是 `open -n`（强制新实例）。
///
/// 结构：判定逻辑是纯函数（可测），向系统要数据的那一小段单独放着（不可测，也不含判断）。
enum InstanceGuard {
    struct RunningInstance: Equatable {
        let bundleIdentifier: String?
        let processIdentifier: pid_t
        let isTerminated: Bool
        /// NSRunningApplication.isTerminated：进程已经退出，只是 LaunchServices 还没回收它的记录。
    }

    /// 找出"同一个 bundle 的另一个还活着的实例"的 pid；没有则 nil。
    static func conflictingPID(
        among instances: [RunningInstance],
        mine: pid_t,
        bundleIdentifier: String?
    ) -> pid_t? {
        // 拿不到 bundle id 就不做判断：宁可放行，也不要误杀正在开发中的裸可执行文件
        // （`swift run` 之类没有 bundle 的场景）。
        guard let bundleIdentifier else { return nil }
        return instances.first {
            $0.bundleIdentifier == bundleIdentifier
                && $0.processIdentifier != mine
                && !$0.isTerminated
        }?.processIdentifier
    }

    static func conflictingPID(
        excluding mine: pid_t = ProcessInfo.processInfo.processIdentifier,
        bundleIdentifier: String? = Bundle.main.bundleIdentifier
    ) -> pid_t? {
        conflictingPID(
            among: NSWorkspace.shared.runningApplications.map {
                RunningInstance(
                    bundleIdentifier: $0.bundleIdentifier,
                    processIdentifier: $0.processIdentifier,
                    isTerminated: $0.isTerminated
                )
            },
            mine: mine,
            bundleIdentifier: bundleIdentifier
        )
    }
}
