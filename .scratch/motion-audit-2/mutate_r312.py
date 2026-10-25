#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R312 的变异表（第 311 轮 / Round 309）：三根轴必须同时可查，删一根就要红。

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
import io
import os
import re
import subprocess
import sys

from readback import single_substitution_lands

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTFILE = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift'
FILTER = 'HeatmapHoverEvidenceTests'
ADJ_TEST = 'testAdjacentHeatLevelsAreSeparableOnTheRightAxis'

MEAN_COL = (u'                                    + "均值通道差=\\(String(format: "%.2f", meanDelta)) "\n')
LUMA_COL = (u'                                    + "亮度差=\\(String(format: "%.2f", lumaDelta)) "\n')
AXIS_DEF = (u'                    XCTAssertGreaterThanOrEqual(maxDelta, meanDelta,\n'
            u'                        "最大通道差不小于均值通道差是这把尺的定义；反了说明取错了轴")\n')
AXIS_DEF_FLIPPED = (u'                    XCTAssertLessThanOrEqual(maxDelta, meanDelta,\n'
                    u'                        "最大通道差不小于均值通道差是这把尺的定义；反了说明取错了轴")\n')

# (刀号, 说明, 目标文件, needle, 替换, 期望红的格子, 期望正文里的串)
ARMS = [
    ('M908', u'删掉均值通道那一列 = 把 356 那次更正的证人拆掉', TESTFILE, MEAN_COL, u'',
     ADJ_TEST, u'读数少了一根轴'),
    ('M909', u'删掉亮度差那一列 = R51/R53 那根轴没了证人', TESTFILE, LUMA_COL, u'',
     ADJ_TEST, u'读数少了一根轴'),
    ('M910', u'把「最大通道 ≥ 均值通道」反号 = 取错轴的定义级卫兵', TESTFILE, AXIS_DEF, AXIS_DEF_FLIPPED,
     ADJ_TEST, u'反了说明取错了轴'),
]

# R313 / BACKLOG 367：这张表**自己声明**哪根是针。`scripts/hidden_arms.py` 见到 `NEEDLES`
# 就把这些臂从「集合存在性（只配当下界）」那一箱挪到「逐根判命中（可加总的真数）」那一箱：
# 一根针在盘上找不到就记一根，而不是等整臂所有候选都不命中才响。
# 为什么现在才声明：R311 改 α 弄腐烂了三根针，而 rot 只报了两根 —— 漏的那根正是被
# 同一臂里还活着的别的字符串洗白的（见 BACKLOG 366）。声明之后这类漏报不再可能。
NEEDLES = {
    "M908": [MEAN_COL],
    "M909": [LUMA_COL],
    "M910": [AXIS_DEF],
}

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
        # R366 / 426：回读判**盘上恰好等于预期 diff**（删臂 repl 为空也成立），不判替换串出现几次 ——
        # 后者两头都不对：repl 在别处本来就有会假红（R350），删臂的 `"abc".count("")` 还会读成 len+1。
        if not single_substitution_lands(original, needle, repl, after):
            print('%s NOT_RUN 落刀后回读与预期 diff 不一致' % arm_id, flush=True)
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
        print('R312_MUTATE NOT_RUN 未知刀号 %s' % sorted(unknown), flush=True)
        return 2
    ran, fails, text = run_swift()
    if not ran or fails:
        print('R312_BASELINE NOT_RUN 基线不绿（跑=%d 红=%s）⇒ 拒绝出表' % (ran, fails), flush=True)
        tail = '\n'.join(line for line in text.splitlines() if 'error:' in line)[:600]
        print(tail, flush=True)
        return 1
    print('R312_BASELINE OK（判据卷 %d 格全绿）' % ran, flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R312_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
