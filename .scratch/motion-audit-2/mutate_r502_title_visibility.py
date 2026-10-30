#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R502 变异表：主窗口标题栏标题策略（M1347–M1348）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="WindowChromeLayoutTests/testMainWindowHidesItsTitlebarTitleButKeepsTheName"
ARMS=[
  ("M1347","标题改为可见（会压到详情头部）",
   '''            window.titleVisibility = .hidden''',
   '''            window.titleVisibility = .visible'''),
  ("M1348","窗口名清空（Mission Control/读屏无据）",
   '''            window.title = "时间剪史"''',
   '''            window.title = ""'''),
  ("M1349","分隔线恢复系统默认",
   '''                window.titlebarSeparatorStyle = .none''',
   '''                window.titlebarSeparatorStyle = .line'''),
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
        if orig.count(old)!=1: print(mid,"needle",orig.count(old)); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
