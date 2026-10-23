#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R308 的变异表（第 307 轮 / Round 305）：悬停那一圈搬到格子外面之后，新契约每一侧都要有牙。

本轮产品 2 个文件：`VisualTokens`（新令牌 `hoverRingGap`、环的透明度 0.30 → 0.20）与
`DailyCopyHeatmapView`（`strokeBorder` → `stroke` + `padding(-gap)`，圆角半径跟着外扩）。
判据侧新立三条、公开更正一条：
· `testHoverLeavesTheDataPixelsUntouched`（整格均值差必须 ≈0，现读 0.000）；
· `HEAT_RING_LEVEL_SPREAD` 那一格（同一动作在五档上的响度离散 ≤1.05，现读 1.000，旧画法 1.73…1.75）；
· halo 分类器的真值表（带不许伸进格子框、位置按行号点验、④c 同心）；
· 更正：`testHoverIsNotLouderThanTheDataRange` 的分子分母不再共用一条带（环搬出去之后
  外径那条带上 empty 与 bucket4 一模一样 ⇒ 分母恒为 0，旧写法会自己红成"没在量东西"）。

六把刀各钉一条独立的轴（D-244：判定按失败的格子名 + 正文里的串，不看退出码）：
· M889 画法退回 `strokeBorder` ⇒ 源码守卫必须点名「画法退回了」。
· M890 外推距离归零 ⇒ 「那一圈还在换掉数据像素」必须红（这条钉的是本轮的产品事实本身）。
· M891 摘掉 `.padding(-gap)` ⇒ 源码守卫必须点名「外推距离不再走令牌」。
· M892 环的透明度抬回 0.30 ⇒ 克制度那条必须红（0.30 在新几何下已越界）。
· M893 把 halo 分类器的**中心**也算错一格（本轮真犯过的那一次）⇒ 真值表必须红。
· M894 把裙边容差压成 0 ⇒ 抗锯齿那一行会被读成「裙边之外」⇒ confinement 必须红。

两种执行器各按自己的结论行认"跑起来了没"：Swift 看 `Executed N tests, with M failures`
（编译错 / 收集不到都不算 CAUGHT = D-243）。needle 恰好命中一次、落刀后回读、还原逐字节一致。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKENS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift'
CELL = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift'
TESTFILE = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift'
FILTER = 'HeatmapHoverEvidenceTests'

DRAW_NEW = (u'                VisualShape.rounded(VisualRadius.heatCell + VisualHeat.hoverRingGap)\n'
            u'                    .stroke(Color.primary.opacity(VisualHeat.hoverRingOpacity(isHovered: isHovered)),\n'
            u'                            lineWidth: VisualHeat.hoverStroke)\n'
            u'                    .padding(-VisualHeat.hoverRingGap)\n')
DRAW_OLD = (u'                VisualShape.rounded(VisualRadius.heatCell)\n'
            u'                    .strokeBorder(Color.primary.opacity(VisualHeat.hoverRingOpacity(isHovered: isHovered)),\n'
            u'                                  lineWidth: VisualHeat.hoverStroke)\n')
GAP_LINE = u'    static let hoverRingGap: CGFloat = 1\n'
GAP_ZERO = u'    static let hoverRingGap: CGFloat = 0\n'
PAD_LINE = u'                    .padding(-VisualHeat.hoverRingGap)\n'
ALPHA = u"        isHovered ? 0.23 : 0"  # R311 重钉：0.20 在 runner 上 17.11 < 地板 18 ⇒ 产品抬到 0.23
ALPHA_LOUD = u'        isHovered ? 0.30 : 0\n'
BAND_CENTER = (u'                let sdf = roundedRectSDF(px: Double(px) + 0.5 - Double(inset) - cellHalf,\n'
               u'                                         py: Double(py) + 0.5 - Double(inset) - cellHalf,\n'
               u'                                         half: outerHalf,\n')
BAND_CENTER_WRONG = (u'                let sdf = roundedRectSDF(px: Double(px) + 0.5 - Double(inset) - outerHalf,\n'
                     u'                                         py: Double(py) + 0.5 - Double(inset) - outerHalf,\n'
                     u'                                         half: outerHalf,\n')
FRINGE_LINE = u'                guard abs(sdf) <= strokePx / 2.0 + 1.5 else { continue }\n'
FRINGE_ZERO = u'                guard abs(sdf) <= strokePx / 2.0 + 0.0 else { continue }\n'

DATA_TEST = 'testHoverLeavesTheDataPixelsUntouched'
SOURCE_TEST = 'testGridCellsRouteThroughTheProductCellView'
LOUD_TEST = 'testHoverIsNotLouderThanOneDataStep'
TABLE_TEST = 'testRingBandSelectorIsATruthTable'
CONFINE_TEST = 'testHoverChangesOnlyTheRingBand'

# (刀号, 说明, 目标文件, needle, 替换, 期望红的格子, 期望正文里的串)
ARMS = [
    ('M889', u'画法退回 strokeBorder（环压回数据像素上）= 源码守卫那一侧', CELL, DRAW_NEW, DRAW_OLD,
     SOURCE_TEST, u'画法退回了'),
    ('M890', u'外推距离归零 = 本轮那条产品事实的牙', TOKENS, GAP_LINE, GAP_ZERO,
     DATA_TEST, u'那一圈还在换掉数据像素'),
    ('M891', u'摘掉 padding = 令牌与画面脱钩那一侧', CELL, PAD_LINE, u'',
     SOURCE_TEST, u'外推距离不再走令牌'),
    ('M892', u'环的透明度抬回 0.30 = 新几何下克制度越界', TOKENS, ALPHA, ALPHA_LOUD,
     LOUD_TEST, u'交互比一次真实的数据变化还响'),
    ('M893', u'把 halo 分类器的中心也算错（本轮真犯过）= 尺子自己的牙', TESTFILE,
     BAND_CENTER, BAND_CENTER_WRONG, TABLE_TEST, u'不再是同一圈'),
    ('M894', u'裙边容差压成 0 = 把抗锯齿读成"别处"', TESTFILE, FRINGE_LINE, FRINGE_ZERO,
     CONFINE_TEST, u'裙边之外有一处变了'),
]

# 结论行有**两种形状**（R168 记过这一族，我又踩了一次）：`Executed 13 tests, with 0 failures`
# 与 `Executed 92 tests, with 4 tests skipped and 0 failures`。只认后一种会把"跑起来了没"读成 0，
# 于是基线闸门以「跑=0」为由拒发整张表 —— 方向是安全的（宁可不出版），但白跑一遍。
EXECUTED = re.compile(r'Executed (\d+) tests?, with (?:\d+ tests? skipped and )?(\d+) failures?')
FAILED_CELL = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def swift_env():
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    return env


def run_swift():
    proc = subprocess.run(['swift', 'test', '--filter', FILTER],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=swift_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ex = EXECUTED.findall(text)
    return (int(ex[-1][0]) if ex else 0), sorted(set(FAILED_CELL.findall(text))), text


def run_arm(arm_id, why, target, needle, repl, want_fail, want_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        after = read(target)
        # 回读自证：删臂（替换串为空）时 `"abc".count("")` 不是 0 而是 len+1 ⇒ 会把一次真落刀
        # 读成"回读不是那一刀"。删臂要判的是**needle 没了**，不是"替换串出现一次"。
        ok = (after.count(repl) == 1) if repl else (after.count(needle) == 0)
        if not ok or after == original:
            print('%s NOT_RUN 落刀后回读不是那一刀' % arm_id, flush=True)
            return 'NOT_RUN'
        ran, fails, text = run_swift()
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    body = [line for line in text.splitlines() if want_text in line]
    if want_fail in fails and body:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d）' % (arm_id, why, ', '.join(fails), ran), flush=True)
        print('   正文=%s' % body[0].strip()[:220], flush=True)
        return 'CAUGHT'
    print('%s %s ｜ 跑=%d 红=%s 正文含串=%s ⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not fails else 'WRONG_CELL', ran, fails, bool(body),
             want_fail, want_text), flush=True)
    return 'ESCAPED' if not fails else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    unknown = only - set(a[0] for a in ARMS)
    if unknown:
        print('R308_MUTATE NOT_RUN 未知刀号 %s' % sorted(unknown), flush=True)
        return 2
    ran, fails, text = run_swift()
    if not ran or fails:
        print('R308_BASELINE NOT_RUN 基线不绿（跑=%d 红=%s）⇒ 拒绝出表' % (ran, fails), flush=True)
        tail = '\n'.join(line for line in text.splitlines() if 'error:' in line)[:600]
        print(tail, flush=True)
        return 1
    print('R308_BASELINE OK（判据卷 %d 格全绿）' % ran, flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R308_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
