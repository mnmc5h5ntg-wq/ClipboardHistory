// R24 的第一把尺子：**文字侧**的对比度（BACKLOG 34 —— 全仓此前只有控件笔画的墨尺，没有正文的）。
//
// 为什么要独立一个命令行工具而不是直接往测试里加断言：
// 阈值必须由**量出来的数**决定。先在 PNG 上把"这块区域的底是什么、字是什么、差多少"读出来，
// 再决定判据卡在哪 —— 反过来（先写 4.5 再去凑）就是 R19 记过的"用错的轴判两态"。
//
// 两个模式：
//   probe <png> <x,y,w,h> [scale]   矩形内的墨/底对比（WCAG sRGB 线性化）
//   rows  <png> <x0,y0,x1,y1> [scale]  逐行打印"这一行有多少个非底色像素"，用来**定位**文字行
//
// probe 的算法（和 R21 的 inkContrast 同族，但为文字改了两处）：
//   1) 底 = 亮度的**众数**（文字只占一小部分像素，均值会被字拉走）；
//   2) 墨 = 离底最远的那一端的 **P1 尾**（不是最值：一个坏点就能把最值抬上去，
//      而 13pt 汉字的笔画在 @2x 下只有 1–2px，最值往往是抗锯齿的中间色）；
//   3) coverage = 离底超过阈值的像素占比 —— 没有它，一块纯色也能"通过"任何对比判据。
import AppKit

let args = CommandLine.arguments
guard args.count >= 4 else {
    FileHandle.standardError.write("usage: ink_probe <probe|rows> <png> <x,y[,w,h]> [scale]\n".data(using: .utf8)!)
    exit(2)
}

func load(_ path: String) -> (NSBitmapImageRep, UnsafeMutablePointer<UInt8>) {
    guard let data = FileManager.default.contents(atPath: path),
          let rep = NSBitmapImageRep(data: data),
          let ptr = rep.bitmapData else {
        FileHandle.standardError.write("读不到像素：\(path)\n".data(using: .utf8)!)
        exit(3)
    }
    return (rep, ptr)
}

func lum(_ r: Int, _ g: Int, _ b: Int) -> Int { (r * 299 + g * 587 + b * 114) / 1000 }

/// sRGB 相对亮度（WCAG）。不线性化就算比是错的 —— R21 在这里错过一次。
func relLuma(_ v: Int) -> Double {
    let c = Double(v) / 255.0
    return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
}

func contrast(_ a: Int, _ b: Int) -> Double {
    let (la, lb) = (relLuma(a), relLuma(b))
    let (hi, lo) = (max(la, lb), min(la, lb))
    return (hi + 0.05) / (lo + 0.05)
}

let (rep, base) = load(args[2])
let scale = args.count > 4 ? (Double(args[4]) ?? 2.0) : 2.0
let rowBytes = rep.samplesPerPixel * rep.bitsPerSample / 8
let width = rep.pixelsWide, height = rep.pixelsHigh

func sample(_ x: Int, _ y: Int) -> (Int, Int, Int) {
    let o = y * rowBytes * width + x * rowBytes
    return (Int(base[o]), Int(base[o + 1]), Int(base[o + 2]))
}

func lumAt(_ x: Int, _ y: Int) -> Int {
    let (r, g, b) = sample(x, y)
    return lum(r, g, b)
}

let box = args[3].split(separator: ",").compactMap { Double($0) }
func ptToPx(_ v: Double) -> Int { Int((v * scale).rounded()) }

if args[1] == "probe" {
    guard box.count == 4 else {
        FileHandle.standardError.write("probe 需要 x,y,w,h（单位 pt）\n".data(using: .utf8)!)
        exit(2)
    }
    let x0 = max(0, ptToPx(box[0])), y0 = max(0, ptToPx(box[1]))
    let x1 = min(width, x0 + ptToPx(box[2])), y1 = min(height, y0 + ptToPx(box[3]))
    guard x1 > x0, y1 > y0 else { print("EMPTY RECT"); exit(0) }

    var lumas: [Int] = []
    lumas.reserveCapacity((x1 - x0) * (y1 - y0))
    for y in y0..<y1 {
        for x in x0..<x1 {
            let (r, g, b) = sample(x, y)
            lumas.append(lum(r, g, b))
        }
    }
    // 众数底
    var hist = [Int: Int]()
    for v in lumas { hist[v, default: 0] += 1 }
    let bg = hist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
    let sorted = lumas.sorted()
    let p1 = sorted[max(0, sorted.count / 100)]
    let pMax = sorted[min(sorted.count - 1, sorted.count - 1 - sorted.count / 100)]
    // 墨在底的哪一端：暗底取亮尾（P99），亮底取暗尾（P1）。两边都报，人来看哪个是真的。
    var covered = 0
    for v in lumas where abs(v - bg) > 40 { covered += 1 }
    let coverage = Double(covered) / Double(lumas.count)
    print("PROBE \(args[2]) rect=\(args[3])pt@\(scale)x px=\(x1 - x0)x\(y1 - y0)")
    print("  bg(众数)=\(bg)  P1=\(p1)  P99=\(pMax)  coverage(Δ>40)=\(String(format: "%.1f", coverage * 100))%")
    print("  contrast(bg,P1)=\(String(format: "%.2f", contrast(bg, p1)))"
        + "  contrast(bg,P99)=\(String(format: "%.2f", contrast(bg, pMax)))")
} else if args[1] == "bandtext" {
    // 这一条就是将来进测试的判据原型：**自己找带、自己分段、自己报对比**。
    // 为什么要自动定位：手写 y 区间等于把"布局今天长什么样"钉进判据 ——
    // 布局一动，框就套到空白上，读出来的数还是"像模像样"的（R21 那两条落空的框就是这么来的）。
    //
    // 分带规则：逐行取众数 RGB ⇒ R−B > 6 算"这条被涂了色"；同一带内众数亮度变化 > 1 就断开
    //（警告 0.12 橙与错误 0.10 红的底色差 3 个亮度级，正好把挨着的两条分开）。
    let x0 = max(0, ptToPx(box[0])), y0 = max(0, ptToPx(box[1]))
    let x1 = min(width, x0 + ptToPx(box[2])), y1 = min(height, y0 + ptToPx(box[3]))
    struct Seg { var startPx: Int; var endPx: Int; var luma: Int; var chroma: Int }
    var segs: [Seg] = []
    var open: (startPx: Int, luma: Int, chroma: Int)? = nil
    func close(_ endPx: Int) {
        guard let s = open else { return }
        if (endPx - s.startPx) / Int(scale) >= 12 {
            segs.append(Seg(startPx: s.startPx, endPx: endPx, luma: s.luma, chroma: s.chroma))
        }
        open = nil
    }
    for y in y0..<y1 {
        var hist = [UInt: Int]()
        for x in x0..<x1 {
            let (r, g, b) = sample(x, y)
            hist[(UInt(r) << 16) | (UInt(g) << 8) | UInt(b), default: 0] += 1
        }
        let top = hist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
        let (rr, gg, bb) = (Int(top >> 16), Int((top >> 8) & 0xFF), Int(top & 0xFF))
        let chroma = rr - bb
        let l = lum(rr, gg, bb)
        if chroma > 6 {
            if let s = open, abs(s.luma - l) <= 1 { /* 同一段，继续 */ }
            else { close(y); open = (y, l, chroma) }
        } else {
            close(y)
        }
    }
    close(y1)
    print("BANDTEXT \(args[2]) 找到 \(segs.count) 段")
    for seg in segs {
        // 只量文字列：左边避开图标（36pt），右边避开动作按钮（帧宽 −95pt）。
        let tx0 = min(x1, x0 + Int(36 * scale))
        let tx1 = max(tx0 + 1, x1 - Int(95 * scale))
        var lumas: [Int] = []
        for y in seg.startPx..<seg.endPx {
            for x in tx0..<tx1 { lumas.append(lumAt(x, y)) }
        }
        guard lumas.count > 200 else { print("  段 y=\(seg.startPx) 样本太少"); continue }
        let bg = seg.luma
        let sorted = lumas.sorted()
        let p1 = sorted[max(0, sorted.count / 100)]
        let p99 = sorted[min(sorted.count - 1, sorted.count - 1 - sorted.count / 100)]
        // 墨在底的哪一端：哪一端离底更远就是墨。
        let ink = abs(p1 - bg) >= abs(p99 - bg) ? p1 : p99
        var covered = 0
        for v in lumas where abs(v - bg) > 40 { covered += 1 }
        let coverage = Double(covered) / Double(lumas.count)
        print(String(format: "  带 y=%.1f..%.1fpt 色度=%d 底=%d 墨=%d 对比=%.2f 墨占比=%.1f%%",
                     Double(seg.startPx) / scale, Double(seg.endPx) / scale,
                     seg.chroma, bg, ink, contrast(bg, ink), coverage * 100))
    }
} else if args[1] == "cols" {
    // R28：把一行带里每一列的颜色打出来，用来**自己找图例方格**（不手写 x）。
    let y0 = max(0, ptToPx(box[1])), y1 = min(height, y0 + ptToPx(box[3]))
    let x0 = max(0, ptToPx(box[0])), x1 = min(width, x0 + ptToPx(box[2]))
    print("COLS \(args[2]) y=\(box[1])..\(box[1] + box[3])pt x=\(box[0])..\(box[0] + box[2])pt")
    var run: (start: Int, rgb: (Int, Int, Int))? = nil
    func flush(_ end: Int) {
        guard let r = run else { return }
        if (end - r.start) / Int(scale) >= 4 {
            print(String(format: "  x=%.1f..%.1fpt  rgb(%d,%d,%d)",
                         Double(r.start) / scale, Double(end) / scale, r.rgb.0, r.rgb.1, r.rgb.2))
        }
        run = nil
    }
    for x in stride(from: x0, to: x1, by: 2) {
        var hist = [UInt: Int]()
        for y in y0..<y1 {
            let (r, g, b) = sample(x, y)
            hist[(UInt(r) << 16) | (UInt(g) << 8) | UInt(b), default: 0] += 1
        }
        let top = hist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
        let rgb = (Int(top >> 16), Int((top >> 8) & 0xFF), Int(top & 0xFF))
        let colored = (max(rgb.0, rgb.1, rgb.2) - min(rgb.0, rgb.1, rgb.2)) > 12
        if colored {
            if let r = run, abs(r.rgb.0 - rgb.0) <= 6 && abs(r.rgb.2 - rgb.2) <= 6 { /* 同一段 */ }
            else { flush(x); run = (x, rgb) }
        } else {
            flush(x)
        }
    }
    flush(x1)
} else if args[1] == "button" {
    // R25：在一条暖色带的**右侧**找那枚动作按钮，报它的上下沿与中心。
    // 为什么不用"中性灰"判：量出来按钮的填充是 (232,226,220) 这一类**暖灰**
    //（`.bordered` 的半透明底把橙底吸进去了），色度轴分不开；
    // 但亮度分得很开：带 244 vs 按钮 226（差 18）。⇒ 轴要按"哪根轴真的分得开"选（R23 立的规矩，反过来用）。
    let x0 = max(0, ptToPx(box[0])), y0 = max(0, ptToPx(box[1]))
    let x1 = min(width, x0 + ptToPx(box[2])), y1 = min(height, y0 + ptToPx(box[3]))
    var rowLuma: [Int: Int] = [:]
    for y in y0..<y1 {
        var hist = [Int: Int]()
        for x in x0..<x1 { hist[lumAt(x, y), default: 0] += 1 }
        rowLuma[y] = hist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
    }
    var bandHist = [Int: Int]()
    for (_, l) in rowLuma { bandHist[l / 4, default: 0] += 1 }
    let band = (bandHist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0) * 4 + 2
    var best: (start: Int, end: Int)? = nil
    var open = -1
    func close(_ end: Int) {
        guard open >= 0 else { return }
        if best == nil || (end - open) > (best!.end - best!.start) { best = (open, end) }
        open = -1
    }
    for y in y0..<y1 {
        if abs(rowLuma[y]! - band) >= 8 { if open < 0 { open = y } } else { close(y) }
    }
    close(y1)
    print("BUTTON \(args[2]) rect=\(args[3])pt 带亮度=\(band)")
    if let b = best {
        print(String(format: "  按钮 y=%.1f..%.1fpt 中心=%.1fpt 高=%.1fpt",
                     Double(b.start) / scale, Double(b.end) / scale,
                     (Double(b.start) + Double(b.end)) / 2 / scale, Double(b.end - b.start) / scale))
    } else {
        print("  没找到偏离带亮度的块 ⇒ 这块矩形里没有按钮")
    }
} else if args[1] == "bands" {
    // 按**色度**找色带：逐行取该行的众数 RGB，R−B 超过阈值算"这块被涂了色"。
    // 存在的理由：判据不该把我手写的 y 区间当真值 —— 布局一动，手写的框就套在空白上报假数据。
    // 先在这里把"色带到底从第几行到第几行"量出来，再决定测试里怎么定位。
    let x0 = max(0, ptToPx(box[0])), y0 = max(0, ptToPx(box[1]))
    let x1 = min(width, x0 + ptToPx(box[2])), y1 = min(height, y0 + ptToPx(box[3]))
    print("BANDS \(args[2]) x=\(box[0])..\(box[0] + box[2])pt")
    var run: (start: Int, chroma: Int, luma: Int)? = nil
    func flush(_ endPx: Int) {
        guard let r = run else { return }
        print(String(format: "  带 y=%.1f..%.1fpt  色度R−B=%d  底色亮度=%d",
                     Double(r.start) / scale, Double(endPx) / scale, r.chroma, r.luma))
        run = nil
    }
    for y in y0..<y1 {
        var hist = [UInt: Int]()
        for x in x0..<x1 {
            let (r, g, b) = sample(x, y)
            hist[(UInt(r) << 16) | (UInt(g) << 8) | UInt(b), default: 0] += 1
        }
        let top = hist.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
        let chroma = Int(top >> 16) - Int(top & 0xFF)
        let isBand = chroma > 6
        if isBand, run == nil { run = (y, chroma, lum(Int(top >> 16), Int((top >> 8) & 0xFF), Int(top & 0xFF))) }
        if !isBand { flush(y) }
    }
    flush(y1)
} else {
    // rows：逐行打印非底色像素数，用来定位"字到底画在第几行"
    let x0 = max(0, ptToPx(box[0])), y0 = max(0, ptToPx(box[1]))
    let x1 = min(width, x0 + ptToPx(box[2])), y1 = min(height, y0 + ptToPx(box[3]))
    print("ROWS \(args[2]) x=\(box[0])..\(box[0] + box[2])pt")
    var lastBucket = -1
    for y in stride(from: y0, to: y1, by: 2) {
        var counts = [Int: Int]()
        for x in x0..<x1 { counts[lumAt(x, y), default: 0] += 1 }
        let bg = counts.max { ($0.value, $0.key) < ($1.value, $1.key) }?.key ?? 0
        var ink = 0
        for x in x0..<x1 where abs(lumAt(x, y) - bg) > 40 { ink += 1 }
        let frac = Double(ink) / Double(max(1, x1 - x0))
        let bucket = Int((frac * 100).rounded())
        if bucket != lastBucket || y == y0 {
            print(String(format: "  y=%5.1fpt  ink=%5.1f%%  bg=%d", Double(y) / scale, frac * 100, bg))
            lastBucket = bucket
        }
    }
}
