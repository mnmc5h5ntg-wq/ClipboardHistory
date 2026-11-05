# -*- coding: utf-8 -*-
"""R587 变异表（两态差尺那一侧）M1550/M1551：判定不许回到子串，词表不许有第二份声明。

与 `mutate_r587_frame.py` 分成两份表的原因同 R586：`mutate_needle_precheck.py` 按位置认臂、
一份表只有一个 `TARGET`。

- M1550 让 `measure()` 改调 `substring_tier` ⇒「判定函数不许用子串法」与「子串法只有一个调用点」两格必须红；
         地板数值那一格不动（1.20 / 1.10 本轮一字未动，这把刀也不许靠改数值来红）。
- M1551 在 `hover_two_state_diff.py` 里重新声明一份 `TIERS` ⇒「词表只有一份真值」那格必须红并点名文件与行；
         按段解析的行为一字未变 ⇒ 其余格子全绿（这才叫摘掉"只有一份"这条约束）。

用法：python3 .scratch/motion-audit-2/mutate_r587_hover.py M1550   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r587/knife_status.txt"
TARGET = "scripts/hover_two_state_diff.py"
TEST = "scripts.tests.test_tier_vocabulary"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

MEASURE_OLD = u"    tier = frame_tier(b_name)\n"
MEASURE_NEW = u"    tier = substring_tier(b_name)  # 刀：判定又用回子串法\n"

IMPORT_OLD = u"from tier_vocabulary import TIERS, tier_alternation, tier_from_name  # noqa: E402\n"
IMPORT_NEW = (u"from tier_vocabulary import tier_alternation, tier_from_name  # noqa: E402\n"
              u"TIERS = ('light', 'dark')  # 刀：又声明了第二份词表\n")

ARMS = [
    ("M1550", u"measure() 改调 substring_tier ⇒「判定不许用子串法」与「子串法只有一个调用点」两格必须红；地板数值那格不动",
     MEASURE_OLD, MEASURE_NEW),
    ("M1551", u"在本文件里重新声明 TIERS ⇒「词表只有一份真值」那格必须红并点名文件与行；解析行为一字未变",
     IMPORT_OLD, IMPORT_NEW),
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
        print(u"用法: mutate_r587_hover.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm
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
