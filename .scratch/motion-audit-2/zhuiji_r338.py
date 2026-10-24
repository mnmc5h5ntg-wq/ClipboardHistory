#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R338 push 之后的两件事，一笔做完。

① **追记 run↔commit**：把 push 之后才存在的两跑成对写回 STATE 的 R339 第 ⓪ 条
   （现读自 `scripts/ci_read.py latest`；回填时 in_progress ⇒ 只登记不轮询，R140 的规矩）。
② **修一处自相矛盾**：STATE 的 ⓪b 写着「本轮新基线（`CHANGED=0` 那四张）」——
   0 与"四张"放在同一句里就是假话。成因：生成器里那段话有**两份**（NOT-RUN ② 那份已经换成
   逐张比的读数，⓪ 那份是早期草稿留下的）。现读应为"与上一轮逐张比 = 变了 4 张"
   （`frame_diff_two_dirs.py` → /tmp/r338_framesdiff.log），基线**更新之后**再对才是 0。
   两处一起改：STATE 与生成器（让下一轮重跑生成器不会再写出那句话）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
STA = os.path.join(ROOT, u"AGENT_STATE.md")
GEN = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledgers_r338.py")
FD_LOG = u"/tmp/r338_framesdiff.log"
RUN_LOG = u"/tmp/r338_run.log"
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def once(t, old, new, tag):
    n = t.count(old)
    if n != 1:
        sys.stderr.write(u"R338_ZHUIJI_DIED 锚点命中 %d 次：%s\n" % (n, tag))
        for p in WRITTEN:
            sys.stderr.write(u"  已写盘：" + p + u"\n")
        sys.exit(1)
    return t.replace(old, new)


fd = rd(FD_LOG)
m = re.search(u"FRAME_DIFF 比了=(\\d+) 变了=(\\d+)", fd)
if not m:
    sys.stderr.write(u"R338_ZHUIJI_DIED 逐张比那行解析不到：" + fd[:200] + u"\n")
    sys.exit(1)
COMPARED, CHANGED = m.group(1), m.group(2)

# ① 现读两跑（in_progress 也照实登记）
env = dict(os.environ)
env[u"PYTHONUTF8"] = u"1"
tip = subprocess.run([sys.executable, u"scripts/ci_read.py", u"latest"], cwd=ROOT, env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")
tm = re.search(u"RUN=(\\d+) sha=(\\w+) status=(\\w+) conclusion=(\\w*)", tip)
if not tm:
    sys.stderr.write(u"R338_ZHUIJI_DIED ci_read latest 没给可解析的行：" + tip[-200:] + u"\n")
    sys.exit(1)
RUN, SHA, STATUS, CONC = tm.groups()
if SHA != u"526e8d7":
    sys.stderr.write(u"R338_ZHUIJI_DIED tip 那一跑不是本轮的账半（sha=%s）⇒ 不登记\n" % SHA)
    sys.exit(1)
wr(RUN_LOG, tip)

BAD = u"⓪b 本轮新基线（`CHANGED=0` 那四张）在 runner 上是不是 changed"
GOOD = (u"⓪b 本轮随基线更新的那几张（与上一轮逐张比：比了 %s 张、变了 %s 张，全是 HTML 两档 × 渲染/原文）"
        u"在 runner 上会不会被判成 changed —— 基线**更新之后**再对才是 CHANGED=0，两个数不是一件事"
        % (COMPARED, CHANGED))

sta = rd(STA)
if BAD in sta:
    sta = once(sta, BAD, GOOD, u"STATE ⓪b 自相矛盾")
    wr(STA, sta)
else:
    print(u"SKIP（已改过）STATE ⓪b")

BAD_GEN = (u"⓪b 本轮新基线（`CHANGED=%s` 那四张）在 runner 上是不是 changed")
gen = rd(GEN)
if BAD_GEN in gen:
    gen = once(gen, BAD_GEN, GOOD.replace(u"%s", u"%s") , u"生成器 ⓪b 同一句")
    wr(GEN, gen)
else:
    print(u"SKIP（已改过）生成器 ⓪b")

# ② 追记那一行（挂在 R338 节的 ⓪ 段开头）
sta = rd(STA)
ANCHOR = (u"下一轮（R339）的靶：⓪ 读 CI 配对（成对：run id ↔ commit，现读自 `scripts/ci_read.py latest`）——\n")
NEW = ANCHOR + (u"**R338 追记现读**：RUN=%s ↔ %s（账半，回填时 status=%s%s ⇒ 只登记不轮询，R140）；"
                u"代码半 d8e6486 的 run id 现读未取（`ci_read latest` 只给 tip 那一跑）。\n"
                % (RUN, SHA, STATUS, u" / conclusion 空" if not CONC else u" / conclusion=" + CONC))
if u"**R338 追记现读**" not in sta:
    sta = once(sta, ANCHOR, NEW, u"STATE 追记行")
    wr(STA, sta)
else:
    print(u"SKIP（已改过）STATE 追记行")

out = subprocess.run([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests"],
                     cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
tail = out.stdout.decode(u"utf-8", u"replace").strip().splitlines()[-3:]
if out.returncode != 0:
    sys.stderr.write(u"R338_ZHUIJI_DIED 电池红了：\n" + u"\n".join(tail) + u"\n")
    sys.exit(1)
print(u"R338_ZHUIJI_OK RUN=%s sha=%s status=%s 逐张比=%s/%s 电池=%s"
      % (RUN, SHA, STATUS, COMPARED, CHANGED, [t for t in tail if t.startswith(u"Ran")][0]))
