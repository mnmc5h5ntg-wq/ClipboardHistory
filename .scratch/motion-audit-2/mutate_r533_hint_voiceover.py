#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R533 变异表：折叠提示的无障碍合并（M1409）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
ARMS=[
  ("M1409","把「知道了」重新合并进一个无障碍元素", FILE,
   """        // R533：不要把「知道了」合并进一个无障碍元素 —— `.combine` 会把按钮动作并掉，
        // VoiceOver 只剩一段文字、按不到确认；文字与按钮各自成元素（信息图标是装饰，已隐藏）。
        .transition(MotionCatalog.transition(for: .contentFade))""",
   """        // R533：不要把「知道了」合并进一个无障碍元素 —— `.combine` 会把按钮动作并掉，
        // VoiceOver 只剩一段文字、按不到确认；文字与按钮各自成元素（信息图标是装饰，已隐藏）。
        .transition(MotionCatalog.transition(for: .contentFade))
        .accessibilityElement(children: .combine)"""),
]
TESTS={"M1409":"MainWindowCollapseTests/testCollapseHintKeepsDismissButtonActionableForVoiceOver"}
def run(test):
    p=subprocess.run(["swift","test","--filter",test],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read()
    code,out=run(TESTS["M1409"]); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    old,new=ARMS[0][3],ARMS[0][4]
    if orig.count(old)!=1: print("needle",orig.count(old)); return 1
    open(path,"w",encoding="utf-8").write(orig.replace(old,new))
    try: code,out=run(TESTS["M1409"])
    finally: open(path,"w",encoding="utf-8").write(orig)
    print("M1409:",code)
    clean=open(path,"rb").read()==orig.encode("utf-8")
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if code=="CAUGHT" and clean else 1
if __name__=="__main__": sys.exit(main())
