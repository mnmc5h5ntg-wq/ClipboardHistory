# -*- coding: utf-8 -*-
"""R590 变异表 M1567–M1571：靶 2（兜底要出声）与靶 1（扫描面要当读数）各钉一把。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r5*.py、判据卷与台账里各读一遍
⇒ 高水位 **M1566**（R589 收到 M1566）⇒ 本表从 **M1567** 起，没抄派单里的数。

五把各摘一条**独立**判据（落刀前逐把自问「我只动了这一对量的一边吗」「这一边有证人吗」）：
- M1567 把 `frame_baseline.py` 的兜底 `else` 换成 `pass` ⇒ R3 的"不出声"那一支必须红（上一版只问有没有 else，读不出来）。
- M1568 只关掉 `body_speaks` 的"退非 0"识别 ⇒ 合法拦路被误报成违规，`test_a_catch_all_that_returns_nonzero…` 必须红。
- M1569 关掉 Swift 那一块扫描面 ⇒ Swift 正对照必须红（这一维的 0 从此没有证人）。
- M1570 把剥注释顺序改回"先行后块" ⇒ R578 那一族复发，块注释之后那个正对照必须红。
- M1571 让 Swift 树缺席时不再具名 ⇒ `WITNESS_SWIFT_NOT_RUN` 那一格必须红（缺席被读成 0）。

用法：python3 .scratch/motion-audit-2/mutate_r590_scope.py M1567
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r590/knife_status.txt"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
# 刀链这一趟**不设** CLIPBOARD_HISTORY_UI_SHOTS：本轮实测两次踩到"捕获进行中就交目录出去"——
# 先是目录存在但 0 张（`REFUSED=no-png` 被断言判成红），再是 284/356 张（名册那一行还没落盘 ⇒ `名册帧缺失=1` 红）。
# 真语料那一格**不是任何一把刀的证人**（五把都判合成样本），所以最稳的做法是让刀跑在不依赖捕获的状态上；
# 真语料的读数由验证链里"帧与门在含本笔的树上现读"那一趟单独签。
ENV.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)

TIER_TEST = u"scripts.tests.test_tier_reporting_shape"
PAIR_TEST = u"scripts.tests.test_identical_frame_witness"
WIRING_TEST = u"scripts.tests.test_ci_shape_guard_wiring"

# 形状：(编号, 说明, 文件, 起锚, 止锚|None, 替换文, 判据卷)
ARMS = [
    (u"M1567", u"兜底 else 换成 pass ⇒ R3 的「不出声」那一支必须红；档位循环那一维不许跟着红",
     u"scripts/frame_baseline.py",
     u'    else:\n        # 兜底分支：两边都说得出且相等', u'    for name in changed:\n',
     u'    else:\n        pass\n', TIER_TEST),
    (u"M1568", u"关掉「退非 0 也算出声」⇒ 合法拦路被误报，负半那格必须红",
     u"scripts/tier_reporting_shape.py",
     u'    if exits:\n        return True, u"退非 0/抛"\n', None,
     u'    if exits:\n        return False, u"退非 0 被关掉（刀）"\n', TIER_TEST),
    (u"M1569", u"关掉 Swift 那块扫描面 ⇒ Swift 正对照三格必须红（这一维的 0 从此没证人）",
     u"scripts/identical_frame_witness.py",
     u"    if swift_dir and os.path.isdir(swift_dir):\n", None,
     u"    if False:\n", PAIR_TEST),
    (u"M1570", u"剥注释改回「先行后块」⇒ 块注释之后那个正对照必须红（R578 那一族复发）",
     u"scripts/identical_frame_witness.py",
     u'    src = re.sub(r"/\\*.*?\\*/", u"", src, flags=re.S)\n    src = re.sub(r"//[^\\n]*", u"", src)\n',
     None,
     u'    src = re.sub(r"//[^\\n]*", u"", src)\n    src = re.sub(r"/\\*.*?\\*/", u"", src, flags=re.S)\n',
     PAIR_TEST),
    (u"M1571", u"Swift 树缺席时不再具名 ⇒ 那一格必须红（缺席被读成 0）",
     u"scripts/identical_frame_witness.py",
     u'    if not scope[u"swift_present"]:\n', None,
     u"    if False:\n", PAIR_TEST),
    (u"M1572", u"把说明重新粘回值槽（R589 那一版）⇒ 「值槽不许多非 ASCII」那一格必须红",
     u".github/workflows/ci.yml",
     u'echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g"\n', None,
     u'echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g（0=判过 / 1=红 / 2=没有对象）"\n', WIRING_TEST),
    (u"M1573", u"负半证人把 machine 改回写死的外机 ⇒ 那一格必须红（本机行=0 就永远走不到红）",
     u"scripts/tests/test_ci_shape_guard_wiring.py",
     u'u"registered_by_round": u"R590", u"machine": machine_key()}]}, ensure_ascii=False))', None,
     u'u"registered_by_round": u"R590", u"machine": u"local:not-this-box"}]}, ensure_ascii=False))',
     WIRING_TEST),
]


def run_tests(test_module):
    proc = subprocess.run([sys.executable, u"-m", u"unittest", test_module],
                          cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=1200)
    out = proc.stdout + proc.stderr
    if u"Ran " not in out:
        return u"DID-NOT-RUN", proc.returncode, out
    return (u"PASSED" if proc.returncode == 0 else u"CAUGHT"), proc.returncode, out


def record(line):
    with io.open(STATUS, u"a", encoding=u"utf-8") as handle:
        handle.write(line + u"\n")


def cut(text, start, stop, replacement):
    """有止锚就删 [起锚, 止锚) 换成 replacement（止锚原样留着）；无止锚只换起锚那一段。"""
    if text.count(start) != 1:
        return None, u"起锚命中 %d 次" % text.count(start)
    if stop is None:
        i = text.index(start)
        return text[:i] + replacement + text[i + len(start):], u""
    if text.count(stop) != 1:
        return None, u"止锚命中 %d 次" % text.count(stop)
    i = text.index(start)
    j = text.index(stop, i)
    if j <= i:
        return None, u"止锚不在起锚之后"
    return text[:i] + replacement + text[j:], u""


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print(u"用法: mutate_r590_scope.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, target, start, stop, replacement, test_module = arm
    path = os.path.join(ROOT, target)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(test_module)
    print(u"%s 预检(%s): %s (rc=%d)" % (mid, test_module, code, pre_rc))
    if code != u"PASSED":
        print(out[-1800:])
        record(u"r590/%s precheck=%s test=%s 未落刀" % (mid, code, test_module))
        return 2
    new_text, err = cut(text, start, stop, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"r590/%s anchor=%s 未落刀" % (mid, err))
        return 1
    if target.endswith(u".py"):
        compile(new_text, target, "exec")      # 刀必须留下一份能编译的树（R590 ⑨·10 那一课）
    with io.open(path, u"w", encoding="utf-8") as handle:
        handle.write(new_text)
    try:
        code, post_rc, out = run_tests(test_module)
    finally:
        open(path, "wb").write(orig)           # "wb"：上一轮这里写成 "rb" 直接崩，变异留在盘上
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith((u"FAIL:", u"ERROR:", u"Ran ", u"AssertionError")):
            print(u"  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r590/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s test=%s target=%s"
           % (mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code, test_module, target))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
