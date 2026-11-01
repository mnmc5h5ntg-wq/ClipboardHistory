#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R532 变异表：折叠提示的确认持久化（M1408）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1408","确认折叠提示后不记已确认（再次折叠又出现）", FILE,
   """        hintAcknowledged = true""",
   """        hintAcknowledged = false"""),
]
TESTS={"M1408":"MainWindowCollapseTests/testCollapseHintShowsUntilAcknowledgedAndPersists"}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read()
    code,out=run(TESTS["M1408"]); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    old,new=ARMS[0][3],ARMS[0][4]
    if orig.count(old)!=1: print("needle",orig.count(old)); return 1
    open(path,"w",encoding="utf-8").write(orig.replace(old,new))
    try: code,out=run(TESTS["M1408"])
    finally: open(path,"w",encoding="utf-8").write(orig)
    print("M1408:",code)
    clean=open(path,"rb").read()==orig.encode("utf-8")
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if code=="CAUGHT" and clean else 1
if __name__=="__main__": sys.exit(main())
