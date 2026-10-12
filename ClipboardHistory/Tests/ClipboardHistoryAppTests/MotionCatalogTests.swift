// 不覆盖管线：本文件钉的是动效目录的**参数、退化表与降级开关**（纯值 + 源码扫描）。
// 「动画真的发生了」由 `MotionFilmstripTests` 的逐帧判据负责（那是能被打红的那一层）——
// 参数对了但没接上线，胶片会照样报「瞬间跳变」。本轮就是这样：纯值 10/10 绿的同时，
// 五条像素场景全红（审计报告 §13.1）。
import SwiftUI
import XCTest
@testable import ClipboardHistoryApp

/// 动效审计 §4 / M11：时长、曲线、减弱动态时的退化，三张表的判据。
///
/// 这一版比第一版多钉了三件第一版量不到的事，都来自报告的 MC-1 / MC-2 / MC-5：
/// 上限要管**真正交出去的那条曲线**而不是常数表；`dampingFraction` 的语义要写对；
/// 目录里不许留没人消费的档位。
@MainActor
final class MotionCatalogTests: XCTestCase {
    override func tearDown() {
        MotionCatalog.overrideReduceMotion = nil
        MotionCatalog.animationsEnabled = true
        super.tearDown()
    }

    // MARK: - 上限管的是产物，不是常数表（MC-2）

    func testEveryRoleStaysUnderTheCeiling() {
        for role in MotionCatalog.Role.allCases {
            let seconds = MotionCatalog.duration(for: role)
            XCTAssertGreaterThan(seconds, 0, "\(role.rawValue) 没有时长")
            if MotionCatalog.isAmbient(role) {
                XCTAssertGreaterThanOrEqual(seconds, MotionCatalog.minimumAmbientDuration,
                                            "\(role.rawValue) 是常驻循环却只有 \(seconds)s：那不是扫光是频闪")
                continue
            }
            XCTAssertLessThanOrEqual(seconds, MotionCatalog.maximumDuration,
                                     "\(role.rawValue) 是 \(seconds)s，超过 \(MotionCatalog.maximumDuration)s 上限：那不是质感是延迟")
        }
    }

    /// 例外必须**只有一个入口**，否则"上限"就变成了一句可以随便绕过去的话。
    ///
    /// 这条断言的三个方向都是必须的：① 例外集合就是 `skeletonSweep` 那一档（别人想挤进来要红）；
    /// ② 例外档必须是**匀速**（循环里带 ease 会被看成每圈都在起步）；
    /// ③ 非例外档**不许**拿到匀速以外的东西？—— 不，那条反过来不成立（进场/退场本来就是控制点），
    /// 所以这里只查"例外 ⇒ 匀速"，反过来不查，免得钉出一条不存在的契约。
    func testAmbientExceptionIsExactlyOneRoleAndIsLinear() {
        let ambient = MotionCatalog.Role.allCases.filter(MotionCatalog.isAmbient)
        XCTAssertEqual(ambient, [.skeletonSweep],
                       "常驻循环档现在不止 `skeletonSweep`：250ms 上限的例外被扩大了，得先看这份例外表对不对")
        for role in ambient {
            XCTAssertEqual(MotionCatalog.curve(for: role, reduceMotion: false).kind,
                           .timingCurve(MotionCatalog.linearControlPoints),
                           "\(role.rawValue) 不是匀速")
            XCTAssertEqual(MotionCatalog.curve(for: role, reduceMotion: true).kind,
                           .timingCurve(MotionCatalog.linearControlPoints),
                           "减弱动态时这一档的**曲线**不变；停不停由 `SkeletonMotion.sweepIsRunning` 决定")
        }
    }

    /// 常驻动画只有**一个驱动**，而且它不是渲染树那条路。
    ///
    /// 报告 §5 红线 2 的原话是"仓库现在一个 `repeatForever` 都没有，这是新增的第一条常驻动画风险"。
    /// 两个方向都钉：
    /// - `repeatForever` 出现 **0** 次 —— 那条路**没被量过**（`SkeletonShimmer.swift` 文件头记着
    ///   取证过程中那三个 0.0000，以及其中一个其实是对比度造成的误判），
    ///   所以本仓库的常驻动画一律走"每拍把相位写回视图状态"这条被量过的路；
    /// - 那个时钟只有 `SkeletonShimmer.swift` 一个文件里有（标记用 `Timer.publish`：
    ///   `HistoryStore` 里那两处 `Timer.scheduledTimer` 是采集轮询，不是动画，不该被这条管住）。
    /// 第二条是单调量：再冒出一个常驻动画驱动，就得先在这里说明它为什么也该被允许。
    func testAmbientLoopIsSingleton() throws {
        var repeatForever: [String] = []
        var sweepDrivers: [String] = []
        for directory in ["Views", "Managers", "Utilities", "Intelligence", "Models"] {
            for (name, source) in try productSources(in: directory) {
                let code = codeOnly(source)
                if code.contains("repeatForever") { repeatForever.append(name) }
                if code.contains("Timer.publish") { sweepDrivers.append(name) }
            }
        }
        XCTAssertTrue(repeatForever.isEmpty, "渲染树循环又出现了：\(repeatForever)")
        XCTAssertEqual(sweepDrivers, ["SkeletonShimmer.swift"],
                       "常驻动画驱动不止一处：\(sweepDrivers)")
    }

    /// 第一版的守卫只检查 `duration(for:)` 那张表，而 `animation(for:)` 在位移档里
    /// **根本不用它**（写死 `response: 0.32`）—— 于是"没有一档超过 0.25s"为真，
    /// 而声明 150ms 的滑入实际跑 200ms。这条断言把那个缺口堵上：
    /// 交给系统的 `Curve.seconds` 必须**等于**时长表，谁也不许自己另带一个数。
    func testCurveSecondsComeFromTheDurationTable() {
        for role in MotionCatalog.Role.allCases {
            for reduceMotion in [false, true] {
                let curve = MotionCatalog.curve(for: role, reduceMotion: reduceMotion)
                XCTAssertEqual(curve.seconds, MotionCatalog.duration(for: role),
                               "\(role.rawValue)（reduce=\(reduceMotion)）的曲线自带时长：上限表管不到它")
                if MotionCatalog.isAmbient(role) {
                    XCTAssertGreaterThanOrEqual(curve.seconds, MotionCatalog.minimumAmbientDuration,
                                                "\(role.rawValue) 真正交出去的是 \(curve.seconds)s，常驻循环不该比这更快")
                } else {
                    XCTAssertLessThanOrEqual(curve.seconds, MotionCatalog.maximumDuration,
                                             "\(role.rawValue) 真正交出去的是 \(curve.seconds)s，超上限")
                }
            }
        }
    }

    /// 反馈类比过渡类快：状态回执要「快得像反馈」，内容换页可以「慢得像过渡」。
    func testFeedbackRolesAreFasterThanContentRoles() {
        XCTAssertLessThan(MotionCatalog.duration(for: .hover), MotionCatalog.duration(for: .contentFade))
        XCTAssertLessThan(MotionCatalog.duration(for: .bannerOut), MotionCatalog.duration(for: .bannerIn))
    }

    /// 进场不许带 ease-in 段（M17）。第一版所有纯淡入档给的是 `.easeInOut` —— 前半段就是
    /// ease-in，而 Emil 的原话是 "Never `ease-in` on UI"、"`ease-out` at 200ms *feels* faster"。
    /// 这条断言的是**控制点本身**，因为 `Animation` 读不回来。
    func testEntranceAndExitUseTheirOwnCurves() {
        XCTAssertEqual(MotionCatalog.curve(for: .contentFade, reduceMotion: false).kind,
                       .timingCurve(MotionCatalog.entranceControlPoints))
        XCTAssertEqual(MotionCatalog.curve(for: .bannerIn, reduceMotion: true).kind,
                       .timingCurve(MotionCatalog.entranceControlPoints))
        XCTAssertEqual(MotionCatalog.curve(for: .bannerOut, reduceMotion: false).kind,
                       .timingCurve(MotionCatalog.exitControlPoints),
                       "退场用进场曲线 = 走的时候先慢后快，视觉上像被拽走")
        XCTAssertLessThan(MotionCatalog.exitControlPoints[1], MotionCatalog.exitControlPoints[3],
                          "exit 曲线 (0.2, 0, 1, 0.9) 的第二个数该小于第四个（先快后慢的收尾）")
    }

    /// 没有一档过冲（MC-1 + MC-3 + WWDC18「默认从 100% damping 开始调弹性」）。
    /// 第一版有两处：`defaultDamping = 0.86` 被注释成"不过冲"（错的，`< 1` 就是欠阻尼、
    /// 必有过冲，仓库自己在 `FilterPillMotion` 里写了正确定义），以及 `emphasis` 单独给 0.62。
    /// 现在"弹一下"交给 macOS 14+ 的 `symbolEffect(.bounce)`，几何过冲一个都不留。
    func testNothingOvershoots() {
        var springRoles: [MotionCatalog.Role] = []
        for role in MotionCatalog.Role.allCases {
            for reduceMotion in [false, true] {
                if case .spring(let damping) = MotionCatalog.curve(for: role, reduceMotion: reduceMotion).kind {
                    XCTAssertEqual(damping, MotionCatalog.criticalDamping,
                                   "\(role.rawValue)：过冲是 1.0 以外的一切，而这里给了 \(damping)")
                    if !reduceMotion { springRoles.append(role) }
                }
            }
        }
        // 阳性对照：确实有档位走弹簧，否则上面那个循环是在扫空集。
        XCTAssertTrue(springRoles.contains(.bannerIn),
                      "bannerIn 是位移档，本该走弹簧：对照失效，上面的循环没有东西可查")
    }

    // MARK: - 减弱动态：替换，不是关掉

    /// 会滑入的那一档，在减弱动态时必须退化成淡入而不是消失。
    func testReduceMotionReplacesSlidesWithFadesInsteadOfRemovingMotion() {
        for role in [MotionCatalog.Role.bannerIn] {
            let open = MotionCatalog.shape(for: role, reduceMotion: false)
            let reduced = MotionCatalog.shape(for: role, reduceMotion: true)
            XCTAssertNotEqual(open.slides, .none, "\(role.rawValue)：前提没了，正常态本来就该有位移")
            XCTAssertEqual(reduced.slides, .none,
                           "\(role.rawValue)：减弱动态时还在滑 —— 大面积平移正是前庭触发源")
        }
    }

    /// 反 Pearcleaner：降级**不许**把时长归零。同类里常见的写法是
    /// `duration: animationEnabled ? 0.35 : 0`，那是"关掉"而不是"替换"，
    /// HIG / MDN / Emil 三个口径都反对。这一条是整张表上最容易"顺手改错"的地方。
    func testReduceMotionNeverZeroesTheDuration() {
        for role in MotionCatalog.Role.allCases {
            XCTAssertGreaterThan(MotionCatalog.curve(for: role, reduceMotion: true).seconds, 0,
                                 "\(role.rawValue)：减弱动态时时长归零 = 界面变成无反馈，那是另一种缺陷")
        }
    }

    func testNothingScalesUnderReduceMotion() {
        for role in MotionCatalog.Role.allCases {
            XCTAssertFalse(MotionCatalog.shape(for: role, reduceMotion: true).scales,
                           "\(role.rawValue)：减弱动态时还在缩放")
        }
        // 阳性对照：正常态里确实有档位是缩放的。
        XCTAssertTrue(MotionCatalog.shape(for: .dropTarget, reduceMotion: false).scales)
    }

    /// 反向钉住「哪些角色本来就不该动位置」，免得有人给 hover/selection 加滑入、
    /// 而上面那条循环一起变红时说不清是谁错了。
    func testRolesThatMustNotMovePositions() {
        for role in [MotionCatalog.Role.hover, .selection, .contentFade, .emphasis, .bannerOut, .dropTarget] {
            XCTAssertEqual(MotionCatalog.shape(for: role, reduceMotion: false).slides, .none,
                           "\(role.rawValue) 不该有位移")
        }
    }

    func testBannerOnlyMovesOnTheWayIn() {
        // 退场不滑：横幅走的时候不该再占一次注意力，也不该把下方内容「拽」一下。
        XCTAssertEqual(MotionCatalog.shape(for: .bannerIn, reduceMotion: false).slides, .top)
        XCTAssertEqual(MotionCatalog.shape(for: .bannerOut, reduceMotion: false).slides, .none)
    }

    func testAnimationFollowsTheCurve() {
        XCTAssertEqual(MotionCatalog.animation(for: .hover, reduceMotion: true),
                       MotionCatalog.animation(for: .hover, reduceMotion: false),
                       "hover 本来就没有位移，减少动态时曲线不该变")
        XCTAssertNotEqual(MotionCatalog.animation(for: .bannerIn, reduceMotion: true),
                          MotionCatalog.animation(for: .bannerIn, reduceMotion: false),
                          "bannerIn 从滑入退化成淡入，曲线必须跟着变")
    }

    // MARK: - 目录卫生

    /// 目录里不留没人消费的档位。已经删掉过三组，每组各有一次实测撑着：
    /// `detailSwap`（换页淡入 = 每次换选一帧空白）、
    /// `listReflow`/`rowInsertion`/`rowRemoval`（`List` 的行过渡跑不出来）、
    /// `panelIn`/`panelOut`（热键呼出路径按规范就不该有动画）。
    /// 留着它们的后果不是多几行，是"参数还在、测试还在断言、界面已经不动了"。
    func testEveryRoleHasAConsumer() throws {
        var text = ""
        for directory in ["Views", "Managers", "Utilities", "Intelligence", "Models"] {
            text += try productSources(in: directory)
                .filter { $0.0 != "MotionCatalog.swift" }
                .map(\.1).joined(separator: "\n")
        }
        XCTAssertFalse(text.isEmpty, "一份产品源码都没读到：这条守卫会静默变成空跑")
        for role in MotionCatalog.Role.allCases {
            let used = text.contains("for: .\(role.rawValue)")
                || text.contains("insertion: .\(role.rawValue)")
                || text.contains("removal: .\(role.rawValue)")
            XCTAssertTrue(used, "\(role.rawValue) 没有任何消费者：接上它，或者从目录里删掉")
        }
    }

    /// 目录里也不留没人读的参数。`Role` 那一半由 `testEveryRoleHasAConsumer` 管，
    /// 这条管常数：一个只有声明、没有任何地方读的 `static let`，就是"看着像有人用、
    /// 其实没人用"的说法 —— 和被删掉的 `emphasisScale` / `slideOffset` 同一类（报告 MC-5）。
    /// 读的人可以是产品代码，也可以是判据：`maximumDuration` 就是后者
    /// （它是预算，由 `testEveryRoleStaysUnderTheCeiling` 执行），所以两边都算。
    func testEveryCatalogConstantIsRead() throws {
        let catalog = codeOnly(try productSource(named: "Utilities/MotionCatalog.swift"))
        var text = ""
        for directory in ["Views", "Managers", "Utilities", "Intelligence", "Models"] {
            text += try productSources(in: directory).map(\.1).joined(separator: "\n")
        }
        let testsDirectory = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for name in try FileManager.default.contentsOfDirectory(atPath: testsDirectory.path) where name.hasSuffix(".swift") {
            text += (try? String(contentsOf: testsDirectory.appendingPathComponent(name), encoding: .utf8)) ?? ""
        }
        for name in catalog.components(separatedBy: "\n").compactMap({ line -> String? in
            let parts = line.trimmingCharacters(in: .whitespaces).split(separator: " ", omittingEmptySubsequences: true)
            guard parts.count >= 3, parts[0] == "static", parts[1] == "let" else { return nil }
            return String(parts[2].split(separator: ":").first ?? Substring(""))
        }) {
            let reads = text.components(separatedBy: name).count - 1
            XCTAssertGreaterThanOrEqual(reads, 2,
                                        "目录里的 `\(name)` 只有声明没有读取：要么接上，要么删掉")
        }
    }

    /// 胶片探针的 A/B 开关必须**默认开**。它是个全局可变量，产品路径不碰它 ——
    /// 万一有人图省事在启动时关掉它，所有动效会静默变成零时长，
    /// 而本文件那几条纯值断言照样全绿。
    func testProbeSwitchIsOnByDefault() {
        XCTAssertTrue(MotionCatalog.animationsEnabled, "探针开关被留在关闭状态：动效全没了，纯值判据却还是绿的")
    }

    /// 落点光晕（M8 后半句）的门控与**唯一消费者**。
    ///
    /// 三个方向都要钉，少一个都会变成"参数在表里、界面上没有"：
    /// ① 只有 `dropTarget` 会发光 —— 别的档悄悄加上 `glows` 就是往高频路径上加模糊；
    /// ② 减弱动态时收掉（HIG 的 "avoid animating into and out of blurs"）；
    /// ③ 侧栏确实读它（MC-12 那一族：纯值全对、没人调用）。
    func testDropTargetGlowIsGatedAndWired() throws {
        XCTAssertTrue(MotionCatalog.glows(for: .dropTarget, reduceMotion: false))
        XCTAssertFalse(MotionCatalog.glows(for: .dropTarget, reduceMotion: true),
                       "减弱动态时还在淡入一层模糊")
        for role in MotionCatalog.Role.allCases where role != .dropTarget {
            XCTAssertFalse(MotionCatalog.glows(for: role, reduceMotion: false),
                           "\(role.rawValue) 也发光了：那一层模糊会往高频路径上扩散")
        }
        let sidebar = codeOnly(try productSource(named: "Views/HistorySidebarView.swift"))
        XCTAssertTrue(sidebar.contains("MotionCatalog.glows(for: .dropTarget)"),
                      "光晕没人读 ⇒ 它只是目录里的两个数")
        XCTAssertTrue(sidebar.contains("MotionCatalog.dropGlowRadius"),
                      "半径没走目录 ⇒ 视图里出现了自己写的模糊值")
    }

    // MARK: - 降级开关（全源门，M16）

    /// 合成规则是**或**不是与：任一来源说要降就降。
    /// 只测 `motionShouldBeReduced` 一次只能拿到机器上的一个真值，
    /// 所以规则被抽成纯函数放在这里，四个格子都能钉。
    func testReduceMotionGateIsAnOrNotAnAnd() {
        XCTAssertTrue(MotionCatalog.isMotionReduced(reduceMotionSetting: false, voiceOverRunning: true),
                      "VoiceOver 在跑却还做动效 —— WCAG 2.2 SC 2.3.3 要的是交互触发的动效必须能关")
        XCTAssertTrue(MotionCatalog.isMotionReduced(reduceMotionSetting: true, voiceOverRunning: false))
        XCTAssertFalse(MotionCatalog.isMotionReduced(reduceMotionSetting: false, voiceOverRunning: false))
        XCTAssertTrue(MotionCatalog.isMotionReduced(reduceMotionSetting: true, voiceOverRunning: true))
    }

    func testReduceMotionSwitchIsReadableAndInjectable() {
        MotionCatalog.overrideReduceMotion = true
        XCTAssertTrue(MotionCatalog.motionShouldBeReduced)
        MotionCatalog.overrideReduceMotion = false
        XCTAssertFalse(MotionCatalog.motionShouldBeReduced)
        MotionCatalog.overrideReduceMotion = nil
        // 交回系统：只要求它给出一个布尔值（值本身取决于机器设置，不钉死）。
        _ = MotionCatalog.motionShouldBeReduced
    }

    /// 视图侧不许再出现裸的 `NSWorkspace.shared.accessibilityDisplayShouldReduceMotion`。
    /// 这一条是「仓库里 15 处淡入没有门控」的根因：门控这件事一旦要每处自己写，就一定有人不写。
    func testViewsReadTheSwitchThroughTheCatalogOnly() throws {
        let offenders = try productSources(in: "Views")
            .filter { codeOnly($1).contains("accessibilityDisplayShouldReduceMotion") }
            .map(\.0)
        XCTAssertTrue(offenders.isEmpty,
                      "这些文件还在自己读系统开关，应该走 MotionCatalog.motionShouldBeReduced：\(offenders)")
    }

    /// 开关的**变化**也要接上（报告 MC-4）：只读一次的话，用户中途在系统设置里打开
    /// 「减弱动态效果」或启动 VoiceOver，已经开着的窗口会一直按老样子动。
    /// 这条是源码扫描 —— 通知注册在测试里没法伪造（除非真的注册），所以它挡得住"把那几行删了"。
    func testAccessibilityOptionChangesAreObserved() throws {
        let body = try XCTUnwrap(
            try productSources(in: "Managers").first { $0.0 == "AppDelegate.swift" }?.1,
            "找不到 AppDelegate.swift：这条守卫没有守卫对象"
        )
        let code = codeOnly(body)
        XCTAssertTrue(code.contains("accessibilityDisplayOptionsDidChangeNotification"),
                      "没接这条通知 = 开关中途变了界面不跟着变（MC-4）")
        XCTAssertTrue(code.contains("NSWorkspace.shared.notificationCenter"),
                      "这条通知只在 NSWorkspace 的通知中心里，用 `NotificationCenter.default` 注册收不到，而且不会报错")
        XCTAssertTrue(code.contains("removeObserver"),
                      "注册了不摘：回调会在被捕获对象没了之后继续被投")
    }

    /// M11 的落点：**参数只有一处作者**。本轮之前全仓 17 处声明各写各的秒数
    /// （同一个"状态变了"分别是 0.11 / 0.12 / 0.14 / 0.15），这一条把它钉成判据。
    ///
    /// 只拦"就地写死的曲线"（`withAnimation(.ease…)` / `.animation(.ease…)`）和
    /// 非零的 `context.duration = 0.x`。刻意**不**拦 `FilterPillMotion` 与
    /// `MultiFilePreviewLayout` 那两处：它们是"参数是纯值、视图消费它"的先例
    /// （AGENTS.md 点名的那两个），各自有自己的守卫，且都吃 reduce-motion。
    func testNoAdHocAnimationParametersOutsideTheCatalog() throws {
        var offenders: [String] = []
        for directory in ["Views", "Managers"] {
            for (name, source) in try productSources(in: directory) where name != "MotionCatalog.swift" {
                let lines = codeOnly(source).split(separator: "\n", omittingEmptySubsequences: false)
                for (index, rawLine) in lines.enumerated() {
                    let line = rawLine.trimmingCharacters(in: .whitespaces)
                    if line.contains("withAnimation(.") || line.contains(".animation(.")
                        || line.range(of: #"\.duration = [1-9]"#, options: .regularExpression) != nil {
                        offenders.append("\(name):\(index + 1): \(line)")
                    }
                }
            }
        }
        XCTAssertTrue(offenders.isEmpty,
                      "这些行还在自己写动画参数，应该走 MotionCatalog：\(offenders)")
    }

    /// 目录之外到底还剩几处自己写曲线？这条把它们**数出来**，而不是留在注释里。
    ///
    /// 上面那条拦的是"就地写死"，而它**刻意放过** `FilterPillMotion`（滑块）与
    /// `MultiFilePreviewLayout`（多文件展开）：参数是纯值、视图消费它、各自有守卫、都吃 reduce-motion。
    /// 但"放过"只写在注释里就意味着每一轮都要重新数一遍 —— 上一轮的账本已经证明注释会过期。
    /// 所以钉成**文件集合相等**：多一个例外要红；把老例外迁进目录也要红（那时把名字从白名单删掉，
    /// 这是设计好的摩擦，不是误报）。
    ///
    /// 顺带记下这两处的性质，免得下一个人以为它们也"不过冲"：
    /// `FilterPillMotion` 的 damping 0.72、`MultiFilePreviewLayout` 在 12/13 走
    /// `interactiveSpring(dampingFraction: 0.88)` —— 两者都有过冲，是目录"一律不过冲"声明之外的**已知例外**。
    func testMotionParametersOutsideTheCatalogAreWhitelisted() throws {
        let needles = ["spring(response", "interactiveSpring", ".snappy(", "timingCurve"]
        let whitelist = ["HistorySidebarView.swift", "DetailView.swift"]
        var found: [String] = []
        for directory in ["Views", "Managers"] {
            for (name, source) in try productSources(in: directory) where name != "MotionCatalog.swift" {
                let code = codeOnly(source)
                if needles.contains(where: code.contains) { found.append(name) }
            }
        }
        XCTAssertEqual(Set(found), Set(whitelist),
                       "目录之外写曲线的文件集合变了。现在扫到 \(found)；白名单 \(whitelist)："
                           + "新增例外要在 `testNoAdHocAnimationParametersOutsideTheCatalog` 那条注释里写清为什么，"
                           + "迁移进目录则把名字从这里删掉")
        XCTAssertEqual(found.count, whitelist.count,
                       "同一个文件里出现第二处会被 Set 吃掉：条数要单独钉（\(found)）")
    }

    /// 详情换页挂在**视图类型身份**上，不是 `entry.id`：文本→文本只换字（不演），
    /// 文本→图片是整块换掉（交叉淡入）。粒度必须和 `DetailView.preview(for:)` 的分支对齐，
    /// 所以"分支变了 ⇔ 类型变了"两个方向都要钉。
    func testDetailPreviewKindTracksThePreviewBranches() {
        func entry(_ content: ClipboardEntryContent) -> ClipboardEntry {
            ClipboardEntry(content: content, timestamp: Date(timeIntervalSince1970: 1_700_000_000),
                           thumbnail: nil, sourceURL: nil, isFavorite: false,
                           sourceUTIs: ["public.utf8-plain-text"],
                           sourceAppBundleID: nil, sourceAppName: nil, ocrText: nil)
        }
        // 两个信号才给渲染（`minimumSignalsToOfferRendering`）：一个标题不算。
        let markdown = "# 标题\n\n- 列表项一\n- 列表项二"
        XCTAssertGreaterThan(MarkdownParsingPolicy.signals(in: markdown).count, 1,
                             "夹具退化成一个信号就不给渲染了，这条断言测的就是别的东西")
        let plain = "只有一行，没有任何 markdown 结构"
        XCTAssertEqual(DetailPreviewKind(entry: entry(.text(plain)), markdownMode: .rendered),
                       DetailPreviewKind(entry: entry(.text("另一行纯文本")), markdownMode: .rendered),
                       "两条纯文本之间换选：视图类型没变，不该演一遍")
        XCTAssertNotEqual(DetailPreviewKind(entry: entry(.text(markdown)), markdownMode: .rendered),
                          DetailPreviewKind(entry: entry(.text(markdown)), markdownMode: .source),
                          "渲染态与原文态是两个不同的视图")
        XCTAssertNotEqual(DetailPreviewKind(entry: entry(.text(plain)), markdownMode: .rendered),
                          DetailPreviewKind(entry: entry(.file(URL(fileURLWithPath: "/tmp/a.txt"))),
                                            markdownMode: .rendered),
                          "文本 → 文件是整块换掉")
        XCTAssertEqual(DetailPreviewKind(entry: entry(.file(URL(fileURLWithPath: "/tmp/a.md"))),
                                         markdownMode: .rendered),
                       DetailPreviewKind(entry: entry(.file(URL(fileURLWithPath: "/tmp/b.txt"))),
                                         markdownMode: .rendered),
                       "两个文件条目走同一个视图：不按 md/非 md 细分，细分出来的是一个不会执行的承诺")
    }

    // MARK: - 分支可达性与"看不见的回执"（MC-12 / MC-13）

    /// 换符号的那三颗按钮必须真的接在"符号替换过渡"上。
    /// 这条扫的是**调用点**：`SymbolMotion` 里写对了但调用方忘传参数，产品上什么都不会发生
    /// —— 上一轮的 `bounceValue` 就是这个形状（一个恒真的实参把另一条分支永久挡住了）。
    func testSymbolChangingButtonsAreWiredToTheReplaceTransition() throws {
        let glass = codeOnly(try productSource(named: "Views/GlassControls.swift"))
        XCTAssertEqual(glass.components(separatedBy: "replaceSymbol: true").count - 1, 3,
                       "收藏/固定/已复制这三颗会换符号的按钮，少一颗接上替换过渡就说明有一处回到了\'啪地换图标\'")
        // MC-12 的教训不是"bounce 不该存在"，而是"两条效果不许写成互斥分支"。
        // 所以这里钉的是**叠加**：bounce 回来了可以，但 `SymbolMotion` 里它必须与 replace 同时挂。
        let motion = codeOnly(try productSource(named: "Views/MotionModifiers.swift"))
        XCTAssertTrue(motion.contains("bounceValue"), "M5 要的\'弹一下\'回来了吗？没有的话是被顺手删了")
        XCTAssertTrue(motion.contains("contentTransition(.symbolEffect(.replace))"),
                      "符号替换过渡是\'换了图标\'这件事的唯一表达，不许为了弹跳把它让掉")
        XCTAssertTrue(motion.contains("bouncing(content.contentTransition"),
                      "bounce 与 replace 又变回互斥分支了（MC-12 的原病）：必须叠加，见 `SymbolMotion`")
        let pill = codeOnly(try productSource(named: "Views/GlassControls.swift"))
        XCTAssertTrue(pill.contains("bounceValue: isFavorite"), "收藏那颗要弹（状态被改了）")
        XCTAssertTrue(pill.contains("bounceValue: isPinned"), "固定那颗要弹")
        XCTAssertFalse(pill.contains("bounceValue: copyConfirmed"),
                       "复制是每天上百次的动作，频率闸门判它不该弹（报告红线 0）")
    }

    /// 读屏回执：能播就必须真的播出去，且 `DetailView` 必须调用它。
    /// 12/13 那一档 API 不存在（编译器实测 macOS 14 起），所以断言跟着 `isSupported` 走 ——
    /// 不是把缺口判成绿，而是"这一档发不出去"这件事本身被钉住。
    func testCopyReceiptIsAnnouncedWhereTheApiExists() throws {
        XCTAssertEqual(VoiceOverReceipt.announce("已复制到剪贴板"), VoiceOverReceipt.isSupported,
                       "announce 的返回值必须如实反映\'这次到底播出去了没有\'")
        let detail = codeOnly(try productSource(named: "Views/DetailView.swift"))
        XCTAssertTrue(detail.contains("VoiceOverReceipt.announce"),
                      "复制回执又变回只有视觉了：看不见的人拿不到\'已复制\'这句话（MC-13）")
        let helper = codeOnly(try productSource(named: "Utilities/VoiceOverReceipt.swift"))
        XCTAssertTrue(helper.contains("macOS 14"),
                      "12/13 没有这个 API 是事实，必须在代码里写明，否则下一个人会以为是漏了")
    }

    // MARK: - 夹具

    private func productSource(named relative: String) throws -> String {
        let directory = String(relative.prefix { $0 != "/" })
        let name = String(relative.dropFirst(directory.count + 1))
        let found = try productSources(in: directory).first { $0.0 == name }
        return try XCTUnwrap(found?.1, "找不到 Sources/ClipboardHistoryApp/\(relative)：守卫找不到被守卫的东西时必须红")
    }

    private func codeOnly(_ source: String) -> String {
        source.components(separatedBy: "\n")
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
    }

    private func productSources(in directory: String) throws -> [(String, String)] {
        var root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<6 {
            let url = root.appendingPathComponent("Sources/ClipboardHistoryApp/" + directory, isDirectory: true)
            guard let names = try? FileManager.default.contentsOfDirectory(atPath: url.path) else {
                root = root.deletingLastPathComponent(); continue
            }
            return names.filter { $0.hasSuffix(".swift") }.compactMap { name in
                guard let text = try? String(contentsOf: url.appendingPathComponent(name), encoding: .utf8)
                else { return nil }
                return (name, text)
            }
        }
        throw NSError(domain: "MotionCatalogTests", code: 1,
                      userInfo: [NSLocalizedDescriptionKey: "找不到 Sources/ClipboardHistoryApp/\(directory)：守卫找不到被守卫的东西时必须红"])
    }
}
