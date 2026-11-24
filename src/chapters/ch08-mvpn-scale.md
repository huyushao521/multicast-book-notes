# ch08 大规模组播：MVPN / MLDP / Provider Multicast / 组播流量工程

> **来源**：Volume II Ch2（Multicast Scalability and Transport Diversification，P.117–P.153）、Ch3（Multicast MPLS VPNs，P.155–P.224）、Williamson Ch16（Multicast Traffic Engineering，P.474–P.507）
> **配图**：[D13 MVPN Default/Data MDT](../diagrams/d13-mvpn.svg)

---

## 学习目标

1. 说清 MVPN 的两个隧道层次：Default MDT 与 Data MDT，以及各自承载什么；
2. 理解 MLDP 信令与 P2MP 隧道、FEC 元素；
3. 解释 Provider Multicast、Multicast Extranet VPN、Route Leaking、VRF Select、融合路由、VASI 的用途；
4. 理解组播流量工程（M-TE / mLDP / Segment Routing）的基本思路；
5. 判断 BIER 的适用场景与现状。

---

## 1. 为什么需要 MVPN

**问题**：企业多站点通过运营商 MPLS VPN 互联，站点间需要组播。

**朴素做法**：把 RP 放在公网（不合理，安全与地址都不允许），或在 VPN 内建一条 **GRE 隧道**把所有 PE 连起来（隧道头开销大、扩展性差、无法叠加 VPN）。

**MVPN（Multicast VPN, RFC 6513/6514）**：把"组播 VPN"作为 MPLS VPN 的一个**地址族**来承载，复用 MPLS 基础设施。

---

## 2. MVPN 的隧道模型

![MVPN Default/Data MDT](../diagrams/d13-mvpn.svg)

### 2.1 两个层次（Volume II Ch3）

| 隧道 | 内容 | 特点 |
|---|---|---|
| **Default MDT**（默认 MDT） | **信令面 + 初始数据面**，承载所有 VPN 内组播的**控制信令**与**低速/未识别流量** | 全 VPN 共享一条 P2MP/LSP，成本低但可能过订 |
| **Data MDT**（数据 MDT） | **数据面**，承载某个 (S,G) 的实际组播流 | **按流动态创建**，点对点或点对多点，用完即拆 |

**触发逻辑（Data MDT 触发）**：

1. 某 PE 收到来自 VPN 的组播流且有接收者；
2. 判断当前流量是否超过 Data MDT 触发阈值（`mdt data threshold`）；
3. 满足则通过信令（MLDP/PIM）向其他 PE 发起 Data MDT 建立请求；
4. 建立后，流量改走 Data MDT；Default MDT 只保留信令；
5. 流量停止后，Data MDT **老化拆除**（默认约 2–3 分钟量级）。

**默认 MDT 的价值**：即使 Data MDT 未建立，业务也能跑（只是共享带宽）→ **兜底能力**，避免信令失败导致业务中断。

### 2.2 MLDP（Multicast Label Distribution Protocol, RFC 6388）

- 用 **FEC（FEC Element）** 描述 P2MP 树；
- FEC 元素类型：
  - **(P2MP, LSP) FEC**：对应一棵 P2MP LSP；
  - **(P2MP, Generic) FEC**：不对应具体 LSP 的抽象 FEC（用于 Default MDT 的共享转发）；
  - **(P2MP, mLDP, mLDP-nbr) FEC**：源发起的 mLDP 树。
- **上行方式**：
  - **In-Band signaling**：信令报文承载在数据报文的 UDP 头上（用 UDP 报文头的 "Label Switched Multicast" 字段携带信令）；
  - **Out-of-Band（Overlay） signaling**：信令与数据分离（更容易做 QoS 与 ACL）。
- **Default MDT Root High Availability（Volume II Ch3）**：Default MDT 的根（Root PE）冗余机制，根失效时切换到备份根。

### 2.3 配置要点（Volume II Ch3 示例）

```cisco
! PE 上
router bgp 65001
 address-family ipv4 mvpn
  neighbor 10.2.2.2 activate
!
multicast-vpn
!
interface GigabitEthernet0/1
 vrf forwarding BLUE
 ip pim sparse-mode
 mdt data 239.1.1.1 239.1.1.10
!
interface TenGigabitEthernet0/0
 mldp
!
```

> 关键点：**Data MDT 的组范围**必须与 VPN 内的组地址规划一致；`mdt data` 声明范围外的组只能走 Default MDT。

---

## 3. Provider Multicast 与企业组播（Volume II Ch2、Ch3）

| 技术 | 说明 |
|---|---|
| **P Multicast Transport** | 运营商在自己的核心提供组播传输（不是 VPN 内的 MVPN，而是"运营商组播业务"） |
| **PE–CE Multicast Routing** | PE 与 CE 之间跑 PIM-SM，PE 上做 **PE-CE 间的组播路由**（CE 侧的 RP 与 PE 侧互通） |
| **CE–CE Multicast Routing** | 同一 VPN 内不同 CE 之间的组播，通过 **MVPN**（Default/Data MDT）承载 |
| **PE–PE Ingress Replication** | 核心不支持组播复制时，由 PE 做**入口复制**（数据面复制而非隧道） |
| **Multicast Extranet VPN** | 把某些 VPN 的组播泄露给其他 VPN（受控的 extranet） |
| **Route Leaking** | 在 PE 间泄露路由以支持跨 VPN 组播 |
| **VRF Fallback** | 若目标组在目标 VRF 中无对应路由，则回退到全局（core）路由表 |
| **VRF Select** | 通过 import/export 规则精确控制 VRF 间的组播互通 |
| **Fusion Router** | 一台设备同时承担 PE 与 CE 角色 |
| **VASI**（VRF-Aware Service Infrastructure） | 跨 VRF 的组播业务（不同 VPN 之间共享同一份媒体流） |

**Ingress Replication vs 隧道**：

| | Ingress Replication | MDT 隧道 |
|---|---|---|
| 复制点 | PE（入口） | 核心 P2MP 节点 |
| 核心要求 | 核心只需单播（**不需要组播能力**） | 核心需支持 MPLS/P2MP 或组播 |
| 带宽 | 复制后每份占核心带宽 | 隧道共享，核心按 P2MP 分叉 |
| 适用 | 核心不支持组播复制时 | 核心支持时更高效 |

> **现实提示**：Volume II Ch2 专门讨论"为什么公有云没有原生组播"——公有云 VPC 普遍不支持组播，因此企业上云时需要用 **Service Reflection（服务反射）/ Unicast-to-Multicast 转换**等替代方案（见 ch09）。

---

## 4. 组播流量工程（Williamson Ch16、Volume II Ch6）

**问题**：默认组播树由 RPF 计算得出，往往与单播路径不一致或未按业务重要性规划。

**手段**：

| 手段 | 说明 |
|---|---|
| **组播 TE（MPLS-TE / mLDP）** | 为组播建立受约束的 P2MP 树，显式指定路径 |
| **mLDP 与 mLDP-TE** | 增强 mLDP 支持 ERO（显式路由对象）与 FRR |
| **Segment Routing + mLDP** | 新一代组播流量工程，与 SR-MPLS 融合 |
| **MPLS-TE P2MP LSP** | 显式建树，路径可控可备份 |
| **组播负载分担与冗余路径** | 两条路径 + PIM Assert 决策 |
| **PIM + Traffic Engineering 排障**（Volume II Ch6） | 常见问题：TE 路径与 RPF 不一致导致丢包 |

**典型问题与对策**：

- **RPF 与 TE 路径不一致**：TE 绕开了 RPF 接口 → 组播被丢。对策：把 TE 路径的入接口纳入 RPF 考量，或用 `ip mroute` 显式指定。
- **主备路径切换抖动**：组播在切换时中断（无组播 FRR）。对策：mLDP FRR / FRR 与组播联动。

---

## 5. BIER（Bit Index Explicit Replication, RFC 8279）

**概念**：在**核心**用"位图"而非"树"来描述组播转发：核心节点按位图复制到出口节点。

| 优势 | 挑战 |
|---|---|
| 不需要维护组播状态树 | 需要 BFER 级的转发架构与封装（BIE） |
| 不需要 MPLS 或 IP 组播支持 | 需要全网一致支持 BIER |
| 收敛快（无信令） | 落地慢、设备支持有限（2020s 逐步成熟） |

> 现状判断：BIER 是组播核心化的"下一代答案"，但当前企业现网仍以 MVPN/MLDP/Provider Multicast 为主。了解概念即可。

---

## 6. 排障命令速查

```cisco
show mdt data                            ! Data MDT 状态
show mdt data detail
show mdt default                         ! Default MDT
show mldp neighbor
show mldp fec
show mldp tunnel
show pim mdt                             ! PIM 视角的 MDT
show mroute vrf BLUE 239.1.1.1
show bgp ipv4 mvpn
show ip pim vrf mdt

debug mldp events
debug mldp packets
```

---

## 7. 生产案例（6 例）

### 案例 8-1：MVPN 中组播不通，Data MDT 未建立

**现象**：跨站点 VPN 内组播不通；`show mroute vrf BLUE` 无条目。
**定位**：`show mdt data` 为空；`show mldp neighbor` 正常但 `show mldp fec` 无对应 FEC。
**根因**：MLDP 未在 PE 间建立 FEC（`mldp` 未配置在核心接口，或 BGP MVPN 地址族未激活）。
**处置**：核心接口配置 `mldp`；BGP 激活 `address-family ipv4 mvpn`。
**复盘**：MVPN 三件套 = MVPN 地址族 + `multicast-vpn` + 核心接口 `mldp`。

### 案例 8-2：组播走 Default MDT 带宽过订

**现象**：多个 VPN 业务共享默认 MDT，核心出现丢包，业务卡顿。
**定位**：`show mdt data` 显示大量组仍在 Default MDT；Default MDT 出口带宽接近线速。
**根因**：Data MDT 触发阈值未配置或过高，业务量未超阈值 → 长期留在 Default MDT。
**处置**：配置 `mdt data <group-range>` 与 `mdt data threshold`；对大流量组显式创建 Data MDT。
**复盘**：Default MDT 是兜底不是目标；大流量业务必须规划 Data MDT。

### 案例 8-3：Data MDT 建立后旧隧道未拆除

**现象**：`show mdt data` 中存在大量 stale 隧道，核心标签资源被占满。
**定位**：MDT 表项处于 Idle 但未删除，标签空间告警。
**根因**：MDT 老化定时器与信令保活不匹配，或对端 PE 故障导致拆除消息未送达。
**处置**：调整 `mdt data timer`；检查信面邻居稳定性。
**复盘**：MDT 资源泄漏要监控，把"MDT 表项数"纳入网管指标。

### 案例 8-4：跨 VRF 组播（Extranet）不通

**现象**：希望 VPN A 与 VPN B 共享同一组播源，配置 route leaking 后仍不通。
**定位**：`show mroute vrf` 在两端均无条目；检查 VRF Select / import-export 配置。
**根因**：VRF Select 规则未允许该组地址跨 VRF，或 Leak 的只是单播前缀而非组播 NLRI。
**处置**：用 VRF Select 的 import/export 精确放行组地址与源地址；确认 MBGP MVPN 通告。
**复盘**：跨 VRF 组播是最容易出安全问题的功能，权限与过滤必须逐条评审。

### 案例 8-5：核心不组播复制导致 MVPN 失败

**现象**：某新平台核心交换机不支持组播复制，MVPN 完全不通。
**定位**：PE 上 MDT 建立失败；核心接口 `show ip mroute` 无组播能力。
**根因**：核心依赖组播复制或 MLDP 转发，但平台不支持。
**处置**：改用 **PE–PE Ingress Replication** 方案（核心只跑单播）；或更换支持的平台。
**复盘**：MVPN 的落地形态取决于核心平台能力，必须在设计初期确认。

### 案例 8-6：组播 TE 路径与 RPF 不一致导致丢包

**现象**：MPLS-TE 建立的组播树正常，但收包有丢；`debug ip mpacket` 报 RPF 失败。
**定位**：对比 TE 路径入接口与 `show ip rpf <source>` 的 RPF 接口。
**根因**：TE 显式路径绕开了 FIB 中的 RPF 路径，组播包从非 RPF 接口进入被丢弃。
**处置**：让 TE 路径与单播 RPF 路径一致；或在该 PE 上配置静态 mroute 指定 RPF 接口（需环路评估）。
**复盘**：**组播 TE 的第一性问题是 RPF 一致性**，路径设计必须同时满足 TE 与 RPF。

---

## 8. 自测清单

1. Default MDT 与 Data MDT 分别承载什么？Data MDT 的触发条件与拆除时机？
2. 为什么 Default MDT 不能省？它的兜底价值在哪？
3. MLDP 的 FEC 元素有哪几类？In-Band 与 Out-of-Band 信令的差别？
4. Ingress Replication 与 MDT 隧道的取舍是什么？
5. VRF Fallback、VRF Select、Route Leaking 三个机制分别解决什么问题？
6. 组播 TE 中"RPF 与 TE 路径不一致"为何是致命问题？
7. BIER 的核心思想是什么？它的落地障碍在哪？

## 9. 延伸阅读

- Volume II Ch2（P.117–P.153）、Ch3（P.155–P.224）
- Williamson Ch16（P.474–P.507）
- Volume II Ch6（P.301–P.344）：Advanced Multicast Troubleshooting（Interdomain / PIM-TE / MVPN / VXLAN 验证）
- 延伸：`RFC 6513`（MVPN）、`RFC 6514`（MVPN 信令）、`RFC 6388`（MLDP）、`RFC 8279`（BIER）
