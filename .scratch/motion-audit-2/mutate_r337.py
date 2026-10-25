#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R337 的变异表（第 336 轮 / Round 334）：新加的那三格引用闸门，每一格都要能被摘掉牙。

R337 做的事是把"全历史回顾"量到的三类洞变成 `scripts/tests/test_ledger_citations.py` 里
三格会红的门（① BACKLOG 引用必须落到条目；② 最近 N 轮 STATE 必须每轮一节；
③ 报告的叙述节不许落后超过 20 轮），并且每格都自带**内存里的正对照**。

四把刀全部打在**门自己**身上（本轮产品 0 文件，动的是判据）：

· M989 ①那一侧：让引用检查永远返回空表 ⇒ 那条正对照必须红（"看不见新写的悬空引用"）。
· M990 ②那一侧：让 STATE 缺节检查永远返回空表 ⇒ 正对照里②必须红。
· M991 ③那一侧：让落后轮数恒等于 0 ⇒ 正对照里③必须红（地板 20 变成摆设）。
· M992 单一权威那一侧：不 import 那支共享的 `ITEM`，而是**另抄一颗只认四位号的尺** ⇒
  ①那一格必须红（所有三位号引用都"查无条目"）。这一把钉的是本轮真正的成因：
  出洞不是因为没人检查，而是因为**两处各写了一颗正则**。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r337.py [M989 … M992]
（python 卷的结论行是 `Ran N tests`；编译错/收集不到 ⇒ NOT_RUN，不算过关 = D-243。）
"""
import io
import os
import re
import subprocess
import sys

from readback import single_substitution_lands

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = u"scripts/tests/test_ledger_citations.py"
MODULE = u"scripts.tests.test_ledger_citations"
FALSIFIABLE = u"test_the_three_checks_are_falsifiable"
CITATION = u"test_every_backlog_citation_resolves_to_an_entry"

NEEDLE_989 = u"    return sorted(set(out))"
REPL_989 = u"    return []   # 变异：引用检查永远看不见悬空"

NEEDLE_990 = u"    return sorted(set(want) - have)"
REPL_990 = u"    return []   # 变异：STATE 缺节永远报没有"

NEEDLE_991 = u"    return int(latest_round_label) - max(tos)"
REPL_991 = u"    return 0   # 变异：落后几轮都不算旧"

NEEDLE_992 = u"from test_ledger_ids import ITEM          # noqa: E402"
REPL_992 = u'ITEM = re.compile(u"^(?:\\\\*\\\\*)?(\\\\d{4})\\\\. ", re.M)   # 变异：另抄一颗只认四位的尺'

# 形状必须是 `(编号, 说明, 文件, needle, 变异文, …)`，而且**编号那格不许写 u"…"** ——
# `arm_ids` 认的是行首 `("M6NN"`，写了 `u"M989"` 就抽不出号：
# 现读 `ARM_TOTAL arms=855` 在我加完四把之后**一个数都没动**，而 needle 预检那边报了 +4。
# 两个计数器对同一件事给出两个数，说明其中一个瞎了 —— 这一族叫"尺自己看不见自己"。
# 第一版还把"跑什么模块"放在第三位、文件放第四位，预检就把模块名当 needle 去数 ⇒ 假腐烂。
# 两处都是**改数据的写法**去落进尺认得的形状，不是放宽尺（同 BACKLOG 条目行那个洞）。
ARMS = [
    ("M989", u"①那一侧：引用检查恒返回空 ⇒ 正对照必须点名", TARGET,
     NEEDLE_989, REPL_989, FALSIFIABLE, u"①的正对照", MODULE),
    ("M990", u"②那一侧：STATE 缺节恒报没有 ⇒ 正对照必须点名", TARGET,
     NEEDLE_990, REPL_990, FALSIFIABLE, u"②的正对照", MODULE),
    ("M991", u"③那一侧：落后轮数恒为 0 ⇒ 正对照必须点名", TARGET,
     NEEDLE_991, REPL_991, FALSIFIABLE, u"③的正对照", MODULE),
    ("M992", u"权威那一侧：不共享 ITEM、另抄一颗只认四位的尺 ⇒ 引用格必须红", TARGET,
     NEEDLE_992, REPL_992, CITATION, u"没有条目", MODULE),
]

RAN = re.compile(r"^Ran (\d+) tests", re.M)
PY_FAIL = re.compile(r"^FAIL: (\w+) ", re.M)


def read(path):
    return io.open(os.path.join(ROOT, path), encoding=u"utf-8").read()


def write(path, text):
    io.open(os.path.join(ROOT, path), u"w", encoding=u"utf-8").write(text)


def run_py(module):
    env = dict(os.environ)
    env[u"PYTHONUTF8"] = u"1"
    env[u"PYTHONDONTWRITEBYTECODE"] = u"1"
    proc = subprocess.run([sys.executable, u"-B", u"-W", u"ignore", u"-m", u"unittest",
                           u"-v", module],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode(u"utf-8", u"replace")
    ran = RAN.findall(text)
    return (int(ran[-1]) if ran else 0), sorted(set(PY_FAIL.findall(text))), text


def run_arm(arm_id, why, target, needle, repl, want_fail, want_text, module):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print(u"%s NOT_RUN needle 命中 %d 次（要恰好 1）" % (arm_id, hits), flush=True)
        return u"NOT_RUN"
    try:
        write(target, original.replace(needle, repl, 1))
        if not single_substitution_lands(original, needle, repl, read(target)):  # R367 / 426：diff 判法
            print(u"%s NOT_RUN 落刀后回读与预期 diff 不一致" % arm_id, flush=True)
            return u"NOT_RUN"
        ran, fails, text = run_py(module)
    finally:
        write(target, original)
        if read(target) != original:
            print(u"%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return u"RESTORE_FAILED"
    if not ran:
        tail = u"\n".join(text.strip().splitlines()[-3:])
        print(u"%s NOT_RUN 没有结论行（收集不到不算 CAUGHT）：%s" % (arm_id, tail), flush=True)
        return u"NOT_RUN"
    body = [l for l in text.splitlines() if want_text in l]
    if want_fail in fails and body:
        print(u"%s CAUGHT %s ｜ 红在 %s（跑=%d）" % (arm_id, why, u", ".join(fails), ran),
              flush=True)
        return u"CAUGHT"
    print(u"%s %s ｜ 跑=%d 红=%s 正文含串=%s ⇒ 期望 %s +「%s」"
          % (arm_id, u"ESCAPED" if not fails else u"WRONG_CELL", ran, fails, bool(body),
             want_fail, want_text), flush=True)
    return u"ESCAPED" if not fails else u"WRONG_CELL"


def main():
    only = set(sys.argv[1:])
    unknown = only - set(a[0] for a in ARMS)
    if unknown:
        print(u"R337_MUTATE NOT_RUN 未知刀号 %s" % sorted(unknown), flush=True)
        return 2
    ran, fails, _ = run_py(MODULE)
    if not ran or fails:
        print(u"R337_PRECHECK_FAILED 基线不绿（跑=%d 红=%s）⇒ 拒绝出表" % (ran, fails), flush=True)
        return 1
    print(u"R337_BASELINE OK（Ran=%d）" % ran, flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count(u"CAUGHT")
    not_run = sum(1 for k in kinds if k in (u"NOT_RUN", u"RESTORE_FAILED"))
    clean = u"no" if u"RESTORE_FAILED" in kinds else u"yes"
    print(u"MUTATE_TABLE n=%d caught=%d escaped=%d not_run=%d RESTORE_CLEAN=%s"
          % (len(arms), caught, sum(1 for k in kinds if k in (u"ESCAPED", u"WRONG_CELL")),
             not_run, clean), flush=True)
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), clean), flush=True)
    return 0 if (caught == len(arms) and clean == u"yes") else 1


if __name__ == u"__main__":
    sys.exit(main())
