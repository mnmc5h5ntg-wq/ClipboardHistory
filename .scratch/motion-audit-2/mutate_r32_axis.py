#!/usr/bin/env python3
"""R32 变异对照：详情区"只有一条左轴"这件事，两半各有一支电池。

四支：
  M137 把共享helper的第二段对齐从 leading 改成 center ⇒ 整块居中，轴离开 gutter
  M138 从helper里删掉列宽上限                    ⇒ 轴仍然在 gutter！必须红在 Round3 那条源码守卫上
  M139 只把"原文正文"那一支退回旧的居中写法        ⇒ 帧判据红在 spread，源码守卫红在调用点计数
  M140 把量尺的正文带切掉首行（回到我第一版犯的错）  ⇒ 必须红，不许安静地"全绿"

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SRC = os.path.join(ROOT, "Sources/ClipboardHistoryApp")
FILES = {
    "ext": os.path.join(SRC, "Views/ViewExtensions.swift"),
    "detail": os.path.join(SRC, "Views/DetailView.swift"),
    "harness": os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"),
}
SHOTS = "/tmp/r32-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

AXIS = "UICaptureTests/testDetailAreaHasASingleLeftAxis"
WIRING = "Round3DetailTypographyTests/testDetailViewIsWiredToTheMeasureAndTheHighlight"

HELPER = """        self.frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)
            .frame(maxWidth: .infinity, alignment: .leading)"""
RAW_ARM = """                )\n                .detailReadableColumn()"""

MUTATIONS = [
    # (id, 标题, 文件, needle, mutant, 测试, 期望的失败文本)
    ("M137", "共享 helper 改成居中", "ext",
     "            .frame(maxWidth: .infinity, alignment: .leading)\n    }",
     "            .frame(maxWidth: .infinity, alignment: .center)\n    }",
     AXIS, "那一块不在内容列上"),
    ("M138", "删掉可读列的宽度上限", "ext",
     HELPER, "        self.frame(maxWidth: .infinity, alignment: .leading)",
     WIRING, "没了列宽上限"),
    ("M139", "只有原文那一支退回居中", "detail",
     RAW_ARM,
     "                )\n"
     "                .frame(maxWidth: DetailTypography.columnWidth(), alignment: .leading)\n"
     "                .frame(maxWidth: .infinity, alignment: .center)",
     AXIS, "左轴最宽差"),
    ("M140", "正文带切掉首行（重犯我第一版的错）", "harness",
     '("detail-0-text", "正文（原文）", CGRect(x: 0, y: 100, width: 720, height: 400))',
     '("detail-0-text", "正文（原文）", CGRect(x: 0, y: 112, width: 720, height: 388))',
     AXIS, "那一块不在内容列上"),
]


def run(test_filter):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    passed = [l for l in lines if "Test Case" in l and "passed" in l]
    failed = [l for l in lines if "Test Case" in l and " failed" in l]
    if not passed and not failed:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:160] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {k: open(v, encoding="utf-8").read() for k, v in FILES.items()}
    digests = {v: open(v, "rb").read() for v in FILES.values()}

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    ok = True
    for test in (AXIS, WIRING):
        verdict, out = run(test)
        print(f"  {test:66s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            ok = False
            print((out.splitlines() or [""])[-1][:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, key, needle, mutant, test, expect in MUTATIONS:
        text = originals[key]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, f"needle 命中 {got} 次，期望 1 ⇒ 不注入"))
            print(f"{mid}: DID-NOT-RUN needle 命中 {got} 次", flush=True)
            continue
        path = FILES[key]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(needle, mutant))
        try:
            verdict, out = run(test)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(path, "wb") as handle:
                handle.write(digests[path])
        reason = ""
        if verdict == "CAUGHT":
            hit = [l for l in out.splitlines() if expect in l][:1]
            reason = "对  「" + hit[0].strip()[-150:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [l for l in out.splitlines() if "error:" in l][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R32 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
