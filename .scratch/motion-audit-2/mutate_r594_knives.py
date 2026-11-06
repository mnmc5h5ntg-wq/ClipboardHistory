# -*- coding: utf-8 -*-
"""R594 变异表 M1611–M1622：靶 2 的预测块守卫、靶 4 的三件仪器、靶 3 的产品界、以及靶 5 的列宽三向。

刀号来源：**落刀前现读** —— `grep -rhno "M1[0-9]{3}"` 在 .scratch/scripts/台账里读到的最大号是
**M1610**（R593 那一表的末把），本轮从 **M1611** 起。

| 刀 | 摘掉的那一件 | 证人 |
|---|---|---|
| M1611 | 把一条预测的判法坐死成 `return True` | `test_prediction_block_guard`（用户点名的"两向都必须响"第一向） |
| M1612 | 判法里把一个常量名写错（R593 留下的那一朵的形状） | 同一卷（真调用就崩 ⇒ NameError 必须被抓到） |
| M1613 | 删掉一条预测的「通道」那一格 | 同一卷（四格齐那一格） |
| M1614 | 抄行守卫里"被抄那一行的表名 ≠ 声称的新表"那一段 | `test_instrument_quote_guard.test_the_r593_shape_...` |
| M1615 | 前置门认"本轮那一节"退回**只看位置** | `test_ledger_preflight`（新增的 locate 对照：乱序必须 一致=0） |
| M1616 | 幂等证人把快照取在第一次落盘**之前** | `test_ledger_idempotency_gate`（幂等写手那格会红在"第一次就算改了盘"） |
| M1617 | 产品里"放不下就不记记忆宽"那一格界（无条件记） | `FoldGeometryMigrationTests.testShouldRememberWidthTruthTable...` |
| M1618 | 同一条界写成**无条件不记**（记忆功能被关掉） | 同一格（两行正对照各红一处） |
| M1619 | `WindowConfigurator` 的 `.fullScreenNone` 换成 `.fullScreenPrimary` | 同一卷 `testTheMainWindowRefusesFullScreen...`（契约格） |
| M1620 | 把 ContentView 那一行的三个值**全钉回常量**（R592/R593 交付里的那一行） | `FoldGeometryReanchorTests.testColumnsFollowTheCurrentWindowWidthNotTheSpecConstant` |
| M1621 | `equalizeColumns` 把中缝放到**观察到的旧值**上 ⇒ 只有右侧跟着窗口变（用户实测那一句） | 同一格（1000/1200 两档的"左右差"） |
| M1622 | 列宽推导**不看 collapsed 分支**（折叠档也按"减中缝再减半"算） | `FoldGeometryReanchorTests.testCollapsedColumnWidthIsNotTheExpandedHalf` |

M1620/M1621/M1622 是用户点名的三向："钉回常量必须红""只改一侧宽度必须红""折叠态用展开态列宽必须红"，
三把各红在**不同的断言**上；M1620 与 M1621 尤其要分开 —— 前者证"锁死不行"、后者证"只修一边也不行"，
只落一把的话另一条坏法还能绿着交付。

M1617 与 M1618 是**同一对反方向**：只测一边等于没测（R577 那一课），两把都必须红、且红在同一格的不同断言上。

用法：python3 .scratch/motion-audit-2/mutate_r594_knives.py M1611
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净/锚点不合格；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r594/knife_status.txt"

PY_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PY_ENV["PYTHONUTF8"] = "1"
PY_ENV["PYTHONDONTWRITEBYTECODE"] = "1"
PY_ENV.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)

POLICY = u"ClipboardHistory/Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
CONFIGURATOR = u"ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"
CONTENT_VIEW = u"ClipboardHistory/Sources/ClipboardHistoryApp/Views/ContentView.swift"
HANDOFF = u".scratch/motion-audit-2/ci_status_r593.py"
QUOTE = u"scripts/instrument_quote_guard.py"
PREFLIGHT = u"scripts/ledger_preflight.py"
IDEM = u"scripts/ledger_idempotency_gate.py"

SWIFT_FILTER = u"FoldGeometryMigrationTests"
SWIFT_FILTER_COLUMN = u"FoldGeometryReanchorTests"
PRED_TESTS = u"scripts.tests.test_prediction_block_guard"
QUOTE_TESTS = u"scripts.tests.test_instrument_quote_guard"
PREFLIGHT_TESTS = u"scripts.tests.test_ledger_preflight"
IDEM_TESTS = u"scripts.tests.test_ledger_idempotency_gate"

ARMS = [
    (u"M1611", u"把交接预测②的判法坐死成 return True ⇒ 空日志也算命中（用户点名的第一向）",
     HANDOFF, u"python",
     u'     u"判法": lambda g: any(u"内层判=" in l for l in g)},',
     u'     u"判法": lambda g: True},', PRED_TESTS),
    (u"M1612", u"判法里把一个常量名写错（R593 那两条未定义常量的形状）⇒ 下一轮真调用就 NameError",
     HANDOFF, u"python",
     u'     u"判法": lambda g: bool(g) and all(any(n in l for n in KNOWN_RUNNER_REDS) for l in g)},',
     u'     u"判法": lambda g: bool(g) and all(any(n in l for n in KNOWN_RUNNER_REDS_TYPO) for l in g)},',
     PRED_TESTS),
    (u"M1613", u"删掉一条预测的「通道」那一格 ⇒ 四格齐的门失去对象（下一轮从问题开始）",
     HANDOFF, u"python",
     u'     u"通道": u"步骤 `On-screen probe coverage floor`',
     u'     u"通道被删": u"步骤 `On-screen probe coverage floor`', PRED_TESTS),
    (u"M1614", u"抄行守卫里「被抄那一行指向另一张表」那一段失效（R593 ④ 那一朵）",
     QUOTE, u"python",
     u"        if named and claimed:\n",
     u"        if False and named and claimed:\n", QUOTE_TESTS),
    (u"M1615", u"前置门认「本轮那一节」退回只看位置 ⇒ 台账一乱序就判到别的轮次上",
     PREFLIGHT, u"python",
     u"        head = by_content\n",
     u"        head = by_pos\n", PREFLIGHT_TESTS),
    (u"M1616", u"幂等证人把快照取在第一次落盘之前 ⇒ 连幂等写手都被判成改了盘",
     IDEM, u"python",
     u"    rc = replay(u\"第一次\")\n    if rc:\n        return rc\n    first = md5s(args.repo)\n",
     u"    first = md5s(args.repo)\n    rc = replay(u\"第一次\")\n    if rc:\n        return rc\n",
     IDEM_TESTS),
    (u"M1617", u"产品的记忆界写成无条件记 ⇒ 放大那一档进了记忆（1470 那种屏形下永久非 √2）",
     POLICY, u"swift",
     u"        return specHeight <= visibleHeight\n",
     u"        return true   // 刀下：无条件记\n", SWIFT_FILTER),
    (u"M1618", u"同一条界写成无条件不记 ⇒ 记忆宽那一支整个被关掉（反方向那一把）",
     POLICY, u"swift",
     u"        guard let visibleHeight, visibleHeight > 0 else { return true }\n",
     u"        guard let visibleHeight, visibleHeight > 0 else { return false }\n", SWIFT_FILTER),
    (u"M1619", u"主窗的全屏契约换成 fullScreenPrimary ⇒ 「全屏对产品窗不可达」这一句变成散文",
     CONFIGURATOR, u"swift",
     u"            window.collectionBehavior = [.managed, .fullScreenNone]\n",
     u"            window.collectionBehavior = [.managed, .fullScreenPrimary]\n", SWIFT_FILTER),
    (u"M1620", u"把 ContentView 那一行三个值全钉回常量（= R592/R593 交付里实际在跑的那一行）",
     CONTENT_VIEW, u"swift",
     u"                .navigationSplitViewColumnWidth(min: 200, ideal: MainWindowCollapsePolicy.columnWidth(contentWidth: MainWindowCollapsePolicy.expandedWidthDefault), max: .infinity)\n",
     u"                .navigationSplitViewColumnWidth(min: MainWindowCollapsePolicy.legacyConstantColumnWidth, ideal: MainWindowCollapsePolicy.legacyConstantColumnWidth, max: MainWindowCollapsePolicy.legacyConstantColumnWidth)\n",
     SWIFT_FILTER_COLUMN),
    (u"M1621", u"等分那一趟把中缝放到「观察到的旧值」上 ⇒ 只有右侧跟着窗口变（用户实测那一句）",
     CONFIGURATOR, u"swift",
     u"            split.splitView.setPosition(want, ofDividerAt: 0)\n",
     u"            split.splitView.setPosition(current, ofDividerAt: 0)\n",
     SWIFT_FILTER_COLUMN),
    (u"M1622", u"列宽推导不看 collapsed 分支 ⇒ 折叠档也被算成「减中缝再减半」（展开档那一半）",
     POLICY, u"swift",
     u"        return collapsed ? contentWidth : (contentWidth - seamDividerThickness) / 2\n",
     u"        return (contentWidth - seamDividerThickness) / 2\n",
     SWIFT_FILTER_COLUMN),
]


def run_python(module):
    proc = subprocess.run([sys.executable, u"-m", u"unittest", module],
                          cwd=ROOT, capture_output=True, text=True, env=PY_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if u"Ran " not in out:
        return u"DID-NOT-RUN", proc.returncode, out
    return (u"PASSED" if proc.returncode == 0 else u"CAUGHT"), proc.returncode, out


def run_swift(filter_name):
    proc = subprocess.run([u"swift", u"test", u"--triple", u"arm64-apple-macosx",
                           u"--filter", filter_name],
                          cwd=os.path.join(ROOT, "ClipboardHistory"),
                          capture_output=True, text=True, env=PY_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    if u"Executed " not in out:
        return u"DID-NOT-RUN", proc.returncode, out
    return (u"PASSED" if proc.returncode == 0 else u"CAUGHT"), proc.returncode, out


def run_tests(kind, witness):
    return run_python(witness) if kind == u"python" else run_swift(witness)


def record(line):
    with io.open(STATUS, u"a", encoding=u"utf-8") as handle:
        handle.write(line + u"\n")


def sub_once(text, needle, replacement):
    n = text.count(needle)
    if n != 1:
        return None, u"原文命中 %d 次" % n
    return text.replace(needle, replacement, 1), u""


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == arg), None)
    if arm is None:
        print(u"用法: mutate_r594_knives.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, target_file, kind, needle, replacement, witness = arm
    path = os.path.join(ROOT, target_file)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(kind, witness)
    print(u"%s 预检(%s/%s): %s (rc=%d)" % (mid, kind, witness, code, pre_rc))
    if code != u"PASSED":
        print(out[-2000:])
        record(u"r594/%s precheck=%s witness=%s 未落刀" % (mid, code, witness))
        return 2
    new_text, err = sub_once(text, needle, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"r594/%s anchor=%s 未落刀" % (mid, err))
        return 1
    if target_file.endswith(u".py"):
        compile(new_text, target_file, u"exec")
    with io.open(path, u"w", encoding="utf-8") as handle:
        handle.write(new_text)
    try:
        code, post_rc, out = run_tests(kind, witness)
    finally:
        open(path, "wb").write(orig)
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        s = line.strip()
        if s.startswith((u"FAIL:", u"ERROR:", u"Ran ", u"Executed ", u"AssertionError")) or u"error:" in s:
            print(u"  读数:", s[:300])
    clean = open(path, "rb").read() == orig
    print(u"%s RESTORE_CLEAN=%d" % (mid, 1 if clean else 0))
    record(u"r594/%s %s witness=%s restore=%s" % (mid, code, witness, u"clean" if clean else u"DIRTY"))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
