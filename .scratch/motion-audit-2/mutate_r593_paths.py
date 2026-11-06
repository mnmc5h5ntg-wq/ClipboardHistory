# -*- coding: utf-8 -*-
"""R593 变异表 M1598–M1610：√2 不变量的"放得下"那一半、三把新守卫、以及本轮修的那处读数行顺序。

刀号来源：**落刀前现读** —— `grep -ho "M1[0-9]{3}"` 在 .scratch/scripts/台账里读到的最大号是
**M1597**（R592 那一表的末把），本轮从 **M1598** 起。

为什么这一表有一半打在守卫上：本轮新增的三把守卫（帧通道盲区 / 台账 ⓪ 前置 / 产物内容）
都是"没有正对照就等于没判"的那一种；它们各自的判据卷里已经内置了合成坏形状，
但**合成坏形状不会自己长腿**——摘掉那一支必须有人红，否则下一轮它就是一段散文。

| 刀 | 摘掉的那一件 | 证人 |
|---|---|---|
| M1598 | 产品里"放不下就不抬"那一格界 | `testHeightLiftTruthTable`（真值表三行各点一档） |
| M1599 | 控制器不再把可见帧高喂给不变量 | `testTheInvariantDeclinesWhenTheLiftWouldNotFitTheScreen` |
| M1600 | 不抬的原因写成别的字样 | 同一格（原因那条断言）⇒ 与 M1599 红在**同一格的不同断言**上，判定按红话字样分开 |
| M1601 | 抬了却不计数 | `testARestoredOffRatioWindowIsLiftedOntoTheSpecRatio`（只抬一次那一格） |
| M1602 | 守卫的 A 支（refs>0 要红）失效 | `test_frame_geometry_blind.test_three_shapes_are_three_different_readings` |
| M1603 | 守卫的 B 支（默认挪走要红）失效 | 同一卷那一格的 B 段（用户点名的"产品变了而尺不响"那一响） |
| M1604 | ⓪ 空着也放行 | `test_ledger_preflight.test_each_shape_gets_its_own_verdict` |
| M1605 | 成对号只认 `RUN=` 一种写法 | 同一卷第二格（台账那种反引号写法） |
| M1606 | 桩解析瞎了不响 | `test_bundle_content_gate.test_three_shapes_are_three_different_verdicts` |
| M1607 | 产物不在时读成干净 | `test_bundle_content_gate.test_the_missing_artifact_is_not_run_and_says_so` |
| M1608 | 顺序扫描认不出"门在读数之前" | `test_reading_order_scan.test_the_bad_shape_is_red...` |
| M1609 | 陈旧豁免不响 | 同一卷的 selfcheck 那一格（第四把正对照） |
| M1610 | 把 `SKIP_ROSTER` 读数行挪回 fail 之后（本轮修的那处的反向） | `test_reading_order_scan.test_the_skip_roster_reading_line_is_now_before_its_gates` |

探针（**不占号**，先跑再看响不响）：`--probe-12` 那一支把 `if #available(macOS 13.0, *)` 换成 12.0，
本机是 13+ ⇒ 行为不变 ⇒ 预计 PASSED = 空刀。它的答案是"12 那一档在本机没有证人"，归具名，不归刀位。

用法：python3 .scratch/motion-audit-2/mutate_r593_paths.py M1598
      python3 .scratch/motion-audit-2/mutate_r593_paths.py --probe-12
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净/锚点不合格；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r593/knife_status.txt"

PY_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PY_ENV["PYTHONUTF8"] = "1"
PY_ENV["PYTHONDONTWRITEBYTECODE"] = "1"
PY_ENV.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)

POLICY = u"ClipboardHistory/Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
CONTROLLER = u"ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
BLIND = u"scripts/frame_geometry_blind.py"
PREFLIGHT = u"scripts/ledger_preflight.py"
CONTENT = u"scripts/bundle_content_gate.py"
ORDER = u"scripts/reading_order_scan.py"
ROSTER_TEST = u"scripts/tests/test_skip_roster.py"

SWIFT_FILTER = u"FoldGeometryMigrationTests"
BLIND_TESTS = u"scripts.tests.test_frame_geometry_blind"
PREFLIGHT_TESTS = u"scripts.tests.test_ledger_preflight"
CONTENT_TESTS = u"scripts.tests.test_bundle_content_gate"
ORDER_TESTS = u"scripts.tests.test_reading_order_scan"

ARMS = [
    (u"M1598", u"摘掉产品里「放不下就不抬」那一格界 ⇒ 1470 宽被抬到 1039.4，比屏幕还高",
     POLICY, u"swift",     # R593 落刀前修：证人 `FoldGeometryMigrationTests` 是 Swift 那一卷，kind 不能写 python
     u"        if let visibleHeight, visibleHeight > 0, target > visibleHeight { return nil }\n",
     u"        if false { return nil }\n", SWIFT_FILTER),
    (u"M1599", u"控制器不再把可见帧高喂给不变量 ⇒ decline 那一档永远不响",
     CONTROLLER, u"swift",
     u"                                                                visibleHeight: visible?.height) {",
     u"                                                                visibleHeight: nil) {",
     SWIFT_FILTER),
    (u"M1600", u"不抬的原因写成 tolerance ⇒ 读数与真值表脱钩",
     CONTROLLER, u"swift",
     u'                heightLiftDecline = "visible-too-short"',
     u'                heightLiftDecline = "tolerance"', SWIFT_FILTER),
    (u"M1601", u"抬了却不计数 ⇒ 『只抬一次』那一格失去对象（计数与写入是两件事）",
     CONTROLLER, u"swift",
     u"                frame.size.height = lifted\n                heightLifts += 1\n",
     u"                frame.size.height = lifted\n", SWIFT_FILTER),
    (u"M1602", u"守卫的 A 支失效（捕获侧已经引用常量了还说盲）",
     BLIND, u"python",
     u"    if refs > 0:\n", u"    if False and refs > 0:\n", BLIND_TESTS),
    (u"M1603", u"守卫的 B 支失效 ⇒ 默认几何改了而帧通道看不见，这一格不响（用户点名的形状）",
     BLIND, u"python",
     u"    if moved:\n", u"    if False and moved:\n", BLIND_TESTS),
    (u"M1604", u"⓪ 空着也放行 ⇒ 顺序纪律又退回散文",
     PREFLIGHT, u"python",
     u'    return 1, u"LEDGER_PREFLIGHT 红：⓪ 那一节既没有 RUN=…↔… 成对号，也没有具名的未到数 ⇒ 这一轮的 CI 根本没读"',
     u'    return 0, u"LEDGER_PREFLIGHT_RESULT=ok 刀下写的：空也放行"', PREFLIGHT_TESTS),
    (u"M1605", u"成对号只认 `RUN=` 一种写法 ⇒ 台账里那种反引号写法被判成『没读』",
     PREFLIGHT, u"python",
     # 针里不许有反斜杠（表里写 `\\d` 会被 Python 吃成 `\d`，与源文件里那两个字符对不上 ⇒ 预检 命中=0），
     # 也不许短于 `MIN_LEN=12`（第一版用 `(?:RUN=)?`，9 个字符：静态预检认了，`hidden_arms` 的候选箱却把它
     # 整条滤掉 ⇒ 报 rot=1「盘上一个都不命中」。两处尺对"针"的长度定义不同，取长的这一种。）
     u'PAIR = re.compile(u"(?:RUN=)?',
     u'PAIR = re.compile(u"RUN=', PREFLIGHT_TESTS),
    (u"M1606", u"桩解析瞎了不响 ⇒ 『没读到桩』被读成『没有桩』（D-029 那把假闸门的形状）",
     CONTENT, u"python",
     u"    if len(stubbed) < EXPECTED_MIN_STUBS:\n", u"    if len(stubbed) < 0:\n", CONTENT_TESTS),
    (u"M1607", u"产物不在时 exit 0 ⇒ not-run 被读成干净",
     CONTENT, u"python",
     u'              u"不许读成『内容干净』")\n        return 2',
     u'              u"不许读成『内容干净』")\n        return 0', CONTENT_TESTS),
    (u"M1608", u"顺序扫描认不出『门在读数之前』⇒ 这一支只会印 ok",
     ORDER, u"python",
     u"    if gate_at is not None:\n", u"    if False and gate_at is not None:\n", ORDER_TESTS),
    (u"M1609", u"陈旧豁免不响 ⇒ 登记的允许门挪到读数之后也没人管",
     ORDER, u"python",
     u"        if min(where) > emit_at:\n", u"        if False:\n", ORDER_TESTS),
    (u"M1610", u"把 `SKIP_ROSTER` 读数行挪回会崩的门之后（本轮修的那一处的反向）",
     ROSTER_TEST, u"python",
     u"        print('SKIP_ROSTER 键=%s 类=%s 内层Ran=%s",
     u"        self.fail(u'刀下加的假门：模拟读数行坐在门后面')\n"
     u"        print('SKIP_ROSTER 键=%s 类=%s 内层Ran=%s", ORDER_TESTS),
]

PROBE_12 = (u"PROBE-12", u"把 √2 那一支的版本门从 13.0 换成 12.0（模拟『12 上也抬』）",
            CONTROLLER, u"swift",
            u"        if #available(macOS 13.0, *) {\n"
            u"            // R592：√2 那条锁的补漏",
            u"            if #available(macOS 12.0, *) {\n"
            u"                // R592：√2 那条锁的补漏", SWIFT_FILTER)


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
    if arg == u"--probe-12":
        arm = PROBE_12
        tag = u"probe"
    else:
        arm = next((a for a in ARMS if a[0] == arg), None)
        tag = u"r593"
        if arm is None:
            print(u"用法: mutate_r593_paths.py " + u"|".join(a[0] for a in ARMS) + u" | --probe-12")
            return 2
    mid, why, target_file, kind, needle, replacement, witness = arm
    path = os.path.join(ROOT, target_file)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(kind, witness)
    print(u"%s 预检(%s/%s): %s (rc=%d)" % (mid, kind, witness, code, pre_rc))
    if code != u"PASSED":
        print(out[-2000:])
        record(u"%s/%s precheck=%s witness=%s 未落刀" % (tag, mid, code, witness))
        return 2
    new_text, err = sub_once(text, needle, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"%s/%s anchor=%s 未落刀" % (tag, mid, err))
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
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"%s/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s kind=%s witness=%s target=%s"
           % (tag, mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code, kind,
              witness, target_file))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
