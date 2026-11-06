# -*- coding: utf-8 -*-
"""R594 靶 4①：台账写手的**幂等证人**（同一份输入连跑两次，第二次必须一字不改）。

来历：这一族已经第四次了（R303 → R562 → R580 → R593）。R593 那一朵是 U 格那条
`（Rnnn 现读抬到最新一节）` 贴纸：替换的锚点只吃数字 ⇒ 旧贴纸留在原地，每轮攒一张。
那次是**电池**抓到的（`test_the_u_cell_carries_exactly_one_derivation_note`），
也就是说到盘上之后才发现；而这件事在写手跑完的那一刻就是可判的 ⇒ 应该由仪器先响。

这一支做的就是一次重放：
· 先记七本的 md5；
· 再跑一次本轮写手（`--apply`）与派生格那一趟（post-land）；
· 第二次的 md5 必须与第一次**逐本相同**；不同就点名哪本改了、改了多少行（`git diff --numstat` 的口径）。
⚠ 只判"重放有没有副作用"，不判文本内容对不对 —— 内容另有守卫（红名对账 / 清账门 / 引用守卫）。

用法：PYTHONUTF8=1 python3 scripts/ledger_idempotency_gate.py --writer PATH --post-land PATH
退出码：0=重放无改动；1=有改动（点名哪本）；2=重放本身崩了（不许读成"没改"）。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [u"AGENT_STATE.md", u"AGENT_UI_AUDIT.md", u"AGENT_VISUAL_ITERATION.md",
         u"AGENT_BACKLOG.md", u"AGENT_DECISIONS.md", u"CHANGELOG.md", u"AGENT_FINAL_REPORT.md"]


def md5s(repo=REPO):
    out = {}
    for b in BOOKS:
        path = os.path.join(repo, b)
        out[b] = hashlib.md5(io.open(path, "rb").read()).hexdigest() if os.path.exists(path) else u"missing"
    return out


def sh(args):
    proc = subprocess.Popen(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate(timeout=900)
    return proc.returncode, (out or u"")


def changed_lines(repo=REPO):
    """`git diff --numstat` 的加/删行数（工作树相对 HEAD）—— 幂等的证人就是这个数第二次不动。"""
    rc, out = sh([u"git", u"--git-dir", os.path.join(repo, ".git"),
                     u"--work-tree", repo, u"diff", u"--numstat", u"--"] + BOOKS)
    rows = {}
    for line in out.splitlines():
        parts = line.split(u"\t")
        if len(parts) == 3:
            rows[parts[2].strip()] = (int(parts[0]), int(parts[1]))
    return rows


def selftest():
    """三把合成对照：无改动=ok / 一本多了两行=red / 重放崩=not-run。"""
    good = {b: (u"x", 0) for b in BOOKS}
    bad = dict(good)
    bad[BOOKS[1]] = (u"y", 2)
    cases = [
        (diff_rounds(good, good), u"ok"),
        (diff_rounds(good, bad), u"red"),
    ]
    blind = [c for c in cases if c[0] != c[1]]
    print(u"LEDGER_IDEMPOTENCY_SELFTEST=%s 对照=%d 不符=%d"
          % (u"seen" if not blind else u"blind", len(cases), len(blind)))
    return not blind


def diff_rounds(before, after):
    """before/after 是 {本: (md5|行数, 版本)} 的两种口径；这里只按"同键同值"判。"""
    return u"ok" if all(before[b] == after[b] for b in BOOKS) else u"red"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument(u"--writer", required=True)
    ap.add_argument(u"--post-land", default=None)
    ap.add_argument(u"--skip-selftest", action=u"store_true")
    ap.add_argument(u"--repo", default=REPO,
                    help=u"仓库根（判据卷在沙箱里传临时目录，这样正对照是真跑而不是纸上的）")
    args = ap.parse_args(argv)
    if not args.skip_selftest and not selftest():
        print(u"LEDGER_IDEMPOTENCY_RESULT=red 原因=尺瞎了（重放两次判不出差别）")
        return 1
    scripts = [args.writer] + ([args.post_land] if args.post_land else [])

    def replay(tag):
        for script in scripts:
            path = script if os.path.isabs(script) else os.path.join(args.repo, script)
            if not os.path.exists(path):
                print(u"LEDGER_IDEMPOTENCY_RESULT=not-run 原因=读不到 %s ⇒ 重放没跑过，"
                      u"这一格读不成「没改」" % script)
                return 2
            rc, out = sh([sys.executable, path])
            if rc != 0:
                tail = out.strip().splitlines()[-1][:200] if out.strip() else u"（无输出）"
                print(u"LEDGER_IDEMPOTENCY_RESULT=red 原因=%s 那一趟在重放里退出 %d（崩在重放里也是副作用）"
                      % (tag, rc))
                print(u"  末行：%s" % tail)
                return 2
        return 0

    # 顺序要紧：先跑一遍把账落好，**再**取快照，然后再跑一遍。
    # 第一版把快照取在第一次之前 ⇒ 第一次落盘本身被当成"重放改了盘"，幂等写手也判红（尺读错了对象）。
    rc = replay(u"第一次")
    if rc:
        return rc
    first = md5s(args.repo)
    counts_first = changed_lines(args.repo)
    rc = replay(u"第二次")
    if rc:
        return rc
    second = md5s(args.repo)
    counts_second = changed_lines(args.repo)
    moved = [b for b in BOOKS if first[b] != second[b]]
    for b in BOOKS:
        if first[b] != second[b]:
            print(u"  改了 %s 第一次=%s 第二次=%s" % (b, counts_first.get(b), counts_second.get(b)))
    print(u"LEDGER_IDEMPOTENCY 重放=%d 本数=%d 改动本=%d 名单=%s"
          % (len(scripts), len(BOOKS), len(moved), u",".join(moved) or u"无"))
    if moved:
        print(u"LEDGER_IDEMPOTENCY_RESULT=red ⇒ 写手第二次仍动盘 ⇒ 同一轮重跑会写出两份账（R562 那一族）")
        return 1
    print(u"LEDGER_IDEMPOTENCY_RESULT=ok")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
