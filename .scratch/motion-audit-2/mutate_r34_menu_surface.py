#!/usr/bin/env python3
"""R34 变异对照：菜单栏帧的"资格"三条 + 判别臂一支。

  M148 产品真的换成 `.menuBarExtraStyle(.window)`      ⇒ 前提那条必须红（这些帧就是产品本身了）
  M149 名单里悄悄少一张帧                              ⇒ 名单≡夹具那条必须红
  M150 产品给那一行加 12pt 右内边距（不再顶到帧边界）    ⇒ 证据那条必须红
  M151 判别臂改成"永远画得出来"                          ⇒ 真值表①（空白帧正对照）必须红
                                                       —— 这一支就是 R33 在 CI 上红的那个形状

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILES = {
    "app": os.path.join(ROOT, "Sources/ClipboardHistoryApp/App.swift"),
    "panel": os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift"),
    "harness": os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"),
}
SHOTS = "/tmp/r34-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
GUARD = "UICaptureTests/testMenuBarFramesAreReplicasOfTheMenuSurface"
TRUTH = "UICaptureTests/testNotRunDiscriminatorTruthTable"

MUTATIONS = [
    ("M148", "产品换成 .window 风格（表面真的变了）", "app",
     """                Button(AppCommand.quit.title) {
                    appDelegate.perform(.quit)
                }
            }
        }""",
     """                Button(AppCommand.quit.title) {
                    appDelegate.perform(.quit)
                }
            }
            .menuBarExtraStyle(.window)
        }""",
     GUARD, "这些帧**就是产品本身**"),
    ("M149", "名单里悄悄少一张帧", "harness",
     '        "menubar-recommendations", "menubar-empty", "menubar-refreshing",',
     '        "menubar-recommendations", "menubar-refreshing",',
     GUARD, "名单与夹具不一致"),
    ("M150", "那一行加了 12pt 右内边距（不再顶边）", "panel",
     """                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())""",
     """                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.trailing, 12)
                        .contentShape(Rectangle())""",
     GUARD, "不再顶到帧边界"),
    ("M151", "判别臂改成永远画得出来（R33 在 CI 上犯的错）", "harness",
     "    static func columnIsDrawable(textInkPixels: Int) -> Bool { textInkPixels > 0 }",
     "    static func columnIsDrawable(textInkPixels: Int) -> Bool { true }",
     TRUTH, "那条 NOT-RUN 分支是死的"),
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
    only = [a for a in sys.argv[1:] if a.startswith("M")]
    originals = {k: open(v, encoding="utf-8").read() for k, v in FILES.items()}
    digests = {v: open(v, "rb").read() for v in FILES.values()}

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    verdict = "ESCAPED"
    for test in (GUARD, TRUTH):
        verdict, out = run(test)
        print(f"  {test:66s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            print((out.splitlines() or [""])[-1][:220], flush=True)
            print("PREFLIGHT_FAILED ⇒ 一支都不注入", flush=True)
            return 2

    results = []
    for mid, title, key, needle, mutant, test, expect in MUTATIONS:
        if only and mid not in only:
            continue
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
            reason = "对  「" + hit[0].strip()[-170:] + "」" if hit else f"!! 红得不对（找不到「{expect}」）"
        if verdict == "DID-NOT-RUN":
            first = [l for l in out.splitlines() if "error:" in l][:1]
            reason = "  " + (first[0][:160] if first else "")
        if verdict == "ESCAPED":
            reason = "!! 变异全绿通过 ⇒ 判据没盖住这条路"
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R34 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [p for p, blob in digests.items() if open(p, "rb").read() != blob]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
