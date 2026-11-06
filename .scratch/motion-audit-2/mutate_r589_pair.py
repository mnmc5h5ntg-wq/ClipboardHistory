# -*- coding: utf-8 -*-
"""R589 变异表（副本名册那一侧）M1563–M1566：四条判据各自要能被单独摘掉。

刀号与上一支表同一趟现读（高水位 M1559 ⇒ 从 M1560 起），这里接 **M1563** 往后。
四把各摘一条**独立**的判据，落刀前逐把自问「我只动了这一对量的一边吗」「这一边有证人吗」：

- M1563 把「未登记」那一格算成恒空 ⇒ `新增副本必须登记` 那三格必须红（派单点名要钉的那一把）。
- M1564 把「唯一像素证人」的判法关掉 ⇒ R-c 那三格（红/绿/负半）里该红的必须红。
- M1565 把机器分家关掉（拿别台的行判这一台）⇒ `MachineTests` 两格必须红。
- M1566 让 loader 不再拒绝缺 `machine` 的行 ⇒ 形状那格必须红。

⚠ 这一表的判据卷要读**真语料**那一格 ⇒ 跑之前必须已经重捕过本轮的帧；
   没有帧时那一格自己会读 `REFUSED=no-shots`（按未读到处理），所以本表在捕获之后再落。

用法：python3 .scratch/motion-audit-2/mutate_r589_pair.py M1563
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀/没抓到/还原不干净；2=预检没过。
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATUS = "/tmp/r589/knife_status.txt"
TARGET = u"scripts/identical_frame_witness.py"
TEST = u"scripts.tests.test_identical_frame_witness"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
if os.path.isdir(u"/tmp/r589/frames"):
    ENV["CLIPBOARD_HISTORY_UI_SHOTS"] = u"/tmp/r589/frames"

ARMS = [
    (u"M1563", u'把「未登记」恒空 ⇒ "新增副本必须登记"那几格必须红',
     u'    unregistered = [g for g in copies if tuple(g[u"names"]) not in registered]\n',
     u"    unregistered = []\n"),
    (u"M1564", u"关掉 R-c 的唯一证人判法 ⇒ 恒正对照那格必须红",
     u"            if len(hit) >= 2 and hit == hit_any:\n",
     u"            if False:\n"),
    (u"M1565", u"关掉机器分家（拿别台的行判这一台）⇒ MachineTests 两格必须红",
     u'    mine = [r for r in rows if str(r.get(u"machine") or u"") == this_machine]\n',
     u"    mine = list(rows)\n"),
    (u"M1566", u"loader 不再拒绝缺 machine 的行 ⇒ 形状那格必须红",
     u'        if not str(row[u"machine"]).strip():\n',
     u"        if False:\n"),
]


def run_tests():
    proc = subprocess.run([sys.executable, u"-m", u"unittest", TEST],
                          cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=1200)
    out = proc.stdout + proc.stderr
    if u"Ran " not in out:
        return u"DID-NOT-RUN", proc.returncode, out
    return (u"PASSED" if proc.returncode == 0 else u"CAUGHT"), proc.returncode, out


def record(line):
    with io.open(STATUS, u"a", encoding=u"utf-8") as handle:
        handle.write(line + u"\n")


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print(u"用法: mutate_r589_pair.py " + u"|".join(a[0] for a in ARMS))
        return 2
    mid, why, old, new = arm
    path = os.path.join(ROOT, TARGET)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run_tests()
    print(u"%s 预检: %s (rc=%d) 帧目录=%s" % (mid, code, pre_rc, ENV.get("CLIPBOARD_HISTORY_UI_SHOTS", u"（无 ⇒ 真语料那格按未读到）")))
    if code != u"PASSED":
        print(out[-1500:])
        record(u"r589/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print(u"needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record(u"r589/%s needle=%d 未落刀" % (mid, hits))
        return 1
    with io.open(path, u"w", encoding=u"utf-8") as handle:
        handle.write(text.replace(old, new, 1))
    try:
        code, post_rc, out = run_tests()
    finally:
        open(path, "wb").write(orig)
    print(u"%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if line.startswith((u"FAIL:", u"ERROR:", u"Ran ", u"AssertionError")):
            print(u"  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print(u"RESTORE_CLEAN=" + (u"yes" if clean else u"NO"))
    record(u"r589/%s rc=%d caught=%d clean=%d precheck=PASSED post=%s"
           % (mid, post_rc, 1 if code == u"CAUGHT" else 0, 1 if clean else 0, code))
    if code != u"CAUGHT" or not clean:
        return 1
    return 0


if __name__ == u"__main__":
    sys.exit(main())
