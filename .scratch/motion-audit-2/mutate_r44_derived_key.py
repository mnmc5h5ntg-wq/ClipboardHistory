#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R44 变异对照：那条会展开派生键的尺，四种坏法各该红一次。

  M206 横幅的驱动换成一条**看着合理但推不到那五条**的键        ⇒ 五条全红
  M207 派生键的 body 里删掉一条（transferNotice 不再被签名读）  ⇒ 只有那一条红
  M208 整条 `.animation` 被删掉                                ⇒ 五条全红（且键数=0）
  M209 新加一条横幅而没登记进名单                              ⇒ 红在名单两边不等

M207 是这一族最值钱的一支：它证明"展开"不是把整棵 body 当万能通行证 ——
签名没点到的那条状态，进出都不会触发动画，那**就是**没电。

needle 一律从 --measure 那一遍的失败消息原文里抄（R41/R42 三次踩坑之后的固定流程）。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CONTENT = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/ContentView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "MotionDriverTests"

ANIMATION_LINE = "        .animation(MotionCatalog.animation(for: .bannerIn), value: noticeSignature)"
SIGNATURE_LINE = "        if historyStore.transferNotice != nil { bits |= 2 }"
BANNER_BLOCK = """        if let retention = historyStore.retentionNotice {
            NoticeBanner(message: retention, tone: .warning) {
                historyStore.dismissRetentionNotice()
            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }"""

MUTATIONS = [
    ("M206", "驱动换成推不到那五条的键", CONTENT, ANIMATION_LINE,
     "        .animation(MotionCatalog.animation(for: .bannerIn), value: historyStore.entries.isEmpty)  // MUTANT",
     ["推到：[\"let dropped = historyStore.droppedFilesNotice\", \"let pasteFailure"]),
    ("M207", "派生键的 body 里不再读 transferNotice", CONTENT, SIGNATURE_LINE,
     "        // MUTANT：这一条被签名漏掉了",
     ["推到：[\"let transfer = historyStore.transferNotice\"]"]),
    ("M208", "整条驱动被删掉", CONTENT, ANIMATION_LINE, "        // MUTANT：驱动没了",
     ["推到：[\"let dropped = historyStore.droppedFilesNotice\", \"let pasteFailure"]),
    ("M209", "多出一条没登记的横幅", CONTENT, BANNER_BLOCK,
     BANNER_BLOCK + "\n" + BANNER_BLOCK.replace("dismissRetentionNotice()", "dismissRetentionNotice()"),
     ["NoticeBanner 调用点的门控名单和产品不一致"]),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if ("error: -[" in line and " failed" in line) or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return "DID-NOT-RUN（整批 skip）", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-1500:])
    print("预检 OK（未变异时这批全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out, failed = run()
        messages = failure_messages(out)
        hit = [n for n in needles if any(n in m for m in messages)]
        right = bool(needles) and len(hit) == len(needles) and "待 --measure" not in needles
        ok = restore(path, original)
        results.append((mid, code, "MEASURE" if measure else ("yes" if right else "NO"),
                        "yes" if ok else "NO", ",".join(f.split(".")[-1] for f in failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure or not right or code != "CAUGHT":
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:420])
            print(out[-400:])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] not in ("yes", "MEASURE")]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


if __name__ == "__main__":
    main()
