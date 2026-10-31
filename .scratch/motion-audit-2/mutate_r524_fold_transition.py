#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R524 变异表：折叠过渡动画与逐帧胶片（M1399–M1401）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
CTRL="Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
POLICY="Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1399","reduce-motion 仍走过渡", CTRL,
   '''        let duration = MainWindowCollapsePolicy.animationDuration(
            reduceMotion: MotionCatalog.motionShouldBeReduced
        )''',
   '''        let duration = MainWindowCollapsePolicy.animationDuration(
            reduceMotion: false
        )'''),
  ("M1400","宽度一帧跳到终点（没有收放过程）", CTRL,
   '''        let width = transitionFromWidth
            + (transitionToWidth - transitionFromWidth) * CGFloat(eased)''',
   '''        let width = transitionToWidth'''),
  ("M1401","中缝阴影永不出现", POLICY,
   '''    static func hingeOpacity(foldProgress: Double) -> Double {
        4 * min(max(foldProgress, 0), 1) * (1 - min(max(foldProgress, 0), 1))
    }''',
   '''    static func hingeOpacity(foldProgress: Double) -> Double {
        0
    }'''),
]
TESTS={
  "M1399": "MainWindowFoldMotionTests/testReduceMotionCutsInstantly",
  "M1400": "MainWindowFoldMotionTests/testCollapseWidthIsMeasuredFrameByFrame",
  "M1401": "MainWindowFoldMotionTests/testFoldProgressDrivesContentOpacityAndHinge",
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
