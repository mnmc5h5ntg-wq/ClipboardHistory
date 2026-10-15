#!/usr/bin/env python3
# R80：把 pt² 尺的真值表换成**算对期望值**的那一版。
# 第一版把夹具说成"左半一块墨"，而 `flatPair` 造出来的是**整张一块墨**（两帧各一块），
# 于是 ②③⑦⑧⑨ 的解析期望全部差了两倍 —— 这一条本身就是账本里"尺的夹具要先算清面积"那一族。
import io
import sys

path = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
text = io.open(path, encoding="utf-8").read()
lines = text.split("\n")

def marker_index(needle):
    hits = [i for i, line in enumerate(lines) if needle in line]
    if len(hits) != 1:
        sys.exit("锚点不唯一或没找到：%r -> %r" % (needle, hits))
    return hits[0]

start = marker_index("R80 · 那两把 pt² 尺的真值表")
end = marker_index("/// R76 / U-116：浮层搜索框的**焦点那一档**")

new_block = u'''    /// R80 · 那两把 pt² 尺的真值表（BACKLOG 109 / D-138）。
    ///
    /// 为什么必须**合成夹具**而不是拿帧来判：本轮要钉的性质是"同一个物理变化在 1× 与 2×
    /// 上给出同一个数"，而这条只能靠**构造**出来 —— 我手上没有第二台机器，
    /// runner 的那一遍读数要等 CI（R70 那一课的对称：能被自己造出来的性质不等 CI）。
    /// 夹具是**直接写字节**的（`flatRep` 那一族的原因同样成立：`setColor(_:atX:y:)`
    /// 在整数格式位图上不落地、而且不报错，而尺子的夹具读到 0 最容易被读成"没差别"）。
    ///
    /// 夹具的形状：一张 **100×20pt** 的图，两帧各自**整张一块均匀的墨**（⑤ 那格单独把
    /// 第二帧的右半改成另一个 alpha）。期望值全是解析数：
    ///   面积 = 100×20 = 2000pt²；每像素动 Δ ⇒ 搬动 = 2000×Δ÷255。
    ///   ② Δalpha=100 ⇒ **784.31**；③ 黑翻蓝（Δ蓝=255，alpha 不变）⇒ **2000.00**；
    ///   ⑤ 右半 1000pt² 动 100 ⇒ 左读 **0**、右读 **392.16**；
    ///   ⑥ Δ=1 ⇒ **0**（地板下）；⑦ Δ=3 ⇒ **23.53**（地板上）；
    ///   ⑨ 单帧 alpha=200 整张 ⇒ **1568.63**；⑧ 旧尺数像素 ⇒ **2000×缩放²**。
    ///
    /// 九个格子各拦一种错：
    ///   ① `same` —— 自己减自己 = 0（拦"尺恒开"）。
    ///   ② `alphaDim` —— 只在 alpha 上动的一整块墨：**两档缩放必须给出同一个 pt²**。
    ///      这一格是整轮的性质所在（R38：地板不能跟着像素网格变）。
    ///   ③ `colorOnly` —— 全不透明、只在蓝通道上动 ⇒ 必须读得出（R77 并集语义的另一半；
    ///      一把只读 alpha 的尺在这里给 0，那一族的后果在 BACKLOG 108）。
    ///   ④ `invisible` —— alpha 恒 0 而 RGB 不同 ⇒ 必须读成 0（合成到底上它就是没画）。
    ///   ⑤ `position` —— 变化只在右半 ⇒ 量左半那块矩形必须读 0（位置同一性，不是"有没有变化"）。
    ///   ⑥⑦ `underFloor` / `overFloor` —— 每像素差 1 与差 3：**成对**给出，
    ///      这样 `noiseFloor` 不是一句注释而是一道有两边的门（只给一边就能被抵消）。
    ///   ⑧ **本轮换尺的理由本身**：同一件物理变化在旧那把尺上按 `缩放²` 变
    ///      （2000 个像素 vs 8000 个）。那道 `≥500 个像素` 的地板在两台机器上量的不是同一件事
    ///      ⇒ R76 那句"本机 1797 / runner 0"里最多 3/4 是网格，剩下那 1/4 才是交给 CI 去分的问题。
    ///   ⑨ `inkPointsSquared` —— 单帧墨面积在两种网格下同一个 pt²（占比那条判据的分母）。
    func testMovedInkRulerIsGridNormalizedAndReadsBothAxes() throws {
        // 一帧一块均匀的墨：`from*` 是第一帧、`to*` 是第二帧（**不是**同一帧的左右两半 ——
        // 第一版我把参数写成 left/right，然后把整张一涂的夹具当成"左半有墨"来算期望值，
        // ②③⑦⑧⑨ 五格集体差了两倍；这一格留在这里当反面教材，因为它是"参数名替事实说话"）。
        func makeRep(scale: Int, alpha: Int, blue: Int) -> NSBitmapImageRep {
            let w = 100 * scale, h = 20 * scale
            let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                                       bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                       isPlanar: false, colorSpaceName: .deviceRGB,
                                       bytesPerRow: 4 * w, bitsPerPixel: 32)!
            guard let data = rep.bitmapData else {
                XCTFail("造不出夹具位图 ⇒ 这把尺的真值表没有对象")
                return rep
            }
            for y in 0..<h {
                for x in 0..<w {
                    let o = y * rep.bytesPerRow + x * 4
                    // 整块都写成同样的字节：**不给抗锯齿**，这几格要的是"整块墨"的形状。
                    data[o] = 0
                    data[o + 1] = 0
                    data[o + 2] = UInt8(blue)
                    data[o + 3] = UInt8(alpha)
                }
            }
            return rep
        }
        func flatPair(scale: Int, fromAlpha: Int, toAlpha: Int,
                      toBlue: Int = 0) -> (NSBitmapImageRep, NSBitmapImageRep) {
            (makeRep(scale: scale, alpha: fromAlpha, blue: 0),
             makeRep(scale: scale, alpha: toAlpha, blue: toBlue))
        }
        var readings: [String] = []
        for scale in [1, 2] {
            let w = 100 * scale, h = 20 * scale
            let wholeRect = CGRect(x: 0, y: 0, width: w, height: h)
            func moved(_ pair: (NSBitmapImageRep, NSBitmapImageRep), _ rect: CGRect) -> Double {
                Self.movedInkPointsSquared(pair.0, pair.1, rect: rect, scale: scale)
            }
            // ①
            XCTAssertEqual(moved(flatPair(scale: scale, fromAlpha: 200, toAlpha: 200), wholeRect),
                           0, accuracy: 0.001, "\\(scale)×：自己减自己必须读 0")
            // ②
            let dim = flatPair(scale: scale, fromAlpha: 200, toAlpha: 100)
            let movedDim = moved(dim, wholeRect)
            XCTAssertEqual(movedDim, 784.31, accuracy: 1.0,
                "\\(scale)×：2000pt² 的墨从 alpha 200 掉到 100，搬动量必须 ≈784.31pt² "
                    + "（实测 \\(String(format: "%.2f", movedDim))）⇒ 这个数一旦跟着缩放走，"
                    + "判据地板就又是『一台机器的读数当另一台的地板』（R38）")
            // ③ 只在蓝通道上动、alpha 拉满：一把只读 alpha 的尺在这里给 0
            let color = flatPair(scale: scale, fromAlpha: 255, toAlpha: 255, toBlue: 255)
            let movedColor = moved(color, wholeRect)
            XCTAssertEqual(movedColor, 2000.0, accuracy: 1.0,
                "\\(scale)×：全不透明的黑翻成蓝，搬动量必须 ≈2000pt²（实测 \\(String(format: "%.2f", movedColor))）"
                    + "⇒ 读到 0 就是这把尺**只认 alpha**，那一族的后果写在 BACKLOG 108")
            // ④ alpha 恒 0 而 RGB 不同 ⇒ 合成到底上是同一块 ⇒ 必须 0
            let ghost = flatPair(scale: scale, fromAlpha: 0, toAlpha: 0, toBlue: 255)
            let movedGhost = moved(ghost, wholeRect)
            XCTAssertEqual(movedGhost, 0, accuracy: 0.001,
                "\\(scale)×：两帧都是全透的（alpha=0），RGB 再怎么不同也**没画** ⇒ 必须读 0，"
                    + "否则这把尺会把『看不见』的东西算成视觉后果")
            // ⑤ 变化只在右半 ⇒ 量左半那块矩形必须读 0（位置同一性）
            let right = flatPair(scale: scale, fromAlpha: 200, toAlpha: 200)
            if let data = right.1.bitmapData {
                for y in 0..<h {
                    for x in (50 * scale)..<w {
                        data[y * (4 * w) + x * 4 + 3] = 100
                    }
                }
            }
            let leftHalf = CGRect(x: 0, y: 0, width: 50 * scale, height: h)
            let rightHalf = CGRect(x: 50 * scale, y: 0, width: 50 * scale, height: h)
            let movedLeft = moved(right, leftHalf)
            let movedRight = moved(right, rightHalf)
            XCTAssertEqual(movedLeft, 0, accuracy: 0.001,
                "\\(scale)×：变化明明在右半，量左半却读出 \\(String(format: "%.2f", movedLeft))pt² ⇒ "
                    + "矩形没起作用，这把尺会把『动在别处』当成『动在这一格』")
            XCTAssertEqual(movedRight, 392.16, accuracy: 1.0,
                "\\(scale)×：右半那 1000pt² 的墨掉一半，应该 ≈392.16pt²（实测 \\(String(format: "%.2f", movedRight))）")
            // ⑥⑦ 噪声地板两边各一格：每像素差 1（<2，必须不算）与差 3（>2，必须算）
            let movedUnder = moved(flatPair(scale: scale, fromAlpha: 200, toAlpha: 199), wholeRect)
            let overPair = flatPair(scale: scale, fromAlpha: 200, toAlpha: 197)
            let movedOver = moved(overPair, wholeRect)
            XCTAssertEqual(movedUnder, 0, accuracy: 0.001,
                "\\(scale)×：每像素只差 1/255 必须被 `noiseFloor` 挡掉（实测 \\(movedUnder)）⇒ "
                    + "地板没有下边这一格，它就等于不存在")
            XCTAssertGreaterThan(movedOver, 0,
                "\\(scale)×：每像素差 3/255 必须过 `noiseFloor` —— 地板只有一边就是一道能被抵消的门")
            XCTAssertEqual(movedOver, 23.53, accuracy: 0.5,
                "\\(scale)×：2000pt² 每像素动 3/255 ⇒ ≈23.53pt²（实测 \\(String(format: "%.2f", movedOver))）")
            // ⑨ 单帧墨面积（占比那条判据的分母）
            let ink = Self.inkPointsSquared(dim.0, rect: wholeRect, scale: scale)
            XCTAssertEqual(ink, 1568.63, accuracy: 1.0,
                "\\(scale)×：整张 2000pt²、alpha=200 的墨，面积必须 ≈1568.63pt² "
                    + "（实测 \\(String(format: "%.2f", ink))）⇒ 它是占比那条判据的分母，"
                    + "分母跟着网格走，整条判据就跟着网格走")
            // ⑧ **本轮换尺的理由**：同一件物理变化在旧尺上按 缩放² 变。
            let changed = Self.changedPixelCount(dim.0, dim.1, clipping: wholeRect)
            XCTAssertEqual(changed, 2000 * scale * scale, accuracy: Double(scale * scale),
                "\\(scale)×：旧那把尺在同一个物理变化上数到 \\(changed) 个像素 —— 它**应该**按 缩放² 变，"
                    + "这一格钉的是『换尺的理由』这件事本身：那道 `≥500 个像素` 的地板在 1× 与 2× 上"
                    + "量的不是同一件事（本机 1797 / runner 0 那句里最多 3/4 是网格）")
            readings.append("\\(scale)×:②搬动=\\(String(format: "%.2f", movedDim)) "
                + "③并集=\\(String(format: "%.2f", movedColor)) ④全透=\\(String(format: "%.2f", movedGhost)) "
                + "⑤左/右=\\(String(format: "%.2f", movedLeft))/\\(String(format: "%.2f", movedRight)) "
                + "⑥⑦地板下/上=\\(String(format: "%.2f", movedUnder))/\\(String(format: "%.2f", movedOver)) "
                + "⑨面积=\\(String(format: "%.2f", ink)) ⑧旧尺像素=\\(changed)")
        }
        emit("CAPTURE_INK_RULER_TRUTH_TABLE " + readings.joined(separator: " | "))
    }

'''
lines[start:end] = new_block.rstrip("\n").split("\n")
io.open(path, "w", encoding="utf-8").write("\n".join(lines))
print("replaced the truth table with the analytic-value version")
