#!/usr/bin/env python3
"""R61 变异对照：每一刀必须让一条**具名**判据变红，否则那把尺是空的。

跑法（仓库根）：
    python3 .scratch/motion-audit-2/mutate_r61_reveal.py
它只改两个产品文件，每刀之后 `git checkout --` 还原；日志写
    .scratch/motion-audit-2/r61_mutation_battery.log

为什么这一族要单独记：本轮的修法本体是"什么时候滚、什么时候不滚"，
四个判据（近处不跳 / 远处滚过去 / 用户滚开不再被拽回 / 只滚不选）
各自钉住一句话。没有这套对照，"四臂全绿"完全可能是"探针根本推不动像素"。
"""
import os
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(REPO, "ClipboardHistory")
REVEALER = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/SelectedRowRevealer.swift"
SIDEBAR = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
SHOTS = "/tmp/r61_mutant_shots"

# (编号, 说明, 文件, 原文, 变异后, 期望被哪条判据抓到, 跑哪个 filter)
MUTATIONS = [
    ("M311", "行号算不到就兜底成第 0 行", REVEALER,
     "        return visibleOrder.firstIndex(of: selectedID)",
     "        return visibleOrder.firstIndex(of: selectedID) ?? 0",
     "SelectedRowRevealTests/testRowIndexTruthTable",
     "SelectedRowRevealTests/testRowIndexTruthTable"),
    # 配套：M313 需要一个"按行号记"的字段，先把它塞进源码（还原时按内容整体回滚）。
    ("M312", "去掉「已经在视口里就不滚」那道闸", REVEALER,
     "        if let scroll = table.enclosingScrollView,\n"
     "           scroll.documentVisibleRect.intersects(table.rect(ofRow: row)) {\n"
     "            lastRevealedKey = key\n"
     "            return\n"
     "        }\n",
     "",
     "臂1 后半句：选中看得见的行不许推动视口",
     "UIInteractionProbeTests/testOffScreenProgrammaticSelectionIsRevealedAndNotJumped"),
    # M313 第一版是"删掉那道闸" —— 它活了下来，而且**删对了**：SwiftUI 在 rowIndex 不变时
    # 根本不再调 updateNSView，所以"没有闸"和"有闸"在同一台机器上读不出差别。
    # 现在这一刀改成"把闸门的键从选中 id 换成行号"：这才是两种写法真会分岔的地方（臂 5 的行号漂移）。
    ("M313", "闸门改按行号判（而不是按选中 id）", REVEALER,
     "        nsView.revealIfSelectionChanged(key: revealKey, row: rowIndex)",
     "        nsView.revealIfSelectionChanged(key: rowIndex.map { AnyHashable($0) }, row: rowIndex)",
     "臂5：选中项只是行号漂了，视口不许动（本轮实测：SURVIVED，见日志里的机制说明）",
     "UIInteractionProbeTests/testOffScreenProgrammaticSelectionIsRevealedAndNotJumped"),
    ("M317", "闸门整个拆掉（每次重算都滚）", REVEALER,
     "        if key == lastRevealedKey { return }\n",
     "",
     "臂3 / 臂5（本轮实测：SwiftUI 不再调 updateNSView 时这一刀可能没人接 ⇒ 记进电池日志，不假称被抓）",
     "UIInteractionProbeTests/testOffScreenProgrammaticSelectionIsRevealedAndNotJumped"),
    ("M314", "同步滚（撤掉推迟一个回合）", REVEALER,
     "        DispatchQueue.main.async { [weak self, weak table] in\n"
     "            guard let self, let table, self.lastRevealedKey == key else { return }\n"
     "            table.scrollRowToVisible(row)\n"
     "        }",
     "        table.scrollRowToVisible(row)",
     "臂2：选中集合必须**只有**那一行（同步滚会留下 [2, 60]）",
     "UIInteractionProbeTests/testOffScreenProgrammaticSelectionIsRevealedAndNotJumped"),
    ("M315", "揭示器顺手把选中也写了（第二个作者）", REVEALER,
     "            table.scrollRowToVisible(row)",
     "            table.scrollRowToVisible(row)\n"
     "            table.selectRowIndexes(IndexSet(integer: row), byExtendingSelection: false)",
     "SelectedRowRevealTests/testRevealerOnlyScrollsAndNeverSelects",
     "SelectedRowRevealTests/testRevealerOnlyScrollsAndNeverSelects"),
    ("M316", "把揭示器从侧栏摘掉", SIDEBAR,
     "        .background(\n"
     "            SelectedRowRevealer(\n"
     "                revealKey: (historyStore.selectedEntry?.id).map { AnyHashable($0) },\n"
     "                rowIndex: SelectionRevealPlan.rowIndex(\n"
     "                    of: historyStore.selectedEntry?.id,\n"
     "                    in: historyStore.filteredEntries.map(\\.id)))\n"
     "        )",
     "",
     "声明守卫 + 臂2（61 复发）",
     "SelectedRowRevealTests/testSidebarDoesNotClaimTheSwiftUIScrollRoute"),
]


def run(cmd, env=None):
    proc = subprocess.run(cmd, shell=True, cwd=PKG, capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, timeout=1800)
    return proc.returncode, proc.stdout + proc.stderr


LOCK = "/tmp/r61_mutate.lock"


def acquire_lock():
    """同一份源码上**同时跑两套变异**是本轮真的发生过的事：
    第一套还没退，第二套就开跑，于是基线读到对面那一刀的产物（红），整套对照作废。
    这里用 pidfile 挡一下：锁存在且进程还活着就直接退出。"""
    if os.path.exists(LOCK):
        old = open(LOCK, encoding="utf-8").read().strip()
        alive = subprocess.run(f"kill -0 {old}", shell=True, capture_output=True).returncode == 0
        if alive:
            print(f"已经有一在跑（pid={old}）⇒ 拒绝并发变异，等它结束")
            return False
    open(LOCK, "w", encoding="utf-8").write(str(os.getpid()))
    return True


def main():
    os.makedirs(SHOTS, exist_ok=True)
    if not acquire_lock():
        return 3
    lines = []

    # 先跑一遍**没有变异**的基线：基线一红，后面每一刀的"CAUGHT"都是假的
    # （第一轮就栽过：判据本身在红，六刀全"被抓"，其实一刀没测）。
    env0 = {"CLIPBOARD_HISTORY_UI_INTERACTION": "1", "CLIPBOARD_HISTORY_UI_SHOTS": SHOTS}
    code0, out0 = run("env -u SDKROOT swift test --filter "
                      "'SelectedRowRevealTests|UIInteractionProbeTests/testOffScreenProgrammaticSelection"
                      "IsRevealedAndNotJumped|UIInteractionProbeTests/testIntakeBehindATallPinnedBlock"
                      "RevealsTheNewRow'", env0)
    if code0 != 0:
        print("基线就是红的 ⇒ 这一整套对照不算数，先修判据本身")
        print("\n".join([l for l in out0.splitlines() if "error: -[" in l][:5]))
        return 2
    print("基线绿（无变异，判据全部通过）⇒ 下面每一刀的红才有意义\n")

    for mid, note, path, old, new, judge, flt in MUTATIONS:
        abs_path = os.path.join(REPO, path)
        src = open(abs_path, encoding="utf-8").read()
        # 还原必须**按内容**，不能用 `git checkout --`：新文件还没进版本库，
        # git 会报 pathspec 不匹配，于是这一刀留在树上、下一刀叠上去
        # （本轮真的这么干过：四刀堆在同一个文件里，读数全是污染的）。
        backup = src
        if old not in src:
            verdict = "BROKEN-MUTATION（原文没找到，这一刀根本没落下 ⇒ 结论不算数）"
            out = ""
        else:
            open(abs_path, "w", encoding="utf-8").write(src.replace(old, new, 1))
            env = {"CLIPBOARD_HISTORY_UI_INTERACTION": "1", "CLIPBOARD_HISTORY_UI_SHOTS": SHOTS}
            code, out = run(f"env -u SDKROOT swift test --filter '{flt}'", env=env)
            open(abs_path, "w", encoding="utf-8").write(backup)
            # "红"必须是**断言红**：编译错误、崩溃、加载失败都会让退出码非 0，
            # 那些情况下这一刀根本没经过判据，记成 CAUGHT 就是假绿的反面 —— 假抓。
            assertion_red = [l for l in out.splitlines() if "error: -[" in l]
            compile_red = [l for l in out.splitlines() if "error: cannot " in l or "error: use of " in l]
            if code != 0 and assertion_red:
                verdict = "CAUGHT（断言红：" + assertion_red[0].split(" : ")[-1][:110] + "）"
            elif code != 0 and compile_red:
                verdict = "BROKEN-MUTATION（编译错误，不是判据抓的：" + compile_red[0][:110] + "）"
            elif code != 0:
                verdict = "BROKEN-MUTATION（退出码非 0 但没有断言红 —— 崩溃或没跑，不算抓到）"
            else:
                verdict = "SURVIVED ⇒ 那把尺没有分辨率（本轮 M313/M317 的原因见文件头注释与 BACKLOG 91）"
        lines.append(f"{mid} {note}\n    期望被抓：{judge}\n    结果：{verdict}\n")
        print(lines[-1], flush=True)
    text = "\n".join(lines)
    out_path = os.path.join(REPO, ".scratch/motion-audit-2/r61_mutation_battery.log")
    open(out_path, "w", encoding="utf-8").write(text)
    bad = [l for l in lines if "SURVIVED" in l or "BROKEN" in l]
    print(f"\n写盘：{out_path}  共 {len(lines)} 刀，可疑 {len(bad)} 刀")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
