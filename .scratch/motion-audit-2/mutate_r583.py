# -*- coding: utf-8 -*-
"""R583 变异表 M1532/M1533/M1534：本轮落的是 `frame_baseline.py check` 里**新接上的三条判定**。

判据对象：`scripts.tests.test_frame_baseline.DriftRegistryTests`（10 格新案 + 旧案改写 1 格 = 该卷 22 格）。

本机现读（`/tmp/r583/gate_registered.log` 与 `/tmp/r583/gate_absent.log`）：
`FRAME_BASELINE_DRIFT 变帧=8 新帧=0 已登记=8 未登记=0 名册对不上帧名=0 名册空理由或空单号=0 陈旧行=0` ⇒ 退 0
`FRAME_BASELINE_DRIFT 变帧=8 新帧=0 已登记=0 未登记=8 …` ⇒ 退 1（名册缺席那一侧）
⇒ 洞是真的补上了：同一棵树、同一批帧，唯一变的就是名册在不在。

三把刀各摘掉**一条新判定**，其余一字不动（落刀前自问"我只动了这一对量的一边吗"）：
- M1532 只把 `blockers` 里的 `unregistered` 一项摘掉 ⇒ "变帧未登记必须红"那格必须红；
        而 missing / 名册对不上 / 缺字段 三条仍在 ⇒ 另三格仍绿（证明四条判定是四个证人，不是一条）。
- M1533 只把名册读取钉成空表 ⇒ "登记之后必须绿"那格必须红；分类器 `judge_drift` 一字未动
        （坏的是"名册到底读不读"这一边，不是判定本身）。
- M1534 只把 `unregistered` 计算里的 **added** 那一半摘掉 ⇒ "新帧未登记也必须红"那格必须红；
        changed 那一半仍在 ⇒ 变帧那格仍红（与 M1532 方向相反的那一边）。

用法：python3 .scratch/motion-audit-2/mutate_r583.py M1532   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
逐把的 `rc/caught/clean/precheck/post` 写进 `/tmp/r583/knife_status.txt`：
rc 由被测那条命令直接产生（派单 ③②），输出不接 head（派单 ③①）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r583/knife_status.txt"
TARGET = "scripts/frame_baseline.py"
TEST = "scripts.tests.test_frame_baseline"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

BLOCK_OLD = u'    blockers = len(missing) + len(verdict["unregistered"]) + len(verdict["unknown"]) + len(verdict["bad_fields"])\n'
BLOCK_NEW = u'    blockers = len(missing) + len(verdict["unknown"]) + len(verdict["bad_fields"])  # 刀：未登记不拦门\n'

READ_OLD = u'            rows = load_drift_registry(registry)\n'
READ_NEW = u'            rows = []  # 刀：名册读成空表\n'

ADD_OLD = (u'    unregistered = [n for n in changed if n not in registered_changed] + \\\n'
           u'                   [n for n in added if n not in registered_added]\n')
ADD_NEW = u'    unregistered = [n for n in changed if n not in registered_changed]  # 刀：added 那一半不判\n'

ARMS = [
    ("M1532", u"把「未登记的变帧必须红」这一项从 blockers 里摘掉 ⇒ 未登记那格红，另三条判定仍绿",
     BLOCK_OLD, BLOCK_NEW),
    ("M1533", u"把登记名册的读取钉成空表 ⇒ 「登记之后必须绿」那格红（judge_drift 一字未动）",
     READ_OLD, READ_NEW),
    ("M1534", u"把 unregistered 计算里的 added 那一半摘掉 ⇒ 「新帧未登记也必须红」那格红（changed 那一半仍在）",
     ADD_OLD, ADD_NEW),
]


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", TEST],
                          cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=900)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", proc.returncode, out
    return ("PASSED" if proc.returncode == 0 else "CAUGHT"), proc.returncode, out


def record(line):
    with io_open(STATUS, "a") as handle:
        handle.write(line + "\n")


def io_open(path, mode):
    import io
    return io.open(path, mode, encoding="utf-8")


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print(u"用法: mutate_r583.py " + u"|".join(a[0] for a in ARMS))
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
        record(u"r583/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r583/%s needle=%d 未落刀" % (mid, hits))
        return 1
    with io_open(path, "w") as handle:
        handle.write(text.replace(old, new, 1))
    try:
        code, post_rc, out = run_tests()
    finally:
        open(path, "wb").write(orig)
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith(("FAIL:", "ERROR:", "Ran ", "AssertionError")) or "FRAME_BASELINE" in line:
            print(u"  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r583/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, precheck, code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
