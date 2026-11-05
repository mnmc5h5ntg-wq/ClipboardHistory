# -*- coding: utf-8 -*-
"""R586 变异表（两态差尺那一侧）M1544/M1545：档位是**段**，不是子串。

为什么这一批单独成表（与 `mutate_r586_frame.py` 开头那条同一个理由）：
`mutate_needle_precheck.py` 按**位置**认臂、一份表只有一个 `TARGET`，而这两把打的文件是
`scripts/hover_two_state_diff.py`。⇒ 改的是新代码的形状，不动老预检（R580 那一课）。

两把各摘掉本轮新落的一条判定（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1544 地板选择回到子串写法 ⇒「名字含 highlight 的暗档必须拿 FLOOR_DARK」那一格与端到端计数那一格必须红；
        `frame_tier` 的真值表那一格不动（针落在**调用处**，不在解析函数里）。
- M1545 认不出档位就默认暗档 ⇒ 只有 `HOVER_TIER_UNKNOWN` 那一格红。

两个地板数值（1.20 / 1.10）本轮一字未动 ⇒ 这两把都不许靠改数值来红（派单 靶 B 的最后一句）。

用法：python3 .scratch/motion-audit-2/mutate_r586_hover.py M1544   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r586/knife_status.txt"
TARGET = "scripts/hover_two_state_diff.py"
TEST = "scripts.tests.test_hover_two_state_diff"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

FLOOR_OLD = u"    floor = FLOOR_LIGHT if tier == 'light' else FLOOR_DARK\n"
FLOOR_NEW = (u"    floor = FLOOR_LIGHT if substring_tier(b_name) == 'light' else FLOOR_DARK"
             u"  # 刀：回到子串写法（拿 1.20 去判暗档）\n")

TIER_OLD = u"    tier = frame_tier(b_name)\n"
TIER_NEW = u"    tier = frame_tier(b_name) or 'dark'  # 刀：认不出档就默认暗档\n"

ARMS = [
    ("M1544", u"地板选择退回子串 ⇒ highlight 那张暗档拿错地板那一格 + 端到端计数那一格必须红；真值表那格不动",
     FLOOR_OLD, FLOOR_NEW),
    ("M1545", u"认不出档位默认暗档 ⇒ HOVER_TIER_UNKNOWN 那一格必须红（不许把「读不出」冒充成「知道是暗的」）",
     TIER_OLD, TIER_NEW),
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
        print(u"用法: mutate_r586_hover.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    if code != "PASSED":
        print(out[-1500:])
        record(u"r586/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r586/%s needle=%d 未落刀" % (mid, hits))
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
    record(u"r586/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, "PASSED", code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
