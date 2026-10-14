// R39 裁剪：把帧上某一矩形（单位 pt，按帧自身的缩放比换算）裁出来给人眼审。
// 用法：swift crop_r39.swift <in.png> <out.png> <x> <y> <w> <h>
// 走 CGImage.cropping(to:)：它的原点在**左上**，与判据里那些尺同一套坐标，
// 所以"我看见的"和"判据读到的"是同一块像素（不用 NSBitmapImageRep.crop 那套翻转语义）。
import AppKit
import CoreGraphics

let a = CommandLine.arguments
guard a.count >= 7,
      let image = NSImage(contentsOfFile: a[1]),
      let rep = NSBitmapImageRep(data: image.tiffRepresentation ?? Data()),
      let cg = rep.cgImage else {
    print("读不到 \(a[1])"); exit(2)
}
let x = Double(a[3])!, y = Double(a[4])!, w = Double(a[5])!, h = Double(a[6])!
// 第 8 个参数 = 这一帧的**逻辑宽度（pt）**。必须显式传：`NSBitmapImageRep(data:)` 读回来的
// `size` 等于像素尺寸（1440×1080 报成 1440×1080pt），拿它当分母会得到 scale=1.0，
// 于是所有按 pt 写的矩形都被当成 px —— 裁出来的是左上角四分之一，看着还像一块正常的界面。
let logicalWidth = a.count >= 8 ? Double(a[7])! : rep.size.width
let scale = Double(cg.width) / logicalWidth
let src = CGRect(x: x * scale, y: y * scale, width: w * scale, height: h * scale).integral
guard src.maxX <= Double(cg.width), src.maxY <= Double(cg.height) else {
    print("矩形超出帧：\(src) vs \(cg.width)x\(cg.height)"); exit(2)
}
guard let cropped = cg.cropping(to: src) else { print("裁不出 \(src)"); exit(2) }
let out = NSBitmapImageRep(cgImage: cropped)
guard let data = out.representation(using: .png, properties: [:]) else { print("编码失败"); exit(2) }
try! data.write(to: URL(fileURLWithPath: a[2]))
print("写出 \(a[2]) \(cropped.width)x\(cropped.height)（源矩形 \(src)，scale=\(scale)）")
