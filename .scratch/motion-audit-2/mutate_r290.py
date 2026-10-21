#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R290 的变异表（第 289 轮 / Round 287）：多文件行的**左端**那条轴，三轴各一把刀（D-244）。

对象是产品源码 `DetailView.swift` 与判据自己 `UICaptureHarness.swift`。判据在**测试进程里现渲染**
（`render` → PNG → 像素），所以这三把刀**不必重捕帧**（与 D-240 那族「重捕型」的区分写在表头，R289 同）。

· M845 产品轴 —— 把分隔线左端退回那颗裸字面量（`.padding(.leading, rowTextLeading)` → `48`）。
  这一刀同时是**改前那笔账的读数**：红话里印出来的差值就是"不导出会差多少"（R289 的 D-268 同族）。
· M846 **漂移轴**（这一把才是本轮真正买的东西）—— 把行首 HStack 的 spacing 改成另一份数（10 → 14）。
  列宽与间距各写一份的时候，文字会走到 90pt 而分隔线还停在 82pt —— 屏幕上看得见，代码里没人红。
  这一刀证明"导出"不是整理风格：它把"两处各写一份数"变成会红的判据。
· M847 尺的对象闸门 —— 把 `columnClusters` 的**默认**缝宽从 12px 抬到 40px（超过列间距 20px）。
  三列会被并成一簇 ⇒ 判据必须红在「墨簇数不够」那条出口上，而不是安静地拿箭头那簇当文字。
  已知答案的对照自己显式传 gap（12 与 4 两侧都钉），所以这一刀只可能红在产品判据那条 —— 两件事分开。

「跑起来了没」按结论行的**形状**认；没有结论行一律 NOT_RUN —— 编译红不算 CAUGHT（D-243）。
判定按**失败正文**而不只按格子名：两条红可能落在同一格里说的是两件事（D-244）。
根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DETAILS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailView.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
LEFT = 'UICaptureTests/testMultiFileRowSeparatorsStartAtTheTextAxis'
CONTROL = 'UICaptureTests/testColumnClusterRulerKnowsItsOwnAnswers'

N_LEADING = '.padding(.leading, MultiFilePreviewLayout.rowTextLeading)'
N_SPACING = 'HStack(spacing: MultiFilePreviewLayout.rowColumnSpacing)'
N_MERGE = 'paperDelta: Int = 24, mergeGapPx: Int = 12) -> [(x0: Int, x1: Int)] {'

ARMS = [
    ('M845', u'分隔线左端退回裸字面量 48 = 产品轴', DETAILS,
     N_LEADING, '.padding(.leading, 48)', LEFT, u'行分隔线左端'),
    ('M846', u'行首列间距另写一份（10→14）而左端没跟上 = 漂移轴', DETAILS,
     N_SPACING, 'HStack(spacing: 14)', LEFT, u'行分隔线左端'),
    ('M847', u'把列缝宽抬到 40px（三列并成一簇）= 对象闸门轴', HARNESS,
     N_MERGE, N_MERGE.replace('mergeGapPx: Int = 12', 'mergeGapPx: Int = 40'), LEFT, u'墨簇'),
]


EXECUTED = re.compile(r'Executed (\d+) tests?, with (\d+) failures?')
FAILED_CASE = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def run(filter_name):
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    proc = subprocess.run(['swift', 'test', '--filter', filter_name],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    executed = EXECUTED.findall(text)
    n_ran = int(executed[-1][0]) if executed else 0
    n_fail = int(executed[-1][1]) if executed else 0
    names = sorted(set(FAILED_CASE.findall(text)))
    return proc.returncode, n_ran, n_fail, names, text


def run_arm(arm_id, why, target, needle, repl, filter_name, expect_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        code, n_ran, n_fail, names, text = run(filter_name)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not n_ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    # 判定按**失败正文**而不是只按格子名：两条红可能落在同一格里说的是两件事（D-244）。
    named = [expect_text in ln for ln in text.splitlines() if 'error:' in ln]
    if n_fail and names and any(named):
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d exit=%d）'
              % (arm_id, why, ', '.join(names), n_ran, n_fail, code), flush=True)
        for line in text.splitlines():
            if expect_text in line and 'error:' in line:
                # 不打折：这一行的正文就是台账里那个「改前读数」的来源（R88：正文里的数字
                # 不许手抄，要从仪器读）。截断会把差值本身截掉。
                print('   正文=%s' % line.strip(), flush=True)
                break
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail,
             filter_name.split('/')[-1], expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    # 允许按刀号单跑（`python3 mutate_r290.py M846`）：重跑全表要三次构建，
    # 而补一格读数常常只要一把。全表判据不变：只数被选中的那些。
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R290_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R290_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
