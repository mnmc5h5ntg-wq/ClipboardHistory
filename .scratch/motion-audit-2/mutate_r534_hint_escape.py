#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R534 变异表：折叠提示的 Esc 关闭（M1410）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1410","摘掉折叠提示的 Esc 快捷键（只能鼠标关）", FILE,
   """                // R534：旧值真机折叠 420×492 下按 Esc，确认键前后都未写 ⇒ 提示只能鼠标关。
                // 一次性的提示不该把人困在鼠标上：Esc 是系统关闭语义，只在提示可见时挂。
                .keyboardShortcut(.cancelAction)""",
   """                // R534：旧值真机折叠 420×492 下按 Esc，确认键前后都未写 ⇒ 提示只能鼠标关。
                // 一次性的提示不该把人困在鼠标上：Esc 是系统关闭语义，只在提示可见时挂。"""),
]
TESTS={"M1410":"MainWindowCollapseTests/testCollapseHintCanBeDismissedWithEscape"}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read()
    code,out=run(TESTS["M1410"]); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    old,new=ARMS[0][3],ARMS[0][4]
    if orig.count(old)!=1: print("needle",orig.count(old)); return 1
    open(path,"w",encoding="utf-8").write(orig.replace(old,new))
    try: code,out=run(TESTS["M1410"])
    finally: open(path,"w",encoding="utf-8").write(orig)
    print("M1410:",code)
    clean=open(path,"rb").read()==orig.encode("utf-8")
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if code=="CAUGHT" and clean else 1
if __name__=="__main__": sys.exit(main())
