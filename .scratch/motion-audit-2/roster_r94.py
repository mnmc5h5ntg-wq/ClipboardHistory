#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R94：按 run 38857388449 的 `NOW_RUNS` 逐条点名，把在屏名册里该翻的翻成 can。

写成脚本而不是手改：这份名册是 `probe_coverage_gate.py` 的输入，手改最容易把 reason 写成散文
而让 `REASONLESS`/`NOW_RUNS` 那两格失去对象（R91 的 U-206 同一族：台账里的断言要能被机器复查）。
每条翻转都必须带**读来的**判定（passed / skipped），不许写"应该是"。
"""
import json
import os
import sys

REPO = '/Users/wangziyi/Codex_Project0'
PATH = os.path.join(REPO, 'scripts/probe_coverage_expectations.json')

# 从 run 38857388449 的 `NOW_RUNS …（判定）` 逐条抄来的，一个字符都不猜。
RAN = {
    "testAccessibilityTreeCoverage": "skipped",
    "testFocusChainReachesTheSearchFieldAndNotOnlyTheDetailTextView": "passed",
    "testFrameIntervalsUnderStateChanges": "passed",
    "testIntakeBehindATallPinnedBlockRevealsTheNewRow": "passed",
    "testMarkdownFilePreviewRendersInARealWindow": "passed",
    "testOffScreenProgrammaticSelectionIsRevealedAndNotJumped": "passed",
}
STUCK = "testRightClickMenusAppKitWouldShowAreChinese"
# R93 才登记的那条（`6c5ca95`），38857388449 跑的是 `8e6ed15`，源码里没有它。
NEW_IN_R93 = "testRowProxyCensusAsksTheConsequenceNotTheShape"

CAUSE = ("run 38857388449（`8e6ed15`）在屏那一步：`ui suite exit: 137  已下结论的用例: 6`、"
         "`UI_PROBE_PROGRESS started=7 concluded=6`、`UI_PROBE_CHANNELS_AGREE=1`。")


def main():
    with open(PATH, encoding='utf-8') as handle:
        data = json.load(handle)
    cases = data['cases']
    for name, verdict in RAN.items():
        if name not in cases:
            raise SystemExit('名册里没有 %s ⇒ 抄来的名单与文件已经脱钩，拒绝写盘' % name)
        entry = cases[name]
        if entry.get('runner') != 'cannot':
            raise SystemExit('%s 登记不是 cannot（是 %r）⇒ 本轮的前提不成立' % (name, entry.get('runner')))
        entry['runner'] = 'can'
        # `can` 只回答"runner 上跑得动、会下结论"这一件事，它**不等于**"这次给了产品判断"：
        # skip 也是结论（证明执行到了），但 skip 不判产品。第一版我给六条写了同一句
        # 「产品结论可以引用它」，而 `testAccessibilityTreeCoverage` 那次读数是
        # `NOW_RUNS …（skipped）` ⇒ 那句话对这一条是假的。判定不同，话就得分开写。
        if verdict == "passed":
            tail = ("⇒ runner 上它**跑完且绿**：以后这条判据的产品结论可以引用那台机器的读数，"
                    "不必再带「只有作者本机跑过」。")
        else:
            tail = ("⇒ 翻 can 只到「runner 跑得动、会给出结论」这一层：这次它的结论是 "
                    "`skipped`，也就是探针自己的前提在那台机器上不成立 —— **"
                    "skip 不是通过**（闸门文档里就写了这句），所以这条在 runner 上今天仍不产出产品判断，"
                    "要等它跑到产品断言。")
        entry['reason'] = ("R94 翻成 can，依据是**读来的**而不是推断：这一次 `probe_coverage_gate.py` "
                           "逐条点名 `NOW_RUNS %s：…而这次它下结论了（%s）`。%s"
                           "%s" % (name, verdict, CAUSE, tail))
    if cases[STUCK].get('runner') != 'cannot':
        raise SystemExit('%s 应当仍是 cannot（它就是那 240 秒里没闭口的那一条）' % STUCK)
    cases[STUCK]['reason'] = (CAUSE + " 本条**就是**那个开口没闭口的：`UI_PROBE_HUNG=%s`，"
                              "240s 看门狗收掉。本机 R93 实测它 2.016 秒跑完 ⇒ 不是恒挂，"
                              "是在这台 runner 上要么挂要么慢 ⇒ BACKLOG 132 第一格：`sample` 它，"
                              "分清挂与慢；不许靠放宽看门狗把它变成「能跑」。" % STUCK)
    for name, entry in cases.items():
        if entry.get('runner') == 'cannot' and name not in (STUCK,):
            if name == NEW_IN_R93:
                # 这一条不能用「排在 STUCK 之后」糊过去：`8e6ed15` 的源码里根本没有它，
                # 闸门那次报的是 `源码用例=10 登记=10`，而它 10-15 才登记（`6c5ca95`）。
                # 写成"排队没到"会给一条**从未被编译过**的判据编一个不存在的成因。
                entry['reason'] = ("%s 不在 `8e6ed15` 的源码里（那次闸门读数是 `源码用例=10 登记=10`），"
                                   "本条是 `%s` 才登记的 ⇒ 那一次谈不上跑没跑。"
                                   "登记仍是 cannot：下一次在屏那步会给出它的名字，届时有读数再翻。"
                                   % (CAUSE, NEW_IN_R93))
                continue
            entry['reason'] = (CAUSE + " 本条排在 `%s` 之后 ⇒ 今天到不了它（132 修好后重估）。" % STUCK)
    data['evidence'] = {
        "run": "38857388449",
        "reading": ("ui suite exit: 137  executed: 0  已下结论的用例: 6 | UI_PROBE_PROGRESS started=7 "
                    "concluded=6 | UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese | "
                    "UI_PROBE_CHANNELS_AGREE=1 | PROBE_COVERAGE_SUMMARY …本次下结论=6 红=6"),
    }
    data['_r94'] = ("R94：闸门自己逐条点名之后，六条翻成 can。判定是读来的、且**分开写**："
                    "`testAccessibilityTreeCoverage` 那次的读数是 skipped ⇒ 它只证明 runner 跑得动，"
                    "今天仍不产出产品判断；其余五条是 passed ⇒ 产品结论第一次能引用那台机器。"
                    "全部六行的名字与判定都来自 `On-screen probe coverage floor` 那一步的 NOW_RUNS，没有一条是猜的"
                    "（同一次 run 的 `Swift tests (executed-count gate)` 步骤里同一卷十条全 skip，"
                    "那是**另一台壳、另一个环境变量**下的结果，按步骤名过滤才不会被读成「探针在 runner 上也是全 skip」——"
                    "这次抓到了 `8e6ed15` 那一步的逐字输出，`已下结论的用例: 6` 与 NOW_RUNS 六行同源）。"
                    "意外收获：`testFrameIntervalsUnderStateChanges` 在 runner 上是 **passed** 而非 skip "
                    "⇒ `FRAME_CHANNEL` 在那台机器上拿到了非零帧样本，R91 留的那格（runner 上 n=0 还是有 tick）"
                    "答案是「有 tick」；而本机同一格是 skip（显示器睡着 ⇒ 0 个样本）"
                    "⇒ 两台机器在这一格上相反，判「没跑」与「跑过」要按机器分开记。"
                    "剩下 5 条仍是 cannot，但成因分三种写法：1 条就是挂住的那条（132）、"
                    "3 条真的排在它之后、1 条（`testRowProxyCensusAsksTheConsequenceNotTheShape`）"
                    "根本不在这次构建的源码里 ⇒ 不许把「没编译过」写成「排队没到」。")
    with open(PATH, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    can = sum(1 for e in cases.values() if e.get('runner') == 'can')
    print('cases=%d can=%d cannot=%d' % (len(cases), can, len(cases) - can))
    return 0


if __name__ == '__main__':
    sys.exit(main())
