#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态站点生成器：把 src/ 下的 Markdown 笔记渲染成与 BGP 读书笔记项目同风格的网页。

用法：
    python tools/build_site.py            # 生成到仓库根目录（index.html + chapters/*.html）
    python tools/build_site.py --serve    # 生成后启动本地预览服务器（默认 8000 端口）

依赖：markdown（pip install markdown）、pygments
"""

import argparse
import http.server
import os
import re
import shutil
import socketserver
import sys
import functools

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
SRC_CHAPTERS = os.path.join(SRC, "chapters")
OUT = ROOT
OUT_CHAPTERS = os.path.join(ROOT, "chapters")

SITE_TITLE = "IP 组播学习路线"
SITE_SUB = "精读笔记 · 四阶段十二章"
GITHUB_URL = "https://github.com/huyushao521/multicast-book-notes"

# ---------------------------------------------------------------- 导航结构
PHASES = [
    ("阶段一 · 地基", [
        ("ch01-basics", "第 1 章 · 基础模型与地址体系"),
        ("ch02-igmp-l2", "第 2 章 · IGMP 与二层组播"),
    ]),
    ("阶段二 · 协议核心", [
        ("ch03-rpf-pim-basics", "第 3 章 · RPF 与 PIM 通用机制"),
        ("ch04-pim-dm", "第 4 章 · PIM-DM 与 PIM-SDM"),
        ("ch05-pim-sm-rp", "第 5 章 · PIM-SM 与 RP 发现"),
        ("ch06-ssm-bidir", "第 6 章 · SSM 与 BIDIR-PIM"),
    ]),
    ("阶段三 · 域间与规模化", [
        ("ch07-msdp-mbgp", "第 7 章 · MSDP 与 MBGP 域间组播"),
        ("ch08-mvpn-scale", "第 8 章 · MVPN / MLDP / 组播 TE"),
    ]),
    ("阶段四 · 场景实战", [
        ("ch09-datacenter-cloud", "第 9 章 · 数据中心与云中的组播"),
        ("ch10-ipv6-multicast", "第 10 章 · IPv6 组播"),
        ("ch11-security", "第 11 章 · 组播安全与过滤"),
        ("ch12-troubleshooting", "第 12 章 · 排障方法论"),
    ]),
]

MD_EXTENSIONS = ["extra", "tables", "fenced_code", "codehilite", "toc", "attr_list", "sane_lists", "admonition"]

# ---------------------------------------------------------------- 布局模板
LAYOUT = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {site_title}</title>
<meta name="description" content="IP 组播学习路线：四阶段十二章精读笔记，78 个生产案例，16 张 SVG 拓扑图。">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%230969da'/><circle cx='16' cy='16' r='4' fill='white'/><circle cx='16' cy='6' r='2.6' fill='white'/><circle cx='25' cy='21' r='2.6' fill='white'/><circle cx='7' cy='21' r='2.6' fill='white'/><path d='M16 10.6V8.6M18.9 17.6l3.4 2M13.1 17.6l-3.4 2' stroke='white' stroke-width='1.6'/></svg>">
<link rel="stylesheet" href="{base}assets/css/site.css">
<script>
/* 尽早写入主题，避免刷新时闪白 */
(function () {{
  var saved = null;
  try {{ saved = localStorage.getItem('mc-theme'); }} catch (e) {{}}
  var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', saved || (dark ? 'dark' : 'light'));
}})();
</script>
</head>
<body>
<div class="progress" id="progress"></div>
<input type="checkbox" id="nav-toggle" hidden>
<label for="nav-toggle" class="nav-toggle-btn">☰ 目录</label>

<button type="button" class="theme-toggle floating" data-theme-toggle aria-label="切换深色/浅色主题" title="切换深色/浅色主题">
  <span class="theme-icon" aria-hidden="true">◐</span><span class="theme-text">深色</span>
</button>

<aside class="sidebar">
  <div class="brand">
    <div class="brand-row">
      <a href="{base}index.html">{site_title}<span>{site_sub}</span></a>
      <button type="button" class="theme-toggle" data-theme-toggle aria-label="切换深色/浅色主题" title="切换深色/浅色主题">
        <span class="theme-icon" aria-hidden="true">◐</span><span class="theme-text">深色</span>
      </button>
    </div>
    <div class="search-wrap">
      <input type="search" id="nav-search" placeholder="搜索章节…" autocomplete="off" aria-label="搜索章节">
    </div>
  </div>

  <nav class="nav">
    <details class="group" id="page-toc-group" open>
      <summary>本页目录</summary>
      <ul class="toc" id="toc-list"></ul>
    </details>

    <details class="group" id="home-group" open>
      <summary>首页</summary>
      <ul><li><a href="{base}index.html" data-path="index.html">学习路线总览</a></li></ul>
    </details>
{nav}
  </nav>
</aside>

<label for="nav-toggle" class="backdrop"></label>

<main class="main">
  <article class="content">
{content}
  </article>
  <footer class="page-foot">
{prevnext}
    <p class="foot-note">内容基于公开出版物整理，仅用于技术学习；命令示例请以设备实际版本手册为准。</p>
  </footer>
</main>

<button type="button" class="to-top" id="to-top" aria-label="回到顶部" title="回到顶部">↑</button>

<script>
(function () {{
  var content = document.querySelector('.content');
  var here = location.pathname;

  /* ---------- 当前章节高亮 + 展开所属分组 ---------- */
  var active = null;
  document.querySelectorAll('.nav a[data-path]').forEach(function (a) {{
    if (here.indexOf('/' + a.dataset.path) !== -1 || here.indexOf(a.dataset.path) !== -1) {{
      a.classList.add('active');
      active = a;
    }}
  }});
  if (active) {{
    var g = active.closest('details');
    if (g) g.open = true;
  }}

  /* ---------- 生成本页目录（取 h2 / h3） ---------- */
  var heads = content ? content.querySelectorAll('h2, h3') : [];
  var tocList = document.getElementById('toc-list');
  heads.forEach(function (h, i) {{
    h.id = 'sec-' + (i + 1);
    var li = document.createElement('li');
    li.className = h.tagName === 'H3' ? 'lvl3' : 'lvl2';
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent.trim();
    li.appendChild(a);
    tocList.appendChild(li);
  }});
  if (!heads.length) {{
    var g = document.getElementById('page-toc-group');
    if (g) g.remove();
  }}

  /* ---------- 目录滚动高亮 ---------- */
  if (heads.length) {{
    var links = tocList.querySelectorAll('a');
    var onScroll = function () {{
      var idx = 0;
      heads.forEach(function (h, i) {{
        if (h.getBoundingClientRect().top <= 100) idx = i;
      }});
      links.forEach(function (a, i) {{ a.classList.toggle('active', i === idx); }});
    }};
    window.addEventListener('scroll', onScroll, {{ passive: true }});
    onScroll();
  }}

  /* ---------- 阅读进度条 ---------- */
  var bar = document.getElementById('progress');
  function paintProgress() {{
    if (!bar) return;
    var h = document.documentElement.scrollHeight - window.innerHeight;
    var p = h > 0 ? (window.scrollY / h) * 100 : 0;
    bar.style.width = Math.min(100, Math.max(0, p)) + '%';
  }}
  window.addEventListener('scroll', paintProgress, {{ passive: true }});
  paintProgress();

  /* ---------- 回到顶部 ---------- */
  var top = document.getElementById('to-top');
  if (top) {{
    top.addEventListener('click', function () {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }});
    window.addEventListener('scroll', function () {{
      top.style.opacity = window.scrollY > 400 ? '1' : '0';
    }}, {{ passive: true }});
  }}

  /* ---------- 侧栏搜索过滤 ---------- */
  var search = document.getElementById('nav-search');
  if (search) {{
    search.addEventListener('input', function () {{
      var q = search.value.trim().toLowerCase();
      document.querySelectorAll('.nav .group.part').forEach(function (grp) {{
        var hit = 0;
        grp.querySelectorAll('li').forEach(function (li) {{
          var t = (li.textContent || '').toLowerCase();
          var ok = !q || t.indexOf(q) !== -1;
          li.style.display = ok ? '' : 'none';
          if (ok) hit++;
        }});
        grp.style.display = hit ? '' : 'none';
        if (q && hit) grp.open = true;
      }});
    }});
  }}

  /* ---------- 代码块复制按钮 ---------- */
  document.querySelectorAll('.content pre').forEach(function (pre) {{
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = '复制';
    btn.addEventListener('click', function () {{
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      navigator.clipboard.writeText(text).then(function () {{
        btn.textContent = '已复制';
        setTimeout(function () {{ btn.textContent = '复制'; }}, 1500);
      }}).catch(function () {{ btn.textContent = '复制失败'; }});
    }});
    pre.appendChild(btn);
  }});

  /* ---------- 移动端点目录后自动收起 ---------- */
  document.querySelectorAll('.nav a[data-path]').forEach(function (a) {{
    a.addEventListener('click', function () {{
      document.getElementById('nav-toggle').checked = false;
    }});
  }});

  /* ---------- 主题切换 ---------- */
  var root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function paintButtons(theme) {{
    var dark = theme === 'dark';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {{
      btn.querySelector('.theme-icon').textContent = dark ? '☀' : '☾';
      btn.querySelector('.theme-text').textContent = dark ? '浅色' : '深色';
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      btn.title = dark ? '切换到浅色主题' : '切换到深色主题';
    }});
  }}

  function applyTheme(theme) {{
    root.setAttribute('data-theme', theme);
    paintButtons(theme);
  }}

  paintButtons(root.getAttribute('data-theme') || 'light');

  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try {{ localStorage.setItem('mc-theme', next); }} catch (e) {{}}
    }});
  }});

  if (mq) {{
    var onScheme = function (e) {{
      var saved = null;
      try {{ saved = localStorage.getItem('mc-theme'); }} catch (err) {{}}
      if (!saved) applyTheme(e.matches ? 'dark' : 'light');
    }};
    if (mq.addEventListener) mq.addEventListener('change', onScheme);
    else if (mq.addListener) mq.addListener(onScheme);
  }}
}})();
</script>
</body>
</html>
"""

EXTRA_CSS = u"""
/* ---------- 组播站点增强 ---------- */
.progress {
  position: fixed;
  top: 0; left: 0;
  height: 3px;
  width: 0;
  background: linear-gradient(90deg, var(--accent), #2da44e);
  z-index: 100;
  transition: width .08s linear;
}

.search-wrap { margin-top: 10px; }
.search-wrap input {
  width: 100%;
  padding: 6px 10px;
  font-family: inherit;
  font-size: 13px;
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  outline: none;
}
.search-wrap input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

/* 章节内图片（SVG 拓扑图） */
.content img {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 1.4em auto;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--border-soft);
  border-radius: 10px;
}

/* python-markdown 的 codehilite 容器与 Rouge 保持一致 */
.content .codehilite { position: relative; }
.content .codehilite pre { margin-top: 0; }

/* 语法高亮：python-markdown(codehilite) 的类名映射 */
.content .codehilite .c, .content .codehilite .c1, .content .codehilite .cm { color: var(--hl-comment); font-style: italic; }
.content .codehilite .k, .content .codehilite .kd, .content .codehilite .kn, .content .codehilite .kp { color: var(--hl-keyword); }
.content .codehilite .s, .content .codehilite .s1, .content .codehilite .s2, .content .codehilite .sb, .content .codehilite .sd { color: var(--hl-string); }
.content .codehilite .na, .content .codehilite .nv, .content .codehilite .nb { color: var(--hl-name); }
.content .codehilite .mi, .content .codehilite .mf, .content .codehilite .m { color: var(--hl-number); }
.content .codehilite .o, .content .codehilite .p { color: var(--text-soft); }
.content .codehilite .err { color: #ff7b72; }
.content .codehilite .gp { color: var(--hl-comment); }
.content .codehilite .hll { background: rgba(255, 214, 10, .12); display: block; }

/* 代码复制按钮 */
.copy-btn {
  position: absolute;
  top: 8px; right: 8px;
  padding: 2px 9px;
  font-family: inherit;
  font-size: 11.5px;
  color: var(--text-soft);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  opacity: 0;
  transition: opacity .15s ease;
}
.content pre:hover .copy-btn { opacity: 1; }
.copy-btn:hover { color: var(--accent); border-color: var(--accent); }

/* 上下章导航 */
.page-foot {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 40px 80px;
}
.pn {
  display: flex;
  gap: 12px;
  margin: 20px 0 10px;
}
.pn a {
  flex: 1;
  display: block;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text);
  text-decoration: none;
  transition: border-color .15s ease, transform .15s ease;
}
.pn a:hover { border-color: var(--accent); transform: translateY(-1px); }
.pn a.next { text-align: right; }
.pn .dir { display: block; font-size: 12px; color: var(--text-muted); }
.pn .ttl { display: block; font-size: 14px; font-weight: 600; color: var(--accent); margin-top: 2px; }
.foot-note { font-size: 12.5px; color: var(--text-faint); border-top: 1px solid var(--border-soft); padding-top: 12px; }

/* 回到顶部 */
.to-top {
  position: fixed;
  right: 22px; bottom: 22px;
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text-soft);
  font-size: 16px;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: opacity .2s ease;
  z-index: 40;
}
.to-top:hover { color: var(--accent); border-color: var(--accent); }

/* 首页表格里的章节链接 */
.content table a { font-weight: 600; }

@media (max-width: 900px) {
  .page-foot { padding: 0 18px 60px; }
  .pn { flex-direction: column; }
  .pn a.next { text-align: left; }
}
"""


def rewrite_links(html):
    """Markdown 源码以 src/ 为基准写路径，输出时统一剥离一层 '../'。

    - src/chapters/x.md 的 ../../diagrams/y.svg → chapters/x.html 的 ../diagrams/y.svg
    - src/index.md 的 ../chapters/x.html      → index.html 的 chapters/x.html
    """
    def fix(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith('../'):
            val = val[3:]
        return '%s="%s"' % (attr, val)
    return re.sub(r'(href|src)="([^"]+)"', fix, html)


def render_md(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs={
        "codehilite": {"linenums": False, "guess_lang": False},
        "toc": {"permalink": False},
    })
    html = md.convert(text)
    md.reset()
    return rewrite_links(html)


def build_nav(active_id=None, base=""):
    out = []
    for phase, items in PHASES:
        out.append('    <details class="group part" data-part="%s" open>' % phase.split("·")[0].strip())
        out.append("      <summary>%s</summary>" % phase)
        out.append("      <ul>")
        for cid, title in items:
            active = " active" if cid == active_id else ""
            out.append('        <li><a href="%schapters/%s.html" data-path="chapters/%s.html"%s>%s</a></li>'
                       % (base, cid, cid, active, title))
        out.append("      </ul>")
        out.append("    </details>")
    return "\n".join(out)


def page_title_for(cid):
    for _, items in PHASES:
        for i, t in items:
            if i == cid:
                return t
    return cid


def prev_next(cid):
    seq = [c for _, items in PHASES for c, _ in items]
    try:
        i = seq.index(cid)
    except ValueError:
        return ""
    parts = []
    if i > 0:
        p = seq[i - 1]
        parts.append('<a class="prev" href="%s.html"><span class="dir">← 上一章</span><span class="ttl">%s</span></a>'
                     % (p, page_title_for(p)))
    if i < len(seq) - 1:
        n = seq[i + 1]
        parts.append('<a class="next" href="%s.html"><span class="dir">下一章 →</span><span class="ttl">%s</span></a>'
                     % (n, page_title_for(n)))
    if not parts:
        return '<a class="next" href="../index.html"><span class="dir">返回 →</span><span class="ttl">学习路线总览</span></a>'
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="生成后启动本地预览服务器")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    if not os.path.isdir(SRC_CHAPTERS):
        print("src/chapters not found:", SRC_CHAPTERS)
        sys.exit(1)

    os.makedirs(OUT_CHAPTERS, exist_ok=True)

    # 1) 首页
    idx_html = render_md(os.path.join(SRC, "index.md"))
    page = LAYOUT.format(title="学习路线总览", site_title=SITE_TITLE, site_sub=SITE_SUB,
                         nav=build_nav(None), content=idx_html, base="",
                         prevnext='<a class="next" href="chapters/ch01-basics.html">'
                                  '<span class="dir">开始阅读 →</span><span class="ttl">第 1 章 · 基础模型与地址体系</span></a>')
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # 2) 各章
    count = 0
    for _, items in PHASES:
        for cid, title in items:
            src = os.path.join(SRC_CHAPTERS, cid + ".md")
            if not os.path.exists(src):
                print("  ! missing:", src)
                continue
            body = render_md(src)
            html = LAYOUT.format(title=title, site_title=SITE_TITLE, site_sub=SITE_SUB,
                                 nav=build_nav(cid, "../"), content=body, base="../",
                                 prevnext=prev_next(cid))
            with open(os.path.join(OUT_CHAPTERS, cid + ".html"), "w", encoding="utf-8") as f:
                f.write(html)
            count += 1

    # 3) 样式：基础 css + 增强 css（每次重建，保证增强块与脚本一致）
    css_path = os.path.join(ROOT, "assets", "css", "site.css")
    marker = "/* ---------- 组播站点增强 ---------- */"
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    if marker in css:
        css = css.split(marker)[0].rstrip()
    css = css + "\n\n" + marker + "\n" + EXTRA_CSS
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)

    # 4) .nojekyll（GitHub Pages 直接按静态文件发布，避免 Jekyll 处理）
    nojekyll = os.path.join(ROOT, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()

    print("built: index.html + %d chapters" % count)

    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("127.0.0.1", args.port), handler) as httpd:
            print("serving http://127.0.0.1:%d/  (Ctrl+C to stop)" % args.port)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nstopped")


if __name__ == "__main__":
    main()
