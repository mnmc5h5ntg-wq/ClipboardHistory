#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R408 变异对照：拖放目标必须写出“松手加入剪贴板历史”。"""
import os, subprocess, sys, time, tempfile, shutil
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SIDE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEXT_NEEDLE = 'Text("松手加入剪贴板历史")'
TEXT_MUTANT = 'Text("松手")'
SEAM_NEEDLE = 'private var isDropTargetedForDrawing: Bool { isDropTargeted || (dropTargetedForCapture ?? false) }'
SEAM_MUTANT = 'private var isDropTargetedForDrawing: Bool { isDropTargeted }'
MUTATIONS = [
    ("M1057", "拖放提示文案被缩短（源判据）", SIDE, TEXT_NEEDLE, TEXT_MUTANT,
     "UICaptureTests/testDropTargetHintIsWiredIntoTheSidebarView",
     ["没有说清松手会发生什么"]),
    ("M1058", "取证键不参与拖放绘制（像素判据）", SIDE, SEAM_NEEDLE, SEAM_MUTANT,
     "UICaptureTests/testDropTargetHintIsVisibleAndOnlyInTheTargetedFrame",
     ["没画出来"]),
]
def read(p):
    with open(p, encoding="utf-8") as h: return h.read()
def run(f):
    shots = tempfile.mkdtemp(prefix="r408-mut-shots-"); env=dict(BASE_ENV); env["CLIPBOARD_HISTORY_UI_SHOTS"]=shots
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
    original=read(SIDE)
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
                [l for l in out.splitlines() if "DROP_TARGET_HINT_BAND" in l][-1:] or "无",
                failed,read(path)==original))
    clean=read(SIDE)==original; reruns=[]
    for f in filters:
        c,_,_=run(f); reruns.append("%s=%s"%(f,c))
    print("还原后复跑："+" ".join(reruns))
    print("R408_DROP_HINT_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"%(len(MUTATIONS),caught,wrong,"yes" if clean else "NO"))
    return 0 if (caught==len(MUTATIONS) and wrong==0 and clean and all(s.endswith("=ESCAPED") for s in reruns)) else 1
if __name__=="__main__": sys.exit(main())
