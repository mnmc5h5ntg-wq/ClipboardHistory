# -*- coding: utf-8 -*-
"""R588 变异表（档位点名那一侧）M1555/M1556：两条规则各自要能被单独摘掉。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r58*.py、判据卷与四本台账里各读一遍
⇒ 高水位 **M1554**（R587 收到 M1554）⇒ 本表从 **M1555** 起，没抄派单里的数。

两把各摘掉一条**独立**的判据（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1555 把取帧循环改回「缺帧就 return」⇒ R1（循环体里不许 return）必须红；R2 那一格不动 ⇒ 缺席格还在。
- M1556 把 `FRAME_STATE_STOPS not-run=%d` 那一行的 token 去掉 ⇒ R2（缺席必须可数）必须红；
        而 R1 不动 ⇒ 「各自点名」还在。⇒ 这才证明我落的是**两条判据**，不是一条判据的两种措辞。

用法：python3 .scratch/motion-audit-2/mutate_r588_shape.py M1555   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r588/knife_status.txt"
TARGET = "scripts/frame_recording_proof.py"
TEST = "scripts.tests.test_tier_reporting_shape"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

RET_OLD = (u"            stops += 1\n"
           u"            continue\n"
           u"        pairs.append((shade, idle, recording))\n")
RET_NEW = (u"            return 1  # 刀：回到短路 return ⇒ 第二档永远不会被点名\n"
           u"        pairs.append((shade, idle, recording))\n")

COUNT_OLD = u'        print("FRAME_STATE_STOPS not-run=%d 有 %d 档的帧没到 ⇒ 这一维今天只判了 %d 档，"\n'
COUNT_NEW = u'        print("FRAME_STATE_STOPS 缺席档=%d 有 %d 档的帧没到 ⇒ 这一维今天只判了 %d 档，"\n'

ARMS = [
    ("M1555", u"取帧循环改回缺帧就 return ⇒ R1 必须红；R2 那格不动（缺席格还在）", RET_OLD, RET_NEW),
    ("M1556", u"把可数的缺席格 token 摘掉 ⇒ R2 必须红；R1 不动（各自点名还在）", COUNT_OLD, COUNT_NEW),
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
        print(u"用法: mutate_r588_shape.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm[:4]
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    if code != "PASSED":
        print(out[-1500:])
        record(u"r588/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r588/%s needle=%d 未落刀" % (mid, hits))
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
    record(u"r588/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, "PASSED", code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
