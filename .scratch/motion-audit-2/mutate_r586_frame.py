# -*- coding: utf-8 -*-
"""R586 变异表（帧基线那一侧）M1541/M1542/M1543/M1546：基线要能说出自己是**哪一笔、按什么倍率**烤的。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r58*.py 与四本台账里各读一遍
⇒ 高水位 M1540 ⇒ 本轮从 M1541 起（没抄派单里的数）。

拆成两份文件的原因（R580 那条"新代码撞老刀 needle 时改新代码、不动老表"的同类）：
`mutate_needle_precheck.py` 按**位置**认臂（`(臂号, 说法, needle, 变异文)`），一份表只能有一个 `TARGET`；
本轮两把刀打在另一份文件（`hover_two_state_diff.py`）上 ⇒ 那两把放在 `mutate_r586_hover.py`。

三把各摘掉本轮新落的一条判定（落刀前各自自问「我只动了这一对量的一边吗」）：
- M1541 基线文档不落 `baked_from_commit` ⇒ 落笔那一格 + 依赖同批的两格必须红；名册/机器键一字未动。
- M1542 只把 `same_bake` 钉成恒 False ⇒ 只有"同批必须红"与"同批不许吃掉未登记那朵"两格红，
        落笔那一格与旧文档那两格都不动 ⇒ 这才叫"摘掉这一支判定"，不是顺手改了别的。
- M1543 缺出处就默认成此刻这一笔 ⇒ 两格旧文档证人必须红（把"不知道"冒充成"知道"），
        同批那两格仍按真出处走 ⇒ 不动。

用法：python3 .scratch/motion-audit-2/mutate_r586_frame.py M1541   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r586/knife_status.txt"
TARGET = "scripts/frame_baseline.py"
TEST = "scripts.tests.test_frame_baseline"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

DROP_OLD = u'        "baked_from_commit": bake["commit"],\n'
DROP_NEW = u'        "baked_from_commit": "",  # 刀：出处不落盘，基线又答不了自己是哪一笔烤的\n'

SAMEB_OLD = u'    same_bake = bool(bake["commit"]) and bake["commit"] == head\n'
SAMEB_NEW = u'    same_bake = False  # 刀：同批这一支不再判\n'

DEFAULT_OLD = u'    same_bake = bool(bake["commit"]) and bake["commit"] == head\n'
DEFAULT_NEW = (u'    bake["commit"] = bake["commit"] or head  # 刀：缺出处就默认成此刻这一笔\n'
               u'    same_bake = bool(bake["commit"]) and bake["commit"] == head\n')

FLAG_OLD = u'或改判逐版本基线 `--against latest-release`；'
FLAG_NEW = u'或改判逐版本基线 `--against release`；  # 刀：印出去的旗标值 argparse 不认（同一行内，不许插换行）'

ARMS = [
    ("M1546", u"出路里那个旗标值退回 argparse 不认的写法 ⇒ 「印出来的每个 --against 值都在 choices 里」那格必须红（R585 空头支票同族，本轮我自己又犯一次）",
     FLAG_OLD, FLAG_NEW),
    ("M1541", u"基线文档不落 baked_from_commit ⇒ 落笔那一格与「同批」那两格必须红（名册/机器键一字未动）",
     DROP_OLD, DROP_NEW),
    ("M1542", u"摘掉 same_bake 判定 ⇒「同批必须红」「同批不许吃掉未登记那朵」两格红，落笔与旧文档那两格不动",
     SAMEB_OLD, SAMEB_NEW),
    ("M1543", u"缺出处被当成「这一笔烤的」 ⇒ 两格旧文档证人必须红（把「不知道」冒充成「知道」）",
     DEFAULT_OLD, DEFAULT_NEW),
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
        print(u"用法: mutate_r586_frame.py " + u"|".join(a[0] for a in ARMS))
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
