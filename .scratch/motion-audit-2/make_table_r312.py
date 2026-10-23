# -*- coding: utf-8 -*-
"""把 mutate_r308.py 复制来的执行器改成 R312 的表：只换常量、ARMS 与结论行前缀。

执行器（needle 恰好命中一次 / 落刀后回读 / 逐字节还原 / 基线不绿就拒发）一个字都不动 ——
那是被证过的形状，重写它就是把风险请回来。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mutate_r312.py")
text = io.open(P, encoding="utf-8").read()

DOC_OLD_START = u'"""R308 的变异表'
DOC_OLD_END = u'needle 恰好命中一次、落刀后回读、还原逐字节一致。\n"""\n'
DOC_NEW = u'''"""R312 的变异表（第 311 轮 / Round 309）：三根轴必须同时可查，删一根就要红。

本轮产品 0 文件，改的是判据本体：`testAdjacentHeatLevelsAreSeparableOnTheRightAxis`
新增一格断言，要求 16 条 `HEAT_ADJACENT` 读数**每一条都同时带**最大通道差 / 均值通道差 /
亮度差三根轴。这条断言钉的不是产品，是本轮那次更正的证人 —— BACKLOG 356 剩下的那一半
说的是「暗档最细一步 17.33 低于地板 18」，而 17.33 是**均值**那一根，承重判据在**最大通道**
那一根（同一步 = 30.00，本机与 runner 两跑都在账上）。两根轴只留一根，下一个人就会把
"色相步被均值冲淡"读成缺陷去改梯子（R51/R53 用亮度轴读出同一个假缺陷，是反方向的同族）。

三把刀（D-244：判定看失败格子名 + 正文里的串，不看退出码）：
· M908 删掉均值那一列 ⇒ 三轴同查必须点名「读数少了一根轴」。
· M909 删掉亮度那一列 ⇒ 同上（这一列是 R51/R53 那次的证人，不许先消失）。
· M910 把「最大通道 ≥ 均值通道」那根轴定义反号 ⇒ 必须红（它是"取错轴"的定义级卫兵）。

两种执行器各按自己的结论行认"跑起来了没"：Swift 看 `Executed N tests, with M failures`
（编译错 / 收集不到都不算 CAUGHT = D-243）。needle 恰好命中一次、落刀后回读、还原逐字节一致。
"""
'''
i = text.index(DOC_OLD_START)
j = text.index(DOC_OLD_END) + len(DOC_OLD_END)
text = text[:i] + DOC_NEW + text[j:]

BLOCK_START = text.index(u"TOKENS = ")
BLOCK_END = text.index(u"# 结论行有**两种形状**")
NEW_BLOCK = u'''TESTFILE = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift'
FILTER = 'HeatmapHoverEvidenceTests'
ADJ_TEST = 'testAdjacentHeatLevelsAreSeparableOnTheRightAxis'

MEAN_COL = (u'                                    + "均值通道差=\\\\(String(format: "%.2f", meanDelta)) "\\n')
LUMA_COL = (u'                                    + "亮度差=\\\\(String(format: "%.2f", lumaDelta)) "\\n')
AXIS_DEF = (u'                    XCTAssertGreaterThanOrEqual(maxDelta, meanDelta,\\n'
            u'                        "最大通道差不小于均值通道差是这把尺的定义；反了说明取错了轴")\\n')
AXIS_DEF_FLIPPED = (u'                    XCTAssertLessThanOrEqual(maxDelta, meanDelta,\\n'
                    u'                        "最大通道差不小于均值通道差是这把尺的定义；反了说明取错了轴")\\n')

# (刀号, 说明, 目标文件, needle, 替换, 期望红的格子, 期望正文里的串)
ARMS = [
    ('M908', u'删掉均值通道那一列 = 把 356 那次更正的证人拆掉', TESTFILE, MEAN_COL, u'',
     ADJ_TEST, u'读数少了一根轴'),
    ('M909', u'删掉亮度差那一列 = R51/R53 那根轴没了证人', TESTFILE, LUMA_COL, u'',
     ADJ_TEST, u'读数少了一根轴'),
    ('M910', u'把「最大通道 ≥ 均值通道」反号 = 取错轴的定义级卫兵', TESTFILE, AXIS_DEF, AXIS_DEF_FLIPPED,
     ADJ_TEST, u'反了说明取错了轴'),
]

'''
text = text[:BLOCK_START] + NEW_BLOCK + text[BLOCK_END:]
text = text.replace(u"R308_MUTATE", u"R312_MUTATE").replace(u"R308_BASELINE", u"R312_BASELINE")

assert u"R308" not in text, [l for l in text.splitlines() if u"R308" in l][:4]
io.open(P, "w", encoding="utf-8").write(text)
import ast
ast.parse(text)
print(u"R312_TABLE_OK lines=%d arms=3" % len(text.splitlines()))
