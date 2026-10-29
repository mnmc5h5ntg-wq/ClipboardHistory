#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R495 变异表：通用页说明字号（M1337–M1338）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Sources/ClipboardHistoryApp/Views/SettingsView.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testSettingsHelperFontsShareOneSize"
ARMS=[
  ("M1337","说明字体永远退回 10pt",
   '''        (settingsHelperFontForCapture ?? true)
            ? .system(size: VisualFont.meta)
            : .system(size: 10)''',
   '''        .system(size: 10)'''),
  ("M1338","OCR 说明单独放大到 14pt",
   '''                        Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                            .font(settingsHelperFont)''',
   '''                        Text("关闭后不再对新入库的图片做文字识别，历史里已有的识别结果保持不变。")
                            .font(.system(size: 14))'''),
]
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
