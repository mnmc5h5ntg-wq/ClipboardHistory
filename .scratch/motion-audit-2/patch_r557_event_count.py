# -*- coding: utf-8 -*-
"""R557：给计数器加"环里事件数"这一格读数（判据要能不加 reset 就量出增量）。"""
import io

p = 'Sources/ClipboardHistoryApp/Utilities/ProtectedFileAccessLedger.swift'
s = io.open(p, encoding='utf-8').read()

old = r'''    /// 这个文件在这一刻总共被碰了几次（四格求和）—— 「选中/预览之前不发生读取」判的就是它为 0。'''
assert s.count(old) == 1

new = r'''    /// 环里现有多少条事件。**跨任意一段代码量增量用这一格** ——
    /// 判据不许为了"数得干净"去加全局 reset（那会把别的判据正在数的东西抹掉），
    /// 而 `前后差` 不需要归零就能回答"这一段代码开过几个受保护文件"。
    static var eventCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return events.count
    }

    /// 这个文件在这一刻总共被碰了几次（四格求和）—— 「选中/预览之前不发生读取」判的就是它为 0。'''
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('eventCount added')
