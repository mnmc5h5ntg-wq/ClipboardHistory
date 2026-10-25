#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""回顾用尺第二支：**同一轮的每一笔提交**里「产品 K 文件」那一句是不是同一个数。

为什么要有它（R336 回顾时现读撞到的）：一轮通常有两笔以上（代码半 / 代码半补 / 账半 / 追记），
而每一笔的标题都带着"第 N 轮 / Round M · 产品 K 文件"这半句。这半句在**一轮内部**说的必须是
同一件事：这一轮的产品面改了几个文件。它一旦在两笔里给出两个数，读 git log 的人就不知道
哪一句作数 —— 而 `scripts/product_streak.py` 只从"代码半"那一笔取数，所以台账内部对得上，
标题之间却可以互相打脸（现读：R334 代码半写 2、R334 账半写 0；R335 两笔都写 7）。

R340 把它从"一次性尺"升成**电池里的门**（BACKLOG 405 的第二半），同时补它自己的两个洞：

· 洞一（**漏扫比误报更坏**）：原来只认"`R<NNN> …（… 产品 K 文件 …）`"这一种开头，
  于是一笔写成 `Round 336: …（U-… · 产品 3 文件…）` 的提交**根本进不了名册** ——
  它带着产品 K 却没有可解析的轮次身份，扫描器一声不吭，读数仍是"内部不一致=2"。
  现在这类笔被点名成 `未识别=K`，K>0 就红：不认"我的形状没覆盖到"，只认"有没有被放过"。
· 洞二：尺自己要有正对照。`parse_rows` / `find_inconsistent` 是纯函数，
  `scripts/tests/test_round_claim_consistency.py` 用合成标题钉住它们
  （真 git log 只能证明"今天没红"，证明不了这把尺看得见红）。

用法：`python3 .scratch/motion-audit-2/review_round_claims.py [扫描笔数]`
退出码：0=每一轮内部只有一个数且没有未识别的笔；1=有（打印轮号与每一笔）；2=用法/环境错。
**它不判**"这一轮的数与 git 派生的是否相同" —— 那一半是 review_commit_claims.py 的活。
"""
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
DEFAULT_WINDOW = 120

# **扫描窗的起点**：现行 subject 形状 `R<NNN> <半名>（第 N 轮 / Round M · 产品 K 文件…）` 第一次出现的那一笔
# （R334 代码半，现读 `git log` 里它是最早能被 `SUBJECT` 解析的一笔）。
# 它之前全是 `Round 219：…` / `R318 代码半：…（产品 0 文件，判据轮）` 那一类老形状 ——
# 老形状里没有可解析的轮次身份，**硬猜就是把"扫不到"写成"没问题"**（R140 的空对账那一族）。
# 所以 cutoff 之前的笔只印不判；cutoff 之内任何一笔带 K 却解析不出来，都必须点名（`未识别=`）。
SHAPE_CUTOFF = u"5d1c246"

# 轮次身份 + 那一格产品数。**只认这一种形状是故意的**：认得越宽，越会把"写错了形状"
# 当成"这一笔与本轮无关"而放过 —— 所以认不出的一律进 unparsed，不许静默消失。
SUBJECT = re.compile(u"^R(\\d{2,4})(?: (\\S+?))?（.*?产品 (\\d+) 文件")
# 带着产品 K 却没有轮次身份的笔：洞一的那一类。
CARRIES_K = re.compile(u"产品 (\\d+) 文件")


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")


def slice_since(log_text, cutoff=SHAPE_CUTOFF):
    u"""从最新往下留到 `cutoff`（含），再往后的老账丢掉。

    cutoff 不在历史里 ⇒ **抛错**，不许退化成"整条历史都扫"（那会把 40 笔老形状一起放进来，
    读数立刻变成没人看得懂的噪音，而噪音比红更坏）。
    """
    rows = [ln for ln in log_text.splitlines() if u"\t" in ln]
    out = []
    for ln in rows:
        out.append(ln)
        if ln.split(u"\t", 1)[0].startswith(cutoff):
            return out
    raise ValueError(u"cutoff %s 不在 git log 里 ⇒ 扫描窗无从确定" % cutoff)


def parse_rows(log_text):
    u"""把 `git log --format=<sha><TAB><subject>` 那种文本切成 (by_round, unparsed, scanned)。

    by_round：`{轮次: [(sha, 半名, K), …]}`；
    unparsed：`[(sha, K, subject 前 60 字)]` —— 标题里明明有「产品 K 文件」，
      却按 `SUBJECT` 认不出轮次身份的那几笔。
    """
    by_round = {}
    unparsed = []
    scanned = 0
    for line in log_text.splitlines():
        if u"\t" not in line:
            continue
        scanned += 1
        sha, subject = line.split(u"\t", 1)
        m = SUBJECT.match(subject)
        if m:
            rnd, kind, claimed = m.group(1), (m.group(2) or u"其他"), int(m.group(3))
            by_round.setdefault(rnd, []).append((sha[:7], kind, claimed))
            continue
        k = CARRIES_K.search(subject)
        if k:
            unparsed.append((sha[:7], int(k.group(1)), subject[:60]))
    return by_round, unparsed, scanned


def find_inconsistent(by_round):
    u"""纯函数：一轮里出现两个以上的 K 就是内部矛盾（按轮号降序给，sha 升序排）。"""
    bad = []
    for rnd, rows in sorted(by_round.items(), key=lambda kv: -int(kv[0])):
        if len(set(r[2] for r in rows)) > 1:
            bad.append((rnd, sorted(rows)))
    return bad


def leftovers(by_round, unparsed, ok_rounds=(), ok_shas=()):
    u"""纯函数：把"已经登记过、并且写明了退场条件"的例外剔掉，剩下的是**必须红的**。

    为什么把剔除写成函数而不是写在 `main` 里：电池要能对着一份**合成**数据问它
    "名单空着的时候你还红不红"（R298 那一课的 `roster_problems` 同一形状）。
    名单只买"不红"，买不到"数对" —— 所以本函数返回的每一条都要能被打印出来。
    """
    out = []
    for rnd, rows in find_inconsistent(by_round):
        if rnd not in ok_rounds:
            out.append((rnd, u"ROUND_K_CONTRADICTION",
                        u" | ".join(u"%s %s=%d" % r for r in rows)))
    for sha, k, head in unparsed:
        if sha not in ok_shas:
            out.append((sha, u"K_WITHOUT_ROUND_IDENTITY",
                        u"带着「产品 %d 文件」却没有可解析的轮次身份｜%s" % (k, head)))
    return out


def main(argv):
    try:
        n = int(argv[0]) if argv else DEFAULT_WINDOW
    except ValueError:
        sys.stderr.write(u"用法：review_round_claims.py [扫描笔数]（要正整数）")
        return 2
    if n <= 0:
        sys.stderr.write(u"扫描窗必须是正整数，实得 %d" % n)
        return 2
    log = sh([u"git", u"log", u"-n", str(n), u"--format=%H%x09%s"])
    try:
        window = slice_since(log)
    except ValueError as exc:
        sys.stderr.write(str(exc))
        return 2
    by_round, unparsed, scanned = parse_rows(u"\n".join(window))
    bad = find_inconsistent(by_round)
    print(u"ROUND_CLAIM_REVIEW 扫了=%d 笔 / %d 轮 内部不一致=%d 未识别=%d 窗起=%s"
          % (scanned, len(by_round), len(bad), len(unparsed), SHAPE_CUTOFF))
    for rnd, rows in bad:
        print(u"  R%s: %s" % (rnd, u" | ".join(u"%s %s=%d" % r for r in rows)))
    for sha, k, head in unparsed:
        print(u"  UNPARSED %s 产品 %d 文件｜%s" % (sha, k, head))
    return 1 if (bad or unparsed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
