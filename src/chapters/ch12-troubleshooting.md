# ch12 组播排障方法论与综合案例

> **来源**：iPexpert 全书（每章的 show/debug 工具箱与 Trouble Ticket 方法论）、Volume II Ch6（Advanced Multicast Troubleshooting，P.301–P.344）
> **配图**：复用 [D05](../diagrams/d05-rpf.svg)、[D08](../diagrams/d08-pim-sm.svg)、[D12](../diagrams/d12-msdp.svg)、[D13](../diagrams/d13-mvpn.svg)、[D14](../diagrams/d14-vxlan.svg)

---

## 学习目标

1. 掌握 iPexpert 的**四步排障法**（控制面/数据面分离 → 症状分类 → 隔离 → 修复验证）；
2. 建立"症状 → 根因"的**决策树**，5 分钟内定位方向；
3. 掌握全量 show/debug 命令速查表；
4. 能独立完成一次跨域/跨 VPN 组播的端到端排障；
5. 建立个人的"组播 case 库"。

---

## 1. 排障总原则（iPexpert 核心思想）

> **"在能够彻底排障之前，理解协议的运行方式是唯一的前提。组播排障的常见根因是 PIM 拓扑与逻辑/物理拓扑不一致。"**
> —— iPexpert Ch1（P.1-5）

**四条铁律**：

1. **控制面与数据面分离**：先看 `show ip mroute`（控制面状态），再看数据包（数据面）。
2. **PIM 拓扑必须与物理/逻辑拓扑一致**：PIM 邻居必须在**直连链路**上建立，不能"跨三层建邻居"。
3. **一个 IGP 域 + 全链路启用 PIM**：多 IGP 或 PIM 未全开 = 高故障率。
4. **组播不是"非开不可"**：不需要组播的接口就 `no ip pim sparse-mode`，减少故障面。

---

## 2. 四步排障法

```
Step 1  症状分类  →  Step 2  控制面验证  →  Step 3  数据面验证  →  Step 4  定位与修复
```

### Step 1：症状分类（四类）

| 症状 | 典型描述 | 首查方向 |
|---|---|---|
| **A. 完全收不到** | 无任何流量 | IGMP 成员 → RPF → RP → PIM 邻居 |
| **B. 收不全** | 部分接收者收不到 | 二层成员表 → mroute 出接口 → IGMP 版本 |
| **C. 时断时续** | 间歇中断、闪断 | 链路收敛、DR 切换、RP 抖动、MTU/分片 |
| **D. 重复/异常** | 流量翻倍、环路、串流 | Assert、静态 mroute、跨域 Peer-RPF、租户泄漏 |

### Step 2：控制面验证（必做 5 条命令）

```cisco
show ip pim neighbor                     ! ① PIM 邻居齐全吗？DR 稳定吗？
show ip pim rp mapping                   ! ② 学到 RP 了吗？
show ip igmp groups                      ! ③ 有成员吗？
show ip mroute                           ! ④ 状态建起来了吗？
show ip mroute <group> detail            ! ⑤ RPF 接口与出接口对吗？
```

### Step 3：数据面验证

```cisco
show ip mroute <group> detail            ! 出接口列表 + 标志位
show ip igmp snooping groups             ! 二层成员口
show ip interface <if> | include multicast
debug ip mpacket <src> <group>          ! 数据包级：是否被丢、为什么
debug ip mroute <group>                  ! 状态机事件
```

### Step 4：定位与修复

按"**四层组件模型**"定位到层（MRPE / MRTM / Unicast / MGMD），再对症下药。

---

## 3. 症状决策树

```
组播不通
├─ 有 IGMP 成员吗？
│   ├─ 无 → 终端侧：IGMP 版本 / 接口 ACL / VLAN / Snooping（ch02 案例 2-1/2-5）
│   └─ 有
│       ├─ mroute 有 (S,G) / (*,G) 吗？
│       │   ├─ 无 → PIM 邻居？DR？RP？→ ch05（RP 发现/注册）、ch03（DR）
│       │   └─ 有
│       │       ├─ RPF 接口正确吗？→ show ip rpf <src> → ch03 案例 3-1
│       │       ├─ 出接口列表有内容吗？→ 无 = 树上无人 / 被 prune
│       │       └─ 有出接口但收不到
│       │           ├─ 二层：Snooping 表里有该端口吗？→ ch02 案例 2-1
│       │           ├─ IGMP 版本一致吗？→ ch02 案例 2-6
│       │           └─ 数据包被丢？→ debug ip mpacket → TTL/ACL/限速
│       └─ 只在部分区域不通 → 边界/Admin Scope → ch01 案例 1-4、ch11
└─ 跨域不通
    ├─ MSDP peer Up？SA 有缓存？→ ch07 案例 7-1/7-2
    ├─ MBGP 组播地址族建立？→ ch07 案例 7-4
    └─ MVPN：MDT 是否建立？→ ch08 案例 8-1
```

---

## 4. 全量命令速查表（按用途分类）

### 4.1 组播路由表

| 命令 | 用途 |
|---|---|
| `show ip mroute` | 全表 |
| `show ip mroute <group>` | 指定组 |
| `show ip mroute <group> detail` | 含 RPF 邻居、出接口标志、Assert |
| `show ip mroute active` | 活动状态 |
| `show ip mroute count` | 状态数（监控用） |
| `show ip mroute vrf <vrf>` | VPN 内 |
| `show ip mroute static` | 静态 mroute |

### 4.2 PIM

| 命令 | 用途 |
|---|---|
| `show ip pim interface` | 模式、DR、邻居数、hello 参数 |
| `show ip pim neighbor` | 邻居明细（DR 选举、优先级） |
| `show ip pim rp mapping` | Group→RP 映射（**最关键**） |
| `show ip pim rp-address` | 本机静态 RP |
| `show ip pim ssm range` | SSM 范围 |
| `show ip pim df` / `show ip pim df detail` | BIDIR DF 选举 |
| `show ip pim state-refresh` | PIM-DM 状态刷新 |
| `show ip pim rp-candidate` / `show ip pim bsr` | RP 候选 / BSR |

### 4.3 IGMP / MLD

| 命令 | 用途 |
|---|---|
| `show ip igmp groups [group] [detail]` | 组成员 |
| `show ip igmp interface [if]` | 接口 IGMP 状态与定时器 |
| `show ip igmp query-interval` | QI/Max RT/QRY |
| `show ip igmp snooping groups [vlan]` | 二层成员表 |
| `show ip igmp snooping mrouter` | 路由器口 |
| `show ip igmp snooping querier` | Querier |
| `show ip igmp ssm-mapping` | SSM 映射 |
| `show ipv6 mld groups` / `show ipv6 mld neighbor` | IPv6 |

### 4.4 MSDP / MBGP / MVPN

| 命令 | 用途 |
|---|---|
| `show ip msdp peer [detail]` | 对等体 + RPF + SA 计数 |
| `show ip msdp summary` | SA 汇总 |
| `show ip msdp sa-cache` | SA 缓存 |
| `show ip msdp originator` | 本机 originator-id |
| `show bgp ipv4 multicast summary` | MBGP 组播地址族 |
| `show bgp l2vpn evpn route-type 3 / 10` | EVPN 组播 NLRI |
| `show mdt data` / `show mdt default` | MVPN 隧道 |
| `show mldp neighbor` / `show mldp fec` | MLDP |

### 4.5 调试（最后手段，按范围缩小）

```cisco
debug ip mpacket                        ! 数据包级：RPF 判定、丢弃原因
debug ip mroute <group>                 ! 状态机事件
debug ip pim <detail>                   ! PIM 状态机
debug ip pim neighbor                   ! 邻居事件（Hello/DR 变化）
debug ip igmp                           ! IGMP 收发
debug ip msdp packets                   ! MSDP 报文
debug ipv6 mld                          ! IPv6
```

> **调试纪律**：先窄后宽（先加组/源过滤），先在维护窗口抓取，**不要在生产高峰开全量 debug**。

---

## 5. 综合生产案例（6 例）

### 案例 12-1：某分公司组播全部不通（跨域 + 静态 RP）

**现象**：总部与分公司之间行情组播不通，分公司本地组播正常。
**定位**：
```
show ip pim rp mapping          ! 分公司无映射
show ip msdp peer               ! peer 状态
show ip bgp ipv4 multicast summary
show ip mroute 239.1.1.1 detail
```
**根因**：MSDP peer 建立在**非直连**地址上（用 Loopback 但中间无单播路由），peer 状态 Down，SA 无法交换 → 分公司 RP 学不到源信息。
**处置**：确保 Loopback 在 IGP/BGP 中可达；peer 必须直连或至少单播可达；建立直连 peer 优先。
**复盘**：MSDP peer 的可达性是跨域组播的第一道门。

### 案例 12-2：组播时断时续（链路冗余切换后中断）

**现象**：主链路故障切换后，组播中断约 2–3 分钟才恢复。
**定位**：`show logging` 看到链路 down/up；`show ip mroute` 在切换后重新建树；对比 `show ip pim neighbor` 重建时间。
**根因**：切换后 RPF 接口变化 → 组播状态需重建；PIM 邻居与 DR 重新选举期间无转发；且 **没有组播 FRR**（只有单播 FRR）。
**处置**：部署 **组播快速重路由**（mLDP FRR / 特定平台组播 FRR）；缩短 Hello holdtime（谨慎）；把冗余链路收敛时间纳入测试。
**复盘**：**组播对链路切换的敏感度远高于单播**，冗余设计必须做"组播收敛测试"。

### 案例 12-3：同一终端组播"卡"但不丢包

**现象**：终端收到流但画面卡顿，丢包统计正常。
**定位**：`show interfaces` 显示 output queue 堆积；QoS 策略命中情况；对比单播业务。
**根因**：组播流量在出接口排队时延大（排队时延而非丢包）；或组播被限速。
**处置**：为组播配置 QoS（EF/AF 分类 + 足够的 shaping）；检查 `ip multicast rate-limit`。
**复盘**：**组播的"卡"往往是排队时延，不是丢包**，排查要看队列而不是只看 drop 计数。

### 案例 12-4：组播在不同批次的交换机上行为不一致

**现象**：部分接入交换机下终端收不到组播，替换设备后正常。
**定位**：`show ip igmp snooping groups` 在故障设备上无条目；对比软件版本与配置。
**根因**：新到货交换机的软件版本不支持某特性（如 MLD Snooping / 显式主机跟踪 / 新的组播 NLRI），或默认配置模板不同。
**处置**：统一软件版本与配置模板；在资产中记录"组播特性支持矩阵"。
**复盘**：组播对**版本与特性**敏感，设备替换必须带"组播特性核对清单"。

### 案例 12-5：业务方报"组播丢包"，实际是源端问题

**现象**：监控显示组播丢包 5%，网络侧无丢包。
**定位**：抓包在源服务器出口即已丢包/错包；组播包在源端就已损坏。
**根因**：源服务器多网卡绑定 + 组播走错误队列，或源端应用发送时未设置 IP_TTL/组播 socket 配置导致异常。
**处置**：在源端抓包定位；检查 bonding 模式与组播出接口。
**复盘**：**"组播丢包"的第一现场常常是源主机**，网络侧要先证明自己无责。

### 案例 12-6：一次变更引发大范围组播中断

**现象**：某核心设备升级后，全域组播中断。
**定位**：升级前后 `show ip pim neighbor`、`show ip pim rp mapping`、`show ip mroute` 对比。
**根因**：升级后新设备默认 `no ip multicast routing` 或 PIM 邻居因 MTU/认证变化未建立，RP 映射丢失。
**处置**：回滚；重新梳理升级 checklist（组播相关配置必须逐条比对）。
**复盘**：**组播配置的"隐性依赖"极多**（IGMP 版本、TTL、querier、静态 mroute、ACL），升级前必须做配置差异审计。

---

## 6. 组播变更检查单（Checklist）

```
□ 新增/变更的接口是否需要 PIM？模式是否正确（sparse / bidir-enable / 不启用）
□ 接口是否需要 ip multicast ttl？值是多少（AutoRP 15 / BSM 255 / 一般 255）
□ 是否新增了静态 mroute？环路分析是否完成并登记
□ RP 发现方式是否受影响（静态/AutoRP/BSR/Anycast/Embedded）？
□ 组播地址段是否与既有规划冲突（SSM 段、私有段、跨域段）？
□ QoS：组播是否需要单独 class？限速阈值是否满足？
□ ACL：新增 ACL 是否误伤 IGMP/PIM 控制报文（224.0.0.x/224.0.1.x）？
□ 二层：新增 VLAN/端口是否启用 Snooping？是否需要 querier？
□ 冗余：是否影响 DR 选举？是否需要重测组播收敛？
□ 验证：show ip pim neighbor / rp mapping / mroute / igmp groups 全部对比
□ 回滚方案是否包含组播状态清理（clear ip mroute * / clear ip pim rp mapping）？
```

---

## 7. 建立个人 Case 库的方法

1. **模板化**：每条 case 固定记录 —— 现象 / 影响范围 / 首查命令 / 根因 / 处置 / 预防；
2. **打标签**：协议层（IGMP/PIM/RP/MSDP/MVPN）、症状类（收不到/不全/闪断/重复）、场景（行情/医疗/视频/云）；
3. **回灌**：每月把新 case 归入对应章节，3 个月后即可形成团队资产；
4. **本项目已提供 76 条初始 case**（ch01–ch12），可直接作为模板库使用。

---

## 8. 自测清单

1. iPexpert 的排障四步法是什么？为什么"控制面与数据面分离"很重要？
2. 四类症状（完全收不到 / 收不全 / 时断时续 / 重复异常）各自的首查方向？
3. 五条必做的控制面命令是什么？
4. 组播"卡但不丢包"最可能的根因是什么？
5. 为什么跨域组播的第一个检查点总是 MSDP peer 与 MBGP 地址族？
6. 组播变更检查单中，哪几项最容易被忽略？

## 9. 延伸阅读

- iPexpert 全书（各章 show/debug 工具箱与 Trouble Ticket）
- Volume II Ch6（P.301–P.344）：Interdomain / PIM-TE / MVPN / VXLAN 高级排障
- Aweya Ch1.10（P.77–P.79）：组播路由体系架构（四组件模型）
- 延伸：`RFC 7761`（PIM-SM 全文，Appendix A 为报文与状态机速查）
