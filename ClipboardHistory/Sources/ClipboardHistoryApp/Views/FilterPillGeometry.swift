import CoreGraphics

/// 分段筛选控件里那枚滑动药丸的**几何规划** —— 纯函数，不碰 SwiftUI、不读环境。
///
/// 为什么要有这个文件（R189 / BACKLOG 210）：这段几何以前是写在 `GeometryReader` 里的两行
/// （`frame(width: w/count - 2)` + `offset(x: idx*(w/count)+1)`），于是"药丸画在哪一段"这句话
/// **没有任何一处能被打红**：它在 R182–R188 七轮里被三次改判（材质合成 → 按钮选中底 → 几何反号），
/// 每一次"证据"都是另一把尺的结论，而 R188 又发现那两把尺对同一批像素给出矛盾形状。
/// AGENTS.md 第 2 条要的就是这个：先建成 `*Geometry` / `*Planner` 纯函数，视图里只留薄胶水。
///
/// 坐标约定（写死在这里，因为原来出错就出在"没说清是谁的坐标系"）：
///   · `track` 与返回值都在**同一个左上角原点、y 向下**的空间里 —— 与 `GeometryReader` 给的空间一致；
///   · 第 `index` 段占 `[index*seg, (index+1)*seg]`，`seg = track.width / count`；
///   · 药丸在该段里左右各内缩 `horizontalInset`，上下各内缩 `verticalInset`（原来是散在视图里的 1 与 2）；
///   · `index` 越界时**夹住**而不是回落到 0：回落到 0 会把"索引算错"这种 bug 画成"药丸在最左段"，
///     而那正好是这个控件最像正常的一种坏法。
enum FilterPillGeometry {
    /// 左右各留 1pt：药丸不许顶到轨道的圆角（`VisualRadius.track` 在两端把内容裁掉，顶边会被啃）。
    static let horizontalInset: CGFloat = 1
    /// 上下各留 1pt：轨道高 26pt，药丸 24pt。
    static let verticalInset: CGFloat = 1

    static func segmentIndex<Segment: Equatable>(_ selection: Segment, in allCases: [Segment]) -> Int {
        guard let found = allCases.firstIndex(of: selection) else { return 0 }
        return found
    }

    /// 药丸该画在哪一块。**唯一入参是轨道尺寸、段数、选中的段号**，三者都来自调用方，
    /// 所以判据可以直接拿同一组数复算 —— 不需要在测试里再抄一次 26 / 128 这类常数。
    static func pillRect(in track: CGRect, count: Int, index: Int) -> CGRect {
        guard count > 0, track.width > 0, track.height > 0 else {
            return .zero
        }
        let clamped = min(max(index, 0), count - 1)
        let segment = track.width / CGFloat(count)
        let width = max(0, segment - 2 * horizontalInset)
        let height = max(0, track.height - 2 * verticalInset)
        return CGRect(x: track.minX + CGFloat(clamped) * segment + horizontalInset,
                      y: track.minY + verticalInset,
                      width: width,
                      height: height)
    }

    /// 判据用的反函数：给定轨道与一个 x 中心，说它在第几段。
    /// 像素那侧只有"中心落在哪一段"这种可观察量，没有矩形本身 —— 这一格就是两边的接口，
    /// 它把"左半/右半"这种口语换成会红的数。
    static func segmentIndex(containingX x: CGFloat, in track: CGRect, count: Int) -> Int {
        guard count > 0, track.width > 0 else { return -1 }
        let segment = track.width / CGFloat(count)
        guard segment > 0, x >= track.minX, x < track.maxX else { return -1 }
        return Int((x - track.minX) / segment)
    }

    // MARK: - 这条离屏通道今天能不能判这件事（R190 / runner 上 `0c97820` 那两朵红换来的）

    /// 底轨至少要占列宽的这个比例，否则"找到底轨"这句话没有内容（整列都是背景也能过）。
    static let trackMustCoverColumnFraction: Double = 0.4

    /// 底轨与侧栏底的最小差（luma）。**地板的来源写在判据的注释里**：本机暗档同一把尺读到 214，
    /// 亮档读到 1，runner 读到的是"底轨根本不存在"—— 三种形状里只有第一种能判。
    static let materialContrastFloor: Double = 30

    /// 纯谓词：给定"底轨宽/列宽"与"底轨与侧栏底之差"，说这一档今天判得了还是判不了。
    /// 抽出来的理由：这条出口如果只在某台机器上被走到，它就永远没有证人 ——
    /// 变成纯函数后，本机就能把三种形状各钉一格（R154 那一课：环境差异不许报成代码结论，
    /// 而"这台机器判不了"这句话本身必须能在不换机器的情况下被打红）。
    static func channelCanSeeMaterial(trackWidth: Int, columnWidth: Int, contrast: Double) -> Bool {
        guard columnWidth > 0, trackWidth > 0 else { return false }
        if Double(trackWidth) / Double(columnWidth) < trackMustCoverColumnFraction { return false }
        return contrast >= materialContrastFloor
    }
}
