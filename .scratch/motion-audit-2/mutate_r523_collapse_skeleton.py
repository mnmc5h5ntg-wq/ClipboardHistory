#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R523 变异表：折叠/展开静态骨架（M1395–M1398）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
POLICY="Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
CTRL="Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1395","折叠宽沿用侧栏 268pt", POLICY,
   '''    static let collapsedWidthDefault: CGFloat = 420''',
   '''    static let collapsedWidthDefault: CGFloat = 268'''),
  ("M1396","折叠最小宽仍用展开的 600", POLICY,
   '''    static func minWidth(collapsed: Bool) -> CGFloat {
        collapsed ? collapsedMinWidth : expandedMinWidth
    }''',
   '''    static func minWidth(collapsed: Bool) -> CGFloat {
        expandedMinWidth
    }'''),
  ("M1397","切换时不记用户 resize 的宽度", CTRL,
   '''        if !isTransitioning, let target { rememberWidth(of: target) }
''',
   ''''''),
  ("M1398","reduce 下时长不归零", POLICY,
   '''        reduceMotion ? 0 : toggleDuration''',
   '''        toggleDuration'''),
]
TESTS={
  "M1395": "MainWindowCollapseTests/testCollapseUsesItsOwnWidthAndExpandRestoresResizedWidth",
  "M1396": "MainWindowCollapseTests/testCollapseUsesItsOwnWidthAndExpandRestoresResizedWidth",
  "M1397": "MainWindowCollapseTests/testUserResizeInEachStateIsRememberedForNextToggle",
  "M1398": "MainWindowCollapseTests/testReduceMotionDurationIsZero",
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
