#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); S=os.path.join(R,"AGENT_STATE.md")
a=rd(A); st=rd(S)
a_old=u"没有放宽 light 档等式，也没有把整列材质带当文字带。修复笔 `e3eb62b`。"
a_new=u"没有放宽 light 档等式，也没有把整列材质带当文字带。修复笔 `e3eb62b`。**同一形状的既有出口**：`41095547380 ↔ e46c29f` 同跑里 R429 的版本行判据早就有 `SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry dark 720带=10/1 负末带=271.0..539.0` ⇒ 暗档整列同极性是这台 runner 的已知通道形状，不是本轮新发现的产品缺陷。"
st_old=u"修复笔 `e3eb62b` 已推（ahead=0）。下一轮编号 R506"
st_new=u"修复笔 `e3eb62b` 已推（ahead=0）。成对回读（R504 三跑已补读）：`41093593814 ↔ 800a45a` failure **4 步** = Release（3 条：sources 格停旧 + skip roster 内层级联 + sources 第二来源）、Swift（1318/81/1 = 身份头判据；同跑另有 Motion 采样红）、Capture（同一命名红）、Motion floor（`testCopyReceipt…` 1<2）；`41095129735 ↔ 79336c7` failure Swift + Capture（同一身份头判据；日志流两次 `CANCEL` ⇒ `CI_LOG_BLOCKED=stream-error`，正文未读）；`41095547380 ↔ e46c29f` failure Swift + Capture（同一红）、同跑 Motion floor **clean**（`judged=4/5 executed=77`、`MOTION_FLOOR_SUITE_CLEAN=0`）、`PROBE_COVERAGE 红=0`。四跑未完成 ⇒ NOT-RUN：`41102621877 ↔ f7ea8b4`、`41102893802 ↔ b94dd83`、`41105579968 ↔ e3eb62b`、`41105861197 ↔ 6543959`（均 in_progress）。下一轮编号 R506"
if a.count(a_old)!=1: raise SystemExit("A anchor %d" % a.count(a_old))
if st.count(st_old)!=1: raise SystemExit("S anchor %d" % st.count(st_old))
wr(A, a.replace(a_old,a_new,1)); wr(S, st.replace(st_old,st_new,1))
print("OK")
