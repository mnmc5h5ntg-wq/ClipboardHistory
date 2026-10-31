#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R517 变异表：批量删除先确认（M1385–M1386）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW="Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
POLICY="Sources/ClipboardHistoryApp/Utilities/BulkDeleteConfirmation.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1385","侧栏绕过确认直接删", VIEW,
   '''                let count = historyStore.selectedCount
                guard BulkDeleteConfirmation.confirm(
                    count: count,
                    using: SystemDestructiveConfirming()
                ) else { return }
                historyStore.perform(.deleteSelection)''',
   '''                historyStore.perform(.deleteSelection)'''),
  ("M1386","策略不问就返回真", POLICY,
   '''        guard count > 0 else { return false }
        return confirming.confirm(
            title: title,
            message: message(count: count),
            confirmTitle: "删除 \(count) 条",
            cancelTitle: "取消"
        )''',
   '''        return count > 0'''),
]
TESTS={
  "M1385": "BulkDeleteConfirmationTests/testTheSidebarAsksBeforeTheBulkDelete",
  "M1386": "BulkDeleteConfirmationTests/testCancelDoesNotConfirmAndNamesTheCount",
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
