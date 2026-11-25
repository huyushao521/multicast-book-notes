# 第 3 章 RPF、分发树与 PIM 通用机制

> 精读来源：**Williamson Ch2（p.34–47，树与泛洪剪枝）、Ch3（p.60，DR）**、**Aweya Ch1（p.15–18）、Ch1.6（p.41–45，RPF 偏好顺序）、Ch3（p.152–160，Hello/DR Priority 选项）**
> 本章解决的问题：所有 PIM 家族共享的那部分机制——**RPF 决定"收不收"，Hello/DR/Assert 决定"谁来发、谁来回"**。

## 学习目标

1. 说清 RPF 检查表的**四条优先级**（静态 mroute → 单播 → MBGP → 缺省），以及为什么"最specific"不是唯一规则；
2. 背出 PIM Hello 的默认周期与 holdtime，说明 Hello 里 **Option 19 DR Priority** 的作用；
3. 说清 DR 选举的两级比较，以及 `DR priority 0` 的工程含义；
4. 解释 Assert 为什么必须存在（多路由器同网段重复发包），以及它的比较顺序；
5. 说清 Join/Prune 的"周期性刷新 + 抑制"模型，理解为什么 PIM 是**软状态**；
6. 能用手上命令判断"是 RPF 问题、DR 问题，还是 Assert 问题"。

---

## 1. RPF 再深入：四张表的优先级

RPF 不是简单的"查单播路由"，它是一个**按优先级回退的查询链**。Aweya 在 p.41–42 明确给出顺序：**静态组播路由（`ip mroute`）优先，其次单播路由，同源多路由时比 Metric Preference（= 管理距离），再比 Metric，最后比等价路径**。

| 优先级 | 来源 | 典型命令 | 什么时候用 |
|---|---|---|---|
| 1 | **静态 mroute** | `ip mroute 10.1.0.0 255.255.0.0 192.168.1.1` | 隧道、非对称、缺省路由场景 |
| 2 | **单播 RIB（含 MBGP 的单播表）** | IGP/静态 | 绝大多数情况 |
| 3 | **MBGP/multicast RIB**（若平台分离） | `address-family ipv4 mdt` / `ip rpf` 专用表 | MVPN、跨域 |
| 4 | **缺省路由** | `0.0.0.0/0` | 会造成"所有源都从同一口来"，需配合 `ip mroute` 修正 |

**关键点（W p.41–42）**：RPF 检查与组播路由表（mroute）是**两张独立的表**。RPF 只看"去往源的最短路径"，mroute 只看"哪些接口要发"。所以：

```cisco
show ip rpf 10.1.1.100        ! 看 RPF 用哪条路由、哪个接口
show ip mroute 239.1.1.10     ! 看 in/out 接口列表
! 两者不一致 → 丢包，且不会报错
```

**RPF 失败的判定顺序**（排障直接用）：

```text
包被丢弃
 ├─ show ip rpf <S> 无输出?            → 路由缺失（最常见）
 ├─ RPF 接口 ≠ 实际入接口?              → 不对称/ECMP/隧道
 ├─ RPF 接口 = Null?                    → 源就在本机或直连但未起 PIM
 └─ 全部正常但仍不通?                    → 转查 Assert / DR / 二层
```

---

## 2. PIM 的共同骨架

Aweya p.15 一句话点明结构：**Hello、Join/Prune、Assert 及其选项是"所有 PIM 类型共有"的**，DM/SM/BIDIR/SSM 只是"树怎么建"不同。四种报文的角色：

| 报文 | 目的地址 | 作用 | 周期/触发 |
|---|---|---|---|
| **Hello** | `224.0.0.13`（All-PIM-Routers） | 邻居发现、参数协商、DR 选举 | **30 s** 周期，holdtime **3.5×30 = 105 s** |
| **Join/Prune** | 上游邻居单播 | 请求/撤销某（S,G）或（*,G） | 触发式 + 周期性刷新（默认 60 s） |
| **Assert** | `224.0.0.13` | 同网段多路由器重复收流时选唯一转发者 | 收到重复数据触发 |
| **Register / Register-Stop** | 单播到 RP | 源 DR 把流量交给 RP（PIM-SM 专有） | 数据触发 |

> Hello 面向 `224.0.0.13`、TTL=1，**不出本网段**——所以你在跨网段抓不到 Hello，这不是配置问题。

---

## 3. Hello：PIM 的"心跳 + 能力清单"

Hello 不只是保活，它是一个**选项协商载体**。Aweya p.152–155 列出了 Hello 的选项字段，其中对现网影响最大的是：

| 选项 | 编号 | 作用 | 工程含义 |
|---|---|---|---|
| Holdtime | 1 | 邻居存活时间 | 默认 105 s；链路抖动时先看它 |
| **DR Priority** | **19** | **DR 选举权重**（PIM-SM 用） | 默认 1；`0` = 不参选 |
| Generation ID | 20 | 重启检测 | 设备重启后 GenID 变化，邻居立即重建状态 |
| LAN Delay | 2 | 共享网段传播时延（prune 延迟） | 默认 500 ms |
| Override Interval | 3 | 覆盖 Join 的抖动 | 默认 2500 ms |
| State Refresh Capable | 6 | **PIM-DM 状态刷新能力**（第 4 章） | DM 域内必须一致，否则 3 分钟抖动 |

```cisco
show ip pim neighbor                  ! Uptime/Expires，Expires 应≈105s
show ip pim neighbor 10.1.1.2 detail  ! 看 DR priority、GenID
debug ip pim hello                    ! 抓 Hello 内容（谨慎，CPU 高）
```

**排障口诀**：`show ip pim neighbor` 为空 → 先查"接口有没有 `ip pim sparse-mode`"，再查"对端有没有发"（`show ip pim interface` 的 `Nbr Count`），最后才查 ACL/CoPP。**PIM 不发 Hello 的接口，永远不会建邻居，也就永远不会转发组播**。

---

## 4. DR 选举：为什么它决定"谁去注册"

每个网段选一台 DR，职责不同（W p.60 明确指出"DR 由组播路由协议选出，具体机制取决于协议"）：

| 场景 | DR 的职责 |
|---|---|
| 有接收者 | 代表网段向上游发 **Join**（IGMP 报告 → PIM Join） |
| 有源 | 代表网段向 RP 发 **Register**（PIM-SM） |
| 共享网段 | 避免每台路由器都向上游建树 |

**选举规则（PIM-SM）**：

```text
1) DR Priority 高者胜（默认 1；0 = 弃权）
2) Priority 相同 → IP 地址高者胜
3) 收到更高 Priority/更高 IP 的 Hello → 让位
```

**`DR priority 0` 的工程用法**：把某台路由器设为"永不参选"，常用于 **Anycast RP / MSDP 场景的 RP 侧**避免抢 DR，或让三层交换机（只是转发）不参与。

**双 DR 的典型症状**：两个上游同时收到 Join，形成两条并行树 → 接收者收到**双份流**（视频花屏、TCP 应用重复响应）。`show ip pim neighbor` 里两台都是 DR，或 `show ip pim interface` 的 DR 字段不一致，就是它。

---

## 5. Assert：同网段"抢活干"的仲裁

**为什么需要**：一条共享链路（如两台路由器都接同一 VLAN），若两台都从上游收到同一（S,G），都会往下游转发 → 重复包。Assert 就是**在同一网段内选唯一转发者**。

**比较顺序**（与单播选路同源，Aweya p.41–42 的偏好思想）：

```text
1) Metric Preference（到源的路由管理距离）—— 小者胜
2) Metric（到源的度量）—— 小者胜
3) IP 地址 —— 大者胜
败者：把该接口置为 Assert Loser，停止转发，但保留状态
```

```cisco
show ip mroute 239.1.1.10          ! 看 (S,G) 的 flags: 出现 "A" 表示 Assert
debug ip pim assert                 ! 观察谁赢
show ip pim interface <int>         ! 看 DR / Assert 相关计数
```

**Assert 的隐性代价**：败者并不删状态，只是"压住不发"；一旦胜者链路失效，要等 Assert 超时或重新收敛才切换（秒级抖动）。所以在**双上联共享 VLAN** 的设计里，Assert 会频繁发生，必须确认两条路径的 metric 有明确差异。

---

## 6. Join/Prune：软状态与"周期性刷新"

PIM 没有"连接建立"概念，全是**软状态**：

```text
收到 IGMP Report → DR 向上游发 Join（触发式，立即）
之后每 60 s 重发一次 Join（刷新）
3 × 60 s（180 s）无刷新 → 状态超时删除
收到 Prune → 起 210 s（DM）/ 立即生效（SM 的显式 Prune）
```

**为什么要周期刷新**：拓扑变化、设备重启、链路切换都靠"刷新不上就超时"来自愈。代价是**收敛慢**——这就是案例 1-6"切换后 8 分钟才恢复"的根源：Join 刷新周期 + RPF 重校验周期叠加。

**Join/Prune 的抑制**：同一网段只有 DR 发 Join，其他路由器听到 Join 后不再重复发（抑制），否则上游会被 N-1 份冗余 Join 打爆。

---

## 7. 拓扑图

![RPF 检查与 RPF 失败的四种形态](../../diagrams/d05-rpf.svg)

**图 3-1 RPF 检查**：R3 的 RPF 接口必须朝 R2。单播路由改成走 R4 后，组播被静默丢弃——**症状是"没有报错、就是不通"**。

![源树、单向共享树与双向共享树](../../diagrams/d06-trees.svg)

**图 3-2 三种分发树对照**：（S,G）源树最短但状态多；（*,G）共享树状态少但绕 RP；双向树无源注册。DR/Assert 决定"谁在这棵树上转发"，树形本身决定"路径长短"。

---

## 8. 工程案例（8 例）

### 案例 3-1：`show ip pim neighbor` 空的三种原因，逐层定位

**现象**：新开局两台路由器直连，PIM 邻居起不来，组播全断。

**定位**
```cisco
show ip pim interface              ! 看 PIM 是否 enable、Nbr Count
show ip pim neighbor               ! 空
show ip interface brief            ! 接口 up/up
show run interface Gi0/0 | include pim
```
**三类根因**（按出现频率）：① 接口只配了 `ip multicast-routing` 但漏了 `ip pim sparse-mode`；② 中间是**二层交换机 + 未放行 224.0.0.13**（少见，因 TTL=1 且多为硬件转发）；③ 接口被 `ip pim passive`（只收不发）或 `ip pim sparse-mode` 被 `no` 掉。

**处置**：补齐接口模式；`ip pim passive` 只用于"有源/有接收者但不需要建邻居"的边缘口，误配就是"永远没邻居"。

**复盘**：PIM 邻居是组播的**第一道门**。开局验收顺序：接口 up → PIM enable → 邻居 up → IGMP 组表 → mroute。

### 案例 3-2：双 DR 导致视频双份、花屏

**现象**：某 VLAN 内两台三层交换机，接收端花屏，抓包显示**同一 RTP 序号出现两次**。

**定位**
```cisco
! 两台设备
show ip pim interface vlan 100     ! 两台都显示 DR = 本机
show ip pim neighbor              ! 两台互为邻居，DR Priority 都是 1
```
**根因**：两台设备 IP 不同，但**其中一台的 Hello 里 DR Priority 被配成了 2**（历史遗留），另一台是默认 1 —— 理论上高者胜，但该平台在 **Hello 发送间隔内**两台都认为自己是 DR，且上游链路是负载分担，导致两条树并存。

**处置**：统一 DR Priority（都设 1，让 IP 高者胜），或显式把其中一台设 `ip pim dr-priority 0`；同时确认上游到源的路径唯一。

**复盘**：**DR 必须是"设计出来的"，不能是"碰出来的"**。设计文档里应写清每个共享网段的 DR。

### 案例 3-3：Assert 霸占接口，主链路闲置

**现象**：双上联（主 100G / 备 10G）接同一 VLAN，组播一直走 10G 备链路，主链路空载。

**定位**
```cisco
show ip mroute 239.1.1.10        ! 出接口是备链路
debug ip pim assert              ! 看到主链路侧为 Loser
show ip route 10.1.1.100         ! 备链路 metric 更小（意外）
```
**根因**：IGP metric 配置错误，备链路到源的 metric 反而更小 → Assert 判定备链路胜；属于"配置错误被 Assert 忠实地执行了"。

**处置**：修正 IGP metric；或对组播源网段用 `ip mroute` 固定主链路（慎用，会掩盖问题）。

**复盘**：Assert 的结果**永远等于单播选路的结果**。看到"组播走错链路"，先去查单播路由，别查 Assert。

### 案例 3-4：静态 mroute 掩盖了路由问题，切换后彻底断

**现象**：某分支用 `ip mroute` 指向上游，长期正常；上游改造后组播全断，且**删掉静态 mroute 反而恢复**。

**定位**
```cisco
show ip rpf 10.1.1.100           ! 用的是静态 mroute 指向旧上游
show ip route 10.1.1.100         ! 单播已改走新上游
show run | include ip mroute
```
**根因**：静态 mroute 优先级最高，把新拓扑"钉"在旧路径上；旧上游已不再转发。

**处置**：删除或更新静态 mroute；若必须保留（如隧道场景），加监控告警（对 `show ip rpf` 结果做定期比对）。

**复盘**：**静态 mroute 是止血药，不是长期方案**。凡是加了 `ip mroute` 的地方，必须登记"为什么加、什么时候能删"。

### 案例 3-5：Hello holdtime 抖动导致邻居反复重建

**现象**：`show ip pim neighbor` 的 Uptime 不断归零，组播每几十秒断一次；CPU 正常。

**定位**
```cisco
show ip pim neighbor              ! Uptime 30–100 s 波动
show interface Gi0/1 | include "input errors|CRC|drops"
show policy-map control-plane     ! CoPP 对 PIM 限速
```
**根因**：链路有 CRC 错误（光衰），或 CoPP 把 PIM Hello 限速到很低 → Hello 丢失 3 次以上即超时（105 s）。本例是**光模块收光功率临界**，Hello 周期性丢失。

**处置**：更换光模块/清洁尾纤；CoPP 为 PIM 单独放行（建议 ≥100 pps，含 Join/Prune 突发）。

**复盘**：组播邻居抖动几乎总是**物理层或控制面限速**，不是 PIM 配置。

### 案例 3-6：Join 刷新被抑制，链路切换后 3 分钟才恢复

**现象**：主备切换后，接收者侧要 3 分钟才有画面。

**定位**
```cisco
show ip mroute 239.1.1.10        ! (S,G) 存在但 OIF 为空，Expires 逐渐减少
show ip pim neighbor             ! 新邻居已 up
```
**根因**：共享网段内只有 DR 发 Join（抑制），切换期间 DR 角色未及时转移；新 DR 要等**下一次 Join 刷新（60 s）** 甚至更久才发，叠加状态超时（180 s）表现为 3 分钟。

**处置**：让 DR 选举更快响应（`ip pim dr-priority` 明确主备，配合 BFD 快速感知）；必要时缩短 `ip pim query-interval`（影响面大，慎用）。

**复盘**：**PIM 是软状态协议，收敛以"秒到分钟"计**。业务 SLA 要求秒级时，必须靠"拓扑快速感知 + 状态快速重建"（BFD + 稳定 RPF）组合。

### 案例 3-7：源直连本机，RPF 接口是 Null

**现象**：本机既是源（推流服务器）又是组播路由器的场景，其他网段收不到流。

**定位**
```cisco
show ip rpf 10.1.1.100     ! 输出 RPF interface: Null, RPF neighbor: 0.0.0.0
show ip mroute 239.1.1.10  ! Incoming interface: Null（正常，源在本机）
show ip mroute 239.1.1.10 count   ! 无 (S,G) 转发计数
```
**根因**：源在本机时 RPF 为 Null 是**正常**的，问题在别处——该平台要求对本地源显式 `ip pim register-source` 或先把流注入环回口，否则（S,G）不生成。

**处置**：配置 `ip pim register-source Loopback0`；确认 `ip multicast-routing` 与接口 PIM 均已启用；用 `show ip mroute 239.1.1.10 active` 确认有流量流入。

**复盘**：**"RPF 是 Null"不等于故障**。源在本机、源直连、或使用 `ip mroute 0.0.0.0 0.0.0.0` 时都可能是 Null，要结合"是否本机源"判断。

### 案例 3-8：PIM 邻居 up 但组播不通——ACL 拦了 IGMP 报告

**现象**：邻居正常、mroute 有（*,G）、上游也有流，但下游主机收不到。

**定位**
```cisco
show ip igmp groups 239.1.1.10     ! 有表项
show ip mroute 239.1.1.10          ! OIF 包含主机所在接口
show ip interface Gi0/2 | include "multicast"
show ip access-lists              ! 检查 interface ACL 是否 permit igmp
```
**根因**：接口入方向 ACL 只放行了 UDP/组播数据，**未放行 IGMP（协议号 2）**，主机 Report 到不了路由器；但 mroute 里的（*,G）是**别的网段**的成员建的，OIF 恰好包含该接口（因为该口还有别的成员），导致"看起来应该能收到"。

**处置**：ACL 增加 `permit igmp any any`（或 `permit 2 any any`）。

**复盘**：**组播的"数据面"和"控制面"是两条 ACL 路径**。数据不通先查控制面是否被 ACL 拦，别只查数据 ACL。

---

## 9. 自测清单

1. RPF 的四级优先顺序？为什么静态 mroute 会"掩盖"单播路由问题？
2. PIM Hello 的目的是什么？为什么它不出本网段？
3. DR Priority 与 DR 的 IP 地址，比较顺序是什么？`dr-priority 0` 用来做什么？
4. Assert 的比较顺序？败者会删除状态吗？
5. PIM 为什么是软状态协议？Join 刷新周期与超时分别是多少？
6. `show ip rpf` 显示 Null 一定是故障吗？举两个正常场景。
7. 双 DR 会造成什么现象？如何确认？
8. 组播走错链路（主备颠倒），应该先查 Assert 还是单播路由？
9. PIM 邻居反复重建，最可能是哪两类原因？
10. 接口 ACL 只放行 UDP 会怎样？

---

## 10. 原文精读索引

> 纸面页码：Williamson = PDF 页 − 22；Aweya = PDF 页 − 21（均经 `tools/srcgrep.py` 实测命中核对）。

| 知识点 | 书/节 | 纸面页 | 原文可核对要点 |
|---|---|---|---|
| Hello/Join-Prune/Assert 为 PIM 共有 | Aweya Ch1 | p.15 | "Hello and Assert, along with their Options, are common to all PIM protocol types" |
| 泛洪-剪枝与两种模型 | Aweya Ch1 | p.16–18 | PIM-DM "implicit join model"、"flood-and-prune"；SM 为显式 join |
| 源侧 DR 概念 | Aweya Ch1 | p.18, p.33 | "the source's Designated Router (DR)" |
| RPF 偏好顺序 | Aweya Ch1.6 | p.41–42 | 静态组播路由 → 单播；Metric Preference(AD) → Metric → 等价 |
| DR 每网段选举 | Williamson Ch3 | p.60 | "The multicast routing protocol selects the DR… depends on the protocol in use" |
| Flood and Prune 行为 | Williamson Ch2 | p.46–47 | Prune 把接口置 Pruned 状态；Prune 有超时，超时后重新泛洪 |
| PIM 报文格式 | Aweya Ch3 | p.152 | Figure 3.4–3.6（Hello/Join-Prune/Assert/Register） |
| **DR Priority 选项（Type 19）** | Aweya Ch3 | p.154–155 | "Option Type 19: DR Priority"、32 位无符号数 |
| Hello 默认定时器 | RFC 4601 | — | 30 s / holdtime 105 s（3.5×）；本书未逐字给出，按标准标注 |

---

## 11. 延伸

- 下一章：PIM-DM（把"泛洪-剪枝"落到报文级）
- 标准：RFC 4601（PIM-SM）、RFC 3973（PIM-DM）、RFC 2362（旧版 SM）
- 命令速查：`show ip rpf` / `show ip pim neighbor` / `show ip pim interface` / `debug ip pim assert`
