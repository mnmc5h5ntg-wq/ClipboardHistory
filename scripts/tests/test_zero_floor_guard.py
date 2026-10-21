#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R284 / BACKLOG 336：地板由被统计量自己推出时，0 地板会把"无从判定"报成一个数。

为什么这一卷存在（R284 现读，两笔叠在一起）：
1. 我给 330 写的 spike 里，`动帧` 的地板是 `峰值 × 0.15`。真卷峰值=0.000 ⇒ 地板=0 ⇒
   谓词 `delta >= 0` 对每一帧成立，于是打印出 **`动帧=26`** 这种看着像结论的假数（真数是"无从判定"）。
2. 而这颗仓库里**早就知道**这件事：`MotionFilmstripTests.lastMovingFrame` 的第二道地板
   `max(floor, minimumVisibleChange)` 的注释写着"两栏全零时线也是 0，而 0 >= 0 会让每一帧都算还在变
   —— 真值表的 (c) 第一次就是这么红的"（R59）。也就是说保护只活在**那一个函数里面**，
   是一个约定，不是一条规则：任何一个新调用点自己写 `>= peak * 0.15` 都会重新踩进去，我就是那个新调用点。

这一卷把那个约定升成会红的扫描：凡是"地板 = 同批样本的峰值/最大值 × 比例"这种写法，
必须同时出现一道**绝对**下限（`minimumVisibleChange` / `min_floor` / `max(` 包起来），
否则点名。豁免要走显式名册（`EXEMPT`），名册本身要能红（空名单=红，R99）。
"""
import io
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCAN_DIRS = ('scripts', os.path.join('ClipboardHistory', 'Tests'))
# 相对地板：同一批样本的峰值/最大值乘一个比例，直接进比较式
RELATIVE_FLOOR = re.compile(r'>=\s*(?:[A-Za-z_][\w.]*\s*\([^)]*\)\s*\*|peak\b[^*\n]*\*)')
# 绝对下限的三种合法形状：常量名、max(...) 包一层、显式 min_floor
ABSOLUTE_CLAMP = re.compile(r'minimumVisibleChange|min_floor|max\s*\(|MIN_VISIBLE|ABSOLUTE_FLOOR')
# 只扫判"有没有在动/还在动"的那几行 —— 别把无关的乘法也判进来
MOTIONISH = re.compile(r'(moving|frames?After|lastMoving|still|changing)', re.I)
EXEMPT = set()   # 显式名册：目前没有一项被豁免（有就要写理由）


def code_lines(path):
    """剥注释后的可执行行（R76/R100：判"用没用"要判它出现在可执行行里）。"""
    text = io.open(path, encoding='utf-8', errors='replace').read()
    out = []
    for no, line in enumerate(text.split('\n'), 1):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('//') or s.startswith('///'):
            continue
        out.append((no, line.split('#', 1)[0].split('//', 1)[0]))
    return out


SELF = 'scripts/tests/test_zero_floor_guard.py'
FUNC_START = re.compile(r'^\s{4}(?:public |private |fileprivate |nonisolated[^\n]* )*static func \w+')


def swift_function_blobs(text):
    """把 Swift 文件按 `static func` 切成块（行号 → 该函数体）。

    R284 现读的第一版**逐行**扫，于是三处合法写法被误点名：它们的绝对下限写在**上一行的 guard** 里
    （`guard let peak = fractions.max(), peak >= minimumVisibleChange else { return nil }`），
    下一行才是 `>= peak * stepFloorRatio`。判"有没有绝对下限"要问的是**那颗函数**，
    不是那一行 —— 与 D-247 同族（守卫必须与被守卫的尺读同一个对象）。
    """
    lines = text.split('\n')
    starts = [i for i, l in enumerate(lines) if FUNC_START.match(l)]
    blobs = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(lines)
        blobs.append((s + 1, e, '\n'.join(lines[s:e])))
    return blobs


def scan(root=REPO):
    offenders, scanned = [], 0
    for base in SCAN_DIRS:
        d = os.path.join(root, base)
        if not os.path.isdir(d):
            raise AssertionError('扫描目录不在：' + d + ' ⇒ 这把尺指不到对象，不许读成没问题')
        for dirpath, _dirs, files in os.walk(d):
            for name in sorted(files):
                if not name.endswith(('.py', '.swift', '.sh')):
                    continue
                path = os.path.join(dirpath, name)
                scanned += 1
                rel = os.path.relpath(path, root)
                if rel in EXEMPT or rel == SELF:
                    # 本文件自己那一行是**正对照样本**（它必须长得像坏写法）—— 排除它，
                    # 而不是排除整类；这一格由 test_the_scanner_finds_the_real_offender_shape 承重。
                    continue
                text = io.open(path, encoding='utf-8', errors='replace').read()
                if name.endswith('.swift'):
                    for s, e, blob in swift_function_blobs(text):
                        for off in RELATIVE_FLOOR.finditer(blob):
                            line = blob[:off.start()].count('\n') + s
                            if not MOTIONISH.search(blob.splitlines()[line - s]):
                                continue
                            if not ABSOLUTE_CLAMP.search(blob):
                                offenders.append('%s:%d' % (rel, line))
                    continue
                for no, line in code_lines(path):
                    if not MOTIONISH.search(line):
                        continue
                    if RELATIVE_FLOOR.search(line) and not ABSOLUTE_CLAMP.search(line):
                        offenders.append('%s:%d' % (rel, no))
    return offenders, scanned


class ZeroFloorGuardTests(unittest.TestCase):
    def test_the_scanner_finds_the_real_offender_shape(self):
        """正对照：本轮真踩的那一行形状必须被抓到（否则这一卷只是在证明"没有东西可红"）。"""
        line = '        let moving = fractions[start...].filter { $0 >= peak * 0.15 }  // moving frames'
        self.assertTrue(MOTIONISH.search(line), '形状词没命中 ⇒ 扫描范围比被测对象窄')
        self.assertTrue(RELATIVE_FLOOR.search(line), '相对地板没被认出来 ⇒ 这把尺坏了')
        self.assertFalse(ABSOLUTE_CLAMP.search(line), '这一行没有绝对下限，对照不该被自己放过')

    def test_the_shipped_clamp_is_not_flagged(self):
        """负对照：仓库里那一行**合法**的写法不许被点名（否则这条门只会逼人删掉判据）。"""
        line = '        return fractions.lastIndex { $0 >= max(floor, minimumVisibleChange) }  // lastMoving'
        self.assertTrue(MOTIONISH.search(line))
        self.assertTrue(ABSOLUTE_CLAMP.search(line), 'max(...) 这一层要认成绝对下限')

    def test_a_multi_line_swift_guard_is_not_a_false_positive(self):
        """负对照（R284 现读）：绝对下限写在上一行的 guard 里，也必须被认成有下限。"""
        blob = ('    static func changedSpanElapsedMilliseconds(stamps: [TimeInterval], fractions: [Double]) -> Double? {\n'
                '        guard let peak = fractions.max(), peak >= minimumVisibleChange else { return nil }\n'
                '        let moving = fractions.indices.filter { fractions[$0] >= peak * stepFloorRatio }\n'
                '        return moving.count == 0 ? nil : 1\n    }\n')
        self.assertTrue(RELATIVE_FLOOR.search(blob.splitlines()[2]), '相对地板没被认出 ⇒ 对照失效')
        self.assertTrue(ABSOLUTE_CLAMP.search(blob), '同一颗函数里的绝对下限必须算数（逐行扫会漏，这就是三处误点名的成因）')

    def test_no_relative_floor_without_an_absolute_clamp_in_the_repo(self):
        offenders, scanned = scan()
        self.assertGreaterEqual(scanned, 50,
                                '只扫到 %d 个文件 ⇒ 扫描范围塌了，这一格是恒真的门' % scanned)
        self.assertEqual([], offenders,
                         '这些行用同批样本的峰值当地板却没有绝对下限：峰值=0 时它们会把"无从判定"'
                         '报成一个数（R284 的 spike 就是这么打印出 动帧=26 的）：%s' % offenders[:8])

    def test_the_exempt_roster_is_not_a_trash_bin(self):
        """名册里每一项都必须真的存在，且当前确实会被点名（否则豁免会腐烂成隐形通道）。"""
        for rel in sorted(EXEMPT):
            self.assertTrue(os.path.exists(os.path.join(REPO, rel)), '豁免名册指向不存在的文件：' + rel)


if __name__ == '__main__':
    o, s = scan()
    print('ZERO_FLOOR_SCAN files=%d offenders=%d named=%s' % (s, len(o), ','.join(o[:6]) or '无'))
    unittest.main(verbosity=2)
