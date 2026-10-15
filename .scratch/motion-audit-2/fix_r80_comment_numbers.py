#!/usr/bin/env python3
# R80：把注释里**我先把数写下来、再去量**的那几行换成判据自己打出来的读数（U-139 那一族：
# 注释不许替事实背书 —— 这次背书的是我自己刚写下的假设数）。
import io
import sys

path = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
lines = io.open(path, encoding="utf-8").read().split("\n")

def find(needle):
    hits = [i for i, l in enumerate(lines) if needle in l]
    if len(hits) != 1:
        sys.exit("锚点不唯一或没找到：%r -> %r" % (needle, hits))
    return hits[0]

a = find("来历（本机 2× 那一遍 `QUICKPICK_FOCUS_INK` 打的数）")
assert "394.5" in lines[a] and "带墨面积 1075" in lines[a + 1], (lines[a + 1],)
assert lines[a + 2].strip().startswith("/// 证人臂撤占位字"), lines[a + 2]
lines[a:a + 3] = [
    "    /// 来历（本机 2× 那一遍 `QUICKPICK_FOCUS_INK` 打的数，亮 / 暗）：",
    "    ///   焦点搬动 **98.7 / 113.3pt²**、那一格现有墨 **268.7 / 330.1pt²**、占比 **0.367 / 0.343**、",
    "    ///   同态重拍噪声 **0.0 / 0.0pt²**、证人臂撤占位字 **268.7 / 330.0pt²**、打进字 **236.7 / 283.9pt²**。",
    "    /// ⇒ 40pt² 是实测焦点搬动量的约 1/2.5～1/3，8% 是实测占比的约 1/4.5；而 runner 那一侧按 R79 读到的",
    "    ///   均值差换算约 **1.3pt²**（0.05×6400÷255）—— 在地板下面 30 倍。这道地板**不是**为 runner 调的",
    "    ///   （R38：不许拿一台机器的读数当另一台的地板），它两边都留了倍数余量；",
    "    ///   runner 过不了的时候由**证人臂**决定那是『尺在这一格瞎了』还是『这台机器不调淡』。",
]

b = find("同一个词在两个判据里含义不同就别统一成一个布尔值）")
assert "1000pt²" in lines[b], lines[b]
lines[b] = lines[b].replace("本机实测这条臂 ≈ 1000pt²。", "本机实测这条臂 268.7 / 330.0pt²。")

c = find("今天它是那一串占位字退后（本机实测 394.5 / 453.9pt²、")
assert lines[c + 1].strip().startswith("+ \"旧那把像素个数尺"), lines[c + 1]
lines[c] = lines[c].replace("394.5 / 453.9pt²", "98.7 / 113.3pt²")

io.open(path, "w", encoding="utf-8").write("\n".join(lines))
print("patched: focus floor provenance + competence provenance + assertion message")
