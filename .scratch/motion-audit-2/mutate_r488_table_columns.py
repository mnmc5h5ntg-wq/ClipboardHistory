#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R488 变异表：表格列制表位（M1321–M1322）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILES=["Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift",
       "Sources/ClipboardHistoryApp/Utilities/TableHeaderPresentation.swift"]
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testTableColumnsAlignAcrossRows"
ARMS=[
      ("M1321","不设表格制表位",FILES[0],'            style.tabStops = MarkdownTablePresentation.columnStops(in: blockText(block))','            style.tabStops = []'),
      ("M1322","只按表头定列宽",FILES[1],'''        var widths = [CGFloat](repeating: 0, count: columnCount)
        for (rowIndex, row) in parsed.enumerated() {
            for (column, cell) in row.enumerated() {
                widths[column] = max(widths[column], width(of: cell, font: fonts[rowIndex]))
            }
        }''','''        var widths = [CGFloat](repeating: 0, count: columnCount)
        for (column, cell) in parsed[0].enumerated() {
            widths[column] = width(of: cell, font: fonts[0])
        }''')]
def run():
    p=subprocess.run(["swift","test","--filter",TEST],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    originals={rel:open(os.path.join(ROOT,rel),encoding="utf-8").read() for rel in FILES}
    code,out=run(); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,rel,old,new in ARMS:
        orig=originals[rel]
        if orig.count(old)!=1: print(mid,"needle",orig.count(old)); ok=False; continue
        path=os.path.join(ROOT,rel)
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=all(open(os.path.join(ROOT,rel),"rb").read()==originals[rel].encode("utf-8") for rel in FILES)
    print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
