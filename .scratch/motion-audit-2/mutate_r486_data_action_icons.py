#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R486 变异表：设置数据页导出/导入图标（M1317–M1318）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Sources/ClipboardHistoryApp/Views/SettingsView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testDataPageExportImportButtonsCarryIcons"
ARMS=[
      ("M1317","导出图标撤掉",'                                    Label("导出历史…", systemImage: "square.and.arrow.up")','                                    Text("导出历史…")'),
      ("M1318","导入图标撤掉",'                                    Label("导入历史…", systemImage: "square.and.arrow.down")','                                    Text("导入历史…")')]
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
