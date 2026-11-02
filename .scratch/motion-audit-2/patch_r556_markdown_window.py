# -*- coding: utf-8 -*-
"""R556 / 629：markdown 标签那一格再补一个「窗口」读数（分岔的最后一格）。"""
import io

p = 'Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift'
s = io.open(p, encoding='utf-8').read()

old = r'''            let sequence = fractions.prefix(12).map { String(format: "%.4f", $0) }.joined(separator: ",")
            emit("MOTION_MARKDOWN_MODE_FADE scale=\(Int(scale))x 帧数=\(frames.count) 过渡帧数=\(span) "
                 + "峰值=\(String(format: "%.4f", peak)) 声明=\(Int(scenario.declaredDurationMilliseconds))ms "
                 + "相邻帧差=[\(sequence)]")'''
assert s.count(old) == 1, s.count(old)

new = r'''            let sequence = fractions.prefix(12).map { String(format: "%.4f", $0) }.joined(separator: ",")
            // R556：`窗口` 是这条判据原来**没有**的那一格（同卷的 `MOTION_SIDEBAR_COUNT` 有）。
            // 没有它，"过程只落在 1 格上"就分不开"真没演"与"每格太稀"——
            // 而这两者的修法相反：一个改产品，一个改采样。补上之后不必再为它单开一跑。
            let window = film.postTriggerWindowMilliseconds
            emit("MOTION_MARKDOWN_MODE_FADE scale=\(Int(scale))x 帧数=\(frames.count) 过渡帧数=\(span) "
                 + "峰值=\(String(format: "%.4f", peak)) 声明=\(Int(scenario.declaredDurationMilliseconds))ms "
                 + "窗口=\(Int(window.rounded()))ms 每格=\(String(format: "%.1f", window / max(Double(frames.count - 1), 1)))ms "
                 + "相邻帧差=[\(sequence)]")'''

s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('window field added')
