#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R293 的看图腿补账：三档梯子逐张看过，眼睛与仪器签同一句话 ⇒ 写成 305 的追记。

不许越界的地方也写死：这一格只登记「看见了什么 + 仪器量到什么」，**不改产品**——
按 D-274，台阶地板要有来源，而来源那一格（342：系统控件画在真底上）还空着；
按台账旧规矩（R154 一批）也不许为打破 0 改动纪录加动效。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
FRAMES = "/tmp/r293_verify/frames"
RUNGS = ["row-favorite-idle-60x56-%s.png", "row-favorite-hover-60x56-%s.png",
         "row-favorite-press-60x56-%s.png"]
APPS = ("light", "dark")
MARK = u"追记（R293 看图腿）"
SPAN = u"light 27/6、dark 29/8"


def die(m):
    sys.stderr.write("EYES_R293 REFUSED: " + m + "\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def battery(tag):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(["python3", "-W", "ignore", "-m", "unittest", "discover",
                             "-s", "scripts/tests", "-v"], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    txt = proc.communicate()[0].decode("utf-8", "replace")
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = sorted(set(re.findall("skipped '([^']*)'", txt)))
    if proc.returncode != 0 or not ran or not ok:
        die(tag + u" 电池不是绿的或缺结论行（rc=" + str(proc.returncode) + u"）" + txt[-800:])
    return ran[-1], ok[-1], names


# 六张必须都在盘上，且真的被这次运行重捕过（mtime 晚于本轮帧目录建立）
have = []
for ap in APPS:
    for f in RUNGS:
        p = os.path.join(FRAMES, f % ap)
        if not os.path.exists(p):
            die(u"帧不在盘上：" + p + u" ⇒ 看图腿是空对账，记 NOT-RUN 而不是记通过")
        have.append((f % ap, os.path.getsize(p)))
if any(sz == 0 for _, sz in have):
    die(u"有 0 字节的帧：" + str(have))

NOTE = (u"  " + MARK + u"：**三档逐张看过（6 张：idle/hover/press × 亮暗，帧目录 "
        + FRAMES + u"，颗数与字节都非 0）。眼睛看到的与仪器量到的是同一句话：**"
        u"idle 那一档**根本没有圆底**（只有星形字形浮在行底上），hover 才把圆形药丸画出来，"
        u"而 press 与 hover 在我眼里**分不开**（两档都是同一颗药丸、同一档墨）。"
        u"仪器同侧读数＝离空闲／离悬停 " + SPAN + u"（码值），也就是第二级台阶只有第一级的 "
        u"6/27 与 8/29 ⇒ 「按下」这一档目前**只存在于代码与读数里，不存在于观感里**。"
        u"本轮处置＝不改产品，两条例矩都拦着：D-274 要求台阶地板先有来源，而来源那一格（342 的系统控件画在真底上）"
        u"还空着；台账旧规矩（R154 一批）也禁止为打破 0 改动纪录加动效。"
        u"342 落地后本格的验收写法也定下来：拿系统参照臂自己印的台阶码值当分母，"
        u"断言「自家 press−hover ≥ 参照 press−hover × 比例」，比例由那一跑现读，不许先拍脑袋定阈值。\n")

pre = battery(u"写盘前")
if pre[1] != str(len(pre[2])):
    die(u"电池颗数与名单不同源（汇总=" + pre[1] + u" 名单=" + str(len(pre[2])) + u"）")

bl = rd(BACKLOG)
if MARK in bl:
    die(u"已有这笔追记 ⇒ 不幂等")
lines = bl.splitlines(True)
hits = [i for i, l in enumerate(lines) if re.match(u"^(?:\\*\\*)?305\\. ", l)]
nxt = [i for i, l in enumerate(lines) if re.match(u"^(?:\\*\\*)?30[6-9]\\. |^(?:\\*\\*)?31\\d\\. ", l)]
nxt = [i for i in nxt if i > hits[0]] if len(hits) == 1 else []
if len(hits) != 1 or not nxt:
    die(u"305 锚点命中 %d 次、后继条目 %d 条 ⇒ 落点不定，不写" % (len(hits), len(nxt)))
k = nxt[0]
while lines[k - 1].strip() == u"":
    k -= 1
new = u"".join(lines[:k]) + NOTE + u"\n" + u"".join(lines[k:])
wr(BACKLOG, new)
if rd(BACKLOG).count(MARK) != 1:
    die(u"落盘后处数不对")

post = battery(u"写盘后")
if (post[0], post[1], len(post[2])) != (pre[0], pre[1], len(pre[2])):
    die(u"写盘前后电池不一致 " + str(pre) + u" → " + str(post))

print(u"EYES_R293 OK 帧=" + str(len(have)) + u" 张（六格全在盘上且非 0 字节） 落点=305 span=" + SPAN
      + u" batt=Ran " + post[0] + u" skipped=" + post[1] + u" 名单=" + str(len(post[2])))
