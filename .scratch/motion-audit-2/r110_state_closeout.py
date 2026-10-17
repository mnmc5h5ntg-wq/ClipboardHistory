#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R110 收尾：§8 搬运 + STATE 轮换 + FINAL_REPORT 计数，全部从**日志解析**，不手抄。

为什么要有这一支而不是手工三段：R109 的 U-352 是"写台账的手自己坏了没人看着"（CHANGELOG 出现两个
`## [Unreleased]`，一路绿着提交）。本轮的 §8 / STATE / FINAL_REPORT 三处都要抄同一批数字，
手抄三次就是三个可能各自坏掉的地方 ⇒ 只允许从 `r110_verify.log` 与 `r102_closeout.py` 的输出里解析。

用法：PYTHONUTF8=1 python3 r110_state_closeout.py <verify.log> <step2.log> [--dry]
"""
import io
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"


def load(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def kv(text, key):
    m = re.search(r"^%s=(\S+)" % re.escape(key), text, re.M)
    return m.group(1) if m else "?"


def line_with(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.strip()
    return ""


def main():
    log_path = sys.argv[1]
    step2 = sys.argv[2]
    dry = "--dry" in sys.argv
    log = load(log_path)
    # 读数搬运：合并两份（U-363 —— MENUBAR_GLYPH 是第 2 步打的，不在电池摘要里）
    merged = "/tmp/r110_merged_readings.log"
    io.open(merged, "w", encoding="utf-8").write(log + "\n" + load(step2) + "\n")
    rows = subprocess.run(
        ["python3", os.path.join(REPO, ".scratch/motion-audit-2/ledger_rows.py"), merged,
         "--pass", "2", "--must-include", "MENUBAR_GLYPH", "CARD_PROBE_COLUMNS", "SELECTION_CHROMA"],
        cwd=REPO, capture_output=True, text=True)
    out = rows.stdout + rows.stderr
    print(out[-1500:])
    if rows.returncode != 0:
        print("ROWS_EXIT=%d ⇒ 不写台账（缺族就是缺族，不许手写补上）" % rows.returncode)
        return 1
    # §8 块 = ledger_rows 输出里从表头开始的那一段
    m = re.search(r"(?m)^(\| 读数行)", out)
    block_start = m.start() if m else None
    sec8 = out[block_start:] if block_start is not None else ""
    if not sec8.strip():
        print("找不到 §8 表体 ⇒ 不落盘")
        return 1
    provenance = (u"\n> 搬运自 `%s` **与** `%s`（第 2 步的原始日志）合并件 `/tmp/r110_merged_readings.log`："
                  u"`MENUBAR_GLYPH` 由 `MenuBarPopulationTests` 打，不在电池摘要里（U-363）。\n"
                  % (os.path.basename(log_path), os.path.basename(step2)))

    p = os.path.join(REPO, "AGENT_VISUAL_ITERATION.md")
    t = load(p)
    head = u"### §8 本轮读数（由 `ledger_rows.py` 从 `r110_verify.log` 搬运）"
    if head in t and u"| 读数行" not in t.split(head, 1)[1].split(u"### §9", 1)[0]:
        tail = t.split(head, 1)[1]
        insert_at = head + "\n" + provenance + "\n" + sec8.strip() + "\n"
        nxt = tail.find(u"### §9")
        body = tail[:nxt] if nxt >= 0 else tail
        new_t = t.replace(head + body, insert_at, 1)
        if not dry:
            io.open(p, "w", encoding="utf-8").write(new_t)
        print("§8 落盘=%d 行数=%d" % (new_t.count(head), sec8.count("\n")))
    else:
        print("§8 已填或锚点不对 ⇒ 跳过（不重复插）")

    # 收尾对账（刀数/表数从解析来）
    close = subprocess.run(["python3", os.path.join(REPO, ".scratch/motion-audit-2/r102_closeout.py"),
                            log_path, "--check"], cwd=REPO, capture_output=True, text=True)
    close_out = close.stdout + close.stderr
    print(close_out[-800:])
    tables = re.search(r"TABLES=(\d+) 合计刀数=(\d+) caught=(\d+)", close_out)
    knife = tables.group(0) if tables else "TABLES=?"

    verify = kv(log, "VERIFY_OK")
    summary = {
        "BUILD_EXIT": kv(log, "BUILD_EXIT"), "BUILD_WARN": kv(log, "BUILD_WARN"),
        "TEST": line_with(log, "TEST_EXIT"), "PROBE": line_with(log, "PROBE_EXIT"),
        "CAPTURE": line_with(log, "CAPTURE_EXIT"), "FRAMES": line_with(log, "FRAMES_EXIT"),
        "PY": line_with(log, "PY_EXIT"), "MUT": line_with(log, "MUT_EXIT"),
        "LEDGER": line_with(log, "LEDGER_EXIT"), "VIS": line_with(log, "VIS_EXIT"),
        "CONTAIN": line_with(log, "CONTAIN_EXIT"), "MISSING": kv(log, "SUMMARY_MISSING"),
        "PRECHECK": line_with(log, "PRECHECK_EXIT"),
    }
    for k, v in summary.items():
        print("%s -> %s" % (k, v))
    print("KNIFE %s" % knife)
    print("VERIFY_OK=%s dry=%d" % (verify, 1 if dry else 0))
    return 0 if verify == "1" else 1


if __name__ == "__main__":
    sys.exit(main())
