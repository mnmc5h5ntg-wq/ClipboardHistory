#!/usr/bin/env python3
"""R62 变异对照：`scripts/probe_coverage_gate.py` 的每条红都必须**有牙**。

跑法（仓库根）：
    PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r62_gate.py
日志写 `.scratch/motion-audit-2/r62_mutation_battery.log`。

为什么这一族值得单独立一支电池：闸门判的是"缺席有没有被登记"，
而它自己坏掉的样子恰好就是"什么都不报 ⇒ 全绿"。
所以每一刀都必须是"删掉一条规则，然后看是哪一条测试红"，
而不是"跑一遍看它没红"（那只能证明它没在跑）。
"""
import os
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
GATE = "scripts/probe_coverage_gate.py"

MUTATIONS = [
    # 每刀的锚都取**整行且唯一**，并且不许带未闭合的括号：
    # 上一版我把 `reds.append(f"UNLISTED {name}` 当锚，那串里少一个 `)`，
    # Python 把它读成"字符串正常结束、元组在这里闭合" ⇒ 整个脚本语法就坏了（刀根本没落下）。
    ("M318", "删掉 UNLISTED 那条规则（新判据不登记也能过）",
     "        if name not in expectations:",
     "        if False:",
     "test_new_unregistered_case_is_red"),
    ("M319", "删掉 STALE（免检牌可以一直攒着）",
     "        if name not in source_names:",
     "        if False:",
     "test_stale_registration_is_red"),
    ("M320", "cannot 不再要求写 reason",
     'elif runner == "cannot" and not str(entry.get("reason", "")).strip():',
     'elif runner == "cannot" and False:',
     "test_cannot_without_reason_is_red"),
    ("M321", "删掉 NOT_RUN（说能跑却没跑也不报）",
     '        if runner == "can" and name not in concluded:',
     "        if False:",
     "test_registered_can_but_absent_is_red"),
    ("M322", "删掉 NOW_RUNS（跑得了也不许改登记）",
     '        if runner == "cannot" and name in concluded:',
     "        if False:",
     "test_registered_cannot_but_concluded_is_red"),
    ("M323", "读不到输入时返回 0（把「没跑成」当成通过）",
     "        return 2",
     "        return 0",
     "test_missing_inputs_are_not_a_pass"),
    ("M324", "源码扫描放宽到正文任意位置（会命中注释里的用例名）",
     r'CASE_FUNC = re.compile(r"^\s*func (test[A-Za-z0-9_]+)\s*\(\s*\)", re.MULTILINE)',
     r'CASE_FUNC = re.compile(r"(test[A-Za-z0-9_]+)\s*\(\s*\)")',
     "test_source_scan_ignores_names_mentioned_in_prose"),
]


def main():
    # 每一刀都要求"同一份改动，连跑两遍结论一致"：结论会随跑序变的电池不能当证据。
    path = os.path.join(REPO, GATE)
    original = open(path, encoding="utf-8").read()
    lines = []
    bad = 0
    only = [a for a in sys.argv[1:] if a.startswith("M")]
    for mid, note, old, new, judge in MUTATIONS:
        if only and mid not in only:
            continue
        if old not in original:
            lines.append(f"{mid} {note}\n    结果：BROKEN-MUTATION（原文没找到，这一刀根本没落下）\n")
            bad += 1
            continue
        open(path, "w", encoding="utf-8").write(original.replace(old, new, 1))
        proc = subprocess.run(
            f"PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest "
            f"scripts.tests.test_probe_coverage_gate."
            f"ProbeCoverageGateTest.{judge}",
            shell=True, cwd=REPO, capture_output=True, text=True)
        open(path, "w", encoding="utf-8").write(original)
        out = proc.stdout + proc.stderr
        assertion_red = "FAILED (failures=" in out or "AssertionError" in out
        crash = "Traceback (most recent call last)" in out and not assertion_red
        if proc.returncode != 0 and assertion_red:
            verdict = "CAUGHT"
        elif proc.returncode != 0 and crash:
            verdict = "BROKEN-MUTATION（是崩溃不是断言红 ⇒ 红会被读成没跑）"
        else:
            verdict = "SURVIVED ⇒ 那条规则其实是装饰"
            bad += 1
        lines.append(f"{mid} {note}\n    期望被抓：{judge}\n    结果：{verdict}\n")
        print(lines[-1], flush=True)
    text = "\n".join(lines)
    out_path = os.path.join(REPO, ".scratch/motion-audit-2/r62_mutation_battery.log")
    open(out_path, "w", encoding="utf-8").write(text)
    print(f"\n写盘 {out_path}；共 {len(MUTATIONS)} 刀，可疑 {bad} 刀")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
