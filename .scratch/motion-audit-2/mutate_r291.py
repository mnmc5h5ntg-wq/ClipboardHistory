#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R291 的变异表（第 290 轮 / Round 288）：详情区段落线"跨整幅"这条约定，三轴各一把刀（D-244）。

判据在测试进程里现渲染（`render` → PNG → 像素），所以三把刀**不必重捕帧**（D-240 那族的区分写在表头）。

· M850 产品轴 —— 把段落线左端抬进内容内缩（`Divider()` → 加 `.padding(.leading, 20)`）：
  它既不是面板的边也不是内容的边 ⇒ 判据必须红，红话里印出「左沿读到 20.0」。
· M851 **身份轴** —— 把"最靠上的细线"那条排序反过来 ⇒ 判据拿行分隔线当段落线，红在「左沿读到 82.0」。
  这一把是本轮补出来的：第一版用"左沿贴着窗边"当线的**身份**，于是 M850 报 WRONG_CELL ——
  两把刀挤在同一个出口上等于只有一把有牙。身份改成按结构认之后，身份本身也要有一把刀。
· M852 对象闸门 —— 把前提从「细线 ≥2 条」抬到 ≥99 ⇒ 必须红在「尺没有对象」，不许安静地通过。

「跑起来了没」按结论行的形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
判定按**失败正文**而不只按格子名（D-244）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DETAILS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailView.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
SECTION = 'UICaptureTests/testDetailSectionRuleSpansTheWholePane'

N_LINE = u'            header(for: entry, detailWidth: detailWidth)\n            Divider()\n'
R_LINE = u'            header(for: entry, detailWidth: detailWidth)\n            Divider()\n                .padding(.leading, 20)\n'
N_SORT = '.sorted { $0.y0 < $1.y0 }'
N_GUARD = 'guard thin.count >= 2, let line = thin.first else {'

ARMS = [
    ('M850', u'段落线左端抬进内容内缩（第三种约定）= 产品轴', DETAILS,
     N_LINE, R_LINE, SECTION, u'左沿读到 20.0'),
    ('M851', u'把"最靠上的细线"反过来认 = 身份轴', HARNESS,
     N_SORT, N_SORT.replace('$0.y0 < $1.y0', '$0.y0 > $1.y0'), SECTION, u'左沿读到 82.0'),
    ('M852', u'前提抬到 ≥99 条（尺该喊没有对象）= 对象闸门轴', HARNESS,
     N_GUARD, N_GUARD.replace('>= 2', '>= 99'), SECTION, u'尺没有对象'),
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
    # 允许按刀号单跑（`python3 mutate_r291.py M850`）：重跑全表要三次构建，
    # 而补一格读数常常只要一把。全表判据不变：只数被选中的那些。
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R291_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R291_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
