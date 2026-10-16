#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 R102 的收尾数字**从产物里算出来**，不靠我手抄（R99 / U-264、R101 / U-287 那一族的根治）。

它做三件事，全部只读：
  ① 拒绝在 `VERIFY_OK` 不是 1 的时候给出任何"绿"的句子（缺格 = 非 0 退出，不补数）；
  ② 从 `MUT_EXIT` 那一行**解析每张表的 `n=`** 并求和 ⇒ 台账里"合计多少刀"这一格从此是被算出来的
     （R102 我两次想用手写的正则去数源码里的臂，一次报 2、一次报 0，两次都错：
      数量只能抄"被计数物自己打印的读数"）；
  ③ 把 §8 那十二行按 markdown 打印出来，供我贴进台账（贴之前先 `--check` 一遍，缺格就非 0）。

用法：
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/r102_closeout.py <verify.log> [--check]
退出码：0=可以收口；1=还不能收口（打印为什么）；2=用法错。
"""
import re
import sys
from pathlib import Path

TABLE_ROW = re.compile(r"\|\s*([a-z0-9_]+)\(exit=(\d+)\): MUTATE_TABLE n=(\d+) caught=(\d+)"
                       r"(?: intended_escaped=(\d+))?.*?mismatch=(\d+) not_run=(\d+)")
KEYS = {
    "构建": r"^BUILD_EXIT=(\d+) BUILD_WARNING_LINES=(\d+)",
    "全量测试": r"^TEST_EXIT=(\d+) (.*)",
    "在屏那一卷": r"^PROBE_EXIT=(\d+) (.*)",
    "捕获卷": r"^CAPTURE_EXIT=(\d+) (.*)",
    "帧基线": r"^FRAMES_EXIT=(\d+) (.*)",
    "脚本电池": r"^PY_EXIT=(\d+) (.*)",
    "台账编号守卫": r"^LEDGER_EXIT=(\d+) (.*)",
    "曲线仪器": r"^VIS_EXIT=(\d+) (.*)",
    "摘要缺值": r"^SUMMARY_MISSING=(\d+)",
    "总结论": r"^VERIFY_OK=(\d+)",
}


def last(text, pattern):
    hits = re.findall(pattern, text, re.M)
    return hits[-1] if hits else None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    log = Path(args[0])
    if not log.exists():
        sys.stderr.write("日志不存在：%s（⇒ 还不能收口，也不要用记忆里的数）\n" % log)
        return 1
    text = log.read_text(encoding="utf-8")
    problems = []
    parsed = {}
    for name, pat in KEYS.items():
        v = last(text, pat)
        if v is None:
            problems.append("日志里没有「%s」这一格" % name)
        else:
            parsed[name] = v
    mut = last(text, r"^(MUT_EXIT=\d+ 跑了=\d+ 期望=\d+ 表=.*)$")
    if mut is None:
        problems.append("日志里没有 MUT_EXIT 那一行")
    tables = TABLE_ROW.findall(mut or "")
    if mut:
        ran = int(re.search(r"跑了=(\d+)", mut).group(1))
        expect = int(re.search(r"期望=(\d+)", mut).group(1))
        if ran != expect:
            problems.append("跑了 %d 张 ≠ 期望 %d 张" % (ran, expect))
        # **这一格不看 `if tables`**：第一版把它写在 `if tables:` 里面，于是解析器自己坏掉时
        # （`\|` 后面漏了一个空格 ⇒ 11 张表一条也没匹配上）它一声不响，只报出 `合计刀数=0`。
        # 那正是这支工具存在的理由：**算不出来必须响，不许安静地给 0**（R102 / U-302 同族）。
        if len(tables) != ran:
            problems.append("能从 MUT_EXIT 行解析出的表数=%d ≠ 跑了=%d ⇒ 解析器或那一行的形状变了，别手抄"
                            % (len(tables), ran))
    total_n = sum(int(t[2]) for t in tables)
    total_caught = sum(int(t[3]) for t in tables)
    total_escaped = sum(int(t[4] or 0) for t in tables)
    total_mismatch = sum(int(t[5]) for t in tables)
    total_notrun = sum(int(t[6]) for t in tables)
    verify_ok = last(text, r"^VERIFY_OK=(\d+)")
    if verify_ok is None or verify_ok[0] != "1":
        problems.append("VERIFY_OK=%s（不是 1 ⇒ 这一版不能写进台账当凭据）"
                        % (verify_ok[0] if verify_ok else "缺失"))

    print("== 派生数字（全部由脚本从日志算出，不是手抄）==")
    print("TABLES=%d  合计刀数=%d  caught=%d  intended_escaped=%d  mismatch=%d  not_run=%d"
          % (len(tables), total_n, total_caught, total_escaped, total_mismatch, total_notrun))
    for name, exit_, n, caught, esc, mm, nr in tables:
        print("   %-12s exit=%s n=%s caught=%s%s%s"
              % (name, exit_, n, caught,
                 " intended_escaped=%s" % esc if esc else "",
                 "  !! mismatch=%s not_run=%s" % (mm, nr) if (mm != "0" or nr != "0") else ""))
    print("ROUNDS 行：%s" % (last(text, r"^(VIS_EXIT=\d+ .*)$") or "缺"))
    print("脚本电池：%s" % (parsed.get("脚本电池"),))
    print("帧基线：%s" % (parsed.get("帧基线"),))
    if "--check" in args:
        if problems:
            print("\n还不能收口：")
            for p in problems:
                print("  - %s" % p)
            return 1
        print("\nCLOSEOUT_OK=1（十二格齐、表数对、VERIFY_OK=1）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
