# -*- coding: utf-8 -*-
"""生成组播学习路线的全部 SVG 拓扑图。运行：python tools/gen_diagrams.py"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "diagrams")
os.makedirs(OUT, exist_ok=True)

C = {
    "stroke": "#1f4e79", "fill": "#dbe9f6", "fill2": "#eaf3e0", "fill3": "#fde9d9",
    "red": "#c00000", "green": "#2e7d32", "gray": "#666666", "bg": "#ffffff",
    "blue": "#1565c0",
}
FONT = "font-family='Segoe UI,Microsoft YaHei,sans-serif'"

def head(w, h, title):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>\n"
            f"<rect width='{w}' height='{h}' fill='{C['bg']}'/>\n"
            f"<text x='{w/2}' y='26' {FONT} font-size='16' font-weight='bold' fill='{C['stroke']}' "
            f"text-anchor='middle'>{title}</text>\n")

def foot(w, h, note=""):
    s = f"</svg>\n"
    if note:
        s = (f"<text x='16' y='{h-12}' {FONT} font-size='11' fill='{C['gray']}'>{note}</text>\n</svg>\n")
    return s

def router(x, y, label, fill=None):
    fill = fill or C["fill"]
    return (f"<g><circle cx='{x}' cy='{y}' r='26' fill='{fill}' stroke='{C['stroke']}' stroke-width='1.6'/>\n"
            f"<path d='M {x-11} {y-7} L {x+11} {y-7} M {x-11} {y} L {x+11} {y} M {x-11} {y+7} L {x+11} {y+7}' "
            f"stroke='{C['stroke']}' stroke-width='1.6'/>\n"
            f"<text x='{x}' y='{y+42}' {FONT} font-size='12' text-anchor='middle' fill='#222'>{label}</text></g>\n")

def sw(x, y, label, w=110, h=34, fill=None):
    fill = fill or C["fill2"]
    return (f"<g><rect x='{x-w/2}' y='{y-h/2}' width='{w}' height='{h}' rx='6' fill='{fill}' "
            f"stroke='{C['stroke']}' stroke-width='1.6'/>\n"
            f"<text x='{x}' y='{y+4}' {FONT} font-size='12' text-anchor='middle' fill='#222'>{label}</text></g>\n")

def host(x, y, label, w=90, h=32, fill=None):
    fill = fill or C["fill3"]
    return (f"<g><rect x='{x-w/2}' y='{y-h/2}' width='{w}' height='{h}' rx='3' fill='{fill}' "
            f"stroke='{C['stroke']}' stroke-width='1.4'/>\n"
            f"<rect x='{x-w/2+8}' y='{y-h/2-9}' width='{w-16}' height='9' fill='{fill}' stroke='{C['stroke']}' stroke-width='1.4'/>\n"
            f"<text x='{x}' y='{y+4}' {FONT} font-size='11' text-anchor='middle' fill='#222'>{label}</text></g>\n")

def rp(x, y, label="RP"):
    return (f"<g><circle cx='{x}' cy='{y}' r='24' fill='#fff2cc' stroke='{C['red']}' stroke-width='2'/>\n"
            f"<text x='{x}' y='{y+5}' {FONT} font-size='13' font-weight='bold' text-anchor='middle' fill='{C['red']}'>{label}</text></g>\n")

def cloud(x, y, label, w=120):
    return (f"<g><ellipse cx='{x}' cy='{y}' rx='{w/2}' ry='30' fill='#f2f2f2' stroke='{C['gray']}' stroke-width='1.4'/>\n"
            f"<text x='{x}' y='{y+5}' {FONT} font-size='12' text-anchor='middle' fill='#444'>{label}</text></g>\n")

def link(x1, y1, x2, y2, label="", color=None, dash=False, lx=None, ly=None):
    color = color or C["stroke"]
    d = ' stroke-dasharray=\'5,4\'' if dash else ""
    s = f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='1.6'{d}/>\n"
    if label:
        mx = lx if lx is not None else (x1 + x2) / 2
        my = ly if ly is not None else (y1 + y2) / 2 - 6
        s += (f"<text x='{mx}' y='{my}' {FONT} font-size='11' text-anchor='middle' fill='{color}'>{label}</text>\n")
    return s

def txt(x, y, s, size=12, color="#222", anchor="start", weight="normal"):
    return (f"<text x='{x}' y='{y}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' "
            f"font-weight='{weight}'>{s}</text>\n")

def save(name, body):
    path = os.path.join(OUT, name)
    open(path, "w", encoding="utf-8").write(body)
    print("wrote", path)

# ---------------------------------------------------------------- d01 地址空间
w, h = 900, 430
s = head(w, h, "D01  IPv4 组播地址空间与作用域划分")
rows = [
    ("224.0.0.0/24", "链路本地控制报文", "#fde9d9", "TTL=1，禁止跨路由转发；IGMP/PIM/OSPF 邻接等"),
    ("224.0.1.0 - 224.0.1.255", "全局协议控制", "#dbe9f6", "IGMPv3 兼容查询等，TTL 需显式设置"),
    ("232.0.0.0/8", "SSM 源特定组播", "#eaf3e0", "232/8 需配合 IGMPv3 或 SSM-Mapping 使用"),
    ("233.0.0.0/8", "GLOP", "#eaf3e0", "按 AS 号分配：233.ASn.x.x，运营���自有全球组播"),
    ("239.0.0.0/8", "管理域私有 (Admin Scoped)", "#dbe9f6", "跨 BGR 边界自动收敛，用于企业私有组播"),
    ("224.0.0.0 - 239.255.255.255", "224.0.0.0/4 完整 Class D 空间", "#f2f2f2", "首 4 bit = 1110，无主机/子网语义"),
]
y = 56
for rng, name, fill, desc in rows:
    s += f"<rect x='20' y='{y}' width='860' height='44' rx='4' fill='{fill}' stroke='{C['stroke']}' stroke-width='1'/>\n"
    s += txt(32, y + 27, rng, 13, C["stroke"], weight="bold")
    s += txt(240, y + 27, name, 13, "#222")
    s += txt(560, y + 27, desc, 11.5, "#555")
    y += 52
s += txt(20, y + 22, "划分依据：IANA 保留段 / 私有段 / SSM 段 / GLOP 段；跨边界时 239/8 受 Admin Scoped 边界约束。", 11.5, C["gray"])
save("d01-address-scope.svg", s + foot(w, h))

# ---------------------------------------------------------------- d02 MAC 映射
w, h = 900, 360
s = head(w, h, "D02  IPv4 组播地址 → 以太网组播 MAC 映射（低 23 位）")
s += txt(30, 62, "224.0.0.0/24 之前的 8 位保留，仅低 23 位参与映射", 12, C["gray"])
items = [("224.0.0.1", "01:00:5e:00:00:01"), ("224.0.1.129", "01:00:5e:00:01:81"),
         ("239.1.2.3", "01:00:5e:01:02:03"), ("232.1.1.1", "01:00:5e:01:01:01")]
x0 = 60
for i, (ip, mac) in enumerate(items):
    x = x0 + i * 210
    s += f"<rect x='{x}' y='90' width='180' height='70' rx='6' fill='{C['fill']}' stroke='{C['stroke']}' stroke-width='1.4'/>\n"
    s += txt(x + 90, 120, ip, 14, C["stroke"], "middle", "bold")
    s += txt(x + 90, 145, "↓  0x01005E + 低23位", 10.5, C["gray"], "middle")
    s += f"<rect x='{x}' y='165' width='180' height='46' rx='6' fill='{C['fill2']}' stroke='{C['stroke']}' stroke-width='1.4'/>\n"
    s += txt(x + 90, 194, mac, 13.5, "#1b5e20", "middle", "bold")
s += sw(450, 280, "交换机 MAC 表 / 组播表", 260)
s += txt(30, 320, "冲突：32 个组播地址共享同一 MAC（224.0.0.1/2/3/4/5 ... 映射到 01:00:5e:00:00:01）→ 需 IGMP Snooping 精确收敛", 11.5, C["red"])
s += txt(30, 340, "IPv6：33:33:xxxx:xxxx → 由低 32 位映射，同样存在 32 路冲突", 11.5, C["gray"])
save("d02-mac-mapping.svg", s + foot(w, h))

# ---------------------------------------------------------------- d03 IGMP 基础
w, h = 900, 340
s = head(w, h, "D03  IGMP 成员管理与 Querier 交互")
s += host(90, 110, "Host A\n(接收 239.1.1.1)")
s += host(90, 230, "Host B\n(接收 239.1.1.1)")
s += sw(300, 170, "L2 交换机\n(IGMP Snooping)")
s += router(560, 170, "R1\n(Queryer / DR)")
s += host(800, 170, "RP / 上游")
s += link(140, 110, 245, 155, "IGMPv3 Report")
s += link(140, 230, 245, 190, "IGMPv2 Report")
s += link(355, 170, 505, 170, "Query", C["green"], True, 430, 160)
s += link(505, 170, 355, 170, "Report", C["gray"], True, 430, 195)
s += txt(30, 300, "Querier：发送 General/Group-Specific Query；由 PIM DR 承担（RP 无需 IGMP）", 11.5, C["gray"])
s += txt(30, 322, "v3 支持 (G,S) 精确订阅 → 源过滤、防伪源注入；v2 为 ( *,G) 共享树", 11.5, C["gray"])
save("d03-igmp-basic.svg", s + foot(w, h))

# ---------------------------------------------------------------- d04 Snooping
w, h = 900, 380
s = head(w, h, "D04  未启用 vs 启用 IGMP Snooping 的组播泛洪差异")
s += txt(30, 60, "未启用 Snooping：组播未知单播 (Unknown Unicast Flooding) 泛洪到所有端口", 12.5, C["red"], weight="bold")
s += sw(180, 120, "SW1", 90)
for i in range(4):
    s += host(380 + i * 130, 120, f"Host{i+1}", 70)
    s += link(225, 120, 340 + i * 130, 120, "泛洪" if i == 0 else "", C["red"], False, 280, 108)
s += txt(30, 200, "启用 Snooping：交换机学习 IGMP Report，仅向有成员端口转发", 12.5, C["green"], weight="bold")
s += sw(180, 270, "SW1", 90)
s += sw(180, 270, "SW1", 90) if False else ""
for i in range(4):
    s += host(380 + i * 130, 270, f"Host{i+1}", 70)
    s += link(225, 270, 340 + i * 130, 270, "转发" if i == 0 else ("剪除" if i == 1 else ""), C["green"], False, 280, 258)
s += txt(600, 258, "仅 Host2 有成员 →", 11.5, C["green"])
s += txt(600, 276, "其余端口剪除", 11.5, C["green"])
s += txt(30, 350, "配套特性：Report Suppression（抑制重复 Report）、Querier（10/60 选举）、Fast Leave、IGMPv3 源过滤表", 11.5, C["gray"])
save("d04-snooping.svg", s + foot(w, h))

# ---------------------------------------------------------------- d05 RPF
w, h = 900, 340
s = head(w, h, "D05  RPF 反向路径转发检查")
s += host(90, 170, "源 S")
s += router(300, 170, "R2")
s += router(560, 170, "R1\n(接收者侧)")
s += host(800, 170, "接收者")
s += link(140, 170, 250, 170, "组播数据")
s += link(350, 170, 510, 170, "RPF 接口")
s += link(610, 170, 750, 170, "组播数据")
s += f"<path d='M 560 150 C 700 60, 300 60, 300 140' fill='none' stroke='{C['green']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(430, 60, "单播路由表：S 的下一跳 = R2 ⇒ RPF 接口为 R2 方向", 11.5, C["green"], "middle")
s += f"<rect x='560' y='215' width='330' height='95' rx='6' fill='#fdf2f2' stroke='{C['red']}' stroke-width='1.3'/>\n"
s += txt(572, 238, "RPF 失败场景：", 12, C["red"], weight="bold")
s += txt(572, 258, "· 静态 mroute 指向错误出接口", 11.5, "#333")
s += txt(572, 277, "· 单播路由不对称 / 缺路由", 11.5, "#333")
s += txt(572, 296, "· 隧道场景缺静态 mroute", 11.5, "#333")
save("d05-rpf.svg", s + foot(w, h))

# ---------------------------------------------------------------- d06 分发树
w, h = 900, 400
s = head(w, h, "D06  源树 (S,G) vs 共享树 (*,G) 与 RPT-bit 切换")
s += txt(30, 58, "PIM-SM 初始：接收者经 RP 走共享树 RPT", 12, C["stroke"], weight="bold")
s += host(90, 110, "源 S")
s += router(300, 110, "R2")
s += rp(520, 110)
s += router(700, 110, "Last-hop")
s += host(860, 110, "接收者")
s += link(140, 110, 250, 110)
s += link(350, 110, 470, 110, "Register")
s += link(570, 110, 650, 110, "(*,G) Join")
s += link(750, 110, 810, 110)
s += txt(30, 220, "SPT 切换：最后一跳收到 (S,G) Join 后向上游建 SPT，并对 RP 发 (S,G,rpt) Prune", 12, C["stroke"], weight="bold")
s += host(90, 280, "源 S")
s += router(300, 280, "R2")
s += router(520, 280, "中转 R3")
s += router(700, 280, "Last-hop")
s += host(860, 280, "接收者")
s += link(140, 280, 250, 280, "SPT 数据")
s += link(350, 280, 470, 280)
s += link(570, 280, 650, 280)
s += link(750, 280, 810, 280)
s += f"<path d='M 700 300 Q 600 400, 520 300' fill='none' stroke='{C['red']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(610, 392, "(S,G,rpt) Prune → 剪断共享树支路", 11.5, C["red"], "middle")
s += txt(30, 372, "阈值：RPT 上游带宽超限（默认 0 kbps 即触发）或收到 (S,G) Join 都会触发切换；SPT-bit 标记在 RPT 上", 11.5, C["gray"])
save("d06-trees.svg", s + foot(w, h))

# ---------------------------------------------------------------- d07 PIM-DM
w, h = 900, 380
s = head(w, h, "D07  PIM-DM 洪泛与剪枝 / PIM-SDM 边界")
s += host(90, 170, "源 S")
s += router(300, 170, "R1")
s += router(520, 170, "R2")
s += router(740, 170, "R3")
s += host(860, 60, "接收者")
s += link(140, 170, 250, 170, "组播泛洪", C["red"])
s += link(350, 170, 470, 170, "泛洪", C["red"])
s += link(570, 170, 690, 170, "泛洪", C["red"])
s += f"<path d='M 740 145 Q 860 100, 860 70' fill='none' stroke='{C['green']}' stroke-width='1.6'/>\n"
s += txt(790, 100, "有接收者 → 不剪枝", 11, C["green"])
s += f"<path d='M 520 195 Q 420 300, 300 195' fill='none' stroke='{C['gray']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(410, 295, "无接收者 → Prune 剪除", 11, C["gray"], "middle")
s += txt(30, 330, "PIM-DM：先泛洪后剪枝（适合密集组）；PIM-SDM：稀疏侧自动回落 PIM-DM 洪泛", 11.5, C["gray"])
s += txt(30, 352, "State-Refresh：周期刷新 (S,G) 状态，避免拓扑变化后重新泛洪", 11.5, C["gray"])
save("d07-pim-dm.svg", s + foot(w, h))

# ---------------------------------------------------------------- d08 PIM-SM
w, h = 900, 420
s = head(w, h, "D08  PIM-SM 三阶段：源注册 → 共享树 Join → SPT 切换")
stages = [("① Register：DR→RP", 90), ("② (*,G) Join 建 RPT", 210), ("③ (S,G) Join 切 SPT", 330)]
for title, yy in stages:
    s += txt(30, yy - 12, title, 12, C["stroke"], weight="bold")
s += host(90, 120, "源 S")
s += router(280, 120, "DR (源侧)")
s += rp(470, 120)
s += router(660, 120, "Last-hop")
s += host(830, 120, "接收者")
s += link(140, 120, 230, 120, "数据")
s += link(330, 120, 420, 120, "Register", C["green"])
s += link(520, 120, 610, 120, "(*,G) Join", C["green"], True)
s += link(710, 120, 780, 120, "数据")
s += host(90, 240, "源 S")
s += router(280, 240, "DR")
s += rp(470, 240)
s += router(660, 240, "Last-hop")
s += host(830, 240, "接收者")
s += link(330, 240, 420, 240, "Register", C["green"])
s += link(520, 240, 610, 240, "(*,G) Join", C["green"], True)
s += host(90, 360, "源 S")
s += router(280, 360, "DR")
s += rp(470, 360)
s += router(660, 360, "Last-hop")
s += host(830, 360, "接收者")
s += link(330, 360, 420, 360, "Register→停止", C["gray"], True)
s += f"<path d='M 280 340 L 280 140' fill='none' stroke='{C['red']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(290, 250, "(S,G) Join\nSPT", 11, C["red"])
s += f"<path d='M 470 250 L 470 150' fill='none' stroke='{C['red']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(478, 205, "(S,G,rpt) Prune", 11, C["red"])
s += txt(30, 405, "关键状态：(*,G)（共享）、(S,G)（源树）、(S,G,rpt)（共享树上有 SPT-bit）", 11.5, C["gray"])
save("d08-pim-sm.svg", s + foot(w, h))

# ---------------------------------------------------------------- d09 RP 发现
w, h = 900, 400
s = head(w, h, "D09  RP 发现体系：静态 / AutoRP / BSR / Embedded-RP")
s += sw(180, 110, "RP1\n(静态)", 100, 46)
s += sw(180, 230, "RP2\n(静态)", 100, 46)
s += sw(450, 170, "Mapping Agent\n(AutoRP)", 150, 46)
s += sw(720, 170, "BSR\n(RP-Candidate)", 130, 46)
s += link(230, 110, 375, 155, "224.0.1.39\n(C-RP Announce)", C["green"], True, 300, 110)
s += link(230, 230, 375, 190, "224.0.1.39", C["green"], True, 300, 245)
s += link(525, 170, 655, 170, "BSR → 224.0.0.13\nBootstrap", C["green"], True, 590, 145)
s += sw(450, 320, "普通路由器\n(Learned RP)", 150, 46)
s += link(450, 195, 450, 292, "RP-Announce\n224.0.1.39", C["blue"], True, 540, 240)
s += txt(30, 60, "AutoRP：候选 RP 宣告 + 映射代理仲裁，仅 IPv4、仅 ASM、需单播路由到 224.0.1.39/32", 11.5, C["gray"])
s += txt(30, 380, "BSR：候选 RP → BSR → Bootstrap 报文(224.0.0.13)分发 group→RP 映射，支持标准 group-list / ACL", 11.5, C["gray"])
s += txt(30, 398, "Embedded-RP：IPv6/静态 RP 常用，RP 地址内嵌于组播地址（RFC 4607）", 11.5, C["gray"])
save("d09-rp-discovery.svg", s + foot(w, h))

# ---------------------------------------------------------------- d10 Anycast-RP
w, h = 900, 400
s = head(w, h, "D10  Anycast-RP 与 MSDP 冗余（MSDP Anycast-RP / PIM Anycast-RP）")
s += rp(250, 120, "RP-A")
s += rp(250, 280, "RP-B")
s += sw(140, 200, "Loopback\n10.10.10.1\nAnycast", 120, 60)
s += link(140, 180, 200, 140, "", C["red"])
s += link(140, 220, 200, 260, "", C["red"])
s += router(560, 200, "AS1 Border")
s += router(760, 200, "AS2 Border")
s += sw(450, 90, "MSDP Peer\n(RP-A ↔ RP-B)", 170, 44)
s += link(560, 175, 535, 120, "SA", C["green"], True)
s += link(760, 175, 535, 120, "SA", C["green"], True)
s += link(560, 225, 535, 280, "SA", C["green"], True)
s += link(760, 225, 535, 280, "SA", C["green"], True)
s += txt(600, 320, "MSDP Anycast-RP：SA 消息携带原始 RP(RP-id) + 原地址", 11.5, C["gray"], "middle")
s += txt(600, 340, "PIM Anycast-RP：靠 MSDP 同步 + Register 复制，无 SA 依赖", 11.5, C["gray"], "middle")
s += txt(30, 60, "核心要点：任何cast IP 相同，路由最优路径收敛到最近 RP；", 11.5, C["gray"])
s += txt(30, 78, "MSDP Anycast-RP 需在 RP 上配置 msdp originator-id，并保留 SA 中的 RP-id", 11.5, C["gray"])
save("d10-anycast-rp.svg", s + foot(w, h))

# ---------------------------------------------------------------- d11 BIDIR
w, h = 900, 380
s = head(w, h, "D11  BIDIR-PIM 双向共享树与 DF 选举")
s += rp(470, 190, "RP-A\n(RPA)")
s += host(120, 120, "源 1")
s += host(120, 260, "接收者")
s += router(300, 120, "DF-1\n(源侧)")
s += router(300, 260, "DF-2\n(接收侧)")
s += link(170, 120, 250, 120, "数据")
s += link(350, 120, 440, 165, "源侧 RPT", C["green"], True)
s += link(350, 260, 440, 215, "接收侧 RPT", C["green"], True)
s += host(800, 190, "源 2")
s += router(700, 190, "DF-3")
s += link(750, 190, 520, 190, "源侧 RPT", C["green"], True)
s += txt(30, 340, "特点：不用 Register、无 (S,G) 状态，只有 (*,G)；适用于大量源、少量接收者的场景（如行情）", 11.5, C["gray"])
s += txt(30, 360, "DF 选举：优先级 → 接口度量 → IP 地址；可用 Offer/Winner/Backoff/Pass 报文增强可靠性", 11.5, C["gray"])
s += txt(30, 378, "Phantom-RP：用 Anycast 地址配置 Phantom RP 提升冗余", 11.5, C["gray"])
save("d11-bidir.svg", s + foot(w, h))

# ---------------------------------------------------------------- d12 MSDP
w, h = 900, 400
s = head(w, h, "D12  MSDP 域间组播：Peer-RPF 与 SA 传播")
s += sw(180, 100, "AS100\n域", 110, 46)
s += sw(180, 300, "AS200\n域", 110, 46)
s += router(400, 100, "RP-AS100")
s += router(400, 300, "RP-AS200")
s += router(700, 200, "MSDP 对等体")
s += host(120, 100, "源")
s += link(170, 100, 350, 100, "Register")
s += link(450, 100, 650, 190, "SA(AS100)", C["green"], True, 540, 120)
s += link(450, 300, 650, 210, "SA(AS200)", C["green"], True, 540, 300)
s += f"<rect x='620' y='60' width='250' height='110' rx='6' fill='#f7f7f7' stroke='{C['gray']}' stroke-width='1.2'/>\n"
s += txt(632, 82, "Peer-RPF 规则（关键）", 12, C["stroke"], weight="bold")
s += txt(632, 102, "1. 源自 SA 的 AS 必须与对等体所在 AS 相同", 11, "#333")
s += txt(632, 120, "2. 对等体为 mesh-group 时按组内规则判定", 11, "#333")
s += txt(632, 138, "3. 默认 peer：源自 AS 内最近的路由器", 11, "#333")
s += txt(632, 156, "4. 首跳 AS 匹配 → 直接接受", 11, "#333")
s += txt(30, 380, "配套：MBGP 通告 (S,G) 与组播源；MSDP SA Cache(SA-Advert/SA-Cache) 控制收敛速度", 11.5, C["gray"])
save("d12-msdp.svg", s + foot(w, h))

# ---------------------------------------------------------------- d13 MVPN
w, h = 900, 400
s = head(w, h, "D13  MVPN：Default MDT 与 Data MDT")
s += cloud(180, 120, "VRF-A CE")
s += cloud(180, 300, "VRF-B CE")
s += router(340, 120, "PE1")
s += router(340, 300, "PE2")
s += router(700, 120, "PE3")
s += router(700, 300, "PE4")
s += sw(520, 210, "MPLS Core\n(Default MDT 隧道)", 190, 54)
s += link(390, 120, 425, 190, "数据 MDT (数据面)", C["green"], True, 470, 140)
s += link(390, 300, 425, 230, "数据 MDT", C["green"], True, 470, 300)
s += link(615, 190, 650, 140, "数据 MDT", C["green"], True, 570, 150)
s += link(615, 230, 650, 280, "数据 MDT", C["green"], True, 570, 290)
s += f"<path d='M 340 140 Q 520 60, 700 140' fill='none' stroke='{C['blue']}' stroke-width='1.6' stroke-dasharray='6,4'/>\n"
s += txt(520, 66, "Default MDT：全组共享的隧道（数据面承载组播业务）", 11.5, C["blue"], "middle")
s += txt(30, 380, "信令面：MLDP/mLDP 或 PIM 在 VPN 内；MLDP FEC 元素建立 Default MDT，Data MDT 按需触发", 11.5, C["gray"])
save("d13-mvpn.svg", s + foot(w, h))

# ---------------------------------------------------------------- d14 VXLAN
w, h = 900, 400
s = head(w, h, "D14  VXLAN/EVPN Fabric 中的组播（Ingress Replication）")
s += host(120, 200, "源 VM", 90)
s += sw(260, 200, "Leaf1", 100)
s += sw(260, 340, "Leaf2", 100)
s += sw(520, 270, "Spine", 110)
s += sw(760, 200, "Leaf3", 100)
s += host(870, 200, "接收 VM", 90)
s += link(170, 200, 205, 200, "组播", C["red"])
s += link(315, 200, 460, 255, "BUM 泛洪/复制", C["red"], True, 380, 205)
s += link(315, 340, 460, 285, "复制", C["red"], True, 380, 350)
s += link(575, 255, 705, 215, "Ingress Replication", C["green"], True, 640, 220)
s += link(575, 285, 705, 325, "复制", C["green"], True, 640, 345)
s += link(815, 200, 825, 200)
s += txt(30, 60, "关键点：组播是 BUM 流量，需靠 EVPN Ingress Replication 复制到各 Leaf，避免 Spine 反射", 11.5, C["gray"])
s += txt(30, 380, "配置要点：EVPN route-type 3/10 携带组播组；Leaf 需开启 ip pim / igmp snooping；跨 VNI 依赖 L3 组播", 11.5, C["gray"])
save("d14-vxlan.svg", s + foot(w, h))

# ---------------------------------------------------------------- d15 IPv6
w, h = 900, 380
s = head(w, h, "D15  IPv6 组播：MLD 与 Embedded-RP")
s += host(120, 120, "IPv6 源")
s += sw(280, 120, "L2 交换机\n(MLD Snooping)", 130, 48)
s += router(460, 120, "DR / RP\n(FF02::2:FFxx:xxxx)")
s += router(700, 120, "上游 (PD)")
s += link(170, 120, 210, 120)
s += link(345, 120, 400, 120, "MLDv2 Report")
s += link(520, 120, 640, 120)
s += txt(30, 60, "MLD ≈ IGMP：MLDv1 (对应 IGMPv2)、MLDv2 (对应 IGMPv3，支持 (G,S))", 11.5, C["gray"])
s += txt(30, 78, "地址：FF00::/8；作用域 2=链路、5=站点、8=组织、0=全球；无 Admin-Scope 边界，用 scope 划分", 11.5, C["gray"])
s += f"<rect x='150' y='210' width='600' height='130' rx='6' fill='#fdf9f0' stroke='{C['red']}' stroke-width='1.3'/>\n"
s += txt(165, 235, "Embedded-RP (RFC 4607)", 13, C["red"], weight="bold")
s += txt(165, 260, "组地址 FF7x:...::/64 中嵌入 RP：末 32 bit = FF02::FFxx:xxxx（RPA）", 11.5, "#333")
s += txt(165, 282, "前提：接收端已配置 ipv6 unicast-routing 且能解析到 RPA 地址", 11.5, "#333")
s += txt(165, 304, "优点：无需 MSDP 即可跨域；SSM 段 FF3x::/32 天然无需 RP", 11.5, "#333")
s += txt(165, 326, "对比 IPv4：IPv6 用 scope 而非 239/8 + BGR 边界来划分域", 11.5, "#333")
save("d15-ipv6.svg", s + foot(w, h))

# ---------------------------------------------------------------- d16 安全
w, h = 900, 380
s = head(w, h, "D16  组播安全边界与过滤")
s += sw(150, 190, "边界路由器\n(BGR)", 120, 50)
s += cloud(360, 190, "AS 内部\n(组播域)", 150)
s += cloud(660, 190, "AS 外部\n(公共域)", 140)
s += link(210, 190, 285, 190, "mroute + ACL", C["red"])
s += link(435, 190, 590, 190, "禁止穿越", C["red"], True, 512, 178)
s += txt(30, 300, "三层过滤：ip mroute ... in/out access-list /  prefix-list", 11.5, "#333")
s += txt(30, 322, "防伪源：ip pim accept-register list / msdp originator-id 校验 / TTL 阈值", 11.5, "#333")
s += txt(30, 344, "限速：ip multicast rate-limit（按接口/组）", 11.5, "#333")
save("d16-security.svg", s + foot(w, h))

print("done")
