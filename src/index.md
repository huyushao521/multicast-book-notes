# IP 组播学习路线 · 精读笔记 · 首页

> **主书单**：*Developing IP Multicast Networks*（Beau Williamson）· *IP Multicast Routing Protocols: Concepts and Designs*（James Aweya）· *IP Multicast, Volume II*（Loveless / Blair / Durai）· *iPexpert IP Multicast Operations and Troubleshooting*
> **产出**：12 章笔记 · 16 张 SVG 拓扑图 · 工程案例库 · 排障方法论与变更检查单（**当前进度见下方「制作进度」**）

<!--STAR-->

---

## 制作进度

<!--PROGRESS-->

---

## 这套笔记解决什么问题

组播（Multicast）最反直觉的地方在于：**它不是"多播一份数据"这么简单，而是一整套与单播完全不同的控制平面**。

- 为什么组播默认只能跑 1 跳？
- 为什么 32 个组播 IP 会共用一个 MAC 地址？
- 为什么 `232.0.0.0/8` 在现网里十有八九是不通的？
- 为什么 ASM 跨域必须拖上 MSDP，而 SSM 不需要？
- 为什么"组播卡住"往往不是丢包，而是排队时延？

本套笔记按 **四阶段 · 十二章** 展开，每章都标注原书章节与页码，配 SVG 拓扑图与真实生产案例。

---

## 学习路线

### 阶段一 · 地基

| 章 | 标题 | 核心问题 | 案例 |
|---|---|---|---|
| [第 1 章](../chapters/ch01-basics.html) | 基础模型、地址体系与分发树 | 地址分区怎么背？MAC 为什么会冲突？ | 8 |
| [第 2 章](../chapters/ch02-igmp-l2.html) | IGMP 与二层组播 | Querier 为什么必须有？Snooping 怎么工作？ | 8 |

### 阶段二 · 协议核心

| 章 | 标题 | 核心问题 | 案例 |
|---|---|---|---|
| [第 3 章](../chapters/ch03-rpf-pim-basics.html) | RPF、分发树与 PIM 通用机制 | RPF 查什么？mroute 字段怎么读？ | 8 |
| [第 4 章](../chapters/ch04-pim-dm.html) | PIM-DM 与 PIM-SDM | 先泛洪后剪枝的代价是什么？ | 8 |
| [第 5 章](../chapters/ch05-pim-sm-rp.html) | PIM-SM 状态机与 RP 发现体系 | Register / SPT 切换 / AutoRP / BSR 全流程 | 9 |
| [第 6 章](../chapters/ch06-ssm-bidir.html) | SSM 与 BIDIR-PIM | 无 RP 无 MSDP 怎么做到？行情为何用 BIDIR？ | 6 |

### 阶段三 · 域间与规模化

| 章 | 标题 | 核心问题 | 案例 |
|---|---|---|---|
| [第 7 章](../chapters/ch07-msdp-mbgp.html) | MSDP 与 MBGP 域间组播 | Peer-RPF 四条规则怎么用？ | 6 |
| [第 8 章](../chapters/ch08-mvpn-scale.html) | MVPN / MLDP / Provider / 组播 TE | Default MDT 与 Data MDT 怎么分工？ | 6 |

### 阶段四 · 场景实战

| 章 | 标题 | 核心问题 | 案例 |
|---|---|---|---|
| [第 9 章](../chapters/ch09-datacenter-cloud.html) | 数据中心与云中的组播 | VXLAN 组播为何退化成广播？云上没有组播怎么办？ | 6 |
| [第 10 章](../chapters/ch10-ipv6-multicast.html) | IPv6 组播 | Embedded-RP 为什么能干掉 MSDP？ | 6 |
| [第 11 章](../chapters/ch11-security.html) | 组播安全、过滤与限速 | 组播反射放大怎么防？源白名单怎么配？ | 6 |
| [第 12 章](../chapters/ch12-troubleshooting.html) | 排障方法论与综合案例 | 四步排障法与症状决策树 | 6 |

---

## 核心结论速览

| 主题 | 一句话结论 |
|---|---|
| 地址 | `0-1 本地，2 源特定，3 GLOP，9 私有`（224/24 本地 · 232/8 SSM · 233/8 GLOP · 239/8 Admin Scope） |
| 二层 | 01:00:5e 只取低 23 位 → **32 个 IP 一个 MAC**，交换机必须做 Snooping |
| RPF | 查**单播路由表**决定组播转发方向；缺单播路由 = 组播必挂 |
| RP | 静态兜底 + 动态发现（AutoRP/BSR/Anycast/Embedded）**双保险** |
| SPT 切换 | `(S,G)` 有 `J`、共享树侧有 `T`、RP 侧有 `R` —— 三个标志缺一即异常 |
| SSM | **无 RP、无 MSDP、无共享树、源过滤安全**；但前提是终端能表达 `(G,S)` |
| BIDIR | 只有 `(*,G)`、无 Register；适合**源多收者少**（行情） |
| 排障 | 控制面与数据面分离；先 `show ip mroute`，再 `debug ip mpacket` |

---

## 生产案例库（已完成 32 例，目标 78 例）

每个案例统一采用：**现象 → 定位命令 → 根因 → 处置 → 复盘**。

> **关于案例来源**：这些是**教学用的典型化场景**——按现网高频故障的共性构造（如 CoPP 限速造成的 260 s 周期抖动、ECMP 打散 `(S,G)`、双 DR 造成 双份流），**并非书中原始案例**，也不是某一次具体故障的取证记录。用来训练"看症状→选命令→定根因"的推理路径；真实排障仍需以现场输出为准。

- [第 1 章 · 基础与地址](../chapters/ch01-basics.html) —— 行情只有部分终端收到、组播只能跑一跳、SSM 组地址被误配、Admin Scope 莫名剪断、GLOP 段误用、多出口导致 RPF 失败
- [第 2 章 · IGMP 与二层](../chapters/ch02-igmp-l2.html) —— 有 Report 无成员表、幽灵流量、Fast Leave 误伤、IGMP 报文风暴、Fast Leave 与共享设备冲突
- [第 5 章 · PIM-SM 与 RP](../chapters/ch05-pim-sm-rp.html) —— RP 未学习到、AutoRP TTL 不足、BSR 与静态冲突、哈希倾斜、Register 分片、Anycast-RP 缺 originator-id
- [第 9 章 · 数据中心](../chapters/ch09-datacenter-cloud.html) —— VXLAN 泛洪、Ingress Replication 缺失、跨 VNI 泄漏、underlay MTU、云上隧道缺静态 mroute

---

## 使用说明

- 左侧目录按 **阶段 → 章** 分组，折叠可展开；`本页目录` 跟随滚动高亮；
- 右上角 ◐ 可切换 **深色 / 浅色** 主题，选择会记住；
- 搜索框可按章节标题快速过滤；
- 每页底部有 **上一章 / 下一章** 导航；
- 所有拓扑图均为 SVG，可直接在浏览器中缩放查看；
- 建议阅读顺序：ch01 → ch02 → ch03 → ch05 → ch12（打基础 + 排障），再按需补 ch04/ch06–ch11。

> 全部章节均为中文；命令与协议字段保留英文原文，便于直接复制到设备。
