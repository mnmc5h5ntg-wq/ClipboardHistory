# -*- coding: utf-8 -*-
"""R591 变异表 M1574–M1580：靶 1（skipped 的两种成因 + 接线顺序）与靶 2（值槽粘连的划界）各钉一把。

刀号来源：**落刀前现读** —— `grep -rhoE 'M1[0-9]{3}'` 在 .scratch、scripts、七本台账里各读一遍
⇒ 高水位 **M1573**（R590 那一表的末把），本轮从 **M1574** 起，没抄派单里的数。
跨表唯一性：M1574–M1580 在其它任何表/台账里现读 0 次（落刀前逐把核过）。

七把各摘一条**独立**判据（落刀前逐把自问「我只动了这一对量的一边吗」「这一边有证人吗」）：
- M1574 把 STEP[11] 的 `if: always()` 撤掉 ⇒ static 那一支必须现读到"无声的证据步骤"并红。
- M1575 让 `prints_channels` 永远返回空 ⇒ 证据型步骤=0，那一格必须红（**尺瞎了要响**，M1572 第一版的教训不重踏）。
- M1576 让"空豁免"检查失效 ⇒ `test_dead_exemption_is_red` 必须红。
- M1577 让 run 模式接受**没点名这一步**的具名 ⇒ 那一格必须红（否则一句带 ③甲 的话就能放行全部 skipped）。
- M1578 把已修的两条 echo 之一**粘回去** ⇒ 接线那一格必须红（派单点名的那把）。
- M1579 让工作流那一侧的粘连扫描失效 ⇒ `test_glue_red_scope_is_the_workflow_echoes` 必须红。
- M1580 让分类退化成都算"读数括号" ⇒ 说明那一半不再拦路 ⇒ 同一格必须红（**划界本身要有牙**）。

用法：python3 .scratch/motion-audit-2/mutate_r591_wiring.py M1574
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r591/knife_status.txt"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
# 刀链这一趟**不设** CLIPBOARD_HISTORY_UI_SHOTS（R590 ⑨·5 那一课：捕获进行中交出去会把合成卷判成红）。
ENV.pop(u"CLIPBOARD_HISTORY_UI_SHOTS", None)

SKIP_TEST = u"scripts.tests.test_ci_skipped_causes"
HYG_TEST = u"scripts.tests.test_ci_channel_hygiene"
WIR_TEST = u"scripts.tests.test_ci_shape_guard_wiring"

# 形状：(编号, 说明, 文件, 起锚, 止锚|None, 替换文, 判据卷)
ARMS = [
    (u"M1574", u"撤掉 STEP[11] 的 if: always() ⇒ 那一步重新变成「上游一红就一行都不印」，static 那一支必须红",
     u".github/workflows/ci.yml",
     u'      - name: "Frame baseline vs working manifest (fixture-set gate)"\n'
     u'        if: always()   # R591 靶 1：证据/报告型步骤必须有机会出声；被上游红连带跳过时它连一行读数都不印\n',
     None,
     u'      - name: "Frame baseline vs working manifest (fixture-set gate)"\n', SKIP_TEST),
    (u"M1575", u"让 prints_channels 永远看不见通道串 ⇒ 证据型步骤=0 ⇒ 「尺有对象」那一格必须红",
     u"scripts/ci_skipped_causes.py",
     u"        if CHANNEL_RE.search(s):\n", None,
     u"        if False:\n", SKIP_TEST),
    (u"M1576", u"让空豁免检查失效 ⇒ 名册里对不上步骤/已带 always() 的行不再被点名 ⇒ 那一格必须红",
     u"scripts/ci_skipped_causes.py",
     u"        if nm not in ev_names:\n", None,
     u"        if False:\n", SKIP_TEST),
    (u"M1577", u"run 模式接受没点名这一步的具名 ⇒ 「一句 ③甲 放行全部 skipped」那一格必须红",
     u"scripts/ci_skipped_causes.py",
     u'                if (CAUSE_JIA in line or CAUSE_YI in line) and (\n'
     u'                        pat in line or r["name"][:24] in line):\n', None,
     u'                if CAUSE_JIA in line or CAUSE_YI in line:\n', SKIP_TEST),
    (u"M1578", u"把已修的那条 echo 粘回去（R589 那一版）⇒ 接线那一格必须红（派单点名的那把）",
     u".github/workflows/ci.yml",
     u'            echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g"\n'
     u'            echo "  这一格的读法：rc=0 判过 / rc=1 红 / rc=2 扫描器没有对象，不许当绿"\n',
     None,
     u'            echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g（0=判过 / 1=红 / 2=扫描器没有对象）"\n',
     WIR_TEST),
    (u"M1579", u"让工作流那一侧的粘连扫描失效 ⇒ 「要拦的那一半有牙」那一格必须红",
     u"scripts/ci_channel_hygiene.py",
     u"        for m in GLUE_RE.finditer(s):\n", None,
     u"        for m in []:\n", HYG_TEST),
    (u"M1580", u"分类退化成都算读数括号 ⇒ 说明那一半不再拦路 ⇒ 同一格必须红（划界本身要有牙）",
     u"scripts/ci_channel_hygiene.py",
     u"    return u'说明'\n", None,
     u"    return u'读数'\n", HYG_TEST),
    (u"M1581", u"撤掉那对 set +o pipefail 括号 ⇒ 工具返回 2 时整步被 bash -e 打死 ⇒ 缺席那一格必须红"
               u"（R591 ⓪ 在 42167592176 上实测到的真缺陷：runner 就是这样 exit code 2 的）",
     u".github/workflows/ci.yml",
     u'          set +o pipefail\n'
     u'          "$PY" scripts/identical_frame_witness.py --shots /tmp/shots-ci 2>&1 | tee /tmp/identical.log\n',
     None,
     u'          "$PY" scripts/identical_frame_witness.py --shots /tmp/shots-ci 2>&1 | tee /tmp/identical.log\n',
     WIR_TEST),
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
        print(u"用法: mutate_r591_wiring.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, target, start, stop, replacement, test_module = arm
    path = os.path.join(ROOT, target)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests(test_module)
    print(u"%s 预检(%s): %s (rc=%d)" % (mid, test_module, code, pre_rc))
    if code != u"PASSED":
        print(out[-1800:])
        record(u"r591/%s precheck=%s test=%s 未落刀" % (mid, code, test_module))
        return 2
    new_text, err = cut(text, start, stop, replacement)
    if new_text is None:
        print(u"锚点不合格：%s ⇒ 不下刀" % err)
        record(u"r591/%s anchor=%s 未落刀" % (mid, err))
        return 1
    if target.endswith(u".py"):
        compile(new_text, target, "exec")     # 刀必须留下一份能编译的树（R590 ⑨·10 那一课）
    with io.open(path, u"w", encoding="utf-8") as handle:
        handle.write(new_text)
    try:
        code, post_rc, out = run_tests(test_module)
    finally:
        open(path, "wb").write(orig)          # "wb"：R589 那里写成 "rb" 直接崩，变异留在盘上
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith((u"FAIL:", u"ERROR:", u"Ran ", u"AssertionError")):
            print(u"  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r591/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s test=%s target=%s"
           % (mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code, test_module, target))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
