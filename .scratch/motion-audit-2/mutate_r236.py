import io, os, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILTER = "MenuBarDismissRowInkTests|MenuBarSwiftUIDismissRowInkTests"

# R236（BACKLOG 264）：三刀两轴。M789 = 12 那棵 AppKit 树的在岗证人（顺带做回归对照），
# M790 = 沿用（即 R235 那枚 ESCAPED 的 M787 同一处变异） R235 那一刀的字面（问「绕过缝就地钉色」有没有牙），M791 = 新加（问「钉进缝里」有没有牙）。
# M790 的 needle 在重构之后仍然命中一次 —— 它钉的就是缝体内那一句 Text，缝没把它搬走。
DISMISS = 'Text("都不是我想要的")'
KNIVES = [
    ("M789", "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift",
     "            menu.addItem(dismissItem)",
     "            dismissItem.attributedTitle = NSAttributedString(\n"
     '                string: "都不是我想要的",\n'
     "                attributes: [.foregroundColor: NSColor.systemBlue])\n"
     "            menu.addItem(dismissItem)",
     "把写死的那颗蓝钉回 12 那棵 AppKit 树（在岗证人：两档静置与选中都必须红）"),
    ("M790", "Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift",
     DISMISS,
     DISMISS + '.foregroundStyle(.blue)',
     "把那颗蓝就地钉回 13 那棵的标签里（绕过缝）⇒ 结构轴 testDismissRowLabelRoutesThroughTheSeam 必须抓到"),
    ("M791", "Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift",
     "static var dismissRowInk: Color? { nil }",
     "static var dismissRowInk: Color? { .blue }",
     "把那颗蓝钉进缝里（缝参与判定）⇒ 行为轴两档 × 两种地板必须抓到"),
]


def run_tests():
    # SDKROOT 必须由子跑剥掉（沿用 mutate_r235 的实测：Xcode 的 swiftc + CLT 的 SDK 让 manifest 直接编不过）
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    p = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=1800)
    return p.stdout + p.stderr


def manifest_broken(out):
    return "Invalid manifest" in out


def red_names(out):
    # 名字列本轮才修对：`split("]")[-1]` 取的是 `]` **之后**那段，对 `--[Mod.Class testFoo]` 恒为空串
    # ⇒ R235 那一版仪器的「红名」列一直是空白（CAUGHT 归类没坏，它靠的是失败行存在性；坏的是名字）。
    # 现在取 [-2]，并加一条同源自证：红名必须非空且含 `test`，否则这一格不许出 CAUGHT。
    names = sorted({ln.split("'")[1].split("]")[-2].strip()
                    for ln in out.splitlines() if "Test Case '-[" in ln and "failed" in ln})
    return [n for n in names if n]


# 基线臂：不改动任何文件先跑一次。它红了 ⇒ 后面所有「红」都不能算产品的（拒绝出表）。
base = run_tests()
io.open("/tmp/r236_mutate_base.log", "w", encoding="utf-8").write(base)
if manifest_broken(base) or "Executed" not in base or red_names(base):
    print("R236_MUTATE_REFUSED 基线臂不可信 manifest_broken=%s executed=%s 红名=%s"
          % (manifest_broken(base), "Executed" in base, ",".join(red_names(base)) or "无"))
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
    clean = "yes" if io.open(path, encoding="utf-8").read() == src else "NO"
    names = red_names(out)
    io.open("/tmp/r236_knife_%s.log" % kid, "w", encoding="utf-8").write(out)
    # 归类顺序不许反：红掉的测试名先算数（失败行本身带 error:，按 error: 判会把 CAUGHT 误判成 NOT_RUN）
    if names:
        verdict, caught = "CAUGHT", caught + 1
    elif manifest_broken(out):
        verdict, not_run = "NOT_RUN(manifest 编不过)", not_run + 1
    elif "Executed" not in out:
        verdict, not_run = "NOT_RUN(卷没跑)", not_run + 1
    else:
        verdict, escaped = "ESCAPED", escaped + 1
    rows.append((kid, verdict, clean + "|" + (";".join(names) if names else verdict)))

for r in rows:
    print("R236_KNIFE %s %s EXTRA=%s" % (r[0], r[1], r[2]))
print("R236_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s"
      % (len(KNIVES), caught, escaped, not_run,
         "yes" if all(x[2].startswith("yes") for x in rows) else "NO"))
