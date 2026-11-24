#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按页取原文：用于写作时精确查阅 4 本书的对应页段。

用法:
    python tools/srcdump.py -b w -p 90-120          # Williamson 第 90-120 页
    python tools/srcdump.py -b a -p 60-66           # Aweya
    python tools/srcdump.py -b v2 -p 33-48          # Volume II
    python tools/srcdump.py -b i -p 120-140         # iPexpert
    python tools/srcdump.py -b w -p 90-120 -o _read/ch03-w.txt
    python tools/srcdump.py --find "Assert" -b a    # 全库检索短语，返回页码
"""
import argparse
import io
import os
import re
import sys

EXTRACT = os.path.join(os.path.expanduser('~'), 'CodeBuddy', '20261124114706',
                       'multicast-book-notes', '_extract')

BOOKS = {
    'w': 'Developing IP Multicast Networks _Beau Williamson_ _z-librar.txt',
    'a': 'IP Multicast Routing Protocols Concepts and Designs _James A.txt',
    'v2': 'IP Multicast_ Volume II Advanced Multicast Concepts and Larg.txt',
    'i': 'iPexpert-ipv4-6-Multicast-Operations-and-Troubleshooting.txt',
}

PAGE_RE = re.compile(r'^===== PAGE (\d+) =====\s*$')


def load(book):
    path = os.path.join(EXTRACT, BOOKS[book])
    if not os.path.exists(path):
        sys.exit('missing: ' + path)
    lines = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
    marks = []          # (page, lineno_of_marker)
    for n, ln in enumerate(lines):
        m = PAGE_RE.match(ln)
        if m:
            marks.append((int(m.group(1)), n))
    return lines, marks


def pages_text(book, start, end):
    lines, marks = load(book)
    out = []
    for pg, ln in marks:
        if start <= pg <= end:
            nxt = None
            for p2, l2 in marks:
                if l2 > ln:
                    nxt = l2
                    break
            seg = lines[ln:nxt] if nxt else lines[ln:]
            out.append('===== PAGE %d =====' % pg)
            out.extend(seg[1:])
    return '\n'.join(out)


def find(book, needle, ctx=1):
    lines, marks = load(book)
    hits = []
    for n, ln in enumerate(lines):
        if needle.lower() in ln.lower():
            pg = 0
            for p, l in marks:
                if l <= n:
                    pg = p
                else:
                    break
            hits.append((pg, ln.strip()))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-b', '--book', choices=sorted(BOOKS), required=True)
    ap.add_argument('-p', '--pages', help='起-止，如 90-120')
    ap.add_argument('-o', '--out')
    ap.add_argument('--find')
    args = ap.parse_args()

    if args.find:
        hits = find(args.book, args.find)
        print('hits: %d' % len(hits))
        for pg, txt in hits[:80]:
            print('  p.%-5d %s' % (pg, txt[:160]))
        return

    if not args.pages:
        sys.exit('need -p or --find')
    a, b = args.pages.split('-')
    txt = pages_text(args.book, int(a), int(b))
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        io.open(args.out, 'w', encoding='utf-8', newline='').write(txt)
        print('wrote %s  (%d chars)' % (args.out, len(txt)))
    else:
        print(txt)


if __name__ == '__main__':
    main()
