# -*- coding: utf-8 -*-
"""R587 变异表（帧基线那一侧）M1547/M1548/M1549(空刀作废)/M1552/M1553：倍率报的是分布，不是一个猜。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r58*.py、判据卷与四本台账里各读一遍
⇒ 高水位 M1546 ⇒ 本轮从 **M1547** 起（没抄派单里的数）。

五把各摘掉本轮新落的一条判定（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1547 摘掉并列检测 ⇒ 「并列不许印一个确定倍率」那两格必须红；混批（3:1）那一格不动 ⇒ 它证明众数本身没坏。
- M1548 让没有尺寸段的帧静默跳过 ⇒ `sizeless` 那一格必须红（这一格是被测试自己挖出来的坏法）。
- M1549 让 `bad` 不再累加 ⇒ `bad` 那一格必须红；`sizeless` 那格不动。**实测 PASSED＝空刀**
  （那一支 `bad += 1` 当时没有任何测试覆盖 ⇒ 结论作废、号不复用，补上证人后用新号 M1553 在同一处再落）。
- M1552 把 print 里那个旗标少写一个字母 ⇒ 「印出来的**成句命令**必须能解析」那格必须红
        （R586 ⑨·7 那一族的仪器化证人：不是又记一笔，是让它必须红）。
        ⚠ 这一把的证人**本轮搬过家**：顺账那一笔把这条守卫从 `test_frame_baseline` 升级成扫 scripts/
        每一支，新家在 `test_tier_vocabulary.PrintedCommandParsesTests` ⇒ 臂上带第 5 位指明模块，
        否则它跑的是已经不认这件事的旧尺（那是空刀的又一种成因：刀没错，证人换了门牌）。
- M1553 与 M1549 同一处、证人已在 ⇒ 「不可读 PNG 不再进 bad」那一格必须红。

用法：python3 .scratch/motion-audit-2/mutate_r587_frame.py M1547   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r587/knife_status.txt"
TARGET = "scripts/frame_baseline.py"
TEST = "scripts.tests.test_frame_baseline"
# M1552 的证人本轮搬到这一支（顺账那条守卫现在扫 scripts/ 每一支，住在 test_tier_vocabulary 里）。
TEST_TIER = "scripts.tests.test_tier_vocabulary"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

TIE_OLD = u"    if len(tied) > 1:\n"
TIE_NEW = u"    if False and len(tied) > 1:  # 刀：并列不再检测 ⇒ 抛硬币的倍率又回来了\n"

SIZELESS_OLD = u"            sizeless += 1\n"
SIZELESS_NEW = u"            pass  # 刀：无尺寸段的那张静默跳过，不计数\n"

BAD_OLD = (u"        if px <= 0 or lx <= 0 or ly <= 0:\n"
           u"            unreadable += 1\n"
           u"            bad += 1\n")
BAD_NEW = (u"        if px <= 0 or lx <= 0 or ly <= 0:\n"
           u"            unreadable += 1\n")

FLAG_OLD = u"              u\"`python3 scripts/frame_baseline.py update <那一台的帧目录> --for-machine`，\"\n"
FLAG_NEW = u"              u\"`python3 scripts/frame_baseline.py update <那一台的帧目录> --for-machin`，\"  # 刀：少一个字母\n"

ARMS = [
    ("M1547", u"摘掉并列检测 ⇒「并列不许印确定倍率」两格必须红；混批 3:1 那一格不动（证明众数本身没坏）",
     TIE_OLD, TIE_NEW),
    ("M1548", u"无尺寸段的帧静默跳过 ⇒ sizeless 那一格必须红（这一格是测试自己挖出来的坏法）",
     SIZELESS_OLD, SIZELESS_NEW),
    ("M1549", u"bad 不再累加 ⇒ bad 那一格必须红；sizeless 那格不动",
     BAD_OLD, BAD_NEW),
    ("M1552", u"print 里的旗标少写一个字母 ⇒「印出来的成句命令必须能解析」那格必须红（R586 ⑨·7 的仪器化证人）",
     FLAG_OLD, FLAG_NEW, TEST_TIER),
    # M1549 第一次落下来是 PASSED（空刀）：那一条 `bad += 1` 当时没有任何测试覆盖 ⇒ 结论作废、号留着记录。
    # 补上证人（`test_unreadable_png_is_counted_as_bad_not_dropped`）之后**同一处**重新落一刀，用新号 M1553：
    # "号不复用"比"看起来更整齐"重要（R491/R560/R567/R577 那四种空刀都记在同一族里）。
    ("M1553", u"同一处再落一次（证人已在）：不可读 PNG 不再进 bad ⇒ 那一格必须红；sizeless 那格不动",
     BAD_OLD, BAD_NEW),
]


def run_tests(test=TEST):
    proc = subprocess.run([sys.executable, "-m", "unittest", test],
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
        print(u"用法: mutate_r587_frame.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm[:4]
    # 第 5 位＝这臂的**证人住在哪个模块**。顺账那一笔把「印出来的命令必须能解析」从
    # `test_frame_baseline` 挪进了 `test_tier_vocabulary`（它现在扫的是 scripts/ 每一支），
    # 于是 M1552 若还按默认模块跑，抓的就是一把已经不在场的旧尺 ⇒ 空刀形状第三种：证人搬了家。
    test = arm[4] if len(arm) > 4 else TEST
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(test)
    print(u"%s 预检: %s (rc=%d) 证人模块=%s" % (mid, code, pre_rc, test.split(".")[-1]))
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
        code, post_rc, out = run_tests(test)
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
