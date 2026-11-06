# -*- coding: utf-8 -*-
"""R589 变异表（倍率分支那一侧）M1560/M1561/M1562：三条判据各自要能被单独摘掉。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 mutate_r58*.py、判据卷与台账里各读一遍
⇒ 高水位 **M1559**（R588 收到 M1559）⇒ 本表从 **M1560** 起，没抄派单里的数。

三把各自只动一边（落刀前自问过「我只动了这一对量的一边吗」）：
- M1560 删掉 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` 那条 `elif` ⇒ 「四格各有名」那格必须红，
        而且它会**误报成 MISMATCH**（`"" != "2.00x"` 成立）⇒ 证明这一格不是"少印一行"而是"印错"。
- M1561 删掉兜底 `else`（`SCALE_MATCH`）⇒ R3 那条守卫必须红（链子失去兜底），四格那格也红；
        档位循环那一维不许跟着红 ⇒ 证明我钉的是**分支链**，不是循环。
- M1562 把 `flatten_chain` 的 elif 摊平关掉 ⇒ 真语料那格必须红（`frame_baseline.py` 从对象里消失），
        这是这把尺自己的盲区证人：0 条链不等于全仓都穷尽。

用法：python3 .scratch/motion-audit-2/mutate_r589_scale.py M1560   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r589/knife_status.txt"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

# (刀号, 说明, 目标文件, 判据卷, 起锚, 止锚 | None, 替换文本)
ARMS = [
    # 形状要紧：预检的静态抽取器认 `(编号, 说明, 文件, needle, …)` —— needle 必须在第 4 格。
    # 第一版把「判据卷名」放在第 4 格 ⇒ 抽取器去数 `scripts.tests.test_frame_baseline` 在
    # `frame_baseline.py` 里命中几次 ⇒ 三把全报 命中=0、NEEDLE_PRECHECK bad=3（刀没坏，是登记形状坏）。
    (u"M1560", u"删掉 BASELINE_UNKNOWN 那条 elif ⇒ 四格各有名那格必须红（并且会误报成 MISMATCH）",
     u"scripts/frame_baseline.py",
     u'    elif not bake["scale"]:\n', u'    elif bake["scale"] != current_scale:\n', u"",
     u"scripts.tests.test_frame_baseline"),
    (u"M1561", u"删掉兜底 else（SCALE_MATCH）⇒ R3 必须红；档位循环那一维不许跟着红",
     u"scripts/frame_baseline.py",
     u'    else:\n        # 兜底分支', u'    for name in changed:\n', u"",
     u"scripts.tests.test_tier_reporting_shape"),
    (u"M1562", u"把 elif 摊平关掉 ⇒ 真语料那格必须红（frame_baseline 从对象里消失 = 这把尺变盲）",
     u"scripts/tier_reporting_shape.py",
     u"    while cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):\n",
     None, u"    while False and cur.orelse:\n",
     u"scripts.tests.test_tier_reporting_shape"),
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
    """刀的形状：`stop` 给了就删 [起锚, 止锚) 这一整段（止锚原样留着），没给就只替换起锚那一行。

    第一版把 arms 里的 `replacement` 传成止锚那一行，于是那行被写了两遍 ⇒ M1560 变成 SyntaxError
    （读成 DID-NOT-RUN），M1561 恰好是合法的重复 `for` 才侥幸抓到红。
    刀的语义必须是"删掉这一支"，不是"把下一行抄两遍"⇒ 现在删除型 arm 的 replacement 一律是空串。
    """
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
        print(u"用法: mutate_r589_scale.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, target, start, stop, replacement, test_module = arm
    path = os.path.join(ROOT, target)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(test_module)
    print(u"%s 预检(%s): %s (rc=%d)" % (mid, test_module, code, pre_rc))
    if code != u"PASSED":
        print(out[-1500:])
        record(u"r589/%s precheck=%s test=%s 未落刀" % (mid, code, test_module))
        return 2
    new_text, err = cut(text, start, stop, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"r589/%s anchor=%s 未落刀" % (mid, err))
        return 1
    with io.open(path, u"w", encoding=u"utf-8") as handle:
        handle.write(new_text)
    try:
        code, post_rc, out = run_tests(test_module)
    finally:
        open(path, "wb").write(orig)
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith((u"FAIL:", u"ERROR:", u"Ran ", u"AssertionError")):
            print(u"  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r589/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s test=%s target=%s"
           % (mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code,
              test_module, target))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
