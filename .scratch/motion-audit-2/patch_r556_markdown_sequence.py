# -*- coding: utf-8 -*-
"""R556 / 629：给 markdown 标签那一格的读数补上「相邻帧差序列」。"""
import io

p = 'Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift'
s = io.open(p, encoding='utf-8').read()

old = r'''            emit("MOTION_MARKDOWN_MODE_FADE scale=\(Int(scale))x 帧数=\(frames.count) 过渡帧数=\(span) "
                 + "峰值=\(String(format: "%.4f", peak)) 声明=\(Int(scenario.declaredDurationMilliseconds))ms")'''
assert s.count(old) == 1, s.count(old)

new = r'''            // R556 / 629：只打「过渡帧数 + 峰值」分不开两种**修法相反**的解释 ——
            // runner 读到 1 帧时，既可能是"标签真的没演"（一步切换），也可能是"这条带在 1x/无头
            // 机器上墨太少、过程被逐帧阈值切碎"。两种的修法一个要改产品、一个要改尺，
            // 而现有读数对二者给的是同一句话。所以把**相邻帧差序列**一起打出来：
            // 单帧尖峰（0,0,.0193,0,0）⇒ 真是一步切换；一串小台阶（.004,.006,.006,.002）⇒ 过程在。
            let sequence = fractions.prefix(12).map { String(format: "%.4f", $0) }.joined(separator: ",")
            emit("MOTION_MARKDOWN_MODE_FADE scale=\(Int(scale))x 帧数=\(frames.count) 过渡帧数=\(span) "
                 + "峰值=\(String(format: "%.4f", peak)) 声明=\(Int(scenario.declaredDurationMilliseconds))ms "
                 + "相邻帧差=[\(sequence)]")'''

s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('patched')
