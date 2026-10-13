import AppKit
import ImageIO

// R28 尺子：设置侧栏那一列 SF Symbol 的"静置可辨性"。
//
// 为什么单独写一把：R21 的 `controlInk` 判据量的是**图标按钮**（有命中区、有底色药丸），
// 侧栏这六枚是 `Label` 里的裸符号 —— 没有底色、没有边框，能靠的只有符号自己的描线与颜色。
// 而 D-8 那批只判过"实心 / 描线混不混"，从没判过"描得够不够黑"。
//
// 用法：
//   <mode> <png> [x0 y0 w h]     mode = bands（默认）| rows | cols
//
// 区域默认就是侧栏：x∈[0, 148pt]，y 全高。

struct Frame {
    let bytes: [UInt8]
    let width: Int
    let height: Int
    let bytesPerRow: Int
    let scale: Int

    subscript(x: Int, y: Int) -> (r: Int, g: Int, b: Int) {
        let o = y * bytesPerRow + x * scale
        return (Int(bytes[o]), Int(bytes[o + 1]), Int(bytes[o + 2]))
    }
}

func load(_ path: String) -> Frame? {
    // 走 CGImageSource 而不是 NSImage：后者会按 DPI 缩放，帧名里的 pt 尺寸就对不上了。
    let url = URL(fileURLWithPath: path)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { return nil }
    let w = cg.width, h = cg.height
    let row = w * 4
    var buf = [UInt8](repeating: 0, count: row * h)
    let space = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: &buf, width: w, height: h, bitsPerComponent: 8,
                              bytesPerRow: row, space: space,
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return nil }
    ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
    // 行序：**这里不翻**。实测证明 CGImageSource + 这个上下文出来的内存第 0 行就是画面顶部
    // （翻一次之后侧栏六行会跑到 y=297..469，而它们真实位置在 71..243 —— 一眼就能证伪）。
    return Frame(bytes: buf, width: w, height: h, bytesPerRow: row, scale: 4)
}

func luma(_ p: (r: Int, g: Int, b: Int)) -> Double {
    0.299 * Double(p.r) + 0.587 * Double(p.g) + 0.114 * Double(p.b)
}

/// 该像素相对"这一块的背景"的墨量（0…1）。背景取区域里出现次数最多的颜色。
func modalColor(_ f: Frame, _ rect: CGRect) -> (r: Int, g: Int, b: Int) {
    var counts: [Int: Int] = [:]
    let x0 = Int(rect.minX), y0 = Int(rect.minY)
    let x1 = min(f.width, Int(rect.maxX)), y1 = min(f.height, Int(rect.maxY))
    for y in y0..<y1 {
        for x in x0..<x1 {
            let p = f[x, y]
            let key = ((p.r / 16) << 8) | ((p.g / 16) << 4) | (p.b / 16)
            counts[key, default: 0] += 1
        }
    }
    let best = counts.max { $0.value < $1.value }?.key ?? 0
    return (r: (best >> 8) * 16 + 8, g: ((best >> 4) & 15) * 16 + 8, b: (best & 15) * 16 + 8)
}

func inkAt(_ f: Frame, _ bg: (r: Int, g: Int, b: Int), x: Int, y: Int, floorDelta: Double = 24) -> Bool {
    let p = f[x, y]
    let d = max(abs(p.r - bg.r), abs(p.g - bg.g), abs(p.b - bg.b))
    return Double(d) > floorDelta
}

func rowProfile(_ f: Frame, rect: CGRect, scale: Int) {
    let bg = modalColor(f, rect)
    print("# bg = (\(bg.r),\(bg.g),\(bg.b))  region pt = \(rect)")
    let y0 = Int(rect.minY) * scale, y1 = min(f.height, Int(rect.maxY) * scale)
    let x0 = Int(rect.minX) * scale, x1 = min(f.width, Int(rect.maxX) * scale)
    for y in y0..<y1 {
        var ink = 0
        var strongest = 0.0
        for x in x0..<x1 where inkAt(f, bg, x: x, y: y, floorDelta: 32) {
            ink += 1
            let p = f[x, y]
            strongest = max(strongest, Double(max(abs(p.r - bg.r), abs(p.g - bg.g), abs(p.b - bg.b))))
        }
        if ink > 0 {
            print(String(format: "y=%4.1fpt inkpx=%4d frac=%.3f maxdelta=%3.0f",
                         Double(y) / Double(scale), ink, Double(ink) / Double(x1 - x0), strongest))
        }
    }
}

func colProfile(_ f: Frame, rect: CGRect, scale: Int) {
    let bg = modalColor(f, rect)
    print("# bg = (\(bg.r),\(bg.g),\(bg.b))  region pt = \(rect)")
    let y0 = Int(rect.minY) * scale, y1 = min(f.height, Int(rect.maxY) * scale)
    let x0 = Int(rect.minX) * scale, x1 = min(f.width, Int(rect.maxX) * scale)
    for x in x0..<x1 {
        var ink = 0
        var strongest = 0.0
        for y in y0..<y1 where inkAt(f, bg, x: x, y: y, floorDelta: 32) {
            ink += 1
            let p = f[x, y]
            strongest = max(strongest, Double(max(abs(p.r - bg.r), abs(p.g - bg.g), abs(p.b - bg.b))))
        }
        if ink > 0 {
            print(String(format: "x=%4.1fpt inkpx=%4d frac=%.3f maxdelta=%3.0f",
                         Double(x) / Double(scale), ink, Double(ink) / Double(y1 - y0), strongest))
        }
    }
}

/// 自动分带：把行墨曲线切成"有内容的行段"，再对每段报图标区 / 文字区。
func bands(_ f: Frame, rect: CGRect, scale: Int, iconRect: CGRect) {
    let bg = modalColor(f, rect)
    let y0 = Int(rect.minY) * scale, y1 = min(f.height, Int(rect.maxY) * scale)
    let x0 = Int(rect.minX) * scale, x1 = min(f.width, Int(rect.maxX) * scale)

    func lin(_ c: Int) -> Double {
        let s = Double(c) / 255.0
        return s <= 0.03928 ? s / 12.92 : pow((s + 0.055) / 1.055, 2.4)
    }
    func contrast(_ p: (r: Int, g: Int, b: Int), _ q: (r: Int, g: Int, b: Int)) -> Double {
        let a = 0.2126 * lin(p.r) + 0.7152 * lin(p.g) + 0.0722 * lin(p.b)
        let b = 0.2126 * lin(q.r) + 0.7152 * lin(q.g) + 0.0722 * lin(q.b)
        let hi = max(a, b), lo = min(a, b)
        return (hi + 0.05) / (lo + 0.05)
    }

    var rowInk = [Double](repeating: 0, count: y1 - y0)
    for y in y0..<y1 {
        var ink = 0
        for x in x0..<x1 where inkAt(f, bg, x: x, y: y, floorDelta: 24) { ink += 1 }
        rowInk[y - y0] = Double(ink) / Double(x1 - x0)
    }
    print("# bg = (\(bg.r),\(bg.g),\(bg.b))")
    var i = 0
    var index = 0
    while i < rowInk.count {
        guard rowInk[i] > 0.002 else { i += 1; continue }
        var j = i
        while j + 1 < rowInk.count && (rowInk[j + 1] > 0.002 || (j + 3 < rowInk.count && rowInk[j + 3] > 0.002)) { j += 1 }
        let startPt = Double(i + y0) / Double(scale)
        let endPt = Double(j + 1 + y0) / Double(scale)
        index += 1

        // 图标区：把 iconRect 平移到这一行带上（上下各放 4pt —— 符号的视觉高度比文字行高略大，
        // 卡着文字带量会把符号的上下沿切掉，那是"尺切窄了"而不是"东西没墨"）。
        let iRect = CGRect(x: iconRect.minX, y: max(rect.minY, startPt - 4),
                           width: iconRect.width,
                           height: max(1, min(rect.maxY, endPt + 4) - max(rect.minY, startPt - 4)))
        let ix0 = Int(iRect.minX) * scale, ix1 = min(f.width, Int(iRect.maxX) * scale)
        let iy0 = Int(iRect.minY) * scale, iy1 = min(f.height, Int(iRect.maxY) * scale)
        var iconInk = 0
        var iconPixels = 0
        var inkLumaSum = 0.0
        var darkest = bg
        var darkestAll = bg
        var maxDeltaAll = 0
        var minX = f.width, maxX = 0, minY = f.height, maxY = 0
        for y in iy0..<iy1 {
            for x in ix0..<ix1 {
                iconPixels += 1
                let p = f[x, y]
                let d = max(abs(p.r - bg.r), abs(p.g - bg.g), abs(p.b - bg.b))
                if d > maxDeltaAll { maxDeltaAll = d; darkestAll = p }
                if inkAt(f, bg, x: x, y: y, floorDelta: 24) {
                    iconInk += 1
                    if luma(p) < luma(darkest) { darkest = p }
                    inkLumaSum += luma(p)
                    minX = min(minX, x); maxX = max(maxX, x)
                    minY = min(minY, y); maxY = max(maxY, y)
                }
            }
        }
        // 文字区（图标右边到侧栏边缘）
        let tx0 = ix1
        var textInk = 0
        var textPixels = 0
        var textDarkest = bg
        for y in iy0..<iy1 {
            for x in tx0..<x1 {
                textPixels += 1
                if inkAt(f, bg, x: x, y: y, floorDelta: 24) {
                    textInk += 1
                    let p = f[x, y]
                    if luma(p) < luma(textDarkest) { textDarkest = p }
                }
            }
        }
        print(String(format: "band %d  y=[%.1f,%.1f]  icon: ink=%.3f maxdelta=%3d contrast=%.2f box=%.1f..%.1f x %.1fx%.1fpt  text: ink=%.3f contrast=%.2f",
                     index, startPt, endPt,
                     iconPixels > 0 ? Double(iconInk) / Double(iconPixels) : -1,
                     maxDeltaAll,
                     contrast(darkestAll, bg),
                     iconInk > 0 ? Double(minX) / Double(scale) : 0,
                     iconInk > 0 ? Double(maxX + 1) / Double(scale) : 0,
                     iconInk > 0 ? Double(maxX - minX + 1) / Double(scale) : 0,
                     iconInk > 0 ? Double(maxY - minY + 1) / Double(scale) : 0,
                     textPixels > 0 ? Double(textInk) / Double(textPixels) : -1,
                     contrast(textDarkest, bg)))
        i = j + 1
    }
}

/// 把一块 pt 区域原样写成 PNG（`sips` 的 cropOffset 语义不可靠，这里自己裁，坐标就是 pt×2）。
func crop(_ f: Frame, rect: CGRect, scale: Int, to path: String) {
    let x0 = Int(rect.minX) * scale, y0 = Int(rect.minY) * scale
    let w = Int(rect.width) * scale, h = Int(rect.height) * scale
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8,
                              bytesPerRow: w * 4, space: CGColorSpaceCreateDeviceRGB(),
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return }
    let dst = ctx.data!.assumingMemoryBound(to: UInt8.self)
    for y in 0..<h {
        for x in 0..<w {
            let s = (y0 + y) * f.bytesPerRow + (x0 + x) * 4
            let d = y * w * 4 + x * 4
            dst[d] = f.bytes[s]; dst[d + 1] = f.bytes[s + 1]
            dst[d + 2] = f.bytes[s + 2]; dst[d + 3] = 255
        }
    }
    guard let out = ctx.makeImage() else { return }
    let rep = NSBitmapImageRep(cgImage: out)
    guard let data = rep.representation(using: .png, properties: [:]) else { return }
    try? data.write(to: URL(fileURLWithPath: path))
    print("wrote \(path) \(w)x\(h)px")
}

/// 把一块区域打成 ASCII 灰度图（每字符 = 1pt×1pt 里最"偏离背景"的那个像素）。
/// 用途：区分"字形完整但整体被调淡"和"字形缺一半"—— 这两种在 ink 分数上可能一样。
func dump(_ f: Frame, rect: CGRect, scale: Int) {
    let bg = modalColor(f, rect)
    print("# bg = (\(bg.r),\(bg.g),\(bg.b)) region pt = \(rect)")
    let ramp = Array(" .:-=+*#%@")
    let y0 = Int(rect.minY) * scale, y1 = min(f.height, Int(rect.maxY) * scale)
    let x0 = Int(rect.minX) * scale, x1 = min(f.width, Int(rect.maxX) * scale)
    for py in stride(from: y0, to: y1, by: scale) {
        var line = ""
        for px in stride(from: x0, to: x1, by: scale) {
            var best = 0
            for dy in 0..<scale {
                for dx in 0..<scale {
                    let p = f[px + dx, py + dy]
                    best = max(best, max(abs(p.r - bg.r), max(abs(p.g - bg.g), abs(p.b - bg.b))))
                }
            }
            let idx = min(ramp.count - 1, best * ramp.count / 256)
            line.append(ramp[idx])
        }
        print(String(format: "%5.1fpt |%@", Double(py) / Double(scale), line))
    }
}

/// 一块区域里"最亮 / 最暗"的像素各是多少（相对背景）。
/// 用来分辨"淡灰"和"其实是白色"—— 两者在 ink 分数上完全一样，含义完全相反。
func minMax(_ f: Frame, rect: CGRect, scale: Int) {
    let bg = modalColor(f, rect)
    let y0 = Int(rect.minY) * scale, y1 = min(f.height, Int(rect.maxY) * scale)
    let x0 = Int(rect.minX) * scale, x1 = min(f.width, Int(rect.maxX) * scale)
    var lightest = bg, darkest = bg
    var lightestD = -1.0
    var darkestD = 1_000_000.0
    var lightestAt = "", darkestAt = ""
    for y in y0..<y1 {
        for x in x0..<x1 {
            let p = f[x, y]
            let dl = luma(p) - luma(bg)
            if dl > lightestD { lightestD = dl; lightest = p; lightestAt = "(\(x / scale),\(y / scale))" }
            if dl < darkestD { darkestD = dl; darkest = p; darkestAt = "(\(x / scale),\(y / scale))" }
        }
    }
    print(String(format: "region %@ bg=(%d,%d,%d)  lightest=(%d,%d,%d) d=%+.0f at %@  darkest=(%d,%d,%d) d=%+.0f at %@",
                 NSStringFromRect(rect), bg.r, bg.g, bg.b,
                 lightest.r, lightest.g, lightest.b, lightestD, lightestAt,
                 darkest.r, darkest.g, darkest.b, darkestD, darkestAt))
}

let args = CommandLine.arguments
let mode = args.count > 1 ? args[1] : "bands"
guard args.count >= 3, let f = load(args[2]) else {
    print("cannot load"); exit(2)
}
let scale = 2
let rest = Array(args.dropFirst(3)).compactMap { Double($0) }
let rect = rest.count == 4
    ? CGRect(x: rest[0], y: rest[1], width: rest[2], height: rest[3])
    : CGRect(x: 0, y: 0, width: 148, height: Double(f.height / scale))
let iconRect = CGRect(x: rest.count >= 6 ? rest[4] : 8, y: 0, width: rest.count >= 6 ? rest[5] : 30, height: 20)

switch mode {
case "rows": rowProfile(f, rect: rect, scale: scale)
case "cols": colProfile(f, rect: rect, scale: scale)
case "crop": crop(f, rect: rect, scale: scale, to: args.last ?? "/tmp/crop.png")
case "dump": dump(f, rect: rect, scale: scale)
case "minmax": minMax(f, rect: rect, scale: scale)
default: bands(f, rect: rect, scale: scale, iconRect: iconRect)
}
