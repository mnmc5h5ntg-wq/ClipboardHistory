#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 的变异表：R194 那条接线扫描（`testFilterFocusExitIsWired`）到底有没有牙。

R194 因为预算尽头把这张表记成 NOT-RUN —— 那条扫描当时只有"跑过一遍绿"一个证人。
四把刀全部打在被扫描的那段判据代码上（M726…M729）， catcher 都是扫描本身，
所以跑的是静态那一条用例，不动前台、不重捕帧。

needle 都带**上一行或下一行**来消歧：扫描自己的字面量里就写着它要数的那个串（R100 那一族，
本轮 R194 我自己又撞过一次），只写前缀会命中两次而整刀 NOT-RUN。
"""
import io, os, re, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"
SCAN = "UIInteractionProbeTests/testFilterFocusExitIsWired"

ARMS = [
    ("M726", "摘掉『接管』那条断言 ⇒ 未判定出口永远不会被换回判据（永久免检）", TEST,
     'XCTAssertGreaterThanOrEqual(reachedFilterBandWithRing, 1,\n            "能 Tab 到筛选段按钮',
     'XCTAssertTrue(reachedFilterBandWithRing >= 0,\n            "能 Tab 到筛选段按钮', SCAN),
    ("M727", "把字段编辑器的身份排除摘掉 ⇒ 回到『把量错对象当成量到了』", TEST,
     "let inBand = !isFieldEditor && inFilterBand(r)",
     "let inBand = inFilterBand(r)", SCAN),
    ("M728", "未判定出口失去名字 ⇒ 它退化成一句注释而不是可复查的读数", TEST,
     'print("FILTER_PILL_FOCUS_UNCOVERED 理由=',
     'print("FILTER_PILL_FOCUS_NOTE 理由=', SCAN),
    ("M729", "读数行的标记被改名 ⇒ 子串锚点看不见这件事（锚点写的是整行前缀）", TEST,
     'print("FILTER_FOCUS 带内候选=',
     'print("FILTER_FOCUSX 带内候选=', SCAN),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name):
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
    only = sys.argv[1:] or None
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        if only and arm_id not in only:
            continue
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）" % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl))
            code, executed, failures, skipped = run_test(filt)
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
            print("%s CAUGHT  %s ⇒ %s（失败 %d）" % (arm_id, filt, why, failures), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R195_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
