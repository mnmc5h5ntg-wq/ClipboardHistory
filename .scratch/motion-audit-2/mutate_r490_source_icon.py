#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R490 变异表：主列表来源图标（M1325–M1326）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testMainListSourceRowsCarryTheSourceAppIcon"
ARMS=[
      ("M1325","来源图标永不画",'                if showsIcon, let icon = SourceAppIconProvider.icon(forBundleID: entry.sourceAppBundleID) {','                if false, let icon = SourceAppIconProvider.icon(forBundleID: entry.sourceAppBundleID) {'),
      ("M1326","无来源也画一个蓝图标",'            if !name.isEmpty {\n                Text(" · 来自 ")','            Rectangle().fill(Color.blue).frame(width: 11, height: 11)\n            if !name.isEmpty {\n                Text(" · 来自 ")')]
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
        if orig.count(old)!=1: print(mid,"needle",orig.count(old)); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
