#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R510 变异表：窄窗标题栏侧栏开关的视图树清理（M1368–M1369）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="WindowChromeLayoutTests"
ARMS=[
  ("M1368","不再清理视图树里的侧栏开关（只摘工具栏项）",
   '''            hideSidebarToggleControls(in: window)''',
   '''            // M1368：这里被删掉'''),
  ("M1369","resize 后不再补延迟清理（晚到的开关漏网）",
   '''        func windowDidResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
            scheduleSidebarCleanup(for: window)
        }''',
   '''        func windowDidResize(_ notification: Notification) {
            guard let window = notification.object as? NSWindow else { return }
            alignTrafficLights(in: window)
            removeSidebarToolbarButton(from: window)
            pinSidebarVisible(in: window)
        }'''),
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
