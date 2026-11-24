#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一修复 Markdown 源码中的相对路径基准。

约定：src/ 下的 Markdown 一律以 "src/" 为基准书写路径
    - src/index.md      → 链接写作 ../chapters/x.html
    - src/chapters/x.md → 图片写作 ../../diagrams/x.svg
构建时由 build_site.py 统一剥离一层 "../"，即可适配各自的输出位置。
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

changed = []

for f in sorted(glob.glob(os.path.join(ROOT, 'src', 'chapters', '*.md'))):
    t = io.open(f, encoding='utf-8').read()
    n = t.replace('](../diagrams/', '](../../diagrams/')
    if n != t:
        io.open(f, 'w', encoding='utf-8', newline='').write(n)
        changed.append(os.path.relpath(f, ROOT))

for f in sorted(glob.glob(os.path.join(ROOT, 'src', '*.md'))):
    t = io.open(f, encoding='utf-8').read()
    n = re.sub(r'\]\(chapters/', '](../chapters/', t)
    n = n.replace('](../diagrams/', '](../diagrams/')
    if n != t:
        io.open(f, 'w', encoding='utf-8', newline='').write(n)
        changed.append(os.path.relpath(f, ROOT))

print('rewritten: %d file(s)' % len(changed))
for c in changed:
    print('  ' + c)
