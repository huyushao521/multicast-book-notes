#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""链接体检：扫描生成页面与 Markdown 源码里的内部链接，找出指向不存在文件的路径。"""
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

HTML_RE = re.compile(r'(?:src|href)="([^"]+)"')
MD_RE = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)')
SKIP = ('http', 'https', '#', 'mailto:', 'data:', 'javascript:', '//')

bad = []
checked = 0


def check(srcfile, ref, basedir):
    global checked
    if ref.startswith(SKIP):
        return
    path = ref.split('#')[0].split('?')[0]
    if not path:
        return
    checked += 1
    target = os.path.normpath(os.path.join(basedir, path))
    if os.path.exists(target):
        return
    # 源文件里可以直接写构建产物名（xxx.html 对应 xxx.md）
    if target.endswith('.html') and os.path.exists(target[:-5] + '.md'):
        return
    bad.append((srcfile, ref, target))


for f in sorted(glob.glob('chapters/*.html')) + ['index.html']:
    html = open(f, encoding='utf-8').read()
    base = os.path.dirname(f)
    for m in HTML_RE.findall(html):
        check(f, m, base)

for f in sorted(glob.glob('src/chapters/*.md')) + ['src/index.md', 'README.md']:
    txt = open(f, encoding='utf-8').read()
    base = os.path.dirname(f)
    for m in MD_RE.findall(txt):
        check(f, m, base)

print('checked refs: %d' % checked)
print('broken: %d' % len(bad))
for src, ref, target in bad:
    print('  %-28s -> %-45s (missing: %s)' % (src, ref, target))
