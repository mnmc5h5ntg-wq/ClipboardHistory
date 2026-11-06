# -*- coding: utf-8 -*-
"""R588 变异表（第③段断言守卫那一侧）M1557/M1558/M1559：三条各自会红的判据。

刀号来源：**落刀前现读** ⇒ 高水位 M1554（R587）+ 本会话另一张表已占 M1555/M1556 ⇒ 本表 **M1557–M1559**。
（先落哪张表不影响号段：跳表唯一由 `mutate_needle_precheck.py` 的 `ARM_TOTAL … dupes/repeats` 签。）

三把各摘掉一条**独立**判据（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1557 把段号识别退回**子串** `第③段` ⇒ 「枚举写法 `第②③段` 要认得」那格必须红（R586 靶 B 那一族：
        名字不是属性，段才是；第一版守卫就是这么漏掉 ITERATION 那一行的）。
- M1558 把反向词表换成永不匹配 ⇒ 「第③段一字未写」那格必须红（守卫若把规矩本身读成违规，
        下一轮就会去关守卫 —— 这一条是防它自己被关掉）。
- M1559 把「切不出轮次节 ⇒ 不判并点名」改回**退回全文** ⇒ 那一格必须红
        （退回全文会把历史里合法的「第③段还没开工」讨论读成无证断言，方向是多红，
          而多红的门最容易被当成"太严"关掉 ⇒ 这条形状要钉住）。

用法：python3 .scratch/motion-audit-2/mutate_r588_stage.py M1557   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r588/knife_status.txt"
TARGET = "scripts/stage_gate_claims.py"
TEST = "scripts.tests.test_stage_gate_claims"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

RX_OLD = u'STAGE3_RX = re.compile(u"第[①②③④]*③段")\n'
RX_NEW = u'STAGE3_RX = re.compile(u"第③段")  # 刀：退回子串 ⇒ 枚举写法读成无关\n'

NEG_OLD = u'NEGATED = re.compile(u"(没开工|未开工|不开工|一字未写|一字没写|一字未动|一字没动|仍未|继续不)")\n'
NEG_NEW = u'NEGATED = re.compile(u"(?!)")  # 刀：反向词永不匹配 ⇒ 规矩本身被读成违规\n'

FALL_OLD = (u"    if not secs:\n"
            u"        # 切不出轮次节 ⇒ 不判、并点名（不许退回全文去判历史）\n"
            u'        return [(u"（没切出轮次节）", u"通道缺席", text[:80])], [], [], u"未切节_不判"\n')
FALL_NEW = (u"    if not secs:\n"
            u'        secs = [(0, text)]  # 刀：退回全文 ⇒ 历史里合法的讨论会被读成无证断言\n')

ARMS = [
    ("M1557", u"段号识别退回子串 ⇒「枚举写法要认得」那格必须红；真值表其余档不动", RX_OLD, RX_NEW),
    ("M1558", u"反向词永不匹配 ⇒「第③段一字未写不许当断言」那格必须红", NEG_OLD, NEG_NEW),
    ("M1559", u"切不出节就退回全文 ⇒「不许把历史读成违规」那格必须红", FALL_OLD, FALL_NEW),
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
        print(u"用法: mutate_r588_stage.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm[:4]
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    if code != "PASSED":
        print(u"  ⚠ 预检不是 PASSED ⇒ 不落刀。本表有一格判的是**台账现状**（R587 那一节仍有冒充段号 ⇒ "
              u"最新一节红），所以这一把必须**在台账落盘之后**落，读数文件要记下两个时刻")
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
