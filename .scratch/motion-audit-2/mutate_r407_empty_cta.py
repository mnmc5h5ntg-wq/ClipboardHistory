#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R407 变异对照：QuickPick 空结果态必须有可见的「清除搜索」CTA。"""
import os, subprocess, sys, time, tempfile, shutil
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CTRL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TITLE_NEEDLE = 'let clear = NSButton(title: "清除搜索", target: self, action: #selector(clearQueryTapped(_:)))'
TITLE_MUTANT = 'let clear = NSButton(title: "", target: self, action: #selector(clearQueryTapped(_:)))'
FADE_NEEDLE = '        fadeEmptyAction(emptyAction, visible: showAction, duration: duration)'
FADE_MUTANT = '        // MUTANT: 空态 CTA 不显隐'
MUTATIONS = [
    ("M1055", "空态按钮标题不是「清除搜索」（源判据）", CTRL, TITLE_NEEDLE, TITLE_MUTANT,
     "UICaptureTests/testQuickPickEmptyStateHasAVisibleClearSearchAction",
     ["空结果态没有「清除搜索」按钮"]),
    ("M1056", "空态 CTA 不显隐（像素判据）", CTRL, FADE_NEEDLE, FADE_MUTANT,
     "UICaptureTests/testQuickPickEmptyStateCTAIsVisibleInTheFrame",
     ["空态 CTA 没有画出来"]),
]
def read(p):
    with open(p, encoding="utf-8") as h: return h.read()
def run(f):
    shots = tempfile.mkdtemp(prefix="r407-mut-shots-"); env=dict(BASE_ENV); env["CLIPBOARD_HISTORY_UI_SHOTS"]=shots
    try:
        p=subprocess.run(["swift","test","--filter",f],cwd=ROOT,capture_output=True,text=True,env=env,timeout=1800)
    finally:
        shutil.rmtree(shots,ignore_errors=True)
    out=p.stdout+p.stderr
    verdicts=[l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts: return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"),out,[]
    if "error:" in out and not any(" failed" in l for l in verdicts): return "BROKEN-MUTATION",out,[]
    failed=[l.split("]")[0].replace("Test Case '-[","") for l in verdicts if " failed" in l]
    return ("CAUGHT" if p.returncode!=0 else "ESCAPED"),out,failed
def main():
    original=read(CTRL)
    for mid,_,path,old,new,_f,_n in MUTATIONS:
        if read(path).count(old)!=1: raise SystemExit("预检中止：%s 针 %d 次"%(mid,read(path).count(old)))
        if old in new: raise SystemExit("预检中止：%s 变异文含原文"%mid)
    filters=[]
    for row in MUTATIONS:
        if row[5] not in filters: filters.append(row[5])
    for f in filters:
        code,out,_=run(f)
        if code!="ESCAPED": raise SystemExit("预检失败 %s %s\n%s"%(f,code,out[-1500:]))
    print("预检 OK "+",".join(filters))
    caught=wrong=0
    for mid,desc,path,old,new,f,needles in MUTATIONS:
        stamp=time.time()+2
        open(path,"w",encoding="utf-8").write(original.replace(old,new,1)); os.utime(path,(stamp,stamp))
        landed=old not in read(path) and new in read(path)
        try: code,out,failed=run(f)
        finally:
            open(path,"w",encoding="utf-8").write(original); os.utime(path,(stamp+1,stamp+1))
        hit=all(n in out for n in needles); right=code=="CAUGHT" and hit and landed
        caught+=1 if code=="CAUGHT" else 0; wrong+=0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              %(mid,desc,code,right,hit,
                [l for l in out.splitlines() if "QUICKPICK_EMPTY_CTA_BAND" in l][-1:] or "无",
                failed,read(path)==original))
    clean=read(CTRL)==original; reruns=[]
    for f in filters:
        c,_,_=run(f); reruns.append("%s=%s"%(f,c))
    print("还原后复跑："+" ".join(reruns))
    print("R407_EMPTY_CTA_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"%(len(MUTATIONS),caught,wrong,"yes" if clean else "NO"))
    return 0 if (caught==len(MUTATIONS) and wrong==0 and clean and all(s.endswith("=ESCAPED") for s in reruns)) else 1
if __name__=="__main__": sys.exit(main())
