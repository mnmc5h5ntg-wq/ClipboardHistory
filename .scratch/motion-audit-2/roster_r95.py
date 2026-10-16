#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R95 的登记刷新：把四条 `cannot` 的**成因**从上一轮那句话换成这一轮读到的那句话。

只改 reason 与 evidence，**不翻任何一条的身份**（翻身份要的是"它下结论了"，
而这一轮四条仍然一次都没轮到 —— 那是排队，不是能力）。这一条纪律来自 D-151。

为什么要再刷一遍：R94 写的四条理由里，三条是"排在 X 之后"，一条是"不在 `8e6ed15` 的源码里"。
后一条在 run 38864545930（`82fbd1f`）之后**已经不成立** —— 那次闸门自己数出 `源码用例=11`，
而 `PROBE_QUEUED` 把它的名字点了出来。留着旧句子不是"少写一行注释"，是把一个**已被读数推翻的成因**
继续留在登记里（R87 那一课的反方向：那次是"没读到的名字不许登记"，这次是"读到的新名字要覆盖旧成因"）。

四条的共同新成因来自这三行读数（逐字取自作业日志，见 `r95_ci_readings.md`）：
    PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
    PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
    PROBE_QUEUED 4/11 条一次都没轮到：…
挂住那一条另算：它由 `UI_PROBE_HUNG` 点名，且 `UI_PROBE_HUNG_CHANNEL=pulse`、
`UI_PROBE_RUNNER_ALIVE=1` ⇒ "它 started 了却没 concluded，而且收掉那一刻进程还在"三件事同向。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/roster_r95.py /tmp/r94_ci_job.log
"""
import json
import re
import sys

PATH = 'scripts/probe_coverage_expectations.json'
RUN = '38864545930'
SHA = '82fbd1f'


def pick(text, pattern, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit('读数缺失：%s 里没找到 %s ⇒ 不写登记（缺读数比缺理由更坏）' % (label, pattern))
    return m


def main():
    log = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    summary = pick(log, r'PROBE_COVERAGE_SUMMARY ([^\n]*)', 'PROBE_COVERAGE_SUMMARY').group(1).strip()
    order = pick(log, r'PROBE_ORDER ([^\n]*)', 'PROBE_ORDER').group(1).strip()
    queued_line = pick(log, r'(PROBE_QUEUED [^\n]*)', 'PROBE_QUEUED').group(1).strip()
    hung = pick(log, r'UI_PROBE_HUNG=(\w+)', 'UI_PROBE_HUNG').group(1)
    alive = pick(log, r'UI_PROBE_RUNNER_ALIVE=(\S+)', 'RUNNER_ALIVE').group(1)
    channel = pick(log, r'UI_PROBE_HUNG_CHANNEL=(\S+)', 'HUNG_CHANNEL').group(1)
    names = queued_line.split('：')[-1].split()
    if len(names) != 4:
        raise SystemExit('PROBE_QUEUED 点了 %d 个名字，不是 4 ⇒ 与登记里的"四条 cannot 里除挂住那条"对不上，'
                         '先去看是哪一条换了身份' % len(names))

    data = json.load(open(PATH, encoding='utf-8'))
    cases = data['cases']
    base = ('run %s（`%s`）在屏那一步的三行读数：`%s`、`%s`、`%s`。'
            % (RUN, SHA, summary, order, queued_line.split('：')[0] + ' 4/11'))
    changed = []
    for name in names:
        if name == hung:
            raise SystemExit('%s 既在 PROBE_QUEUED 里又被 UI_PROBE_HUNG 点名 ⇒ 两条读数互相矛盾，'
                             '本轮不改登记' % name)
        if name not in cases:
            raise SystemExit('PROBE_QUEUED 点了登记里没有的名字 %s ⇒ 登记缺条，先补条再来刷理由' % name)
        if cases[name]['runner'] != 'cannot':
            raise SystemExit('%s 登记是 can，却出现在一次都没轮到的名单里 ⇒ 那是 NOT_RUN 那一格该红的事，'
                             '不该由脚本悄悄翻身份' % name)
        cases[name]['reason'] = (base + ' 本条**一次都没轮到**（名字由 `PROBE_QUEUED` 逐条点名，'
                                        '不再是从字母序推的）⇒ 排队没到，不是跑不动。'
                                 '132 那格（挂住前先把栈拍下来）修好之后重估。')
        changed.append(name)
    # 挂住那条：成因仍然是"挂"，但这一轮多了两格同向的读数，把它们写进理由。
    if hung in cases:
        cases[hung]['reason'] = (
            'run %s（`%s`）：`UI_PROBE_HUNG=%s`、`UI_PROBE_HUNG_CHANNEL=%s`、'
            '`UI_PROBE_RUNNER_ALIVE=%s`（看门狗收掉那一刻它还在）。三件事同向 ⇒ '
            '"它 started 了却没下结论"不是通道丢字，是它自己没往下走。'
            '**它挂在什么上仍然没有依据** —— 132 那格拍下来的 `sample` 栈才是答案，'
            '在那之前不许写成"它只是慢"。' % (RUN, SHA, hung, channel, alive))
        changed.append(hung + '（挂住那条：只补读数，不改判定）')
    ev = data.get('evidence')
    if not isinstance(ev, dict):
        raise SystemExit('evidence 不是 dict（%s）⇒ 别按自己的形状重写登记' % type(ev).__name__)
    ev['run'] = RUN
    ev['sha'] = SHA
    # 沿用登记原有的 `reading` 那一格（一条竖线分隔的读数串），不新造键：
    # 造新键会让下一次对账的人去猜"哪个才是出处"。
    ev['reading'] = ' | '.join([summary, order, queued_line,
                                'UI_PROBE_HUNG=%s' % hung,
                                'UI_PROBE_HUNG_CHANNEL=%s' % channel,
                                'UI_PROBE_RUNNER_ALIVE=%s' % alive])
    data['evidence'] = ev
    data['_r95'] = ('四条 cannot 的成因按 run %s 的 `PROBE_QUEUED` 逐条点名重写；'
                    '其中 `testRowProxyCensusAsksTheConsequenceNotTheShape` 的旧理由'
                    '（"不在 8e6ed15 的源码里"）已被那次 `源码用例=11` 推翻 ⇒ 换成"排队没到"。'
                    '身份一条没翻：这一轮没有任何一条新下结论。' % RUN)
    with open(PATH, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write('\n')
    print('ROSTER_R95 改了 %d 条理由：%s' % (len(changed), '、'.join(changed)))
    print('ROSTER_R95 身份变化=0（can=%d cannot=%d）'
          % (sum(1 for v in cases.values() if isinstance(v, dict) and v.get('runner') == 'can'),
             sum(1 for v in cases.values() if isinstance(v, dict) and v.get('runner') == 'cannot')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
