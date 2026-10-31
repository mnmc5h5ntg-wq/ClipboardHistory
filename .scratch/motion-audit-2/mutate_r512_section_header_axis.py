#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R512 变异表：侧栏分组标题与行图标列同轴（M1375–M1376）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Views/SidebarSectionHeader.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="UICaptureTests/testSidebarSectionHeaderAlignsWithTheRowIconColumn"
ARMS=[
  ("M1375","分组标题退回旧缩进 22", 
   '''            .padding(.leading, 6)''',
   '''            .padding(.leading, 22)'''),
  ("M1376","分组标题对齐到行标题列（96）",
   '''            .padding(.leading, 6)''',
   '''            .padding(.leading, 82)'''),
]
def run():
    p=subprocess.run(["swift","test","--filter",TEST],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read(); code,out=run(); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,old,new in ARMS:
        n=orig.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
