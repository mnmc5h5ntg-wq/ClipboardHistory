#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 的变异表（**补登**，R206 由 BACKLOG 228③ 搬进名册）：拖入回执那两条轴各有一把刀。

为什么这一张要存在：R205 那两把刀是**内联**跑的（临时 python 打补丁），
没进 `mutate_needle_precheck.py` 的 TABLES ⇒ 下一轮复查不到，刀号跨表唯一性也没被检查过。
这一张不新增刀号（M736/M737 与 R205 那笔台账里写的是同一对），只是把当时那条命令变成可重跑的东西。

两条轴分开钉（这是本轮真正的收获 —— 一把刀只能证明"有一处会红"，不能证明"红在哪一句"）：

M736 把 `attemptedCount ?? urls.count` 退回 `urls.count` ⇒ "声称是文件却解出 0 个"那一格**根本不说话** ⇒
     `testDroppedProvidersThatDecodeToNothingStillSpeakUp` 的 `XCTAssertNotNil(notice)` 红。
     这把刀钉的是**会不会说话**。
M737 只把文案里的 `\(attempted)` 换成 `\(urls.count)` ⇒ 话照说、但说的是"0 项" ⇒
     同一颗判据里那条 `notice?.contains("2 项")` 红。
     这把刀钉的是**说的是不是那个数** —— 没有它，"永远说 0 项"这种半修好的东西能带着绿活很多轮。

按实记账（不在本表里，别当成已交付）：**调用点没有守卫**。
把 `HistorySidebarView` 里的 `attemptedCount: wanted.count` 摘掉，本表两把刀都不会红 —— 因为判据是从 store 入口进的，
不读调用点。那一格的牙要另配一条源码形状断言（与 R43/R44 那族"零调用点的死尺"同一个洞），
今天仍欠 ⇒ 记在 BACKLOG 230。
"""
import io, os, re, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
STORE = "Sources/ClipboardHistoryApp/Managers/HistoryStore.swift"
RECEIPT = "DroppedFileImportTests/testDroppedProvidersThatDecodeToNothingStillSpeakUp"

ARMS = [
    ("M736", "attemptedCount 被丢掉（声称有几个却解出 0 ⇒ 那一格重新变静默）", STORE,
     r"let attempted = attemptedCount ?? urls.count",
     r"let attempted = urls.count", RECEIPT),
    ("M737", "回执改口说解出的个数（话照说、数永远是 0 ⇒ 半修好）", STORE,
     r"拖入的 \(attempted) 项不是本机文件",
     r"拖入的 \(urls.count) 项不是本机文件", RECEIPT),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run(filter_name):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(["swift", "test", "--filter", filter_name], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    executed = failures = skipped = None
    for line in text.splitlines():
        if line.strip().startswith("Executed "):
            m = re.search(r"Executed (\d+) tests?, with (\d+) failures?", line)
            if m:
                executed, failures = int(m.group(1)), int(m.group(2))
            s = re.search(r"(\d+) tests? skipped", line)
            if s:
                skipped = int(s.group(1))
    return proc.returncode, executed, failures, skipped


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）" % (arm_id, hits), flush=True)
            continue
        if needle == repl:
            not_run += 1
            print("%s NOT_RUN 变异文与原文逐字相同 ⇒ 这一刀没有对象" % arm_id, flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl))
            code, executed, failures, skipped = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        if not executed or skipped:
            not_run += 1
            print("%s NOT_RUN 跑到=%s skip=%s ⇒ 不算 CAUGHT：%s" % (arm_id, executed, skipped, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s（失败 %d，跑到 %d）" % (arm_id, filt, why, failures, executed), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R205_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
