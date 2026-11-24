# ch02 IGMP 与二层组播（IGMP Snooping / Proxy / Fast Leave）

> **来源**：Aweya Ch2（P.86–P.167，IGMPv1/v2/v3、Snooping、Proxy、Query Solicitation）、Williamson Ch3/Ch14–15、P.413–P.470（IGMP Snooping 与 CGMP）、iPexpert Ch2（P.2-1–2-26）
> **配图**：[D03 IGMP 交互](../diagrams/d03-igmp-basic.svg)｜[D04 Snooping 效果](../diagrams/d04-snooping.svg)

---

## 学习目标

1. 说清 IGMPv1/v2/v3 的报文类型、定时器与行为差异，并判断该用哪一版；
2. 解释 Querier 的选举机制与"为什么必须有 Querier"；
3. 解释 IGMP Snooping 的工作原理、Report Suppression、Fast Leave 与 Querier 的关系；
4. 能在现网选择并配置 IGMP Snooping / PIM Snooping / IGMP Proxy / Query Solicitation；
5. 掌握 IGMP 类故障的定位命令与常见根因。

---

## 1. IGMP 报文总览

| 版本 | 报文 | 方向 | 作用 |
|---|---|---|---|
| v1 | **Membership Query**（`130`） | Querier → 全体 | 问"有没有人要这个组" |
| v1 | **Membership Report**（`131`） | 主机 → Querier | 我要加入 G |
| v2 | Query（`130`，含 Max Resp Time） | Querier → 全体 | 同 v1，但带响应时间窗 |
| v2 | **Leave Group**（`132`） | 主机 → Querier | 我要走（触发具体查询） |
| v2 | Report（`131`） | 主机 → Querier | 报告成员关系（可抑制） |
| v3 | Membership Query（`130`，带 QRV 与 S/QRV） | Querier → 全体 | 支持 General / Group-Specific / Group-and-Source-Specific |
| v3 | Membership Report（`131`，含 Record Type） | 主机 → Querier | 支持 `IS_INCLUDE`/`IS_EXCLUDE`/`TO_IN`/`TO_EX` |
| v3 | **IGMPv3 Report 的特殊用法** | 主机 → 路由器 | `IGMPv3 Report` 也可作为**离开通知**（`TO_IN` 空源列表） |

### 1.1 IGMPv1

- 只有 Query 与 Report；
- **无 Leave 消息** → 主机离开后，路由器必须等 **3× Query Interval（约 3 分钟）** 才会把组从表项中删除 → "幽灵流量"；
- **Report 抑制机制**：同一子网内多个主机加入同组时，只有第一个主机发 Report，其余主机**不发**，减少流量（也造成"交换机看不到全部成员"，需靠 Snooping 的 Report 抑制计数补偿）。

### 1.2 IGMPv2

改进三点：

1. **Leave Group 消息**：主机离开立即通知，路由器随即发 Group-Specific Query 确认（无成员则删表项）；
2. **Group-Specific Query**：路由器向 224.0.1.102（G）发送，只问该组还有没有人；
3. **Report 抑制**：同一组同一时刻只允许一个主机发 Report（抑制窗口由 Query 携带的 Max Response Time 决定，默认为 10s）。

**关键定时器（默认值）**：

| 定时器 | 默认 | 含义 |
|---|---|---|
| Query Interval (QI) | 125 s | Querier 发送 General Query 的间隔 |
| Max Response Time | 10 s | 主机回复 Report 的随机抖动上限 |
| Group Membership Interval | 260 s ≈ 2×QI+10 | 组成员老化时间 |

### 1.3 IGMPv3

核心是**源过滤**与**精确订阅**：

- Report 携带 `Record Type`：`IS_INCLUDE`（我要收 S1,S2）、`IS_EXCLUDE`（我要收"除 S3 外所有源"）、`TO_IN`、`TO_EX`；
- 支持 **SSM**：`IGMPv3 Report (G,S)` 直接告诉路由器"只要 S 的这个组" → 不需要 RP，天然防伪源；
- 主机可**一次报文完成加入与退出**（你的笔记已记录此点）；
- Query 中带 **QRV（Querier Robustness Variable）**：接收端用它参与 Querier 选举——**数值大的优先**（v3 的选举规则与 v1/v2 的"IP 小者胜"相反！）。

> **版本兼容坑**：IGMPv2 主机无法参与 v3 的 QRV 选举，因此混合版本环境下 Querier 选举会出现"v2 主机不支持 QRV"的兼容问题（RFC 3376 有专门的兼容处理）。

---

## 2. Querier：谁在问？

![IGMP 交互](../diagrams/d03-igmp-basic.svg)

**为什么要 Querier**：二层交换机做 IGMP Snooping 后，需要知道"这个 VLAN 里谁是路由器"，才能把组播从路由器口转发到成员口。Querier 就是这个"锚点"。

**选举规则**：

- **IGMPv1/v2**：所有启用了组播路由的路由器都发 Query，**IP 地址最小者**成为 Querier；
- **IGMPv3**：比较 QRV，**QRV 大者**胜；QRV 相同比 IP，小者胜；
- 选举失败风险：若 Querier 所在设备故障且无人接替，Snooping 表项将因老化被清空 → 组播中断。

**Querier 与 PIM DR 的关系**：PIM DR 本身就发送 IGMP Query（因为 PIM DR 需要维护 IGMP 成员关系以做最后一跳与 SPT 切换）。因此在纯 PIM 网络中，通常**不需要额外配置 querier**；只有当 VLAN 内**没有路由器的 IGMP 接口**（如纯二层旁路、嵌入式设备）时，才需要 `ip igmp snooping querier`。

```cisco
! 二层交换机上做 Querier（指定地址与版本）
ip igmp snooping querier 10.1.1.1
ip igmp snooping vlan 10
ip igmp snooping vlan 10 querier 10.1.1.1   ! 或用 loopback 地址
```

---

## 3. IGMP Snooping：二层组播的核心

![Snooping 效果](../diagrams/d04-snooping.svg)

**工作原理**：

1. 交换机监听所有经过的 IGMP 报文；
2. 收到 **Report** → 在"组播组 + 端口"表项中加入该端口（成员口）；
3. 收到 **Leave**（v2）→ 标记该端口为"待剪除"，并**由 Querier 发 Group-Specific Query**；若在响应窗口内无 Report，则剪除该端口；
4. 收到 **Query** → 记录"路由器口（mrouter port）"，组播从该口进来时正常转发；
5. 组播包到达时：**仅在 mrouter 口 + 成员口转发**，其余端口剪除。

**Report Suppression 的二层含义**：一个 Report 来自某端口，交换机把该端口加入成员表；其他主机再发相同 Report 会被抑制（因为交换机做了抑制转发）。因此交换机的成员端口计数可能小于实际主机数——**排查时不要以端口数当主机数**。

**Fast Leave（快速离开）**：

- 收到 Leave 后**立即剪除该端口**，不做 Group-Specific Query 确认；
- 前提：交换机知道"该端口后面只有这一个主机"（**explicit host tracking**，即交换机通过 `show ip igmp snooping groups` 学习到端口上的主机数量）；
- **风险**：若一个端口后面接了 IPTV 机顶盒（STB）盒子 + 机顶盒后面还有电视/其他共享设备，直接剪除会造成**其他设备断流**。

```cisco
! Fast Leave 配置（全局或按组）
ip igmp snooping fast-leave
ip igmp snooping vlan 10 fast-leave
! 明确跟踪端口主机数（用于确认哪些端口可以 fast leave）
ip igmp snooping explicit-host-tracking vlan 10
```

**相关技术对比**：

| 机制 | 工作层 | 特点 |
|---|---|---|
| **IGMP Snooping** | L2 | 标准做法，按 IGMP 报文学习组播成员 |
| **PIM Snooping** | L2 | 监听 PIM Join/Prune 来学习组播转发关系，比 IGMP Snooping 更精确（知道上游是谁），但需 L3 设备参与 |
| **CGMP**（Cisco 私有） | L2 | 老方案，交换机与 CGMP 服务器通信，现已基本被 IGMP Snooping 取代 |
| **IGMP Proxy** | L3 设备 | 见下节 |

---

## 4. IGMP Proxy 与 Query Solicitation

### 4.1 IGMP Proxy

**场景**：接入交换机不支持 Snooping（或非组播感知设备），需要在 L3 网关（如路由器、无线 AC、防火墙）上"代理"主机完成成员管理。

- 网关**代替主机**发 IGMP Report（对上游），并**代替路由器**向主机发 Query；
- 网关自己维护"哪些主机要哪个组"的本地表。

```cisco
ip igmp proxy
interface Vlan10
 ip igmp proxy
```

**代价**：网关成为单点；组播数据仍需经网关转发（除非网关做组播路由）。

### 4.2 IGMP Query Solicitation（Aweya 2.8）

**场景**：接入交换机做 Snooping，但 VLAN 内没有路由器（数据来自外部组播源或运营商专线）。

**做法**：网关/路由器**自己发** IGMP Query Solicitation，让交换机误以为它是 Querier，从而保持 mrouter 口并维持成员表。

```cisco
interface Gi0/1
 ip igmp query-solicitation
```

---

## 5. 排障命令速查（iPexpert Ch2）

```cisco
! 二层侧
show ip igmp snooping groups            ! 组 → 端口映射（成员口/标志位）
show ip igmp snooping groups vlan 10
show ip igmp snooping mrouter            ! 路由器口列表
show ip igmp snooping querier            ! 当前 Querier 是谁
show ip igmp snooping vlan 10 detail     ! 每端口主机明细（explicit host tracking）

! 三层侧
show ip igmp groups                      ! 路由器上的 IGMP 成员表
show ip igmp groups 239.1.1.1 detail
show ip igmp interface Gi0/1
show ip igmp query-interval              ! QI / Max Response Time / QRY

! 调试（慎用，会很吵）
debug ip igmp
debug igmp packets
```

---

## 6. 生产案例（8 例）

### 案例 2-1：主机加入组播但交换机无成员表项

**现象**：PC 加入 `239.1.1.1`，PC 能收到流，但同 VLAN 另一台 PC 收不到；交换机上查不到该组的成员口。
**定位**：`show ip igmp snooping groups vlan 10` 为空；`show ip igmp snooping mrouter` 为空。
**根因**：VLAN 内**没有 Querier**，交换机从未收到 Query，因此不认为任何口是 mrouter 口，也不建立老化计时器；或交换机上未启用 `ip igmp snooping vlan 10`。
**处置**：在汇聚层路由器上确认已有 Query（`debug ip igmp`）；若该 VLAN 无路由接口，则在交换机上配置 `ip igmp snooping querier`。
**复盘**：每个承载组播的 VLAN 必须有 Querier（路由器或静态 querier）。

### 案例 2-2：主机离开后组播仍在占用带宽

**现象**：用户下线后，其端口仍在接收组播，交换机端口流量不降。
**定位**：`show ip igmp snooping groups` 中该端口带 `L`（leave）标志但未消失；`show ip igmp snooping querier` 显示 querier 为 `0.0.0.0`。
**根因**：IGMPv1 主机（无 Leave）或 Querier 缺失 → 只能等待老化（3×QI ≈ 6 分钟）。
**处置**：终端统一升级到 IGMPv2/v3；确认 Querier 存在。
**复盘**：终端 IGMP 版本不一致是组播"幽灵流量"的常见根因，必须纳入资产检查项。

### 案例 2-3：Fast Leave 导致同端口其他设备断流

**现象**：某 IPTV 端口用户拔线重启后，机顶盒正常但同 IPTV 共享的其他设备（如机顶盒后接的终端）断流。
**定位**：交换机日志有 `IGMP_FAST_LEAVE`；该端口下挂着多个 MAC。
**根因**：开启了 Fast Leave，但该端口并非"单主机"（IPTV 场景常见"STB+PC 共享"或串接设备）。
**处置**：关闭该 VLAN 的 fast-leave，或用 explicit host tracking 精确配置。
**复盘**：Fast Leave 只在"端口=单主机"或"已确认设备独占"的场景使用。

### 案例 2-4：交换机 CPU 被 IGMP 报文打满

**现象**：某接入交换机 CPU 占用 80%+，业务时延抖动。
**定位**：`show processes cpu sorted` 显示 `IP Input` 居首；`debug ip igmp` 显示大量 IGMP 报文。
**根因**：大量主机频繁发 IGMP Report（如视频客户端异常重连），或存在 **IGMP 报文环路/风暴**（两台设备间互发 Query）。
**处置**：配置 `ip igmp snooping` 抑制多余 Report；对不可信端口做 IGMP 过滤（ACL 只允许 224.0.0.1/22 与必要组）。
**复盘**：IGMP 也是可被攻击的放大面，需在边界做限速。

### 案例 2-5：主机报 IGMP 但路由侧无组成员

**现象**：PC 抓包能看到 IGMPv3 Report，但 `show ip igmp groups` 空。
**定位**：对比 `show ip igmp groups` 与 `show ip igmp interface`；检查该接口是否 `ip pim sparse-mode`；检查 `ip igmp` 是否被 `ip igmp access-group` 过滤。
**根因**：接口未启用 PIM；或接口上配置了 `ip igmp ssm-mapping` 但主机发送的是 `IS_EXCLUDE`（IGMPv2 语义），SSM 段不匹配。
**处置**：接口配置 `ip pim sparse-mode`；核对 SSM range 与映射表。
**复盘**："主机发了 Report"≠"路由器收下"，中间还有接口 ACL、IGMP 版本、SSM 范围三道门。

### 案例 2-6：跨 VLAN 的组播在三层交换机上不通

**现象**：同 VLAN 正常，跨 VLAN 不通。
**定位**：`show ip igmp groups` 在 SVI 上有成员；`show ip mroute` 无条目或 RPF 失败。
**根因**：SVI 上未启用 `ip pim sparse-mode`；或 SVI 到源的单播路由缺失导致 RPF 失败。
**处置**：`interface Vlan10 / ip pim sparse-mode`；补齐到源的路由（必要时静态 mroute）。
**复盘**：组播 VLAN 间的转发依赖 **SVI 上的 PIM + 到源的路由**，缺一不可。

### 案例 2-7：二层使用 PIM Snooping 后反而不通

**现象**：改造前组播正常，改成 PIM Snooping 后部分业务不通。
**定位**：`show ip igmp snooping groups` 与 `show ip pim snooping` 对比，发现部分组在 IGMP Snooping 表里有、PIM Snooping 表里没有。
**根因**：PIM Snooping 需要设备能收到 PIM Join/Prune 并解析出上游口；若 PIM 报文被 ACL 过滤或该 VLAN 内无 PIM 邻居，则无法建立条目。
**处置**：放行 PIM 协议（224.0.0.13），或回退到 IGMP Snooping。
**复盘**：PIM Snooping 不是 IGMP Snooping 的"升级版"，二者依赖不同报文，改造需重新验证。

### 案例 2-8：无线终端加入组播后频繁掉线

**现象**：Wi-Fi 终端订阅组播后，AP 上有组播流量但客户端看视频卡顿。
**定位**：`show ip igmp snooping groups vlan <无线VLAN>` 发现终端 MAC 不在成员表；检查 AP 是否有 "multicast optimization / IGMP snooping" 选项。
**根因**：部分 AP/控制器默认对组播做 **IGMP snooping 剪枝**，或 AP 自身不做组播转发（需在 WLAN 配置中启用 multicast）。
**处置**：在控制器上启用组播直传/组播优化，或对无线 VLAN 关闭 AP 侧剪枝。
**复盘**：无线是组播的"隐形黑洞"，PoC 必须覆盖无线接入。

---

## 7. 自测清单

1. IGMPv1 主机离开组后，为什么组播流量还会持续约 3 分钟？
2. IGMPv3 的 Querier 选举规则与 v1/v2 有何不同？为什么会出现兼容问题？
3. Report Suppression 对交换机成员表项计数有什么影响？为什么 `show ip igmp snooping groups` 的端口数不等于主机数？
4. 什么条件下 Fast Leave 是安全的？
5. IGMP Proxy 与 IGMP Snooping 分别在哪一层、解决什么问题？
6. `ip igmp query-solicitation` 什么时候必须配？

## 8. 延伸阅读

- Aweya Ch2.3–2.10（P.87–P.167）：IGMPv1/v2/v3 报文与状态机、IGMP Snooping、IGMP Proxy、Query Solicitation、Fast Leave
- Williamson Ch14（P.408–P.442）：IGMP Snooping 完整过程、CGMP、交换机泛洪抑制
- Williamson Ch15（P.444–P.470）：NBMA 上的组播（伪广播、PIM NBMA 模式）
- iPexpert Ch2（P.2-1–2-26）：IGMP 排障场景与命令工具
- 延伸：`RFC 1112`（IGMPv1）、`RFC 2236`（IGMPv2）、`RFC 3376`（IGMPv3）
