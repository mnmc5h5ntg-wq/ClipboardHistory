#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R514 变异表：破坏性动词实心核心 + 614 工具栏回加拦截（M1379–M1380）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
CHROME="Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1379","删除动词退回 1px 轮廓", VIEW,
   '''                Image(systemName: "trash.fill")''',
   '''                Image(systemName: "trash")'''),
  ("M1380","工具栏回加拦截认错对象", CHROME,
   '''                  toolbar === window.toolbar,''',
   '''                  toolbar !== window.toolbar,'''),
]
TESTS={
  "M1379": "UICaptureTests/testDestructiveBulkVerbKeepsAFilledCore",
  "M1380": "WindowToolbarSidebarClassificationTests/testToolbarAddObserverRemovesTheSidebarToggleAndKeepsOrdinaryItems",
}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    paths=sorted({os.path.join(ROOT,a[2]) for a in ARMS})
    orig={p:open(p,encoding="utf-8").read() for p in paths}
    for mid,desc,rel,old,new in ARMS:
        code,out=run(TESTS[mid]); print("预检 %s: %s"%(mid,code))
        if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,rel,old,new in ARMS:
        path=os.path.join(ROOT,rel); cur=orig[path]
        n=cur.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(cur.replace(old,new))
        try: code,out=run(TESTS[mid])
        finally: open(path,"w",encoding="utf-8").write(orig[path])
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=all(open(p,"rb").read()==orig[p].encode("utf-8") for p in paths)
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
