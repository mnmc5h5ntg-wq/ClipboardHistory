#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R310 的变异表（第 309 轮 / Round 307）：新搬进仓库的「腐烂针」尺，六个方向各钉一条。

靶：`scripts/hidden_arms.py`；被搜的卷：`scripts/tests/test_hidden_arms.py`（合成已知答案 + 真产物棘轮）。
判法与假正例的来历写在尺自己的 docstring 里（第一版把中文说明与目标路径当候选 ⇒ 191 张表上报 152 rot，
其中包含当天刚全 CAUGHT 的 r308 / r309 —— 那是判法不成立，不是仓库真烂了 152 把）。

· M902 rot 判定不许恒不响（摘掉 ⇒ 现读 rot=0 与上界不符 ⇒ 棘轮必须红）
· M903 双向：只判"不许超过"⇒ 正对照里"变少也要响"那一半必须红
· M904 常量传播不许摘（摘掉 ⇒ 变量里的针看不见 ⇒ 数就漂）
· M905 路径型候选的过滤不许摘（摘掉 ⇒ 死刀被路径命中洗活 ⇒ 数漂回 30/5）
· ~~M906 合成夹具不许进语料~~ **R368 退役**：把排除项从 fixtures 改成 fixtures_x 之后
  `HIDDEN_ARMS` 的三组数（rot=33 / 抽不出=6 / 已声明=6）**一个都没动** ⇒ 这条排除对今天的语料
  没有作用，刀已无牙。退役理由与读数见 BACKLOG 426 的 R368 追记；宁可不登记，也不留一把空刀。
· M907 抽不出候选的臂不许静默丢掉（那就是 364 原本的形状）

判定按失败正文（D-244）；没有结论行一律 NOT_RUN（D-243）；未落刀先跑基线；根由 `__file__` 推。
"""
import io
import os
import re
import subprocess
import sys

from readback import single_substitution_lands

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = "scripts/hidden_arms.py"
GUARD = u"python:scripts.tests.test_hidden_arms"

N_ROT = u'            if not any(c in text for c in cands):'
R_ROT = u'            if False:  # MUTANT rot 判定恒不响'
N_DOWN = u'    if info[u"rot"] != rot_ceiling:'
R_DOWN = u'    if info[u"rot"] > rot_ceiling:  # MUTANT 只判上界'
N_PROP = u'        elif isinstance(sub, ast.Name) and sub.id in cmap:'
R_PROP = u'        elif False:  # MUTANT 不做常量传播'
N_PATH = u'    return [c for c in out if len(c) >= MIN_LEN and not _is_pathish(c)]'
R_PATH = u'    return [c for c in out if len(c) >= MIN_LEN]  # MUTANT 不滤路径'
N_FIXT = u'if d not in (".build", "__pycache__", ".git", "fixtures")]'
R_FIXT = u'if d not in (".build", "__pycache__", ".git", "fixtures_x")]'
N_OPAQ = u'            if not cands:\n                opaque += 1\n                opaque_rows.append((name, u"臂#" + str(idx), u"抽不出候选"))\n                continue'
R_OPAQ = u'            if not cands:\n                continue  # MUTANT 抽不出候选的臂被静默丢掉'

ARMS = [
    ("M902", u"rot 判定不许恒不响", TARGET, N_ROT, R_ROT, GUARD, u"与上界不符"),
    ("M903", u"双向棘轮：变少也要响", TARGET, N_DOWN, R_DOWN, GUARD, u"变少不响"),
    ("M904", u"常量传播有牙（摘掉就数漂）", TARGET, N_PROP, R_PROP, GUARD, u"与上界不符"),
    ("M905", u"路径型候选的过滤有牙", TARGET, N_PATH, R_PATH, GUARD, u"与上界不符"),
    ("M907", u"抽不出候选的臂必须被登记", TARGET, N_OPAQ, R_OPAQ, GUARD, u"不许静默丢掉"),
]

PY_RAN = re.compile(r"^Ran (\d+) tests?", re.M)
PY_FAIL = re.compile(r"^FAILED \((?:failures=(\d+)|errors=(\d+))", re.M)
PY_HEAD = re.compile(r"^(test\w+) \([\w.]+\)")
PY_RESULT = re.compile(r"\.\.\. (FAIL|ERROR)")


def base_env():
    env = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    return env


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as h:
        return h.read()


def write(rel, text):
    with io.open(os.path.join(ROOT, rel), "w", encoding="utf-8") as h:
        h.write(text)


def py_failed_cases(text):
    names, cur = [], None
    for line in text.split("\n"):
        head = PY_HEAD.match(line)
        if head:
            cur = head.group(1)
            if PY_RESULT.search(line):
                names.append(cur)
                cur = None
            continue
        if cur is not None and PY_RESULT.search(line):
            names.append(cur)
            cur = None
    return sorted(set(names))


def run_guard():
    proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "-v",
                           GUARD.split(u":", 1)[1]],
                          cwd=ROOT, env=base_env(),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    ran = PY_RAN.findall(text)
    fails = PY_FAIL.findall(text)
    n_fail = sum(int(a or b) for pair in fails for a, b in [pair]) if fails else 0
    return (proc.returncode, int(ran[-1]) if ran else 0, n_fail, py_failed_cases(text), text)


def run_arm(arm_id, why, target, needle, repl, _filter, expect_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print("%s NOT_RUN needle 命中 %d 次（要恰好 1）" % (arm_id, hits), flush=True)
        return "NOT_RUN"
    try:
        write(target, original.replace(needle, repl, 1))
        after = read(target)
        # R368 / 426：判「盘上恰好等于预期 diff」（删臂也成立），不判替换串出现几次。
        if not single_substitution_lands(original, needle, repl, after):
            print("%s NOT_RUN 落刀后回读与预期 diff 不一致" % arm_id, flush=True)
            return "NOT_RUN"
        code, n_ran, n_fail, names, text = run_guard()
    finally:
        write(target, original)
        if read(target) != original:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return "RESTORE_FAILED"
    if not n_ran:
        print("%s NOT_RUN 没有结论行：%s"
              % (arm_id, "\n".join(text.strip().splitlines()[-3:])), flush=True)
        return "NOT_RUN"
    if n_fail and names and any(expect_text in ln for ln in text.splitlines()):
        print("%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d exit=%d）"
              % (arm_id, why, ", ".join(names), n_ran, n_fail, code), flush=True)
        return "CAUGHT"
    print("%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望正文含「%s」"
          % (arm_id, "ESCAPED" if not n_fail else "WRONG_CELL", names, n_ran, n_fail,
             expect_text), flush=True)
    return "ESCAPED" if not n_fail else "WRONG_CELL"


def main():
    only = set(sys.argv[1:])
    bad_ids = only - set(a[0] for a in ARMS)
    if bad_ids:
        print("R310_MUTATE ARG_ERROR 未知刀号 %s" % sorted(bad_ids), flush=True)
        return 2
    code0, ran0, fail0, names0, _t0 = run_guard()
    if not ran0 or fail0 or code0 != 0:
        print("R310_MUTATE PRECHECK_FAILED 基线不绿（跑=%d 失败=%d exit=%d 红在 %s）"
              % (ran0, fail0, code0, names0), flush=True)
        return 1
    print("R310_MUTATE BASELINE 跑=%d 失败=0 exit=%d ⇒ 后面的 CAUGHT 才有意义"
          % (ran0, code0), flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    if not arms:
        print("R310_MUTATE ARG_ERROR 一臂都没选中", flush=True)
        return 2
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count("CAUGHT")
    escaped = sum(1 for k in kinds if k in ("ESCAPED", "WRONG_CELL"))
    not_run = sum(1 for k in kinds if k in ("NOT_RUN", "RESTORE_FAILED"))
    clean = "no" if "RESTORE_FAILED" in kinds else "yes"
    print("R310_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s"
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == "yes") else 1


if __name__ == "__main__":
    sys.exit(main())
