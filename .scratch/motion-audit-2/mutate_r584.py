# -*- coding: utf-8 -*-
"""R584 变异表 M1535/M1536/M1537：本轮落的是「登记的键是 (机器, 帧)」与「基线带署名」这两条新判定。

判据对象：`scripts.tests.test_frame_baseline`（DriftRegistryTests + MachineDimensionTests，共 35 格）。

本机现读（三份日志都在 /tmp/r584/）：
`判=判 变帧=8 本机行=8 已登记=8 未登记=0` ⇒ 退 0（local2.txt，与上一轮那一格逐字同数）
`判=不判 变帧=8 本机行=0 他机行=8 未登记（不判）=8` ⇒ 退 0（sim2.txt，换机器键那一侧）
`判=判 本机行=0 已登记=0 未登记=8` ⇒ 退 1（absent.txt，换名册路径那一侧 = 反证）

三把刀各摘掉**一条新判定**，其余一字不动（落刀前自问「我只动了这一对量的一边吗」）：
- M1535 只把 `mine/foreign` 的分机器过滤摘掉（谁登记都放行）⇒「他机行不许豁免本机漂移」那两格必须红；
        `rows_without_machine` 那一半一字未动 ⇒ 缺字段那格仍红（与 M1536 互为对照，各钉一边）。
- M1536 只把名册读取里缺 `machine` 的那一行填成通配 `*` ⇒「缺机器字段必须红并指名」那格必须红；
        判定本身（judge_drift）没动 —— 坏的是"读进来的行带不带机器"这一边。
- M1537 只把 `judged` 钉成恒真（署名不符也照判）⇒「署名不符 ⇒ 具名不判」那两格必须红；
        这一把的方向与 M1535 相反：M1535 是让名册跨机器，M1537 是让基线跨机器。

用法：python3 .scratch/motion-audit-2/mutate_r584.py M1535   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
逐把的 `rc/caught/clean/precheck/post` 写进 `/tmp/r584/knife_status.txt`：
rc 由被测那条命令直接产生（派单 ③），输出不接 head（派单 ③），每把单独起一次进程取码。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r584/knife_status.txt"
TARGET = "scripts/frame_baseline.py"
TEST = "scripts.tests.test_frame_baseline"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

# —— M1535：只动"分不分机器"这一边。
FILTER_OLD = (u'    mine = [r for r in rows if r.get("machine", "") == machine]\n'
              u'    foreign = [r for r in rows if r.get("machine", "") != machine]\n')
FILTER_NEW = u'    mine = list(rows)  # 刀：不分机器，谁登记的都放行\n    foreign = []\n'

# —— M1536：只动"缺机器字段读成什么"这一边（判定本身未动）。
FIELD_OLD = u'                    "machine": str(row.get("machine", "")),\n'
FIELD_NEW = u'                    "machine": str(row.get("machine") or "*"),  # 刀：缺字段当成通配 = 适用所有机器\n'

# —— M1537：只动"基线认不认这台机器"这一边（名册那一半未动）。
OWNER_OLD = u'    judged = (owner != "" and owner == machine)\n'
OWNER_NEW = u'    judged = True  # 刀：署名不符也照判\n'

ARMS = [
    ("M1535", u"摘掉 mine/foreign 的分机器过滤 ⇒ 他机行放行本机漂移那两格必须红（rows_without_machine 未动）",
     FILTER_OLD, FILTER_NEW),
    ("M1536", u"缺 machine 字段的行填成通配 ⇒ 「缺机器必须红并指名」那格必须红（judge_drift 未动）",
     FIELD_OLD, FIELD_NEW),
    ("M1537", u"judged 钉成恒真 ⇒ 「署名不符具名不判」那两格必须红（名册那一半未动，与 M1535 方向相反）",
     OWNER_OLD, OWNER_NEW),
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
        print(u"用法: mutate_r584.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    precheck = code
    if code != "PASSED":
        print(out[-1500:])
        record(u"r584/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r584/%s needle=%d 未落刀" % (mid, hits))
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
    # ⚠ 上一版这里写的是 `pre_rc and code`：预检通过时 pre_rc=0 ⇒ 表达式求值成 0，
    #    status 文件那一列印的是布尔而不是 PASSED（读数自伤，代价=三行作废重跑）。
    record(u"r584/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, precheck, code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
