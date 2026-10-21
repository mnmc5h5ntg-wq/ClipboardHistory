#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R289 的变异表（第 288 轮 / Round 286）：多文件详情区「两条右轴」那一格，三轴各一把刀（D-244）。

对象是产品源码 `DetailView.swift` 与判据自己 `UICaptureHarness.swift`。判据在**测试进程里现渲染**
（`render` → PNG → 像素），所以这三把刀**不必重捕帧** —— 与 D-240 那族「重捕型」不同：那族量的产物
在磁盘上，这一格量的产物在测试进程里现画。这条区分要写在账上，否则下一轮会以为「改了产品没重捕」。

· M842 产品轴 —— 把分隔线右端的内缩摘掉（`.padding(.trailing, …Inset)` → `0`）。
  这一刀同时是**改前那笔账的读数**：红话里印出来的差值就是「不接这份内缩时同一颗尺读到多少 pt」，
  我不用手抄（R88 的规矩：台账正文里的数字要从仪器读）。
· M843 尺的对象闸门 —— 把 `flatBands` 的**默认**跨度闸门从 0.5 抬到 0.98。
  正对照那一格（`testFlatBandRulerKnowsItsOwnAnswers`）自己显式传参，不受默认值影响 ⇒
  这一刀只可能红在产品判据那条「没量到对象」的出口上（`judged != 2`）。
  它钉的是「尺失去对象时必须响」，不是「产品把线画短了」—— 两种成因的红话不同，所以按正文判。
· M844 比较轴 —— 把 `changedXSpan` 的右端从「按比较赋值」退回 `hi = x`。
  这是本轮**真实撞过**的坏法：最后一行（药丸下沿的圆角）比中间行短 11px，
  于是 700.0pt 被读成 694.5pt，判据红在产品一条不存在的边界上。
  它必须红在已知答案的对照那一格（「右端读成 22」），因为那块形状就是为它造的。

「跑起来了没」按结论行的**形状**认；没有结论行一律 NOT_RUN —— 编译红不算 CAUGHT（D-243）。
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
PRODUCT = 'UICaptureTests/testMultiFileRowSeparatorsEndOnThePillRightAxis'
CONTROL = 'UICaptureTests/testChangedXSpanRulerKnowsItsOwnAnswers'

N_PRODUCT = '.padding(.trailing, MultiFilePreviewLayout.rowHorizontalInset)'
N_GATE = 'bytesPerRow: Int, minSpanFraction: Double = 0.5) -> [FlatBand] {'
# `if x > hi { hi = x }` 在卷子里出现 4 次（`changedXRange` 那一族也用同样的形状），所以锚点带上
# 它上面那行注释的尾巴 —— 整行字面、现读命中恰好 1 次（R88：位置锚点要整行，裸子串会撞）。
N_SPAN = u'那块形状钉住。\n                    if x > hi { hi = x }'
R_SPAN = u'那块形状钉住。\n                    hi = x'

ARMS = [
    ('M842', u'分隔线右端不再读那份内缩（trailing=0）= 产品轴', DETAILS,
     N_PRODUCT, '.padding(.trailing, 0)', PRODUCT, u'行分隔线右沿'),
    ('M843', u'把跨度闸门抬到 0.98（尺失去对象）= 对象闸门轴', HARNESS,
     N_GATE, N_GATE.replace('0.5', '0.98'), PRODUCT, u'尺没有对象'),
    ('M844', u'右端退回「最后一行」而不是全局最右 = 比较轴', HARNESS,
     N_SPAN, R_SPAN, CONTROL, u'右端读成 22'),
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
    # 允许按刀号单跑（`python3 mutate_r289.py M842`）：重跑全表要三次构建，
    # 而补一格读数常常只要一把。全表判据不变：只数被选中的那些。
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R289_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R289_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
