#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R524 变异表：折叠过渡动画与逐帧胶片（M1399–M1401）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
CTRL="Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
POLICY="Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  # R552 重钉三臂：折叠改成一步切换（D-552）之后，这三臂原来钉的坏法（reduce 仍走过渡 /
  # 宽度逐拍收放 / 中缝阴影）在源码里已经没有对应行了。针与描述一起挪到本轮钉的三格：
  ("M1399","reduce 路径跳过几何（与普通路径不同形）", CTRL,
   '''        switches += 1
        applyState(collapsed)''',
   '''        switches += 1
        applyState(collapsed)
        if MotionCatalog.motionShouldBeReduced { return }'''),
  ("M1400","折叠时仍按展开档算目标宽", CTRL,
   '''        let width = MainWindowCollapsePolicy.targetWidth(
            collapsed: isCollapsed,''',
   '''        let width = MainWindowCollapsePolicy.targetWidth(
            collapsed: false,'''),
  ("M1401","折叠时 detail 可见性判断反了", POLICY,
   '''    static func detailVisible(collapsed: Bool) -> Bool { !collapsed }''',
   '''    static func detailVisible(collapsed: Bool) -> Bool { collapsed }'''),
]
TESTS={
  "M1399": "MainWindowFoldMotionTests/testReduceMotionPathIsTheSameOneStep",
  "M1400": "MainWindowFoldMotionTests/testCollapseIsOneStepWithNoIntermediateState",
  "M1401": "MainWindowCollapseTests/testDetailIsNotRenderedWhenCollapsed",
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
