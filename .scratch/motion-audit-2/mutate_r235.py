import io, os, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILTER = "MenuBarDismissRowInkTests"

KNIVES = [
    ("M786", "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift",
     "            menu.addItem(dismissItem)",
     "            dismissItem.attributedTitle = NSAttributedString(\n"
     '                string: "\u90fd\u4e0d\u662f\u6211\u60f3\u8981\u7684",\n'
     "                attributes: [.foregroundColor: NSColor.systemBlue])\n"
     "            menu.addItem(dismissItem)",
     "把写死的那颗蓝钉回 12 那棵 AppKit 树（静置与选中两条地板都必须红，且红名必须点名新格）"),
    ("M787", "Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift",
     'Text("\u90fd\u4e0d\u662f\u6211\u60f3\u8981\u7684")',
     'Text("\u90fd\u4e0d\u662f\u6211\u60f3\u8981\u7684").foregroundStyle(.blue)',
     "把写死的那颗蓝钉回 13 那棵 SwiftUI 树 —— 这一刀问的是「那条路径上有没有会红的判据」"),
]

def run_tests():
    # SDKROOT 必须由子跑剥掉：这台机器上 Xcode 的 swiftc + CommandLineTools 的 SDK 会让
    # Package.swift 的 manifest 直接编不过（error: 'clipboardhistory': Invalid manifest，
    # 正文是 SDK 里 Swift.swiftinterface 的 7 万余条 error:）⇒ 卷根本没跑。
    # 上一版没剥它，两刀都成了 NOT_RUN（牙未被证明）。沿用 mutate_r234 的做法。
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    p = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=1800)
    return p.stdout + p.stderr


def manifest_broken(out):
    return "Invalid manifest" in out


# 基线臂：不改动任何文件先跑一次。它红了 ⇒ 后面所有"红"都不能算产品的（拒绝出表）。
base = run_tests()
io.open("/tmp/r235_mutate_base.log", "w", encoding="utf-8").write(base)
base_names = sorted({ln.split("'")[1].split("]")[-1].strip()
                     for ln in base.splitlines() if "Test Case '-[" in ln and "failed" in ln})
if manifest_broken(base) or "Executed" not in base or base_names:
    print("R235_MUTATE_REFUSED 基线臂不可信 manifest_broken=%s executed=%s 红名=%s"
          % (manifest_broken(base), "Executed" in base, ",".join(base_names) or "无"))
    sys.exit(1)

caught = escaped = not_run = 0
rows = []
for kid, rel, anchor, repl, why in KNIVES:
    path = os.path.join(ROOT, rel)
    src = io.open(path, encoding="utf-8").read()
    n = src.count(anchor)
    if n != 1:
        rows.append((kid, "ANCHOR=%d" % n, "-"))
        not_run += 1
        continue
    io.open(path, "w", encoding="utf-8").write(src.replace(anchor, repl))
    try:
        out = run_tests()
    finally:
        io.open(path, "w", encoding="utf-8").write(src)
    back = io.open(path, encoding="utf-8").read()
    clean = "yes" if back == src else "NO"
    names = sorted({ln.split("'")[1].split("]")[-1].strip()
                    for ln in out.splitlines() if "Test Case '-[" in ln and "failed" in ln})
    io.open("/tmp/r235_knife_%s.log" % kid, "w", encoding="utf-8").write(out)
    # 归类顺序不许反：红掉的测试名先算数（XCTest 的失败行本身带 "error:"，
    # 上一版把「输出里有 error: 且有 Compiling」当编译失败 ⇒ 两刀都被误判成 NOT_RUN）。
    if names:
        verdict = "CAUGHT"
        caught += 1
    elif manifest_broken(out):
        verdict = "NOT_RUN(manifest 编不过)"
        not_run += 1
    elif "Executed" not in out:
        verdict = "NOT_RUN(卷没跑)"
        not_run += 1
    else:
        verdict = "ESCAPED"
        escaped += 1
    rows.append((kid, verdict, clean + " " + ";".join(names) if names else clean + " " + verdict))

for r in rows:
    print("R235_KNIFE %s %s RESTORE_CLEAN=%s" % (r[0], r[1], r[2]))
print("R235_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s"
      % (len(KNIVES), caught, escaped, not_run,
         "yes" if all(x[2].startswith("yes") for x in rows) else "NO"))
