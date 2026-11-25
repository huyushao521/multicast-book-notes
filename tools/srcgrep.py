#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在原文纯文本里按关键词检索，直接输出【书 + 纸面页码 + 命中行】。

用法：
    python tools/srcgrep.py -b w -r "Hello|Assert" -n 8
    python tools/srcgrep.py -b a -r "state refresh" --json
"""
import argparse
import io
import json
import os
import re
import sys

BOOKS = {
    "w": ("Developing IP Multicast Networks _Beau Williamson_ _z-librar.txt", 21),
    "a": ("IP Multicast Routing Protocols Concepts and Designs _James A.txt", 21),
    "v2": ("IP Multicast_ Volume II Advanced Multicast Concepts and Larg.txt", 18),
    "i": ("iPexpert-ipv4-6-Multicast-Operations-and-Troubleshooting.txt", 0),
}
def find_extract():
    """向上回溯找到含 _extract 的目录（书籍文本存于同级的另一个项目目录）。"""
    cands = []
    p = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        p = os.path.dirname(p)
        cands.append(os.path.join(p, "20261124114706", "multicast-book-notes", "_extract"))
        cands.append(os.path.join(p, "_extract"))
        for name in ("_extract",):
            for d in os.listdir(p) if os.path.isdir(p) else []:
                cands.append(os.path.join(p, d, name))
    for c in cands:
        if os.path.isdir(c):
            return c
    raise SystemExit("找不到 _extract 目录")


EXTRACT = find_extract()


def find_book(key):
    name, off = BOOKS[key]
    path = os.path.join(EXTRACT, name)
    if os.path.exists(path):
        return path, off
    # 文件名可能被截断，做一次模糊匹配
    for f in os.listdir(EXTRACT):
        if f.lower().startswith(name[:18].lower()):
            return os.path.join(EXTRACT, f), off
    raise SystemExit("not found: " + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--book", default="w", choices=list(BOOKS))
    ap.add_argument("-r", "--regex", required=True)
    ap.add_argument("-n", "--max", type=int, default=12, help="每个模式最多输出几条")
    ap.add_argument("-c", "--context", type=int, default=0, help="命中行后附加行数")
    ap.add_argument("-f", "--from", dest="pfrom", type=int, default=0, help="起始纸面页")
    ap.add_argument("-t", "--to", dest="pto", type=int, default=0, help="结束纸面页")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path, off = find_book(args.book)
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    pat = re.compile(args.regex, re.I)

    page = None
    rows = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"\s*=+\s*PAGE\s+(\d+)", line, re.I)
        if m:
            page = int(m.group(1))
            continue
        if page is None or page - off < 1:      # 跳过目录（罗马页码／未编页）
            continue
        paper = page - off
        if args.pfrom and paper < args.pfrom:
            continue
        if args.pto and paper > args.pto:
            continue
        if not pat.search(line):
            continue
        body = line.strip()
        if len(body) < 8:
            continue
        extra = ""
        if args.context:
            extra = " | ".join(x.strip() for x in lines[i + 1:i + 1 + args.context] if x.strip())
        rows.append({"pdf": page, "page": page - off, "text": body[:180], "next": extra[:180]})
        if len(rows) >= args.max * 4:
            break

    if args.json:
        print(json.dumps(rows[: args.max], ensure_ascii=False, indent=1))
        return
    print("[%s] 命中 %d 条（纸面页=PDF-%d）" % (args.book, len(rows), off))
    for r in rows[: args.max]:
        print("p.%-4s | %s" % (r["page"], r["text"]))
        if r["next"]:
            print("        + %s" % r["next"])


if __name__ == "__main__":
    main()
