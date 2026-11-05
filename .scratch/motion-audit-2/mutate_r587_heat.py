# -*- coding: utf-8 -*-
"""R587 变异表（热图真帧通道那一侧）M1554：缺席那一档必须被点名，且与词表顺序无关。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r58*.py、判据卷与四本台账里各读一遍
⇒ 高水位 M1553 ⇒ 本把 **M1554**。

这一把为什么值得落（本轮的现场经过）：
靶 B 把 `('dark','light')` 收成共用词表 `('light','dark')` 之后，既有那一格
`test_log_covering_only_one_appearance_is_not_a_pass` **当场变红**。红得对，但红在脚本身上：
它在第一个 stop 处就 `return 2`，所以"缺席那一档被点名"从来靠的是**循环顺序**，不是契约。
修法是 stop 不再短路（两档各自点名后再收口），并把那一格改成两档各当一次"在场"。

- M1554 把 `判据日志里没有那一档` 这一支改回短路 ⇒ 两个 subTest 都必须红
  （红在 `HEAT_FRAME_VERDICT not-run=1` 那一断言上：短路时 ok/not-run 两行都到不了）。
  帧缺失那一支**不动** ⇒ 它证明我摘的是"日志缺档"这一边，不是整段循环（R567 那条：落刀前先问"我只动了一边吗"）。

用法：python3 .scratch/motion-audit-2/mutate_r587_heat.py M1554   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r587/knife_status.txt"
TARGET = "scripts/heatmap_frame_levels.py"
TEST = "scripts.tests.test_heatmap_frame_levels"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

STOP_OLD = (u"        if tag not in judg:\n"
            u"            print('HEAT_FRAME_INPUT_MISSING 判据日志里没有 %s 那 4 对 ⇒ 两通道没法对账（不许 KeyError 当成跑过了）' % tag)\n"
            u"            stops += 1\n"
            u"            continue\n")
STOP_NEW = (u"        if tag not in judg:\n"
            u"            print('HEAT_FRAME_INPUT_MISSING 判据日志里没有 %s 那 4 对 ⇒ 两通道没法对账（不许 KeyError 当成跑过了）' % tag)\n"
            u"            return 2  # 刀：回到短路 return ⇒ 另一档从此靠顺序才被点名\n")

ARMS = [
    ("M1554", u"日志缺档那一支改回短路 return ⇒ 两个 subTest 必须红；缺帧那一支不动（只动一边）",
     STOP_OLD, STOP_NEW),
]


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", TEST],
                          cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=900)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", proc.returncode, out
    return ("PASSED" if proc.returncode == 0 else "CAUGHT"), proc.returncode, out


def record(line):
    with io.open(STATUS, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print(u"用法: mutate_r587_heat.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm[:4]
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    if code != "PASSED":
        print(out[-1500:])
        record(u"r587/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r587/%s needle=%d 未落刀" % (mid, hits))
        return 1
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text.replace(old, new, 1))
    try:
        code, post_rc, out = run_tests()
    finally:
        open(path, "wb").write(orig)
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith(("FAIL:", "ERROR:", "Ran ", "AssertionError")):
            print(u"  读数:", line.strip()[:240])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r587/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, "PASSED", code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
