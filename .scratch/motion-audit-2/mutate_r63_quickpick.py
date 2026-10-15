#!/usr/bin/env python3
"""R63 的变异对照：新加的两条快速选择浮层判据，每一条都得被"故意弄坏产品"抓到。

规矩沿用 R61/R62 那两份电池：
  · **按内容还原**，不用 `git checkout --`（那个坑：未跟踪文件还原失败，
    还顺手把同目录里未提交的修改一起回滚了）；
  · 一把 pidfile 锁，防两条电池同时跑互相读脏（R61 实测过：基线读到对方的变异）；
  · 每条变异前先证明**基线是绿的**，否则这条的"红"没有意义；
  · 变异必须**自证落地**：还原前后各比一次文件内容，替换没发生就报 DRIFT-NOT-APPLIED，
    而不是安静地记一条"没抓到"。

判据：
  testQuickPickOverlayFillsItsPanelAndCanBeCaptured
      rows>0 / dataSourceIsController / transparent<0.9 / stack 两条轴都占满面板 / visibleRect ≥ 2 行
  testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot
      那句话在、没被藏、alphaValue==1、且紧跟在搜索框下面（≤24pt）
"""
import os
import re
import subprocess
import sys
import time

REPO = "/Users/wangziyi/Codex_Project0"
CONTROLLER = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
CASES = [
    "testQuickPickOverlayFillsItsPanelAndCanBeCaptured",
    "testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot",
]
LOCK = "/tmp/r63_mutate.lock"

# (编号, 说明, 原文, 变异后, 期望红的用例)
MUTATIONS = [
    # 编号从 M325 起。R63 跑过两轮：第一轮 M330/M331/M333 三刀绿着回来，
    # 于是那三处代码本轮**删掉了**（没有作者的行不留）；M332 也绿着回来，
    # 但它逼出了"长查询词"那一档判据，而那一档立刻抓到本轮自己改出来的
    # 「面板从 420 被顶到 899」—— 所以这一批的读法是：**刀绿 = 判据或代码要重审**，
    # 不是"电池失败"。
    ("M325", "把贴边约束换成 R63 之前那个尺寸形状（24×49 落在 420×300 里）⇒ 两条轴 + 能不能拍 都该红",
     """            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),
            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 12),
            stack.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -12),""",
     """            stack.widthAnchor.constraint(equalTo: content.widthAnchor, multiplier: 0.057),
            stack.heightAnchor.constraint(equalTo: content.heightAnchor, multiplier: 0.163),""",
     CASES[0]),
    ("M326", "只撤竖向两条贴边约束（横向留着）⇒ 只有高度那条轴该红",
     """            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 12),
            stack.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -12),""",
     """            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 12),""",
     CASES[0]),
    ("M327", "只撤横向两条贴边约束（竖向留着）⇒ 只有宽度那条轴该红",
     """            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -12),""",
     """            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 12),""",
     CASES[0]),
    ("M328", "撤掉 `empty.wantsLayer = true` ⇒ 那句话的模型值回到动画手里",
     "        empty.wantsLayer = true",
     "        // M328：撤掉图层 ⇒ 非图层 view 上 `animator()` 不提交模型值",
     CASES[1]),
    ("M329", "把那句话挪回列表**下面**（R7 的老位置）⇒ 竖向位置那条该红",
     "        let stack = NSStackView(views: [field, empty, scroll])",
     "        let stack = NSStackView(views: [field, scroll, empty])",
     CASES[1]),
    ("M335", "撤掉句子的抗压缩降级 ⇒ 面板被顶宽（本轮真实抓到过的缺陷：420 → 899）",
     "        empty.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)",
     "        // M335：撤掉这一行 ⇒ 抗压缩回到默认 750",
     CASES[1]),
]


def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = ""
        try:
            holder = open(LOCK).read().strip()
        except OSError:
            pass
        if holder and os.path.isdir(f"/proc/{holder}"):
            pass
        print(f"DRIFT-LOCK {LOCK} 已被 {holder or '另一个进程'} 占用 ⇒ 退出，不共享读数")
        sys.exit(2)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run_cases():
    """返回 {用例名: 'green'|'red'|'absent'}。absent = 这一条根本没跑（filter 打错/编译失败）。"""
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(
        ["swift", "test", "--filter", "UICaptureTests/testQuickPick"],
        cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
        capture_output=True, text=True, timeout=1500,
    )
    text = proc.stdout + proc.stderr
    verdicts = {}
    for case in CASES:
        passed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text)
        failed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text)
        verdicts[case] = "red" if failed else ("green" if passed else "absent")
    if "error: " in text and all(v == "absent" for v in verdicts.values()):
        first = next((line for line in text.splitlines() if "error:" in line), "")
        print("   编译/运行诊断：" + first.strip()[:200])
    return verdicts, text


def main():
    acquire_lock()
    try:
        original = read(CONTROLLER)
        print("=== 基线（未变异）必须先全绿 ===")
        verdicts, _ = run_cases()
        print("   baseline " + " ".join(f"{k.split('test')[-1][:28]}={v}" for k, v in verdicts.items()))
        if any(v != "green" for v in verdicts.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条'红'都不能算抓到的证据，整批作废")
            return 1
        for tag, note, needle, replacement, expected in MUTATIONS:
            print(f"\n{tag} {note}")
            source = read(CONTROLLER)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文在这份源码里找不到 ⇒ 这条没有跑")
                continue
            mutated = source.replace(needle, replacement, 1)
            write(CONTROLLER, mutated)
            # 自证落地：**原文不在了**且**变异文在场**才算落地。
            # 上一版这里写反了（"原文已不在"被我当成回读失败报出去），
            # 于是每一刀都打了一条看起来像警告、其实是成功确认的行 —— 读日志的人会以为电池坏了。
            after = read(CONTROLLER)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地 ⇒ 这条的结论作废")
                continue
            try:
                verdicts, _ = run_cases()
                got = verdicts[expected]
                others = {k: v for k, v in verdicts.items() if k != expected}
                mark = "CAUGHT" if got == "red" else ("ESCAPED" if got == "green" else "NOT-RUN")
                print(f"   {mark} 期望红的={expected.split('test')[-1][:34]} 实测={got}  其余={others}")
            finally:
                write(CONTROLLER, original)
                restored = read(CONTROLLER) == original
                print(f"   还原{'成功（按内容比对）' if restored else '失败！立刻手工恢复 ' + CONTROLLER}")
                if not restored:
                    return 3
            time.sleep(0.2)
        print("\n电池结束。日志请自行留存：本脚本只往 stdout 打，重定向进 .scratch/motion-audit-2/r63_mutation_battery.log")
        return 0
    finally:
        try:
            os.unlink(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
