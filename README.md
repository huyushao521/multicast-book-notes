# IP 组播学习路线（Multicast Learning Path）

> 由 4 本书精读 + 自有笔记提炼而成的**由浅入深**学习路线。
> 目标：12 章走完，从"看懂 IGMP 报文"到"能独立完成运营商 MVPN / 数据中心组播的落地与排障"。
>
> **在线阅读**：<https://huyushao521.github.io/multicast-book-notes/> （GitHub Pages）

---

## 一、资料来源与分工

| 书 | 定位 | 在路线中的角色 |
|---|---|---|
| **Developing IP Multicast Networks**（Beau Williamson） | 组播原理 + Cisco 落地配置（Part I–V，17 章） | 原理地基、L2 组播（IGMP Snooping/CGMP）、NBMA、组播流量工程与域间 |
| **IP Multicast Routing Protocols: Concepts and Designs**（James Aweya） | 协议级权威细节（7 章，483 页） | PIM 消息格式、状态机、RP 发现、MSDP、BIDIR-PIM 的**细节来源** |
| **IP Multicast, Volume II**（Loveless/Blair/Durai，Cisco Press） | 大规模与场景化设计（6 章） | MVPN/MLDP、Provider Multicast、数据中心 VXLAN/ACI、行业解决方案 |
| **IPv4/6 Multicast Operation and Troubleshooting**（iPexpert） | 排障方法论 + show/debug 工具箱 | 每章的**排障框架与命令清单**来源 |
| `IP multicast - concepts, design and troubleshooting.docx`（自有笔记） | 你自己的框架 | 已并入本路线知识骨架（ASM/SSM/BiDir、RP 发现、RPF 排查清单） |

> 原书 PDF **不随仓库分发**（版权原因），仅保留在本机 `book/` 目录。

## 二、四阶段 · 十二章路线图

```
阶段一  地基（2 章）      组播是什么 → 成员怎么加入
  ch01 组播基础模型、地址体系与分发树模型
  ch02 IGMP 与二层组播（IGMP Snooping / Proxy / Fast Leave）

阶段二  协议核心（4 章）  转发怎么算 → 状态怎么建
  ch03 RPF、分发树与 PIM 通用机制（Hello/DR/Assert/定时器）
  ch04 PIM-DM 与 PIM-SDM（洪泛剪枝、State-Refresh、边界）
  ch05 PIM-SM 状态机与 RP 发现体系（AutoRP/BSR/Anycast-RP/Embedded-RP）
  ch06 SSM 与 BIDIR-PIM（去 RP 化与双向共享树）

阶段三  域间与规模（2 章） 跨域怎么通 → 规模怎么撑
  ch07 MSDP 与 MBGP（Peer-RPF、SA Cache、Anycast-RP over MSDP）
  ch08 大规模组播（MVPN / MLDP / Provider / 组播 TE）※ BIER 尚未展开

阶段四  场景与实战（4 章） 数据中心 → IPv6 → 安全 → 排障
  ch09 数据中心与云中的组播（VXLAN/EVPN/ACI/公有云）
  ch10 IPv6 组播（MLD、Embedded-RP、IPv6 MVPN）
  ch11 组播安全、过滤与限速
  ch12 组播排障方法论与综合案例（决策树 + 命令速查）
```

## 三、章节索引

| 章 | 标题 | 在线阅读 | 主要来源 | 拓扑图 | 案例数 | 核对 |
|---|---|---|---|---|---|---|
| 01 | [组播基础模型、地址体系与分发树](src/chapters/ch01-basics.md) | [阅读](chapters/ch01-basics.html) | Williamson Ch1–2 / Aweya Ch1.1–1.9 | [D01](diagrams/d01-address-scope.svg) [D02](diagrams/d02-mac-mapping.svg) [D05](diagrams/d05-rpf.svg) [D06](diagrams/d06-trees.svg) | 8 | 已精读 |
| 02 | [IGMP 与二层组播](src/chapters/ch02-igmp-l2.md) | [阅读](chapters/ch02-igmp-l2.html) | Williamson Ch3/Ch14–15 / Aweya Ch2 / iPexpert Ch2 | [D03](diagrams/d03-igmp-basic.svg) [D04](diagrams/d04-snooping.svg) | 8 | 已精读 |
| 03 | [RPF、分发树与 PIM 通用机制](src/chapters/ch03-rpf-pim-basics.md) | [阅读](chapters/ch03-rpf-pim-basics.html) | Aweya Ch1.6/1.10, Ch3, Ch5.6 / iPexpert Ch3–4 | [D05](diagrams/d05-rpf.svg) [D06](diagrams/d06-trees.svg) | 8 | 已精读 |
| 04 | [PIM-DM 与 PIM-SDM](src/chapters/ch04-pim-dm.md) | [阅读](chapters/ch04-pim-dm.html) | Williamson Ch6/Ch10 / Aweya Ch4 / iPexpert Ch3、Ch5 | [D07](diagrams/d07-pim-dm.svg) | 8 | 已精读 |
| 05 | [PIM-SM 状态机与 RP 发现](src/chapters/ch05-pim-sm-rp.md) | [阅读](chapters/ch05-pim-sm-rp.html) | Williamson Ch7/Ch8/Ch12 / Aweya Ch5 / iPexpert Ch4、Ch7–9 | [D08](diagrams/d08-pim-sm.svg) [D09](diagrams/d09-rp-discovery.svg) | 8 | 已精读 |
| 06 | [SSM 与 BIDIR-PIM](src/chapters/ch06-ssm-bidir.md) | [阅读](chapters/ch06-ssm-bidir.html) | Williamson Ch9 / Aweya Ch7、5.17–5.18 / iPexpert Ch6 | [D10](diagrams/d10-anycast-rp.svg) [D11](diagrams/d11-bidir.svg) | 8 | 已精读 |
| 07 | [MSDP 与 MBGP 域间组播](src/chapters/ch07-msdp-mbgp.md) | [阅读](chapters/ch07-msdp-mbgp.html) | Williamson Ch17 / Aweya Ch6 / iPexpert Ch10、Ch12 | [D12](diagrams/d12-msdp.svg) [D10](diagrams/d10-anycast-rp.svg) | 8 | 已精读 |
| 08 | [大规模组播：MVPN/MLDP/Provider/TE](src/chapters/ch08-mvpn-scale.md) | [阅读](chapters/ch08-mvpn-scale.html) | Volume II Ch2–Ch3 / Williamson Ch16 | [D13](diagrams/d13-mvpn.svg) | 8 | **部分核对** |
| 09 | [数据中心与云中的组播](src/chapters/ch09-datacenter-cloud.md) | [阅读](chapters/ch09-datacenter-cloud.html) | Volume II Ch4–Ch5 | [D14](diagrams/d14-vxlan.svg) | 8 | 已精读 |
| 10 | [IPv6 组播](src/chapters/ch10-ipv6-multicast.md) | [阅读](chapters/ch10-ipv6-multicast.html) | iPexpert Ch14 / Aweya 1.4.5 / Volume II Ch3 | [D15](diagrams/d15-ipv6.svg) | 8 | 已精读 |
| 11 | [组播安全、过滤与限速](src/chapters/ch11-security.md) | [阅读](chapters/ch11-security.html) | iPexpert Ch13 / Volume II Ch1、Ch5 | [D16](diagrams/d16-security.svg) | 8 | 已精读 |
| 12 | [排障方法论与综合案例](src/chapters/ch12-troubleshooting.md) | [阅读](chapters/ch12-troubleshooting.html) | iPexpert 全书 / Volume II Ch6 | 全部 | 8 | 已精读（方法论为原创） |

> 合计 **96 个生产案例（12 章 × 8 例）**。每章均含：学习目标 / 核心精讲 / 拓扑图 / 8 例工程案例 / 10 问自测 / **原文精读索引（书·节·纸面页）** / 延伸。
>
> **核对口径**：`已精读` = 该章主体能在原书找到对应页码，索引表逐条可回查；`部分核对` = 章节主题在四本原书中覆盖不足（如 ch08 的 mVPN/mLDP），只能按 RFC 6513/6514/6388 整理，索引表显式标注「无原书覆盖」，**不编页码**。

## 四、推荐节奏（8 周）

| 周 | 章节 | 交付物 |
|---|---|---|
| W1 | ch01–ch02 | 画出你现网的组播地址规划与 IGMP 版本现状表 |
| W2 | ch03–ch04 | 完成 RPF 定位演练：在实验环境人为制造 3 类 RPF 失败并定位 |
| W3 | ch05 | 完成 1 套 PIM-SM + BSR + Anycast-RP 实验环境并输出验证命令清单 |
| W4 | ch06–ch07 | 完成 SSM / BIDIR / MSDP 三套实验，产出对比表 |
| W5 | ch08–ch09 | 画出 MVPN Default/Data MDT 数据路径图；评估 VXLAN 组播可行性 |
| W6 | ch10–ch11 | IPv6 组播 POC 清单 + 现网组播过滤加固方案 |
| W7 | ch12 | 把 96 个案例过一遍，形成个人 case 库 |
| W8 | 复盘 | 选一个真实业务做端到端设计文档 |

## 五、每章统一模板

```
## 学习目标            —— 读完能做什么
## 核心精讲            —— 协议细节 / 报文 / 定时器 / 状态机 / 命令
## 拓扑图              —— SVG 图 + 图注
## 8 个工程案例        —— 现象 → 定位命令 → 根因 → 处置 → 复盘
## 10 问自测            —— 面试/评审级问题
## 原文精读索引        —— 书 / 节 / 纸面页 / 可核对要点
## 延伸                —— 标准与动手练习
```

## 六、贯穿全书的 5 条主线（复盘时用来串起来）

1. **成员管理线**：IGMPv1/v2/v3 → MLD → IGMP Snooping → SSM-Mapping
2. **转发决策线**：RPF → (S,G)/(*,G) → RPT/SPT → SPT-bit → Assert
3. **RP 演进线**：静态 RP → AutoRP → BSR → Anycast-RP → Embedded-RP → Phantom-RP → BIDIR 无 RP
4. **跨域线**：MSDP + MBGP → MVPN → Provider Multicast → BIER
5. **排障线**：症状分类（收不到 / 收不全 / 抖动 / 环路）→ RPF → mroute → 组播路由表 → 二层表

## 七、目录结构与本地预览

```
multicast-book-notes/
├── index.html                  ← 生成：站点首页
├── chapters/*.html             ← 生成：12 章网页
├── src/
│   ├── index.md                ← 首页源文件
│   └── chapters/*.md           ← 12 章笔记源文件（唯一真相源）
├── assets/css/site.css         ← 站点样式（浅色/深色主题）
├── diagrams/                   ← 16 张 SVG 拓扑图
├── tools/
│   ├── build_site.py           ← 静态站点生成器（Markdown → HTML，含进度面板与 Star 按钮）
│   ├── gen_diagrams.py         ← 拓扑图生成脚本
│   ├── srcgrep.py              ← 原书检索：按关键词取纸面页码（支持 -f/-t 页码范围）
│   ├── srcdump.py              ← 原书整页/整段导出，用于逐句核对
│   └── check_links.py          ← 站内链接体检
└── .nojekyll                   ← 让 GitHub Pages 按静态文件直出
```

**本地生成与预览**

```bash
pip install markdown pygments
python tools/build_site.py --serve --port 8000
# 浏览器打开 http://127.0.0.1:8000/index.html
```

修改 `src/` 下的 Markdown 后重新执行即可；`tools/gen_diagrams.py` 可重新生成拓扑图。

## 八、站点功能

- 左侧目录按 **阶段 → 章** 分组折叠，顶部搜索框可按标题过滤；
- `本页目录` 跟随滚动高亮；
- ◐ 按钮切换 **深色 / 浅色** 主题（记忆在 localStorage）；
- 顶部阅读进度条、代码块一键复制、底部上一章/下一章导航；
- 移动端自适应（汉堡菜单 + 浮动主题按钮）。
