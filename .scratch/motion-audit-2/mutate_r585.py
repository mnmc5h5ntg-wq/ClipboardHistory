# -*- coding: utf-8 -*-
"""R585 变异表 M1538/M1539/M1540：本轮落的是「印给读者的出路必须真做得到」这一族三条新判定。

判据对象：`scripts.tests.test_frame_baseline`（DriftRegistryTests + MachineDimensionTests +
RemedyDriveTests，共 45 格；本轮新增 10 格）。

本机现读（都在 /tmp/r585/）：
`register-drift --restamp` ⇒ `FRAME_BASELINE_RESTAMP=8 机器=local:MacBook-Air.local 基线出处=c16144dfd33b` ⇒ 门
`判=判 … 名册无出处=0 出处对不上=0 已登记=8 未登记=0` ⇒ 退 0（after_restamp3.txt）
补出处**之前**同一棵树是 `名册无出处=8 拦路=8` ⇒ 退 1（before_restamp.txt）⇒ 这一对就是"补的是判定不是措辞"。

三把刀各摘掉**一条新判定**，其余一字不动（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1538 只让 `update` 忽略 `--for-machine` ⇒ 「照 stdout 印的那条命令原样跑一遍 ⇒ 判=判」那格必须红；
        名册那一侧（register-drift / 出处）一字未动 ⇒ 另两格仍绿。
- M1539 只把 `verify_provenance` 的调用换成空表 ⇒ 「手抄一行必须红并点名」「出处对不上必须红」两格必须红；
        写路径本身（register-drift 落 observed）未动 —— 坏的是"读的时候查不查"这一边。
- M1540 只让 note 的**原文保留**失效 ⇒ 「restamp 不许冲掉人写的句子」那格必须红；行内容与出处一字未动。
        这一把钉的是本轮真实犯过的那一处（第一次 --restamp 冲掉了 R583 那句）。

用法：python3 .scratch/motion-audit-2/mutate_r585.py M1538   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
逐把的 `rc/caught/clean/precheck/post` 写进 /tmp/r585/knife_status.txt：rc 由被测那条命令直接产生，
输出不接 head（派单 ③①②），刀链跑着的时候不改任何仪器（派单 ③）。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r585/knife_status.txt"
TARGET = "scripts/frame_baseline.py"
TEST = "scripts.tests.test_frame_baseline"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

FLAG_OLD = u'        if args.for_machine:\n'
FLAG_NEW = u'        if False and args.for_machine:  # 刀：旗标被忽略 ⇒ 印出来的出路做不到\n'

VERIFY_OLD = (u'    provenance = verify_provenance(rows or [], machine, current, digest,\n'
              u'                                   drifting=list(changed) + list(added))\n')
VERIFY_NEW = u'    provenance = {"no_proof": [], "mismatch": []}  # 刀：证伪那一支不查了\n'

NOTE_OLD = u'            if kept:\n                note = kept\n'
NOTE_NEW = u'            if False:\n                note = kept  # 刀：人写的原文又被生成器覆盖\n'

ARMS = [
    ("M1538", u"update 忽略 --for-machine ⇒「照印出来的命令跑一遍就判」那格必须红（名册那一侧未动）",
     FLAG_OLD, FLAG_NEW),
    ("M1539", u"摘掉 verify_provenance 的调用 ⇒ 手抄行/过期行两格必须红（写路径未动）",
     VERIFY_OLD, VERIFY_NEW),
    ("M1540", u"让 note 的原文保留失效 ⇒ restamp 不许冲掉人写句子那格必须红（行与出处未动）",
     NOTE_OLD, NOTE_NEW),
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
        print(u"用法: mutate_r585.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    precheck = code
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    if code != "PASSED":
        print(out[-1500:])
        record(u"r585/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r585/%s needle=%d 未落刀" % (mid, hits))
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
            print(u"  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r585/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, precheck, code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
