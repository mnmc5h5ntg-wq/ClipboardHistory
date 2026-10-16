#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R93：把在屏探针的 runner 名册成因改成 R91 CI 实测的那句，并登记新加的诊断判据。

写成脚本而不是手改 JSON：这份名册是**闸门读的**，手改容易把 reason 写成散文而让
`REASONLESS`/`NOW_RUNS` 那两格失去对象（R91 的 U-206 同一族：台账里的断言要能被机器复查）。
"""
import json
import os
import sys

REPO = '/Users/wangziyi/Codex_Project0'
PATH = os.path.join(REPO, 'scripts/probe_coverage_expectations.json')

CAUSE = (
    "R93 更正成因（旧写法「整卷在第一条结论之前就被收掉」是错的）："
    "run 38852286519（`83439f8`，删掉僵尸拖选探针之后）在屏那一步自己打的是 "
    "`ui suite exit: 137  已下结论的用例: 6`、`UI_PROBE_PROGRESS started=7 concluded=6`、"
    "`UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese`、`UI_PROBE_CHANNELS_AGREE=1`。"
    "⇒ 这一卷**能**在 runner 上跑到结论（六条），但走到 `testRightClickMenus…` 就开口没闭口，"
    "240s 看门狗收掉 ⇒ 排在它后面的用例今天到不了。")

AFTER_HANG = CAUSE + " 本条排在它之后 ⇒ 今天到不了它，不是它自己跑不动。"


def main():
    with open(PATH, encoding='utf-8') as handle:
        data = json.load(handle)
    cases = data['cases']
    for name, entry in cases.items():
        if name == 'testRightClickMenusAppKitWouldShowAreChinese':
            entry['reason'] = (CAUSE + " 本条自己就是那具「第二具僵尸」：本机 R93 实测整卷 11 条 "
                                      "15.351 秒里它跑得完 ⇒ 不是恒挂，是在这台 runner 上要么挂要么慢到"
                                      "吃满看门狗 ⇒ BACKLOG 132 第一格（在 runner 上 `sample` 它）。")
        elif name == 'testRowProxyCensusAsksTheConsequenceNotTheShape':
            continue
        else:
            entry['reason'] = AFTER_HANG
    cases['testRowProxyCensusAsksTheConsequenceNotTheShape'] = {
        "runner": "cannot",
        "reason": (
            "R93 新加的诊断判据（BACKLOG 127 的正对照）。登记 cannot 的理由不是「它跑不动」，"
            "而是「runner 上今天到不了它」：它排在 `testRightClickMenus…` 之后，而那条在 "
            "run 38852286519 里开口没闭口（132）。本机 R93 实测它跑完并打出 "
            "`ROW_PROXY_CENSUS 侧栏@窗口320pt 代理=2 行=1 首行各代理宽=[148+148]`、"
            "`@250pt → [113+113]`、两个都 `acceptsFirstResponder=false`、"
            "`ROW_PROXY_LISTROWS 行视图=11 个` ⇒ 127 的定性由它给出：是**判据的期望写错**"
            "（把宿主级的 key-view 代理当成了行），不是产品的无障碍结构坏。"
            "132 修好之后这条要改成 can。"),
    }
    data['evidence'] = {
        "run": "38852286519",
        "reading": ("ui suite exit: 137  executed: 0  已下结论的用例: 6 | "
                    "UI_PROBE_PROGRESS started=7 concluded=6 | "
                    "UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese | "
                    "UI_PROBE_CHANNELS_AGREE=1"),
    }
    data['_r93'] = (
        "R93：十条 reason 从「整卷在第一条结论之前就被收掉」改成上面那句实测成因，"
        "并登记新加的 `testRowProxyCensusAsksTheConsequenceNotTheShape`。"
        "**为什么六条明明在 runner 上下过结论、这里仍登记 cannot**：那六条的**名字**今天还没读到"
        "（`已下结论的用例: 6` 只数了行，名字随被 SIGKILL 带走的那块 stdout 缓冲一起没了），"
        "而按字典序去猜是哪六条属于「没量过的推断」——R87 那一课的规矩是"
        "「预先登记的预测被推翻只写没证实」。R92 推送的 CI（`9c10569`）第一次带着"
        "「闸门读真日志」的修法，那一步会逐条印出结论名 ⇒ 下一轮按它把该翻 can 的翻掉；"
        "翻错会被 NOW_RUNS / NOT_RUN 挡回来，这正是留那两格的意义。")
    with open(PATH, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print('cases=%d，其中 can=%d' % (
        len(cases), sum(1 for e in cases.values() if e.get('runner') == 'can')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
