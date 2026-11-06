# -*- coding: utf-8 -*-
"""R592 变异表 M1582–M1595：升级迁移（用户签字的那条硬验收）与构建落点（BACKLOG 620）各钉一把。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 .scratch、scripts、七本台账里各读一遍
⇒ 高水位 **M1581**（R591 那一表的末把），本轮从 **M1582** 起，没抄派单里的数。

为什么要两半各一把：本轮同时改了**产品的几何迁移**和**构建产物的落点**，两种坏法修法相反；
只钉一半的话，下一轮把另一半撤掉没有任何东西会红。

臂的形状是 `(编号, 说明, 文件, kind, 原文, 变异文, 证人)` —— 这一版是按
`mutate_needle_precheck.arm_sites` 认识的那一种写的（第一版把 kind 放在第三位，
预检抽不出 needle ⇒ 只能把它改成能被静态认的形状）。

| 刀 | 摘掉的那一件 | 证人（必须红的格子） |
|---|---|---|
| M1582 | 产品入口里那句迁移调用 | `testLegacyMemoryIsRaisedOnceThroughTheControllerEntry` |
| M1583 | 「恰好等于旧默认对」这个条件 ⇒ 一律抬 | `testAUserWhoActuallyResizedIsLeftAlone`（用户自己调过的被抹） |
| M1584 | 版本键不写 | `testVersionKeyIsWhyTheSecondLaunchLeavesTheUsersOwnWidthAlone`（第二跑又抬） |
| M1585 | 恢复帧整块不改（含分栏帧那一半） | 「恢复帧的宽没抬」那三条断言 |
| M1586 | 顶边不回算（y 原样写回） | 「顶边动了」+ 纯字符串那两格 ⇒ **与 M1585 红在同一格的不同断言上，判定按红话里的字样分开** |
| M1587 | 只摘分栏帧那一支 | 「分栏子视图帧还留着」那一条（把 M1585 的两支拆开，各判各的） |
| M1588 | Makefile 又把 .app 落回仓库根 | `test_make_bundle_recipe_never_writes_the_repo_root` |
| M1589 | 换装脚本默认又指回仓库根 | `test_the_default_bundle_is_the_staging_dir_not_the_repo_root` |
| M1590 | 「违规就不许装」那一格失效 | `test_a_bundle_left_at_the_repo_root_refuses_the_whole_install` |
| M1591 | 沙箱强制不启动那一支失效 | `test_a_non_applications_dest_cannot_launch_a_second_copy` |
| M1592 | 守卫里「红」被 not-run 掩掉（顺序换回去） | `test_red_is_not_masked_by_a_missing_build_object` |
| M1593 | 守卫的扫描函数变成恒空（**尺盲要响**） | `test_it_sees_the_bundle_at_the_root_and_ignores_nested_fixtures` |
| M1594 | 恢复帧的键匹配放宽成「所有 NSWindow Frame 键」 | `testTheMigrationOnlyRecognisesItsOwnMainWindowKeys` |
| M1595 | 判据里把旧默认对换成产品常量以外的数 | `testPlanTruthTableNamesAllFourExits`（证明它按产品常量喂输入） |

用法：python3 .scratch/motion-audit-2/mutate_r592_migration.py M1582
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净/锚点不合格；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r592/knife_status.txt"

PY_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PY_ENV["PYTHONUTF8"] = "1"
PY_ENV["PYTHONDONTWRITEBYTECODE"] = "1"
PY_ENV.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)

POLICY = u"ClipboardHistory/Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
CONTROLLER = u"ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
MIG_TEST = u"ClipboardHistory/Tests/ClipboardHistoryAppTests/FoldGeometryMigrationTests.swift"
SWIFT_FILTER = u"FoldGeometryMigrationTests"
GUARD_TESTS = u"scripts.tests.test_repo_root_bundle"
INSTALL_TESTS = u"scripts.tests.test_install_local"

V_STAMP = u'        if outcome.stampsVersion { defaults.set(currentVersion, forKey: versionKey) }\n'

# (编号, 说明, 文件, kind, 原文, 变异文, 证人)
ARMS = [
    (u"M1582", u"摘掉产品入口里那句迁移调用 ⇒ 旧记忆压住新默认值这一族当场回来",
     CONTROLLER, u"swift",
     u'        if persists { geometryMigration = MainWindowGeometryMigration.apply(to: defaults) }\n',
     u'', SWIFT_FILTER),
    (u"M1583", u"把「恰好等于旧默认对」放宽成「有记忆值就抬」⇒ 抹掉用户自己调过的宽度",
     POLICY, u"swift",
     u'        if storedExpanded == legacyExpandedWidth, storedCollapsed == legacyCollapsedWidth {\n',
     u'        if storedExpanded != nil {\n', SWIFT_FILTER),
    (u"M1584", u"抬完不打版本键 ⇒ 「只抬一次」没有证人，第二跑还会再抬",
     POLICY, u"swift", V_STAMP, u'', SWIFT_FILTER),
    (u"M1585", u"恢复帧那一整块都不做 ⇒ 启动后 AppKit 仍按 750×492 把窗口盖回来",
     POLICY, u"swift",
     u'        if outcome.rewritesRestoredFrames {\n'
     u'            for key in defaults.dictionaryRepresentation().keys where isMainWindowFrameKey(key) {\n'
     u'                guard let stored = defaults.string(forKey: key),\n'
     u'                      let rewritten = restoredFrameString(stored,\n'
     u'                                                          width: MainWindowCollapsePolicy.expandedWidthDefault,\n'
     u'                                                          height: MainWindowCollapsePolicy.contentHeightDefault)\n'
     u'                else { continue }\n'
     u'                defaults.set(rewritten, forKey: key)\n'
     u'            }\n',
     u'        if outcome.rewritesRestoredFrames && false {\n'
     u'            for key in defaults.dictionaryRepresentation().keys where isMainWindowFrameKey(key) {\n'
     u'                guard let stored = defaults.string(forKey: key),\n'
     u'                      let rewritten = restoredFrameString(stored,\n'
     u'                                                          width: MainWindowCollapsePolicy.expandedWidthDefault,\n'
     u'                                                          height: MainWindowCollapsePolicy.contentHeightDefault)\n'
     u'                else { continue }\n'
     u'                defaults.set(rewritten, forKey: key)\n'
     u'            }\n', SWIFT_FILTER),
    (u"M1586", u"改写恢复帧时不回算顶边 ⇒ 用户的窗口被挪走（红话=「顶边动了」）",
     POLICY, u"swift",
     u'        return String(format: "%.0f %.0f %.0f %.0f", x, top - Double(height),\n',
     u'        return String(format: "%.0f %.0f %.0f %.0f", x, y,\n', SWIFT_FILTER),
    (u"M1587", u"只摘分栏子视图帧那一支 ⇒ 详情列还是那条 326.5，两栏不等宽",
     POLICY, u"swift",
     u'            for key in defaults.dictionaryRepresentation().keys where isMainWindowSplitKey(key) {\n',
     u'            for key in defaults.dictionaryRepresentation().keys where false && isMainWindowSplitKey(key) {\n',
     SWIFT_FILTER),
    (u"M1588", u"Makefile 把 BUNDLE 指回仓库根 ⇒ 配方又往仓库根落一份可执行 .app（620 复发）",
     u"Makefile", u"python",
     u'BUNDLE  := $(STAGE)/$(APP_NAME).app\n',
     u'BUNDLE  := $(APP_NAME).app\n', GUARD_TESTS),
    (u"M1589", u"换装脚本的默认包又指回仓库根",
     u"scripts/install_local.sh", u"python",
     u'bundle="/tmp/${app_name}_bundle/${app_name}.app"\n',
     u'bundle="${repo_root}/${app_name}.app"\n', INSTALL_TESTS),
    (u"M1590", u"摘掉「违规就不许装」那一格 ⇒ 仓库根还有构建产物时照样把现场改了",
     u"scripts/install_local.sh", u"python",
     u'\tif [ "$rc" = 1 ]; then\n', u'\tif false; then\n', INSTALL_TESTS),
    (u"M1591", u"沙箱那一支失效 ⇒ `--dest` 不是 /Applications 时仍会启动一份同 id 副本",
     u"scripts/install_local.sh", u"python",
     u'if [ "$dest_dir" != "/Applications" ] && [ "$launch" = 1 ]; then\n',
     u'if false; then\n', INSTALL_TESTS),
    (u"M1592", u"守卫里把 not-run 排到红前面 ⇒ 真违规被读成「没判到」",
     u"scripts/repo_root_bundle.py", u"python",
     u'    found = app_bundles_at(root)\n'
     u'    if found:\n'
     u'        return (1, found, u"red", u"仓库根有可执行 .app ⇒ 同 id 第二份，登录项/Dock 会指向它")\n'
     u'    if not is_built_bundle(staged):\n'
     u'        return (2, found, u"not-run", u"暂存目录里没有构建产物 ⇒ 这一维没判到，不许读成干净")\n',
     u'    found = app_bundles_at(root)\n'
     u'    if not is_built_bundle(staged):\n'
     u'        return (2, found, u"not-run", u"暂存目录里没有构建产物 ⇒ 这一维没判到，不许读成干净")\n'
     u'    if found:\n'
     u'        return (1, found, u"red", u"仓库根有可执行 .app ⇒ 同 id 第二份，登录项/Dock 会指向它")\n',
     GUARD_TESTS),
    (u"M1593", u"扫描函数变成恒空（尺盲）⇒ 「名单=空」那句话不再承重",
     u"scripts/repo_root_bundle.py", u"python",
     u'        if os.path.exists(os.path.join(path, "Contents", "MacOS")):\n            out.append(name)\n',
     u'        if False:\n            out.append(name)\n', GUARD_TESTS),
    (u"M1594", u"恢复帧的键匹配放宽成「所有 NSWindow Frame 键」⇒ 系统面板的键也被改",
     POLICY, u"swift",
     u'        key.hasPrefix("NSWindow Frame ") && key.contains("ClipboardHistoryApp.") && key.contains("-AppWindow-")\n',
     u'        key.hasPrefix("NSWindow Frame ")\n', SWIFT_FILTER),
    (u"M1596", u"摄掉 applyGeometry 里那段 √2 不变量 ⇒ 恢复的 492 永远留在用户的窗口上，⑤a 那格必须红",
     CONTROLLER, u"swift",
     u'            if let lifted = MainWindowCollapsePolicy.heightLift(collapsed: isCollapsed,\n'
     u'                                                                width: width,\n'
     u'                                                                height: frame.height) {\n'
     u'                frame.size.height = lifted\n'
     u'                heightLifts += 1\n'
     u'            }\n',
     u'', SWIFT_FILTER),
    (u"M1597", u"容差写成负数（于是恒抬）⇒ 用户等比拖出来的 900×637 也被抹回 600"
               u"：⑤a 的第二趟与真值表那格必须红（容差本身要有牙）",
     POLICY, u"swift",
     u'                           tolerance: CGFloat = 0.02) -> CGFloat? {\n',
     u'                           tolerance: CGFloat = -1) -> CGFloat? {\n', SWIFT_FILTER),
    (u"M1595", u"判据里把旧默认对换成产品常量以外的数 ⇒ 真值表那一格必须跟着产品常量走",
     MIG_TEST, u"swift",
     u'            storedExpanded: MainWindowGeometryMigration.legacyExpandedWidth,\n'
     u'            storedCollapsed: MainWindowGeometryMigration.legacyCollapsedWidth,\n',
     u'            storedExpanded: 700,\n'
     u'            storedCollapsed: 390,\n', SWIFT_FILTER),
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
    return (run_python(witness) if kind == u"python" else run_swift(witness))


def record(line):
    with io.open(STATUS, u"a", encoding=u"utf-8") as handle:
        handle.write(line + u"\n")


def sub_once(text, needle, replacement):
    n = text.count(needle)
    if n != 1:
        return None, u"原文命中 %d 次" % n
    return text.replace(needle, replacement, 1), u""


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print(u"用法: mutate_r592_migration.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, target_file, kind, needle, replacement, witness = arm
    path = os.path.join(ROOT, target_file)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(kind, witness)
    print(u"%s 预检(%s/%s): %s (rc=%d)" % (mid, kind, witness, code, pre_rc))
    if code != u"PASSED":
        print(out[-2000:])
        record(u"r592/%s precheck=%s witness=%s 未落刀" % (mid, code, witness))
        return 2
    new_text, err = sub_once(text, needle, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"r592/%s anchor=%s 未落刀" % (mid, err))
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
    record(u"r592/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s kind=%s witness=%s target=%s"
           % (mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code, kind, witness,
              target_file))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
