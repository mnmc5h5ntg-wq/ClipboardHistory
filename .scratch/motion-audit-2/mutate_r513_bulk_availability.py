#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R513 变异表：多选栏按选区禁用空操作动词（M1377–M1378）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
POLICY="Sources/ClipboardHistoryApp/Utilities/BulkActionAvailability.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1377","取消固定不再按选区禁用/调暗", VIEW,
   '''            .disabled(!availability.canUnpin)
            .opacity(availability.canUnpin ? 1 : 0.35)''',
   '''            // M1377：禁用与调暗被删掉'''),
  ("M1378","策略永远认为可以取消固定", POLICY,
   '''        canUnpin = selectedEntries.contains { $0.isPinned }''',
   '''        canUnpin = true'''),
]
TESTS={
  "M1377": "UICaptureTests/testBulkActionBarDimsTheUnpinnableVerb",
  "M1378": "BulkActionAvailabilityTests/testAvailabilityFollowsTheSelection",
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
