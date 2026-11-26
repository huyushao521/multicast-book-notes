# -*- coding: utf-8 -*-
"""统计各章「原文精读索引」引用的纸面页码，给出书级覆盖率。

口径：只统计索引表里**显式写出**的纸面页（含区间），去重后与全书页数相除。
它是"能回查到的页"的下限，不代表逐页通读。
"""
import io
import os
import re

CHAPTERS = os.path.join(os.path.dirname(__file__), '..', 'src', 'chapters')

TOTALS = {
    'w': ('Williamson《Developing IP Multicast Networks》', 589),
    'a': ('Aweya《IP Multicast Routing Protocols》', 483),
    'v2': ('Volume II《Advanced Multicast Concepts》', 370),
    'i': ('iPexpert《IPv4/6 Multicast Ops & Troubleshooting》', 478),
}

BOOK_PATTERNS = [
    ('w', r'Williamson|\bW\s*(?:Ch|§|p\.)'),
    ('a', r'Aweya'),
    ('v2', r'\bv2\b|Volume\s*II'),
    ('i', r'iPexpert|\biP\b'),
]

PAGE_RE = re.compile(r'p\.\s*(\d+)(?:\s*[–\-~]\s*(\d+))?')


def iter_index_rows():
    for name in sorted(os.listdir(CHAPTERS)):
        if not name.endswith('.md'):
            continue
        text = io.open(os.path.join(CHAPTERS, name), encoding='utf-8').read()
        m = re.search(r'^##+\s*.*原文精读索引.*$', text, re.M)
        if not m:
            continue
        block = text[m.end():]
        nxt = re.search(r'^##\s', block, re.M)
        if nxt:
            block = block[:nxt.start()]
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith('|') or set(line) <= set('|- '):
                continue
            yield name, line


def main():
    pages = {k: set() for k in TOTALS}
    rows = 0
    for _, line in iter_index_rows():
        books = [k for k, pat in BOOK_PATTERNS if re.search(pat, line)]
        if not books:
            continue
        for b in books:
            for m in PAGE_RE.finditer(line):
                lo = int(m.group(1))
                hi = int(m.group(2)) if m.group(2) else lo
                if hi < lo:
                    lo, hi = hi, lo
                if hi - lo > 40:
                    hi = lo
                pages[b].update(range(lo, hi + 1))
        rows += 1

    total_cited = 0
    total_pages = 0
    print('索引行: %d' % rows)
    for k, (title, total) in TOTALS.items():
        n = len([p for p in pages[k] if 1 <= p <= total])
        total_cited += n
        total_pages += total
        print('%-6s %-58s %4d / %4d 页  %5.1f%%' % (k, title, n, total, 100.0 * n / total))
    print('合计: %d / %d 页  %.1f%%' % (total_cited, total_pages, 100.0 * total_cited / total_pages))


if __name__ == '__main__':
    main()
