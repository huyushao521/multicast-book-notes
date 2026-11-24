#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽查生成页面中的导航链接与图片路径。"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

h = open('chapters/ch01-basics.html', encoding='utf-8').read()
print('chapter nav href :', re.findall(r'href="([^"]*chapters/[^"]*)"', h)[:3])
print('chapter img src  :', re.findall(r'<img[^>]+src="([^"]+)"', h))
print('chapter next/prev:', re.findall(r'<a class="(?:prev|next)" href="([^"]+)"', h))

idx = open('index.html', encoding='utf-8').read()
print('index links      :', re.findall(r'href="(chapters/[^"]+)"', idx)[:3])
print('index img src    :', re.findall(r'<img[^>]+src="([^"]+)"', idx))
