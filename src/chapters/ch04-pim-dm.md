# ch04 PIM-DM 与 PIM-SDM（洪泛剪枝模型）

> **来源**：Williamson Ch6（原理）/ Ch10（配置）/ Ch13（DVMRP 互操作，P.352–P.404）、Aweya Ch4（P.205–P.240）、iPexpert Ch3（PIM-DM）、Ch5（PIM-SDM）
> **配图**：[D07 PIM-DM 洪泛与剪枝](../../diagrams/d07-pim-dm.svg)

---

## 学习目标

1. 解释 PIM-DM 的"先泛洪后剪枝"模型，与 ASM/SM 的差异；
2. 说清 (S,G) 状态的建立、剪枝、Graft 与 State-Refresh 机制；
3. 理解 PIM-SDM（稀疏-稠密混合）的自动回落机制与适用场景；
4. 掌握 PIM-DM 排障命令与典型故障；
5. 判断一个业务该用 PIM-DM、PIM-SDM 还是 PIM-SM。

---

## 1. 为什么还需要 PIM-DM

PIM-DM 是**最原始**的组播协议（DVMRP 的简化版），设计前提是"**接收者密集分布在全网**"。

| 维度 | PIM-DM | PIM-SM |
|---|---|---|
| 初始行为 | **先泛洪**全网，再剪除无用分支 | 从 RP 开始**按需**建树 |
| 状态 | 只有 `(S,G)`，无共享树 | `(*,G)` + `(S,G)` |
| 需要 RP | 否 | 是 |
| 源注册 | 无 | Register |
| 收敛速度 | 慢（先泛洪后剪） | 快（按需） |
| 适用 | 源稀疏、接收者密集（如企业网内"全网都收"的培训流） | 通用 |

**当前现网定位**：PIM-DM 基本只出现在以下场景：
1. **遗留网络**（老设备、老终端、老业务）；
2. **与 DVMRP 互联**（Williamson Ch13 专门讲这个）；
3. **PIM-SDM 模式**：在 PIM-SM 域的"稀疏侧"自动回落。

> 实战建议：新建组播网络一律用 PIM-SM/SSM；PIM-DM 只在"必须兼容"的场景使用，并且要在设计文档中说明理由。

---

## 2. PIM-DM 核心流程（Aweya 4.8）

### 2.1 初始泛洪

1. 源发包，DR 收到后检查 RPF 接口，**从所有其他接口泛洪**；
2. 每台下游路由器收到后，若 RPF 检查通过且**没有该 (S,G) 状态**，则：
   - 建立 `(S,G)` 状态；
   - 若该接口上**无成员**（无 IGMP 成员、无下游 (S,G)）→ 向上游发送 **Prune**；
   - 若有成员 → 继续泛洪。

### 2.2 剪枝消息（Prune）

- Prune 携带 **Prune State Refresh（PSR）位**：`1` = 希望上游发 State-Refresh（"别再洪泛了"）；`0` = 希望上游继续泛泛（默认，因上游可能还有其他源）。
- **Prune Override**：若某条链路是 **点到点链路**且两端都是 PIM 路由器，上游收到 Prune 后**不会剪除该链路**（因为链路上可能有其他路由器需要这条 flooded 树）→ 这是 PIM-DM 在点到点网络上的"洪泛保留"优化。

### 2.3 Graft 机制

被剪掉的支路上有新接收者出现时，需要**重新接入**：

```
接收侧 → 上游: Join（携带该 (S,G) 的 Graft）
上游 → 接收侧: Graft-Ack（确认）
```

- Graft 沿树上行传播直到源侧 DR；
- 中间路由器如果因为 State-Refresh 已删除状态，则重新建立；
- **Graft 风暴风险**：多个下游同时 Graft → 上游需用 **Graft 抑制/合并机制**。

### 2.4 State-Refresh 机制

**问题**：PIM-DM 的洪泛是"周期性重来"还是"记忆型"？答案是记忆型——状态保存在路由器上。但如果上游重启或状态丢失，需要重新洪泛。

**State-Refresh 报文**：

- 周期性地沿树向下发，带 `(S,G)` 与**跳数度量**；
- 下游收到后：刷新状态老化时间、确认路径正确；
- 若收到的度量与本地不符 → 说明路径变化 → **删除旧状态并重新洪泛**。

关键参数：

```cisco
ip pim state-refresh interval 60      ! 发送周期（秒）
ip pim state-refresh ttl 255           ! State-Refresh 的 TTL
```

### 2.5 Assert in PIM-DM

与 PIM-SM 的 Assert 类似，但比较维度是 **(S,G) 的跳数度量**（Aweya 4.9）：多路访问网段上离源最近的路由器成为 Assert Winner，避免重复转发。

---

## 3. PIM-SDM（稀疏-稠密混合，Williamson Ch5/10、iPexpert Ch5）

**动机**：真实网络常常"大部分区域稀疏（只有少数接收者），少部分区域稠密（大量接收者）"。

**PIM-SDM 的机制**：

1. 默认按 **PIM-SM** 运作（有 RP，走共享树）；
2. 当 RP 上收到某源的 **Register** 但该源没有对应的 `(S,G)` 共享树状态时（说明该源所在区域是"稠密"的），该区域**自动切换到 PIM-DM 行为**：源侧直接向全网泛洪；
3. 稠密区与稀疏区之间通过 **PIM-DM/PIM-SM 边界**协调（Williamson Ch10 有专门的边界配置）。

```cisco
! 稀疏-稠密边界路由器上的配置
ip pim sparse-dense-mode
interface Gi0/1
 ip pim sparse-dense-mode
```

**代价**：

- 边界路由器上需要 **MSDP** 来交换跨域的源信息；
- 复杂度显著上升，状态量增加。

> 现实中 **PIM-SDM 已很少使用**，主流是纯 PIM-SM / SSM。阅读本书主要是理解其"边界"与"回落"思想。

---

## 4. 与 DVMRP 的互操作（Williamson Ch13）

DVMRP（Distance Vector Multicast Routing Protocol）是老牌组播协议，历史上用于 MBone。

**关键概念**：

- **DVMRP Distance**：到源的跳数度量，用于 Assert 与剪枝决策；
- **Distance Offset（偏移）**：允许在边界对度量做偏移，避免 DVMRP 域与 PIM 域之间出现度量冲突；
- **PIM-DVMRP 边界**：DVMRP 域与 PIM 域互联时用隧道（GRE）或物理接口，边界路由器做 **unicast-multicast congruence（单播-组播一致）** 检查——DVMRP 依赖单播路由，边界处必须保证两边单播路径一致，否则 RPF 判定不一致导致环路。

> 现实价值：几乎为零。除非你要维护一套 20 年前的 MBone 遗留网络。这一章读懂"为什么组播强依赖单播一致性"即可。

---

## 5. 排障命令

```cisco
! PIM-DM 专用
show ip pim interface                       ! 模式：sparse / dense / sparse-dense
show ip mroute dense                        ! 仅看稠密模式表项
show ip mroute 239.1.1.1 detail             ! 查看 Prune / Assert / Graft 状态
show ip pim neighbor                        ! 邻居与 DR
debug ip pim dense-mode                     ! 密度模式调试
debug pim message dense-mode                ! 报文级调试
debug ip mpacket                           ! 数据包级（含 RPF 判定）

! 状态刷新
show ip pim state-refresh                  ! PSR 状态
```

---

## 6. 生产案例（6 例）

### 案例 4-1：PIM-DM 网络中组播风暴（带宽打满）

**现象**：某分支链路带宽 100% 打满，但只有 3 个接收端。
**定位**：`show ip mroute 239.1.1.1 detail` 显示大量接口在 Outgoing list；`debug ip pim dense-mode` 看到持续泛洪。
**根因**：PIM-DM 在**多路访问网段**（同交换机下多台路由器）泛洪时，需要 Assert 消重；若 Assert 被 ACL 过滤或接口配置为 `ip pim dense-mode` 但未启用 Assert 抑制，导致重复泛洪。
**处置**：放行 224.0.0.13；确认 `ip pim assert` 生效；检查网段是否需要改为 PIM-SM。
**复盘**：新建网络不用 PIM-DM；存量 PIM-DM 改造为 PIM-SM 是根本解法。

### 案例 4-2：Prune 后无法恢复（Graft 失败）

**现象**：接收端新加入组后一直收不到流；重启接收侧路由器后恢复。
**定位**：`debug pim message` 看到 Graft 发出但无 Graft-Ack 返回；上游状态中 (S,G) 不存在。
**根因**：上游因 State-Refresh 已删除状态，Graft 无人应答，树上无路径。
**处置**：手工触发一次洪泛（重启源侧 DR 或 `clear ip mroute *`）；长期方案是改用 PIM-SM。
**复盘**：PIM-DM 的恢复机制脆弱，生产上出现过一次即应立项改造。

### 案例 4-3：Prune Override 导致支路无法剪除

**现象**：某点到点链路上的组播流量一直不下线，即使对端无人接收。
**定位**：链路上游收到 Prune 但未剪除；确认链路为点到点。
**根因**：Prune Override 机制：点到点链路上游不剪除（怕影响链路上其他路由器）。
**处置**：接受该行为；或改为 PIM-SM（共享树按需剪除，无此问题）。
**复盘**：PIM-DM 的剪枝语义天然"粗"，业务上要接受一定冗余。

### 案例 4-4：PIM-SDM 域边界处组播单向可达

**现象**：稀疏区与稠密区之间，稠密区→稀疏区正常，稀疏区→稠密区不通。
**定位**：边界路由器 `show ip mroute` 两侧状态不一致；`show ip msdp peer` 显示 MSDP peer 缺失。
**根因**：PIM-SDM 边界需要 MSDP 交换源信息，MSDP peer 未建立。
**处置**：配置 MSDP peer 并保证 peer-RPF 通过。
**复盘**：PIM-SDM 边界 = "PIM-DM 域 + PIM-SM 域 + MSDP"，缺一不可。

### 案例 4-5：State-Refresh 路径不一致导致状态反复重建

**现象**：组播流量周期性闪断，每隔几分钟重连一次。
**定位**：`debug ip pim state-refresh` 显示收到的度量与本地记录不符；随后状态被删除并重新泛洪。
**根因**：链路冗余切换后 State-Refresh 仍沿旧路径到达，度量不匹配。
**处置**：确认链路切换后的收敛时间；升级软件版本（PIM State-Refresh 处理有增强）。
**复盘**：组播对链路抖动的敏感度高于单播，冗余链路切换要专门做组播收敛测试。

### 案例 4-6：DVMRP 遗留域与 PIM 域互联后出现环路

**现象**：组播包在两域之间来回转发，TTL 异常递减。
**定位**：边界路由器 `debug ip mpacket` 显示包在 DVMRP 与 PIM 之间循环。
**根因**：**单播-组播一致性（unicast-multicast congruence）** 被破坏——两域的单播路径不对称，而 DVMRP 与 PIM 都依赖单播做 RPF。
**处置**：修正单播路由使两域对称；或改用隧道 + 静态 mroute 明确路径。
**复盘**：这是"组播强依赖单播"最极端的例子，遗留互联必须做对称性设计。

---

## 7. 自测清单

1. PIM-DM 的"先泛洪后剪枝"与 PIM-SM 的"按需建树"在收敛时间与状态量上的差别？
2. Prune 报文中的 PSR 位作用是什么？
3. Prune Override 在什么链路类型下生效？为什么？
4. Graft/Graft-Ack 机制解决什么问题？它的风险是什么？
5. State-Refresh 报文里的度量不匹配会导致什么动作？
6. PIM-SDM 自动切换到 DM 的触发条件是什么？
7. 单播-组播一致性的含义是什么？破坏它会导致什么后果？

## 8. 延伸阅读

- Aweya Ch4（P.205–P.240）：PIM-DM 协议状态、Prune/Join/Graft、Assert、State-Refresh
- Williamson Ch6（P.128–P.177）、Ch10（P.214–P.239）、Ch13（P.352–P.404）
- iPexpert Ch3（P.3-1–3-49）、Ch5（P.5-1–5-40）
