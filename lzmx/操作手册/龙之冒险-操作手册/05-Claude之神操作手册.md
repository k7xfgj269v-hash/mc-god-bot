# Claude 之神 操作手册(2026-08-15 上线)

让 Claude 在游戏里当神:你说话,我听到;我发指令,游戏执行。朋友无感、零改动。

## 一、系统架构(一句话)

```
你/朋友在游戏里说话(带触发词) → bot(ludwiggod,OP) → inbox.jsonl → Claude 实时收到
Claude 写 outbox.jsonl → bot 每秒轮询 → 以 OP 执行指令/广播 → 游戏内生效
```

三个组件,全在本机:

| 组件 | 位置 | 作用 |
|---|---|---|
| 假玩家 bot | `~/Documents/Projects/mc-lzmx/mc-god-bot.js` | mineflayer 连 51620,OP 身份收发消息、执行指令 |
| kubejs 桥 | 游戏目录 `kubejs/server_scripts/god-bridge.js` | 1) ludwiggod 上线自动 OP 2) 触发词聊天回执"收到" |
| 消息文件 | 游戏目录 `mc-bridge/inbox.jsonl`(事件)/ `outbox.jsonl`(指令) | 双向通道 |
| 监视器 | Claude 会话内的 Monitor | 盯 inbox.jsonl,事件实时推送给我 |

## 二、日常使用

**呼我**:游戏聊天里说带"神"的话,例:
- `神,给我一把钻石剑`
- `神,把时间调到晚上`
- `神,我死了帮我复活`

你说完会先收到回执 `[神] 收到,稍等片刻…`,然后我处理,通过广播或指令生效。

**死亡通知**:ludwiggod 会把你的死亡广播写进 inbox(如 `[death] ludwigxu was slain by ...`),Claude 收到后可手动处理(复活/发东西等)。**不再自动调整血量**(2026-08-16 按需求移除,HP_MAP 值改回 null)。

## 三、启动顺序(每次开机联机)

```bash
# 1. 游戏开房(端口 51620,在线模式关)
bash ~/Documents/Projects/mc-lzmx/fix-lzmx-client.sh
# 2. 进世界后,启动 bot
cd ~/Documents/Projects/mc-lzmx && nohup node mc-god-bot.js > /tmp/mc-god-bot.log 2>&1 &
# 3. 确认上线
grep "上线" /tmp/mc-god-bot.log
# 4. 若 kubejs 桥有改动,游戏里敲 /kubejs reload server_scripts
```

Claude 会话里已挂 Monitor,启动 bot 后事件自动到达。

## 四、事件分级(噪音控制)

| 级别 | 内容 | 去向 |
|---|---|---|
| 触发 | 聊天含"神"/god/@claude | inbox(我收到) |
| 重要 | 玩家加入/退出、死亡(仅通知,不自动补血)、指令执行回执 | inbox |
| 忽略 | 普通聊天、系统广播(进度/时间等) | 仅 bot 本地日志,不打扰我 |

## 五、我能执行的指令(OP 权限,示例)

```text
give <玩家> <物品> <数量>           发物品,如 give ludwigxu minecraft:diamond 64
attribute ludwigxu minecraft:generic.max_health base set 20   最大血量(默认20;1000000方案已停用)
effect give <玩家> minecraft:resistance 999999 4 true   无敌
time set day / night
weather clear
gamerule keepInventory true       死亡不掉落
summon touhou_little_maid:entity.passive.maid ~ ~1 ~    召唤女仆
tp / kill / kick / ban            管理类
say <消息>                         全服广播(Claude 说话)
```

## 六、故障排查

| 现象 | 处理 |
|---|---|
| bot 掉线/被踢 | 自动重连(5 秒);持续失败看 `/tmp/mc-god-bot.log` |
| bot 上线但没 OP | 游戏里敲 `/kubejs reload server_scripts`,再重启 bot 触发 auto-op |
| 呼我没反应 | ① 检查 `pgrep -f mc-god-bot` ② 检查 inbox 是否有事件 `tail mc-bridge/inbox.jsonl` ③ 喊话内容是否带触发词 |
| 指令没生效 | 看 bot 日志 `grep exec /tmp/mc-god-bot.log`;权限问题按上行处理 |
| 游戏重启了 | bot 会自动重连(轮询 51620),无需手动重启 |

## 七、关键文件

- bot:`~/Documents/Projects/mc-lzmx/mc-god-bot.js`(改触发词/轮询间隔在这;文件头 `HP_MAP` 是死亡通知名单,值 null=不自动补血)
- kubejs 桥:游戏目录 `kubejs/server_scripts/god-bridge.js`
- 通道文件:游戏目录 `mc-bridge/`
- bot 日志:`/tmp/mc-god-bot.log`
- Forge 握手补丁:`node_modules/@tcortega/minecraft-protocol-forge/`(fml3.json 的 ServerRegistry snapshot 改为 restBuffer)+ `node_modules/minecraft-data/minecraft-data/data/pc/1.20/protocol.json` 三处**字段级** restBuffer(declare_recipes、unlock_recipes、entity_metadata)

## 八、踩过的坑(为什么长这样)

1. 开房模式**没有 RCON**(原版机制,仅专用服务端有)→ 放弃 RCON 方案
2. kubejs 6 **类过滤器封死 Java IO**(Java.loadClass 只放行白名单)→ kubejs 内不能读写文件 → 通道移到外部 bot 进程
3. powerfuljs 1.6.1 无 $http;KJS6 的 `java()` 全局废弃,用 `Java.loadClass`
4. vanilla 协议被 Forge 拒(需 FML 握手)→ npm 的 minecraft-protocol-forge@1.0.0 无 FML3 → 换 `@tcortega/minecraft-protocol-forge@1.2.0`
5. 1.20.1 服务器 mod 列表被编码,autoVersionForge 解不出 → 手动 hook 注入本地 mod 列表(`modid@version`,224 个)
6. ServerRegistry 快照协议定义不匹配 → snapshot 改 restBuffer 吞掉
7. declare_recipes / unlock_recipes(8668 个 mod 配方/解锁列表)解析错位 → 字段级 restBuffer(bot 不需要配方)
8. 聊天消息含引号会被服务器踢(illegal_characters)→ 广播消息别带引号
9. bot 上线后曾因进度广播/普通聊天刷 inbox → 事件分级过滤
10. **declare_commands 千万不能 restBuffer**:mod 命令树(女仆/KubeJS 命令)原版解析会 PartialReadError,但那是良性的(等更多数据);一旦 restBuffer 会吞掉配置阶段字节,破坏 set_compression 压缩协商 → 后续所有包 zlib 解压失败(日志刷 "problem inflating chunk")→ 永远不 spawn。保持原版定义,登录时会有 4 次左右良性 PartialReadError,不影响。
11. mineflayer 插件在 `inject_allowed` 事件(loader.js setTimeout 0,**emit 在 bot 上,不在 bot._client**)才注册 handler → 须在 `bot.on('inject_allowed')` 里把 entity_metadata / declare_commands 监听换成 no-op,否则 restBuffer 的 Buffer 让 entities.js 的 fromEntries 崩
12. **压缩层合并包丢包(2026-08-15 定位的最深坑)**:minecraft-protocol 的 compression.js 只处理每个 TCP 块(chunk)里的第一个包,Forge 服务器把多个包合并进同一块发送时**后续包全被丢弃** → bot 收不到 spawn、服务器 30 秒踢人("连接中断")循环。已重写为循环消费 + 二分找压缩流边界 + 跨 chunk 累积缓冲
13. **chat.js 登录后复活**:minecraft-protocol 的签名聊天插件在登录成功(success 包)后才注册 declare_commands handler(play.js:76),会覆盖 inject 时的 no-op → 须在 `bot.on('login')` 里再 removeAllListeners('declare_commands') 一次
14. bot 上线自动设置:**旁观者模式(spectator)+ 隐身**,脚本里 `setGod()` 在 spawn 回调执行,另有每 3s 看门狗重设直到进旁观者(tp 触发二次 spawn,重复设置无害)。**2026-09-03 修订:旧写法是"创造模式 + 隐身",创造会让 bot 显形、玩家可见可被攻击,已改成 spectator**(代码 `mc-god-bot.js` ~100-105)。另 spawn 时 `setViewDistance(5)`(~80 格半径,原为 2 太小,大范围 /fill 需要这个值)
15. **mod 箱子 block_action 崩溃(2026-08-15)**:玩家开 mod 箱子(深渊等)时,block_action 包里的 metadata 解析不出 facing → mineflayer block_actions.js 的 `Object.values(FACING_MAP[undefined])` 抛 TypeError;异常从包解析流(protodef)抛出会毁掉连接流 → 30 秒 keepalive 超时 → 断线循环(日志特征:`Cannot convert undefined or null to object` + `client timed out after 30000`)。修复:inject_allowed 里 block_action 也换 no-op(bot 不需要箱子开合动画);该插件只在注入时注册一次,无需 login 再补

## 九、游戏内运维卡点(2026-09-03 回写,补足上表没覆盖的)

1. **大范围 /fill 的节奏是最大坑**:bot 一个 poll 会把 outbox 里多行**毫秒级连发**;tp 和 fill 写在同一行批次时,区块没时间加载 → fill 报 `That position is not loaded`、或**静默返回 0/no-op**。铁律:**tp 单独写 → sleep≥3s → 再单独写 fill → 再探针验证**。
2. **目标区块没加载时的报错会骗人**:距 bot 超 ~80-120 格执行 block 探测/fill,报错可能是 `Unknown or incomplete command`(看着像语法错,实为区块未加载)、`not loaded`,或干脆静默。先 `/tp ludwiggod` 到场再动手;判定以 `execute if block <x> <y> <z> minecraft:<方块> run say TAG` 探针为准,别只信 "Successfully filled N"。
3. **/fill 单条上限 32768 方块**,大面积要分段(如 80×4×91≈29120)。厚 4 层、y0..90 的四壁按 80 长一段切,约 29k/段。
4. **fill 报 success 但几秒后消失** = 多半被玩家点燃连锁炸掉(引燃的 TNT 实体清方块)。铺完立刻探针验证留存,别当 bug 重复铺。
5. **进程判活用 `pgrep -fl 'mc-god-bot\.js'` / `pgrep -f openjdk`**;`ps aux | grep` 可能误判 DOWN(bot 其实活着)。
6. **fix-lzmx-client.sh 必须绝对路径调用**(`bash /Users/ludwigxu/Documents/mc-lzmx/fix-lzmx-client.sh`)。若在 mc-lzmx 目录用相对 `bash fix-lzmx-client.sh`,脚本 cd 到游戏目录后 `dirname $0`=`.` → 找不到 `lzmx-classpath.py`,java 根本没起(日志: can't open file .../minecraft/./lzmx-classpath.py)。
7. **游戏启动偶发崩溃 `java.lang.IllegalStateException: Image is not allocated`**(NativeImage/纹理图集,栈里含 modernfix 并发重载/ xaero)→ 进程退出、bot 进重连循环。属偶发,**直接重启即可**;重启后看 `/tmp/lzmx-fixed.log` 过没过 Server thread 初始化、`crash-reports/` 有没有新文件。反复出现再查 crash-report 顶部的 Description。
8. **FTB 任务进度操作**:
   - 活跃存档目录是 `saves/呢松的世界-回档前备份-20260818-0916`(名字带"备份"但被当活存档用),不是 `saves/呢松的世界`。用 mtime/游戏日志确认哪个在写。
   - 任务定义:`config/ftbquests/quests/chapters/*.snbt`。**任务本体 id 在 3-tab 缩进行,奖励/任务内部 id 在 4-tab**(抓 4-tab 会拿到 reward id,是错的)。
   - 「暮色森林」不是独立章节,是主线章 `716C86B2D2A52F2A.snbt`(23k 行/436+ 任务)里靠依赖链连成的连续块。定位用「入口任务 id + 依赖下游子树」。
   - 进度文件:`world/ftbquests/<teamUUID>.snbt`,`completed: { QUESTID: timestampL }`。**mtime 只在 FTB 落盘时更新**(自动存档/关服),改完别拿旧文件判失败;要立即落盘可触发 save(但本服 `/save-all` 会报 Unknown command)。
   - 完成单任务命令:`/ftbquests change_progress <玩家> complete <任务ID>`(带/则去掉);成功回显是 lang key `commands.ftbquests.change_progress.text`,不是明文。`complete-all` 会把**整本任务书**全通关(含女仆/钓鱼/BOSS攻略等无关章),慎用。
9. **游戏内语音转文字乱码**:坐标/高度常乱(如 "-4786 1337 -4486 -564 高度区间180-90 到正90")。动大工程(大量方块/不可逆)前,先 `/tp` bot 到目标、探玩家位置与地形确认意图,规模离谱就先广播让玩家确认,别盲目铺。
10. **FTB 内存态改动会被崩溃吞掉**:`/ftbquests change_progress` 改的是**内存态**,进度文件只在自动存档/干净关服时落盘。若改完世界崩溃/强杀(如 `Image is not allocated`),未落盘改动**直接丢**。稳妥流程:改完 → 保持游戏跑 ≥1 个自动存档周期(单机约 5 分钟)再关,或重载世界后复核 `world/ftbquests/<teamUUID>.snbt` 里 `completed` 是否有对应 QUESTID+新时间戳。**2026-09-03 实例:暮色 18 个任务改完,进度文件 mtime 仍停在改前的 06:13,随后 06:42 崩溃 → 这 18 个大概率没落盘,世界重载后要复核,丢了就重跑一遍。**
11. **玩家喊"作废"只是不做后续,已放方块仍在地图上**:如本次铺一半的 TNT 墙(作废后仍在),属潜在引爆点。作废前记下坐标,之后要清用分段 air fill(每段 ≤32768),别整片一把梭。
12. **同世界两份目录、同一 FTB team UUID 的坑**:`saves/呢松的世界` 和 `saves/呢松的世界-回档前备份-20260818-0916` 的进度文件 UUID 相同(b7344338…),内容却互不同步。核对任务进度/改文件务必对着**正在被游戏写入的那份**(看 mtime),否则容易改错文件、或拿另一份的旧状态误判。
13. **给玩家通关一条任务线(软锁安全完整流程,2026-09-04 糖果洞实例沉淀)**:
   - FTB 没有"一键通关某一章/某一线"指令(`complete-all` 是整本任务书全清,含女仆/钓鱼等无关章,别用),只能**逐任务 `complete`**,且必须按依赖序、缺前置补前置,否则软锁。
   - **任务 id 是 16 位大写十六进制**(不是 32)。任务本体 = 章节文件里**顶级 `quests:[` 数组元素**,字段 `id`(3-tab)/`subtitle`(显示名)/`description`/`dependencies`;奖励和任务的 id 嵌在 4-tab 深处,抓错就 give 到 reward id。糖果洞/暮色都在主章 `716C86B2D2A52F2A.snbt`(499 任务,基本一条链)。
   - `dependencies` 是纯 id 数组(`dependencies: ["父id"]`,绝大多数单父)→ 全包主线近似线性链,目标任务常有压在头上的未完成前置。
   - 判定"已完成":读活存档 `world/ftbquests/<teamUUID>.snbt` 的 `completed: { QUESTID: ts, … }`(**map,混有 task id**;任务做没做看 quest id 在不在)。注意 mtime 只在 FTB 落盘时更新。
   - **流程**:①解析章节拿到目标任务集(按关键词/坐标区);②从每个未完成任务沿 `dependencies` 向上 BFS 直到命中已完成 → 得"待完成集合"(目标+缺失前置);③按依赖拓扑序(父先子后)逐个发 `{"cmd":"ftbquests change_progress <玩家> complete <QUESTID>"}`;④成功回显是 lang key `commands.ftbquests.change_progress.text`(非明文);⑤落盘靠自动存档(~5min)/关服,本服 `/save-all` 是 Unknown command,复核读 completed 有没有对应 QUESTID+新时间戳。
   - **软锁红线**:前置没完成就 complete → 任务显示 100% 但领不了奖励、后续 complete 变 no-op,只能先 reset 再按序重来。所以必须先补前置、父先子后。
   - 实例:糖果龋洞 8 个糖果任务中 5 个早完成,剩 3 个(糖果白马 `3299AAFE…`→吃甜食加血量上限 `6FA6CD…`→糖果龋洞主线 `267ECC…`),但它们解锁链上压着 3 个未完成前置(究极药水 `62E77C…`→南瓜领主 `577F72…`→混沌恶魔统领 `3B80A5…`)→ 连同前置共 6 个按序 complete 即整条糖果线点亮,不软锁。

## 十、建造工作流工具链(2026-09-14 沉淀)

从一份 schematic 文件到「整栋建筑落地、核验、再清掉」的完整工具链。脚本就在本目录,编号 **07–20**,外加不被 import 的解析层 `mc_lib.py`。**人一般不用直接敲这些**,它们是 Claude 执行大工程时调的工具;这一节是给"想知道它在干什么/要改它"的人看的。

### 10.1 分工与顺序

| 段 | 编号 | 脚本 | 干什么 |
|---|---|---|---|
| 看懂 | 07 / 16 | 存档地形普查(手写版 / 库版) | 列顶高度、方块分布、方块实体;两份是**独立实现**,互相印证 |
| | 12 | 存档分层查看 | 逐层看存档 |
| | 13 / 14 / 15 | 示意 dump / 分层查看 / 楼层包围盒 | 看 **schematic 文件**本身(不是存档) |
| 生成 | 08 | 计划生成 | schematic + 坐标 → `/fill` 计划(合并长方体、按 32768 切、四象限分站点);`--no-support` 关掉它自造的支撑底座 |
| 投喂 | 09 | 投喂驱动 | 读计划、发 outbox、按序核对「bot 侧 [exec]」+「服务端 [msg]」两级回执 |
| 核验 | 10 | 探针核验 | 聊天探针抽样(把期望方块编码成经验值,靠回显读回) |
| | 18 | 存档缺口核对 | **穷尽**核对:直接读 region 逐格比计划 |
| | 11 | 补漏重放 | 重放 09 报 no-op 的那些 |
| 清除 | 17 | 清除计划生成 | 由建造计划反推「逐格填空气」,自带恒等核对 |
| | 20 | 遗留物清除 | 拿老存档当基线,找出**没进过任何计划**的遗留方块 |
| | 19 | 基线疤痕核对 | 反向:找出被我们删掉的天然地形 |

`mc_lib.py` 是解析层(NBT / schematic / .mca region),被 08/12/13/14/15/16/18/19/20 共 9 个脚本 import。07 是**手写解析器**,故意不 import 它——两套独立实现能互相验伪,别把 07 收敛过去。

### 10.2 铁律(本轮实战踩出来的,不是推测)

1. **存档是唯一权威判据**。聊天探针(10)只能抽样——本栋建筑 58,573 格,探不完;真判据是 18 直接读 region 逐格比。探针显示的「OK」只说明抽样点对,不等于全对。
2. **`No blocks were filled` 是歧义信号,不是失败判据**。本轮建造 17 个 no-op、清除 534 个,绝大多数是**良性**的(盒子与已填区域重叠、或该格本来就是目标态),重发一次仍是 no-op 而格子是对的;只有少数真没落地(目标区块未加载)。09 会把这些写进 `/tmp/mc-drive-noop.txt` 当"需复核信号",**不要**直接当失败结论去重铺一整片。
3. **清单式清除有结构性漏洞**。清除计划只能删「计划里登记过的格子」——没进过任何计划的方块,它永远看不见。本轮就是这样:建筑本体 58,573 格清得干干净净,但最初那版「带支撑」方案留下的 **73,367 格石头底座**从头到尾没被登记,原地站了整轮才被发现。**发现遗漏的唯一办法是拿一份建城前的存档当基线逐格比**(脚本 20)。本轮基线 = `saves/呢松的世界`,冻结在 8/18,比建城早近一个月(活存档是 `saves/呢松的世界-回档前备份-20260818-0916`,名字带"备份"但一直在被写)。
4. **保护格必须显式排除**。玩家那口箱子 `(-646, 73, -310)` 恰好不在任何 fill 盒子里,但清除计划仍要**显式挖掉这一格**(17 的第三个参数),否则填空气会连箱子带内容一起没。别指望"它不在计划里所以安全"。
5. **驱动吞吐的口径**:09 在每批之间有个 sleep。本轮实测 **批 100 + 间隔 0.6s ≈ 76 条/秒**,其中 **96 秒是纯 sleep**(占近一半)。要快就加大批、把间隔调到 0:`09-投喂驱动-mc-drive.py <计划> 0 999999 1000 0`。
6. **合并算法不是瓶颈**。08 的合并是「不区分轴向的贪心长方体」,实测同状态相邻对被拆进不同盒子的比例只有 **7.3%**,单格盒多(62.5%)是建筑本身细碎(阶梯/台阶/原木柱)所致,不是算法坏。
7. **`tp` 单独写 → sleep ≥3s → 再单独写 `fill`**(§九.1 的老铁律)。09 里写死了 4 秒观察窗;tp 落地 ≠ 区块加载好。
8. **`/fill` 单条上限 32768 方块**,08 会自动切。

### 10.3 本轮实测数字(留作基线)

- 建造:计划 15,956 条 fill / 58,573 格,4 个站点,驱动 0 条丢失。
- 清除:同样 15,956 条,0 条丢失;服务端回执 15,422 成功 / 534 no-op;清完核对**计划格仍是实心的 0 格**。
- 疤痕:与 8/18 基线逐格比,真正被删掉的天然地形只有 **51 格**(石 24 / 草方块 18 / 砾石 9);另有 **2,013 格**草方块被上方方块压成泥土(游戏机制,草会长回来)。
- 遗留:**73,367 格**石头底座(见 10.2 第 3 条),发现时仍在,尚未清除。
- 一句话教训:**"Successfully filled N" 只能证明指令被执行,不能证明结果正确;结果只有存档说了算。**

### 10.4 归档

被取代的旧版本(初版手写解析 `mc_nbt.py`、`schem2fill.py` 等 23 个)已移到 `/tmp/mc-scripts-retired-20260915/`(附 `SHA256SUMS-20260915.txt`)。⚠️ `/tmp` 会被系统清理,需要长期保留就自己拷走——**能用的那套已经在手册目录里了**,归档只是万一要看旧实现。
