#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R313 的变异表（第 312 轮 / Round 310）：本轮新写的那一箱必须有牙。

`scripts/hidden_arms.py` 从一箱变两箱（BACKLOG 367 第一步）：未声明的臂维持 `any(候选命中)`——它只配当下界（366 现读证伪了两种把它做成上界的静态办法）；表里写了 `NEEDLES = {刀号: [针, …]}` 的臂改走逐根判，可加总。三把刀分别钉：
· M911 把 `arm_label_of` 摘掉 ⇒ 声明那一箱塌回 0，正对照格必须抓到；
· M912 把下界的 `any()` 写成 `all()` ⇒ rot 会把变异文也算成死针，棘轮必须响；
· M913 把已声明死针的棘轮改成只判一个方向 ⇒ "变少"这一半没有牙，正对照必须响。

执行器与 R310 同一支（python 侧看 `Ran N tests` / `FAILED (failures=…)`；
编译/收集错不算 CAUGHT = D-243）。needle 恰好命中一次、落刀后回读、还原逐字节一致。
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

TARGET = "scripts/hidden_arms.py"
GUARD = u"python:scripts.tests.test_hidden_arms"

# 三把刀各钉本轮新写的那一条轴（D-244：判定看失败的用例名 + 正文里的串，不看退出码）。
# 每一根针都必须**恰好命中一次**，所以它们钉的是 R313 改完之后的形状，不是 R310 的。
N_LABEL = (u'    for sub in ast.walk(elt):\n'
           u'        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and ARM_LABEL.match(sub.value):\n'
           u'            return sub.value\n'
           u'    return u""\n')
R_LABEL = (u'    for sub in ast.walk(elt):\n'
           u'        if False:  # MUTANT 刀号那一格永远取不到\n'
           u'            return sub.value\n'
           u'    return u""\n')
N_ANY = u'            if not any(c in text for c in cands):'
R_ALL = u'            if not all(c in text for c in cands):  # MUTANT 下界改成"有一根死就算烂"'
N_DEAD = u'    if info[u"declared_dead"] != declared_dead_ceiling:'
R_DEAD_UP = u'    if info[u"declared_dead"] > declared_dead_ceiling:  # MUTANT 只判上界'

ARMS = [
    ("M911", u"刀号取不出来 ⇒ 声明那一箱整箱塌回 0（正对照必须抓到）", TARGET, N_LABEL, R_LABEL,
     GUARD, u"已声明那一箱必须逐根数出死针"),
    ("M912", u"下界那一箱写成 all() ⇒ rot 会把变异文也算成死针", TARGET, N_ANY, R_ALL, GUARD,
     u"与上界不符"),
    ("M913", u"已声明死针只判一个方向 ⇒ 清零也能蒙过去", TARGET, N_DEAD, R_DEAD_UP, GUARD,
     u"变少不响"),
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
        # R367 / 426：判「盘上恰好等于预期 diff」（删臂也成立），不判替换串出现几次。
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
        print("R313_MUTATE ARG_ERROR 未知刀号 %s" % sorted(bad_ids), flush=True)
        return 2
    code0, ran0, fail0, names0, _t0 = run_guard()
    if not ran0 or fail0 or code0 != 0:
        print("R313_MUTATE PRECHECK_FAILED 基线不绿（跑=%d 失败=%d exit=%d 红在 %s）"
              % (ran0, fail0, code0, names0), flush=True)
        return 1
    print("R313_MUTATE BASELINE 跑=%d 失败=0 exit=%d ⇒ 后面的 CAUGHT 才有意义"
          % (ran0, code0), flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    if not arms:
        print("R313_MUTATE ARG_ERROR 一臂都没选中", flush=True)
        return 2
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count("CAUGHT")
    escaped = sum(1 for k in kinds if k in ("ESCAPED", "WRONG_CELL"))
    not_run = sum(1 for k in kinds if k in ("NOT_RUN", "RESTORE_FAILED"))
    clean = "no" if "RESTORE_FAILED" in kinds else "yes"
    print("R313_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s"
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == "yes") else 1


if __name__ == "__main__":
    sys.exit(main())
