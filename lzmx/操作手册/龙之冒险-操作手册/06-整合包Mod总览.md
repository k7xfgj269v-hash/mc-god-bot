# 06 整合包 Mod 总览:龙之冒险:新征程 v2.4

> 本文件是《龙之冒险:新征程 v2.4》整合包的 Mod 体系总览,重点是**神赐物品**:即用 `/give` 直接发放强力物品的 ID 速查。所有 give ID 均来自本机 mods 目录内 jar 的语言文件(即游戏实际生效的 ID),并尽量经过 MC百科/CurseForge/Modrinth/GitHub 等网络资料交叉验证;无法查证的标注 **待验证**。
>
> 用法:`/give 玩家名 modid:itemid 数量`(局域网开房 + OP 权限,命令无前缀)。
> 示例(已实测成功):`/give ludwigxu gobber2:gobber2_sword_end 1`、`/give ludwigxu iceandfire:dragonsteel_fire_sword 1`

---

## 一、整合包概况

| 项目 | 内容 |
|---|---|
| 整合包 | 龙之冒险:新征程 v2.4(国创整合包,MC百科词条 737) |
| 游戏版本 / 加载器 | Minecraft 1.20.1 / Forge 47.3.22 |
| Mod 数量 | 224 个(本机 mods 目录 227 个 jar,含 2 个重复前置) |
| 核心玩法一句话 | 硬核冒险整合包:强制佩戴七咒之戒、生命值无法自然恢复、所有装备有品质,围绕 40+ Boss、9 个新维度、1000+ FTB 任务推进,最终目标是击败 2.1 版最终双 BOSS(含圣约·博卓卡斯替) |

包内几个"定死全局规则"的机制(来自整合包官方更新日志与包内配置):

1. **七咒之戒强制佩戴**(神秘遗物 `enigmaticlegacy`):开局强制戴诅咒戒指,死亡掉落灵魂水晶,影响大部分强力遗物使用条件。
2. **生命值无法自然恢复**(`hardernaturalhealing` 更难的自然愈合 + `roughtweaks` 难度调整):回血手段变得重要(治愈营火、治疗勋章、女仆、食物等)。
3. **所有物品拥有品质**(`quality_equipment` 装备品质):武器/护甲/工具/饰品全部带随机品质,锻造台可重铸。
4. **口渴值**(`thirst`):需要喝水。
5. **末地之眼**(`endrem`):末地传送门激活方式被改,需集齐 12 种眼睛。
6. **末影龙强化**(`dragonfight` 更凶猛的末影龙):末影龙 4 阶段强化战斗。
7. **战斗机制改动**(`celestial_overhaul` 星月改革 + `bettercombat` 更好的战斗 + `armordamagelimit` 盔甲耐久损失限制):剑可右键格挡 50% 减伤、伤害百分比化、附魔机制调整等。

---

## 二、Mod 体系分类总览(按大类,全部 modid)

> 中文名取自 jar 文件名(整合包作者翻译),括号内为备注。

### 战斗 / Boss / 怪物

| modid | 中文名 | 说明 |
|---|---|---|
| iceandfire | 冰与火之歌 CE 1.2.6 | 龙与神话生物,龙钢三系装备(核心) |
| cataclysm | 灾厄(末影灾厄)3.31 | 8 个 Boss + 12 小 Boss,腾炎/咒魂套(核心) |
| twilightforest | 暮色森林 | 独立维度 + 流程 Boss(核心) |
| alternative_twilight | 暮色另类(国创) | 暮色森林魔改版 |
| dragonfight | 更凶猛的末影龙 | 强化末影龙 |
| mutantmonsters | 突变生物 | 突变僵尸/苦力怕/末影人等 |
| born_in_chaos_v1 | 生于混沌 | 恐怖怪物 + 暗黑金属装备 |
| eeeabsmobs | EEEAB 的生物(国创) | 幽灵武士/守卫者 Boss 等 |
| legendary_monsters | 传奇怪物(国创) | 湮灭者/雷霆之钺等 |
| mowziesmobs | Mowzie 的生物 | 地裂护手/山魈等 |
| bosses_of_mass_destruction | 更多 BOSS(BOMD) | 遁地尖矛/虚空荆棘 |
| alexsmobs | Alex 的生物 | 动物图鉴/维度撕裂者 |
| alexscaves | Alex 的洞穴 | 6 种地下洞穴群系 + 射线枪 |
| aquamirae | 海灵物语 | 海底冒险 + 分裂者 |
| graveyard | 墓园 | 墓园结构与亡灵 |
| trials | 试炼密室 | 试炼密室结构 |
| golemdungeons | 傀儡地牢(国创) | 巨人武器 + 傀儡地牢 |
| ash_of_sin_soul_like_boss_battle | 罪业余烬:类魂BOSS战(国创) | 类魂 Boss |
| abyssal_corrupter | 深渊侵蚀者(国创) | 召唤祭坛 + 深渊侵蚀者 Boss |
| jvs | Jaki 多功能结构 | 小型战斗结构 |
| goblintraders | 哥布林商人 | 商人交易 |
| guardvillagers | 警卫村民 | 村民卫兵 |
| letmedespawn | 让我绝望 | 防止怪物无限刷怪 |
| incontrol | 生成控制 | 怪物生成规则(魔改) |
| badmobs | 生成禁止 | 禁用指定生物 |
| champions | 精英怪(冠军) | 怪物带精英词条 |
| petconnect | 收容宠物(国创) | 宠物收纳 |
| soulbound | 灵魂绑定(国创) | 物品死亡不掉落 |
| watut | 他们在干什么 | 村民/NPC 行为 AI |
| nanhealthfixer | 假死修复(国创) | 修复假死判定 |

### 装备 / 武器 / 工具

| modid | 中文名 | 说明 |
|---|---|---|
| gobber2 | 戈伯2 | 三阶矿物 + 毕业级装备(核心) |
| the_zenith_sword | 天顶剑(国创) | 泰拉瑞亚终极武器移植 |
| murasama | 鬼妖村正(国创) | 可成长妖刀,多联动变体 |
| lm | 镜回·龙冒特供版(国创) | 齐天大圣套 + 如意金箍棒 |
| simplyswords | 简易刀剑 | 60+ 把特效武器,支持双持 |
| tetra | 锻造之艺 | 模块化武器锻造 |
| tetraextras / tetranomicon / tetrasimplyaddon / vvaddon / tetratic_combat_expanded | 锻造之艺附属×5 | 模块拓展/手册/刀剑附属/属性拓展/战斗兼容 |
| immersive_armors | 沉浸式盔甲 | 骨/神圣/蒸汽朋克/海晶等 15 套 |
| wstweaks | 凋灵骷髅调整 | 凋灵骷髅战利品调整 |
| somanyenchantments | 附魔扩展 | 大量新附魔 |
| wolfenchantmentlib | 狼王的附魔库(国创) | 附魔库前置 |
| enchantinginfuser | 附魔灌注台 | 自定义附魔 |
| quality_equipment | 装备品质(国创) | 全局品质 + 重铸站 |
| bettercombat + better_combat_reach_fix + playeranimator | 更好的战斗体系 | 双持战斗 + 攻击距离修复 |

### 饰品 / 遗物

| modid | 中文名 | 说明 |
|---|---|---|
| enigmaticlegacy | 神秘遗物 | 七咒系统 + 顶级遗物(核心) |
| enigmaticaddons | 神秘遗物扩展(国创) | 寂灭之决/救赎线 |
| architectbypass | 神秘遗物附属(国创) | 遗物兼容调整 |
| confluence | 泰拉饰品(国创) | 泰拉瑞亚饰品全套移植(326 件) |
| relics | 遗物 | 魔镜/空间传送器等 30 件 |
| dragonheart | 龙冒饰品(国创,包内自制) | 圣剑菈/魔剑阿波菲斯等 20+ 件 |
| celestial_core | 星月核心(国创) | 飞升之翼/纯净之星 |
| curios | 饰品栏 | 饰品槽位前置 |
| caelus | 鞘翅 API | 前置 |

### 探索 / 结构 / 维度

| modid | 中文名 | 说明 |
|---|---|---|
| endrem | 末地之眼 | 12 种眼睛开启末地 |
| dungeons_arise | 地牢浮现之时 | 大量新结构 |
| repurposed_structures | 结构变体 | 原版结构改版 |
| totw_modded | 旷野之息高塔(再重制) | 高塔结构 |
| skyvillages | 天空村庄 | 天空村庄 |
| philipsruins | 菲利普遗迹 | 遗迹结构 |
| kaleidoscope_tavern | 森罗物语:酒馆(国创) | 酒馆/厨房结构 + 酿酒 |
| naturescompass | 自然罗盘 | 找生物群系 |
| explorerscompass | 探险家指南针(修改版) | 找结构 |
| waystones | 传送石碑 | 传送点 |
| wormholepotion | 虫洞药水(国创) | 队友传送药水 |
| immersive_gateways | 传送门 | 原版传送门美化 |
| enderteleport | 末影阅历(国创) | 末影传送机制 |
| lootr | 战利品箱 | 每人独立战利品 |
| lootjs | 战利品修改 | 战利品表魔改 |
| jeresources + jerintegration | 资源统计 | 掉落统计 |

### 农业 / 食物 / 烹饪

| modid | 中文名 | 说明 |
|---|---|---|
| farmersdelight | 农夫乐事 | 烹饪体系底座 |
| ends_delight | 末地乐事 | 末地食材 |
| twilightdelight | 暮色风味乐事 | 暮色食材 |
| mynethersdelight | 下界乐事 | 下界食材 |
| fruitsdelight | 果园乐事 | 水果 |
| cuisinedelight | 料理乐事(国创) | 中式炒锅 |
| enigmaticdelicacy | 神秘佳肴(国创) | 遗物主题食物 |
| vanillacookbook | 原版烹饪书 | 原版食材扩展 |
| crockpot | 烹饪锅(饥荒锅) | 炖菜 |
| fox_trot_brew | 狐步酿香(国创) | 女仆酿酒(酒类) |
| farmingforblockheads | 农场贸易 | 农场商店 |
| right_click_get_crops | 右键收菜(国创) | 一键收菜 |
| solcarrot | 生活调味料:胡萝卜版 | 食物多样性奖励 |
| appleskin | 苹果皮 | 饱和度显示 |
| aquaculture | 水产品2 | 钓鱼扩展 |
| thirst | 口渴 | 口渴值系统 |
| fastleafdecay | 树叶快速腐烂 | 优化 |

### 科技 / 存储 / 物流

| modid | 中文名 | 说明 |
|---|---|---|
| refinedstorage | 精致存储 | 数字存储网络 |
| refinedstorageaddons / rsinfinitybooster | 精致存储附属 | 无线范围增幅 |
| sophisticatedbackpacks + sophisticatedcore | 精妙背包 | 可升级背包(最高下界合金) |
| ironchest | 更多箱子 | 铁→水晶→黑曜石箱子 |
| betterfurnacesreforged + factory_api | 更好的熔炉重铸版 | 升级熔炉 |
| chickenchunks + codechickenlib | 区块载入器 | 强制加载区块 |
| carryon | 搬运 | 搬方块/生物 |
| astikorcarts | 马车 | 马车 |
| immersive_aircraft | 沉浸式飞机 | 飞机 |
| constructionwand | 建筑手杖 | 快速建筑 |
| toolbelt | 工具皮带 | 快捷换工具 |
| torchmaster | 火炬大师 | 刷怪抑制 |
| modulargolems + l2library | 傀儡装配(国创) | 组装巨型傀儡守卫 |
| healingcampfire | 治愈营火 | 回血营火 |
| visualworkbench | 可视化工作台 | 工作台材料预览 |
| ante | 不昂贵 | 铁砧不涨价 |

### 魔法

| modid | 中文名 | 说明 |
|---|---|---|
| goety | 诡厄巫法 | 黑暗魔法 + 仆从军团 |
| goety_revelation | 诡厄巫法·启示录(国创) | 延伸内容 |
| goety_cataclysm | 诡厄灾变 | 与灾厄联动 |
| goety_addition | 诡厄巫法附属(国创) | 附加内容 |
| patchouli | 帕秋莉手册 | 指南书前置 |

### 建筑 / 装饰 / 氛围

| modid | 中文名 | 说明 |
|---|---|---|
| adorn | 装饰 | 家具 |
| chimes | 铃声 | 风铃 |
| comforts | 舒适用品 | 睡袋/羊毛毯 |
| medievalmusic | 中世纪音乐 | 音乐 |
| biomemusic | 生物群系音乐 | 群系配乐 |
| torchesbecomesunlight | 薪火造炬成阳(国创,龙冒特供版) | 光源机制 + BOSS 圣约·博卓卡斯替 |
| snowwaifu | 雪の嫁(国创) | 雪女装饰/机制 |

### 女仆体系(本包特色)

| modid | 中文名 | 说明 |
|---|---|---|
| touhou_little_maid | 车万女仆 1.5.3 | 女仆本体(详见 02/04 文档) |
| maidsoulkitchen | 女仆厨房(国创) | 女仆自动烹饪 |
| fox_trot_brew | 狐步酿香(国创) | 女仆酿酒 |
| hotai | hotai(国创) | 女仆 AI 相关(包内自制,无公开资料) |

### 任务 / 经济

| modid | 中文名 | 说明 |
|---|---|---|
| ftbquests + questsadditions + ftbteams + ftblibrary + ftbxmodcompat | FTB 任务体系 | 1000+ 任务引导 |
| ftbessentials | FTB 基础指令 | /home /tpa 等 |
| ftbbackups2 | FTB 备份2 | 自动备份 |
| ftbultimine | 连锁破坏 | 连锁挖掘 |
| currency | 货币多多2 | 硬币货币系统 |
| firstjoinmessage | 首次加入世界信息(国创) | 新手引导 |
| starterkit | 初始套件 | 出生奖励 |

### 辅助 / UI

| modid | 中文名 | 说明 |
|---|---|---|
| jei | JEI 物品管理器 | 配方查询 |
| jade | 玉 | 方块信息 |
| xaerominimap / xaeroworldmap | Xaero 小地图/世界地图 | 地图 |
| inventoryhud | 物品栏HUD | 背包悬浮 |
| itemzoom | 物品缩放 | 按住查看物品 |
| inventoryspam | 拾取提示 | 拾取播报 |
| expcounter | 经验值显示 | 经验条 |
| wwta | 聊天栏时间显示 | 时间显示 |
| worldplaytime | 世界游玩时间显示(国创) | 时长显示 |
| classicandsimplestatusbars | 经典且简易的状态栏(国创) | 状态栏 |
| tslatentitystatus | 伤害显示 | 怪物血条 |
| dummmmmmy | 试验假人 | DPS 测试 |
| jeed | JEI 药水效果 | 药水查看 |
| tipsmod | 提示 | 加载界面提示 |
| catalogue | 模组目录 | 模组列表 |
| corpse | 遗体 | 死亡掉落箱 |
| trashslot | 垃圾槽 | 垃圾桶格 |
| transmog | 幻化 | 装备外观替换 |
| polymorph | 多态合成 | 冲突配方选择 |
| stackablepotions | 药水堆叠 | 药水可堆叠 |
| customskinloader | 万用皮肤补丁(国创) | 皮肤加载 |
| travelertitles | 旅行标题 | 进群系/维度横幅 |
| itemfilters | 物品过滤器 | 任务过滤 |
| oworld2create | 别创建新世界(国创) | 禁创建新世界 |
| dream_stone | 梦之石(国创) | 快速旅行机制 |
| bbsmc_ad | bbsmc 广告(国创) | 广告 mod(可忽略) |

### 性能 / 修复 / 前置库

| modid | 说明 |
|---|---|
| modernfix / ferritecore / packetfixer / gpumemleakfix / yeetusexperimentus / nightconfigfixes / attributefix | 性能与修复 |
| kubejs / powerfuljs / rhino / openloader / paxi / propertymodifier | 脚本与魔改引擎 |
| 前置库 | architectury, balm, bookshelf, citadel, collective, corgilib, coroutil, cupboard, framework, geckolib, iceberg, kotlinforforge, libipn, majruszlibrary, moonlight, mutil, obscure_api, octolib, placebo, polylib, puzzleslib, searchables, yungsapi, cloth_config, cerbons_api, jupiter(配置重定向), uranus(iafenvoy 库), redirector(异引定址) |

---

## 三、重点 Mod 详解

### 1. Gobber2 戈伯2(gobber2)★毕业级装备来源

三阶矿物(戈伯→下界戈伯→末地戈伯)体系的装备 mod,是本包最直接的毕业装备来源。剑类有:基础/下界/末地三档 + 两把特殊剑。

**神赐物品(give ID 均为 jar 内实测):**

| 物品 | give ID | 说明 |
|---|---|---|
| 末地剑 | `gobber2:gobber2_sword_end` | 攻击 16,生存合成自带无法破坏,进阶材料(已实测) |
| 狙击手之剑 | `gobber2:gobber2_sword_sniper` | 无法破坏,右键射箭,单发伤害 61(需蓄力),有冷却 |
| 旅行者之剑 | `gobber2:gobber2_sword_traveler` | 无法破坏,右键起跳无冷却 |
| 下界剑 | `gobber2:gobber2_sword_nether` | 攻击 12 左右,凋灵骷髅头颅友好 |
| 末地全套 | `gobber2:gobber2_helmet_end / chestplate_end / leggings_end / boots_end` | 快速补食/水下呼吸/免摔落/防中毒等 |
| 龙之全套 | `gobber2:gobber2_helmet_dragon / chestplate_dragon / leggings_dragon / boots_dragon` | 由末地套 + 龙之星/龙之鞘翅锻造升级;全套永久飞行 + 免疫全部负面效果(2.7.11 后部分被动被削,但这是包内 2.8.7 版,锻造继承附魔) |
| 龙之鞘翅(材料) | `gobber2:gobber2_dragon_elytra` | 仅合成材料,非真鞘翅 |
| 龙之星 | `gobber2:dragon_star` | 龙套升级材料 |
| 末地全能镐 | `gobber2:gobber2_paxel_end` | 镐斧锹三合一 + 3x3 |
| 末地弓 | `gobber2:gobber2_bow_end` | 高伤弓 |
| 治疗勋章 III | `gobber2:gobber2_medallion_healing3` | 强力持续回血(配合本包禁自然回血) |
| 经验勋章 | `gobber2:gobber2_medallion_exp` | 经验翻倍 |
| 凤凰戒指 | `gobber2:gobber2_ring_phoenix` | 免疫火焰 + 复活(待验证具体机制) |
| 末影箱戒指 | `gobber2:gobber2_ring_enderchest` | 随时开末影箱 |
| 瞬移戒指 | `gobber2:gobber2_ring_blink` | 闪烁位移 |

来源:jar 内 zh_cn/en_us 语言文件 + MC百科戈伯2 条目(mcmod.cn/class/2547)、末影剑(mcmod.cn/item/286696)、龙之胸甲(mcmod.cn/item/470034)。

### 2. 冰与火之歌 CE(iceandfire)★龙战核心

包内为 Community Edition 1.2.6。三种龙钢(火/冰/霆)是仅次于戈伯龙套的毕业装备;注意 **龙钢套装只有头盔/胸甲/战靴三件,没有护腿**(语言文件确认)。

**神赐物品:**

| 物品 | give ID |
|---|---|
| 龙炎钢剑(火) | `iceandfire:dragonsteel_fire_sword`(已实测) |
| 龙霜钢剑(冰) | `iceandfire:dragonsteel_ice_sword` |
| 龙霆钢剑(雷) | `iceandfire:dragonsteel_lightning_sword` |
| 龙炎/霜/霆钢全套 | `iceandfire:dragonsteel_{fire,ice,lightning}_{helmet,chestplate,boots}` |
| 三系钢镐/斧/锹/锄 | `iceandfire:dragonsteel_{fire,ice,lightning}_{pickaxe,axe,shovel,hoe}` |
| 龙炎骨血剑 | `iceandfire:dragonbone_sword_fire`(龙骨+龙血,进阶前强力) |
| 幻灵剑 | `iceandfire:ghost_sword`(投射穿透方块旋转剑) |
| 鸡蛇节杖 | `iceandfire:cockatrice_scepter`(凋零远程) |
| 龙骨长弓 | `iceandfire:dragonbone_bow` |
| 龙铠(给龙穿) | `iceandfire:dragonarmor_dragon_steel_lightning` 等三系 |

来源:jar 语言文件 + 用户实测 + MC百科冰与火条目。

### 3. 灾厄 Cataclysm(cataclysm)★Boss 与顶级装备

8 大 Boss(焰魔、虚空恐惧、斯库拉等)。两套毕业甲:**腾炎套**(下界合金 + 锻造模板升级,总护甲 32/韧性 16,炽热烙印机制)与**咒魂套**(含死亡复活等特效)。

**神赐物品:**

| 物品 | give ID |
|---|---|
| 炎葬 | `cataclysm:the_incinerator`(蓄力烈焰轰击) |
| 献祭者 | `cataclysm:the_immolator`(对炽热烙印目标必暴击) |
| 歼灭战锤 | `cataclysm:the_annihilator`(双持副手可范围攻击) |
| 腾炎全套 | `cataclysm:ignitium_helmet/chestplate/leggings/boots` |
| 腾炎鞘翅胸甲 | `cataclysm:ignitium_elytra_chestplate`(胸甲+鞘翅二合一) |
| 咒魂全套 | `cataclysm:cursium_helmet/chestplate/leggings/boots`(胸甲=死亡复活) |
| 虚空锻锤 | `cataclysm:void_forge`(远程虚空符文,镐类) |
| 断魂战戟 | `cataclysm:soul_render`(冲刺/幻影戟) |
| 末影双手剑 | `cataclysm:zweiender`(背击双倍) |
| 沙暴之怒 | `cataclysm:wrath_of_the_desert`(3 发沙暴弹) |
| 虚空/凋灵突击肩炮 | `cataclysm:void_assault_shoulder_weapon` / `wither_assault_shoulder_weapon` |
| 激光加特林 | `cataclysm:laser_gatling`(红石装弹) |
| 绞肉锯 | `cataclysm:meat_shredder`(无视无敌帧) |
| 神怒长槊/掣雷巨锤/霆浪锚戟 | `cataclysm:astrape` / `brontes` / `ceraunus` |
| 火焰壁垒 | `cataclysm:bulwark_of_the_flame`(冲锋盾) |
| 缚魂之链 | `cataclysm:chain_of_soul_binding`(拉拽链) |
| 末影合金锭 | `cataclysm:enderite_ingot`(材料) |

来源:jar 语言文件 + MC百科腾炎套装条目(mcmod.cn/item/545536)。

### 4. 暮色森林(twilightforest)★独立维度

流程维度:Boss 顺序推进(娜迦→巫妖→米诺陶→九头蛇→雪怪首领→幻影骑士→冰雪女王→暮色恶魂)。毕业目标是**炽铁套**(九头蛇血浇铸,灼烧 15 秒)。

**神赐物品:**

| 物品 | give ID |
|---|---|
| 炽铁剑 | `twilightforest:fiery_sword`(攻击 8,灼烧 15 秒,合成自带,MC百科确认指令 `/give @p twilightforest:fiery_sword 1`) |
| 炽铁全套 | `twilightforest:fiery_helmet/chestplate/leggings/boots`(灼烧攻击者) |
| 炽铁镐 | `twilightforest:fiery_pickaxe`(自动烧炼) |
| 骑士剑/骑士盾 | `twilightforest:knightmetal_sword` / `knightmetal_shield` |
| 骑士全套 | `twilightforest:knightmetal_helmet/chestplate/leggings/boots` |
| 娜迦胸甲/护腿 | `twilightforest:naga_chestplate` / `naga_leggings` |
| 钢叶全套 | `twilightforest:steeleaf_*`(剑/斧/镐/锹/锄/甲) |
| 寒冰剑/寒冰弓 | `twilightforest:ice_sword` / `ice_bow` |
| 末影弓 | `twilightforest:ender_bow` |
| 湮灭立方 | `twilightforest:cube_of_annihilation`(吸引破坏方块) |
| 瓦解之号角 | `twilightforest:crumble_horn`(瓦解石头/金属) |
| 巨人剑/巨人镐 | `twilightforest:giant_sword` / `giant_pickaxe` |
| 米诺陶战斧 | `twilightforest:gold_minotaur_axe` / `diamond_minotaur_axe` |
| 玻璃剑 | `twilightforest:glass_sword`(仅创造可用) |
| 魔豆 | `twilightforest:magic_beans`(豆茎上天) |

来源:jar 语言文件 + MC百科炽铁剑条目(mcmod.cn/item/3972)。

### 5. 天顶剑(the_zenith_sword)★泰拉瑞亚终极武器

包内只有一个物品:**天顶剑**(item ID `the_zenith_sword:zenith`)。攻击 8 + 攻速 30+,右键/自动发射剑雨(对路径敌人 0.1 倍 + 1% 最大生命伤害),**完全无法破坏**,配方需 6 把原版剑 + 海洋之心 + 下界之星 + 龙息。物品栏右键切换射程,Shift+右键切换目标模式。

**神赐:** `/give ludwigxu the_zenith_sword:zenith 1`(jar 内确认 + MC百科 class/23975 确认)

### 6. 鬼妖村正(murasama)★多联动妖刀

可成长妖刀,击杀充能 100% 右键出鞘强化。本包含多把联动变体:

| 物品 | give ID | 联动来源 |
|---|---|---|
| 鬼妖村正(深渊) | `murasama:murasama` | 本体,充能出鞘 |
| 烬灭之刃 | `murasama:murasama_fire` | 灾厄联动(耐久 2900,MC百科确认 `/give @p murasama:murasama_fire 1`) |
| 密特拉斯 | `murasama:murasama_mithras` | 诡厄巫法启示录联动(真实伤害铭文) |
| 圣骑 | `murasama:murasama_posessed_paladin` | 传奇怪物联动(格挡反弹) |
| 切伦科夫 | `murasama:infinity_murasama` | 无尽贪婪联动(本包未装无尽贪婪,标**待验证**) |
| Terraria! | `murasama:murasama_terraria` | 泰拉瑞亚彩蛋 |
| 铜村正 | `murasama:murasama_copper` | 破伤风梗剑 |

### 7. 镜回·龙冒特供版(lm)★齐天大圣套

整合包特供版本。2.1 版起**大圣套不再有合成配方,只能在终末圣堂获取**;配套结构"仙王宫"掉**神珍烫金灵铜**(`lm:tj`,材料)。

| 物品 | give ID |
|---|---|
| 如意金箍棒 | `lm:jgb` |
| 凤翅紫金冠 | `lm:dashengtao_helmet` |
| 锁子黄金甲 | `lm:dashengtao_chestplate` |
| 锁子黄金裙甲 | `lm:dashengtao_leggings` |
| 藕丝步云履 | `lm:dashengtao_boots`(全套带筋斗云/多种 BUFF) |
| 龙镜 | `lm:lj` |
| 龙牙刀 | `lm:lonhyad` |
| 水龙套 | `lm:llonggui_{helmet,chestplate,leggings,boots}` |

来源:jar 语言文件 + 整合包更新日志(mcmod.cn/modpack/version/737,镜回更新日志 class/16931)。

### 8. 龙冒饰品(dragonheart)★包内自制饰品

整合包自制 mod,2.0 版新增 18 个自制饰品,后续又加 5 个。**圣剑菈/魔剑阿波菲斯/无止之言/倒转之启**对最终 BOSS 圣约·博卓卡斯替有增伤兼容(官方更新日志)。

**神赐物品(全部 jar 内确认):**

| 物品 | give ID |
|---|---|
| 圣剑-菈 | `dragonheart:abelun_sword`(对悚怖生物/博卓卡斯替增伤) |
| 魔剑-阿波菲斯 | `dragonheart:bad_sword`(对 Boss 增伤%) |
| 剑神之戒 | `dragonheart:sword_ring`(附加虚空伤害) |
| 神龙之心 | `dragonheart:dragoncurios`(饰品) |
| 火神之铠/火神之爪 | `dragonheart:blaze_armor` / `blaze_hands` |
| 破妄金瞳 | `dragonheart:bow_miracle` |
| 瞑煌龙的鳞甲 | `dragonheart:dragon_roar` |
| 堕天魔戒 | `dragonheart:fallen_angel_ring` |
| 紫水晶巨蟹的祝福 | `dragonheart:amethyst_crab_shelter` |
| 南瓜领主的灵魂 | `dragonheart:pumpkin_soul` |
| 巨兽石板 | `dragonheart:beast_plaque` |
| 愤怒皇冠/女神之骰/始源宝珠/比干的认可 | `dragonheart:angry_head` / `goddess_dice` / `origin_orb` / `bi_gan` |
| 救赎项链/救赎脚环 | `dragonheart:redemption_necklace` / `redemption_anklet` |
| 咒魂灵符 | `dragonheart:haunted_talisman` |
| 幸识 | `dragonheart:core_sour` |
| 村里最好的剑 | `dragonheart:best_village_sword` |
| 创世之星/超限石/匠神之锤 | `dragonheart:create_star` / `super_limit_stone` / `pickaxe_god`(具体效果**待验证**) |
| 龙套/以太/海王升级模板 | `dragonheart:template.best_dragon_armor_template` / `template.ether_armor_template` / `template.sea_king_armor_template`(实际物品 ID 待验证,可能是 `best_dragon_armor_template`) |

### 9. 神秘遗物(enigmaticlegacy)★七咒体系

包内强制七咒之戒,整个遗物体系围绕诅咒与救赎展开。死亡掉灵魂水晶;被诅咒玩家可装备专属强力物品。

**神赐物品:**

| 物品 | give ID | 说明 |
|---|---|---|
| 无止之言 | `enigmaticlegacy:the_infinitum` | 深渊系顶级剑:16 攻,+200% 对 Boss/玩家伤害,持有时 80% 免致命伤;需七咒且 99.5% 时间处于七咒(本包强制七咒,可直接用);官方日志确认对博卓卡斯替增伤 |
| 星光破坏锤 | `enigmaticlegacy:astral_breaker` | 3x3 挖掘 + 攻击 10,可拆"不可破坏"方块 |
| 倒转之启 | `enigmaticlegacy:the_twist` | 七咒系饰品(对博卓卡斯替增伤) |
| 以太阔剑 | `enigmaticlegacy:etherium_sword` | 以太锭武器 |
| 壮丽鞘翅 | `enigmaticlegacy:enigmatic_elytra` | 强力鞘翅 |
| 末影之屠 | `enigmaticlegacy:ender_slayer` | 对末影增伤 |
| 七咒之戒 | `enigmaticlegacy:cursed_ring` | 包内强制佩戴的诅咒戒指 |
| 错位之戒/磁力之戒 | `enigmaticlegacy:super_magnet_ring` / `magnet_ring` | 大范围吸物 |
| 非欧立方 | `enigmaticlegacy:the_cube` | 强力多用途方块(官方日志:2.0 起 JEI 可见配方) |
| 战后召回卷轴 | `enigmaticlegacy:escape_scroll` | 死亡自动回城 |
| 寰宇之心/星云之眼/魔像之心 | `enigmaticlegacy:cosmic_heart` / `eye_of_nebula` / `golem_heart` | 强力饰品材料 |

来源:jar 语言文件 + MC百科星光破坏锤(item/219293)、无止之言(item/897621,注:部分版本该物品归属"神秘遗物+",本包 2.30.1 的 jar 内直接存在 `enigmaticlegacy:the_infinitum`,以本地为准)。

**神秘遗物扩展(enigmaticaddons):** 寂灭之决 `enigmaticaddons:annihilating_sword`、星光穿刺者 `astral_spear`、混沌之傲 `chaos_elytra`、救赎之戒 `bless_ring`、极尽奢华之戒 `avarice_ring`(jar 内确认)。

### 10. 泰拉饰品(confluence)★326 件泰拉瑞亚饰品

国创 TerraCurio,全套泰拉瑞亚饰品移植,配合龙冒饰品组成"饰品图鉴"任务章节。顶级饰品:

| 物品 | give ID |
|---|---|
| 十字章护盾 | `confluence:ankh_shield`(免疫大部分负面状态,毕业级) |
| 天界石 | `confluence:celestial_stone`(全属性增益) |
| 手机 | `confluence:cell_phone`(全信息聚合) |
| 复仇者勋章 | `confluence:avenger_emblem`(+12% 伤害类) |
| 混乱之脑 | `confluence:brain_of_confusion`(闪避) |
| 狂战士手套 | `confluence:berserkers_glove`(攻速+仇恨) |
| 水陆两用靴 | `confluence:ambhipian_boots` |
| 马掌气球束 | `confluence:bundle_of_horseshoe_balloons`(多重跳+免摔落) |
| 黑腰带 | `confluence:black_belt`(闪避) |
| 再生手环 | `confluence:band_of_regeneration` |

(jar 内全部确认;具体数值以游戏内为准)

### 11. 诡厄巫法体系(goety + goety_revelation + goety_cataclysm + goety_addition)★黑暗魔法

灵魂能量 + 仆从军团 + 头冠法袍套装效果。**黑暗套**=顶级防御(全套 +30% 爆炸/火焰抗性、每秒回血、免疫黑暗失明);**死灵套**(死灵王冠+长袍)强化亡灵仆从;**无名魔杖**=死灵法术终极武器。

| 物品 | give ID |
|---|---|
| 黑暗套 | `goety:dark_helmet/chestplate/leggings/boots`(每件+5%灵魂折扣) |
| 黑暗魔杖 | `goety:dark_wand` |
| 无名魔杖 | `goety:nameless_staff`(6 攻无限耐久,升级死灵法术) |
| 虚空魔杖 | `goety:void_staff` |
| 死灵王冠/死灵长袍/死灵魔杖 | `goety:necro_crown` / `necro_cape` / `necro_staff` |
| 黑暗镰刀/不祥镰刀 | `goety:dark_metal_scythe` / `dark_scythe` |
| 龙息戒指 | `goety:ring_of_the_dragon` |
| 原力戒指 | `goety:ring_of_force` |

(jar 内确认 + MC百科诡厄巫法条目 class/7635、黑暗套装 item/753246)

### 12. 车万女仆(touhou_little_maid)★本包特色(详见 02/04 文档)

- 女仆刷怪蛋:`touhou_little_maid:maid_spawn_egg`(1.1.5 起生存仅创造/村民交易,OP give 无限制;MC百科确认指令 `/give @p touhou_little_maid:maid_spawn_egg 64`)
- 女仆妖精刷怪蛋:`touhou_little_maid:fairy_spawn_egg`(P 点来源)
- 博丽的御币:`touhou_little_maid:hakurei_gohei`(女仆远程弹幕所需)
- 魔理沙的扫帚:`touhou_little_maid:broom`(飞行)
- 大背包:`touhou_little_maid:maid_backpack_big`(背包扩到 36 格)
- 饰品(护身符类):物品磁铁 `item_magnet_bauble`、溺水保护 `drown_protect_bauble`、火焰保护 `fire_protect_bauble`、摔落保护 `fall_protect_bauble`、爆炸保护 `explosion_protect_bauble`、药水保护 `magic_protect_bauble`

**女仆厨房(maidsoulkitchen):** 烹饪中枢 `maidsoulkitchen:culinary_hub`、燃着保护饰品 `burn_protect_bauble`。核心玩法是让女仆用农夫乐事/CrockPot/料理乐事/森罗酒馆厨具**自动做饭**(与包内食物系 mod 天然联动)。

### 13. 其他大 mod 一览

**Alex 的洞穴(alexscaves):** 射线枪 `alexscaves:raygun`(持续镭射 + 40 秒辐照,MC百科确认指令 `/give @p alexscaves:raygun 1`)、螺纹长枪 `ortholance`、阻尼盾牌 `resistor_shield`、磁力采石场粉碎器 `quarry_smasher`、潜水服 `diving_*`。

**Alex 的生物(alexsmobs):** 维度撕裂者 `dimensional_carver`(传送到高处)、血液喷射器 `blood_sprayer`、宇宙鳕鱼 `cosmic_cod`(骑乘飞行?待验证)。

**海灵物语(aquamirae):** 分裂者 `aquamirae:divider`、珊瑚长矛 `coral_lance`、贪婪匕首 `dagger_of_greed`、晦暗深海套 `abyssal_heaume/brigantine/leggings/boots`、氧气罐 `oxygen_tank`。

**突变生物(mutantmonsters):** 巨人之锤 `mutantmonsters:hulk_hammer`(右键砸地)、末影之手 `endersoul_hand`(传送拉怪)、试剂X `chemical_x`、骷髅突变体套 `mutant_skeleton_{helmet,chestplate,leggings,boots}`。

**生于混沌(born_in_chaos):** 斩龙 `born_in_chaos_v1:darkwarblade`、霜噬之刃 `frostbitten_blade`、大收割者之斧 `great_reaper_axe`、碎颅锤 `skullbreaker_hammer`、灵魂分割者 `spiritual_sword`、暗黑金属套 `dark_metal_armor_*`、梦魇套 `nightmare_mantleofthe_night_*`、止锤 `stop_hammer`。

**EEEAB 的生物(eeeabsmobs):** 守卫者战斧 `eeeabsmobs:guardian_axe`(无视护甲冲击波)、守卫者核心 `guardian_core`(激光武器)、粉碎者 `demolisher`(榴弹)、幽冥武士套 `ghost_warrior_*`。

**传奇怪物(legendary_monsters):** 湮灭者套 `annihilator_{helmet,chestplate,leggings,boots}`(半血爆炸无敌/暴击 AOE)、雷霆之钺 `axe_of_lightning`(右键雷击,无视护甲)、紫颂之刃 `chorus_blade`、末影钣锤 `ender_hammer`、终末金属 `enderitium_*`。

**更多BOSS(BOMD):** 遁地尖矛 `bosses_of_mass_destruction:earthdive_spear`、虚空荆棘 `void_thorn`、充能末影珍珠 `charged_ender_pearl`、灵魂之星 `soul_star`、黑曜石之心 `obsidian_heart`。

**Mowzie 的生物(mowziesmobs):** 地裂护手 `mowziesmobs:earthrend_gauntlet`、满月骇爪 `elokosa_paw_full`、地卜师套 `geomancer_{beads,belt,robe,sandals}`、吹筒 `blowgun`。

**遗物(relics):** 魔镜 `relics:magic_mirror`(回城)、空间传送器 `space_dissector`、暗影飞刃 `shadow_glaive`、无限火腿 `infinity_ham`、岩浆靴 `magma_walker`、狂怒手套 `rage_glove`、弹反项链 `reflection_necklace`。

**傀儡装配(modulargolems,国创):** 组装巨型傀儡(金属傀儡手臂/身体 `metal_golem_arm/body`、傀儡皮肤 `golem_facade`、斩铁巨斧 `golem_slicing_axe`),包内联动"傀儡地牢"。

**星月核心(celestial_core,国创):** 飞升之翼 `celestial_core:soaring_wings`、纯净之星 `pure_nether_star`、死亡/火焰/海洋/虚空精华、监守者骨片 `warden_sclerite`(材料向;合成链以游戏内 JEI 为准)。

**深渊侵蚀者(abyssal_corrupter,国创):** 深渊召唤祭坛 `abyssal_corrupter:abyssal_summoning_altar` + 深渊侵蚀者之卵 `abyssal_corrupter:abyssal_corrupter_spawn_egg`。

**罪业余烬(ash_of_sin,国创):** 类魂 Boss 战 mod,jar 内无语言文件,give ID **待验证**(以游戏内 JEI 为准)。

**薪火造炬成阳(torchesbecomesunlight,国创特供):** 光源机制 + BOSS 圣约·博卓卡斯替(2.1 版最终双 BOSS 之一);特供版与 mod 原版不同。

**梦之石(dream_stone,国创):** `dream_stone:dream_stone`(快速旅行)。

**虫洞药水(wormholepotion):** `wormholepotion:wormhole_potion`(传送到队友处)。

**简易刀剑(simplyswords):** 60+ 特效武器(含符文剑、彩虹剑等),具体 ID 以游戏内 JEI 查询为准;双持配合 bettercombat。

**锻造之艺(tetra):** 模块化武器,`/give` 只能给基础模块(如工具头/手柄),成品需在锻造台装配,故不给具体武器 ID(建议直接给材料或成品模块,详见游戏内手册《Tetra 论》)。

---

## 四、神赐强力物品速查表(物品名 → give 命令)

> 全部命令形如 `/give ludwigxu <id> <数量>`,可自行替换玩家名。来源:jar 语言文件实测 + 网络交叉验证;未验证的标注。

### 毕业级(神装,发一套直接通关体验)

| 物品 | 命令 |
|---|---|
| 天顶剑 | `/give ludwigxu the_zenith_sword:zenith 1` |
| 龙之套×4 | `/give ludwigxu gobber2:gobber2_helmet_dragon 1` 等 4 件 |
| 末地剑 | `/give ludwigxu gobber2:gobber2_sword_end 1`(已实测) |
| 狙击手之剑 | `/give ludwigxu gobber2:gobber2_sword_sniper 1` |
| 龙炎钢剑 | `/give ludwigxu iceandfire:dragonsteel_fire_sword 1`(已实测) |
| 龙霜/龙霆钢剑 | `/give ludwigxu iceandfire:dragonsteel_ice_sword 1` / `dragonsteel_lightning_sword 1` |
| 三系龙钢套 | `/give ludwigxu iceandfire:dragonsteel_fire_chestplate 1` 等(仅头/胸/靴) |
| 腾炎套×4 | `/give ludwigxu cataclysm:ignitium_helmet 1` 等 |
| 炎葬/献祭者/歼灭战锤 | `/give ludwigxu cataclysm:the_incinerator 1` / `the_immolator 1` / `the_annihilator 1` |
| 无止之言 | `/give ludwigxu enigmaticlegacy:the_infinitum 1`(需七咒,本包默认) |
| 如意金箍棒 | `/give ludwigxu lm:jgb 1` |
| 大圣套×4 | `/give ludwigxu lm:dashengtao_helmet 1` 等 |
| 烬灭之刃 | `/give ludwigxu murasama:murasama_fire 1` |
| 密特拉斯 | `/give ludwigxu murasama:murasama_mithras 1` |
| 圣剑-菈 | `/give ludwigxu dragonheart:abelun_sword 1` |
| 魔剑-阿波菲斯 | `/give ludwigxu dragonheart:bad_sword 1` |
| 剑神之戒 | `/give ludwigxu dragonheart:sword_ring 1` |

### 进阶(中后期强力,但还不是神装)

| 物品 | 命令 |
|---|---|
| 末地套×4 | `/give ludwigxu gobber2:gobber2_helmet_end 1` 等 |
| 旅行者之剑 | `/give ludwigxu gobber2:gobber2_sword_traveler 1` |
| 炽铁剑/炽铁套 | `/give ludwigxu twilightforest:fiery_sword 1` 等 |
| 咒魂套×4 | `/give ludwigxu cataclysm:cursium_helmet 1` 等 |
| 虚空锻锤/断魂战戟 | `/give ludwigxu cataclysm:void_forge 1` / `soul_render 1` |
| 虚空/凋灵肩炮 | `/give ludwigxu cataclysm:void_assault_shoulder_weapon 1` / `wither_assault_shoulder_weapon 1` |
| 星光破坏锤 | `/give ludwigxu enigmaticlegacy:astral_breaker 1` |
| 以太阔剑/壮丽鞘翅 | `/give ludwigxu enigmaticlegacy:etherium_sword 1` / `enigmatic_elytra 1` |
| 寂灭之决/星光穿刺者 | `/give ludwigxu enigmaticaddons:annihilating_sword 1` / `astral_spear 1` |
| 十字章护盾/天界石/手机 | `/give ludwigxu confluence:ankh_shield 1` / `celestial_stone 1` / `cell_phone 1` |
| 黑暗套×4 | `/give ludwigxu goety:dark_helmet 1` 等 |
| 无名魔杖/虚空魔杖 | `/give ludwigxu goety:nameless_staff 1` / `void_staff 1` |
| 圣骑村正 | `/give ludwigxu murasama:murasama_posessed_paladin 1` |
| 湮灭者套×4 | `/give ludwigxu legendary_monsters:annihilator_helmet 1` 等 |
| 雷霆之钺 | `/give ludwigxu legendary_monsters:axe_of_lightning 1` |
| 守卫者战斧/守卫者核心 | `/give ludwigxu eeeabsmobs:guardian_axe 1` / `guardian_core 1` |
| 射线枪 | `/give ludwigxu alexscaves:raygun 1` |
| 分裂者 | `/give ludwigxu aquamirae:divider 1` |
| 斩龙/霜噬之刃 | `/give ludwigxu born_in_chaos_v1:darkwarblade 1` / `frostbitten_blade 1` |
| 巨人之锤 | `/give ludwigxu mutantmonsters:hulk_hammer 1` |
| 地裂护手/满月骇爪 | `/give ludwigxu mowziesmobs:earthrend_gauntlet 1` / `elokosa_paw_full 1` |
| 遁地尖矛 | `/give ludwigxu bosses_of_mass_destruction:earthdive_spear 1` |
| 神龙之心 | `/give ludwigxu dragonheart:dragoncurios 1` |
| 飞升之翼 | `/give ludwigxu celestial_core:soaring_wings 1`(效果待验证) |

### 实用(日常体验/女仆/便利)

| 物品 | 命令 |
|---|---|
| 女仆刷怪蛋×64 | `/give ludwigxu touhou_little_maid:maid_spawn_egg 64`(MC百科确认) |
| 大背包(女仆) | `/give ludwigxu touhou_little_maid:maid_backpack_big 1` |
| 博丽的御币 | `/give ludwigxu touhou_little_maid:hakurei_gohei 1` |
| 烹饪中枢 | `/give ludwigxu maidsoulkitchen:culinary_hub 1` |
| 下界合金背包 | `/give ludwigxu sophisticatedbackpacks:netherite_backpack 1` |
| 水晶箱子 | `/give ludwigxu ironchest:crystal_chest 1` |
| 滑翔伞 | `/give ludwigxu paraglider:paraglider 1` |
| 虫洞药水 | `/give ludwigxu wormholepotion:wormhole_potion 8` |
| 治疗勋章 III | `/give ludwigxu gobber2:gobber2_medallion_healing3 1`(禁自然回血下刚需) |
| 经验勋章 | `/give ludwigxu gobber2:gobber2_medallion_exp 1` |
| 凤凰戒指 | `/give ludwigxu gobber2:gobber2_ring_phoenix 1` |
| 末影箱戒指 | `/give ludwigxu gobber2:gobber2_ring_enderchest 1` |
| 错位之戒 | `/give ludwigxu enigmaticlegacy:super_magnet_ring 1` |
| 战后召回卷轴 | `/give ludwigxu enigmaticlegacy:escape_scroll 1` |
| 魔镜 | `/give ludwigxu relics:magic_mirror 1` |
| 空间传送器 | `/give ludwigxu relics:space_dissector 1` |
| 无限火腿 | `/give ludwigxu relics:infinity_ham 1` |
| 龙镜 | `/give ludwigxu lm:lj 1` |
| 梦之石 | `/give ludwigxu dream_stone:dream_stone 1` |
| 湮灭立方 | `/give ludwigxu twilightforest:cube_of_annihilation 1` |
| 末地之眼×12(整套) | `/give ludwigxu endrem:black_eye 1` 等 12 种(开启末地) |
| 深渊侵蚀者之卵 | `/give ludwigxu abyssal_corrupter:abyssal_corrupter_spawn_egg 1`(召唤 Boss) |

---

## 五、Mod 联动关系(哪些要一起玩才有意义)

1. **女仆自动化链**:车万女仆 + 女仆厨房(自动烹饪)+ 农夫乐事/CrockPot/料理乐事/森罗物语酒馆厨具 + 狐步酿香(酿酒)。女仆是"厨房奴隶",缺了食物 mod 意义减半。
2. **龙冒终局链**:镜回(大圣套)+ 龙冒饰品 + 薪火造炬成阳(最终 BOSS 博卓卡斯替)+ 神秘遗物(无止之言/倒转之启对 BOSS 增伤)。圣剑菈/魔剑阿波菲斯/无止之言/倒转之启四件套是针对最终战的官方配装。
3. **泰拉瑞亚彩蛋链**:泰拉饰品(confluence)+ 天顶剑 + 村正 Terraria 变体 + 龙冒"饰品图鉴"任务章节。
4. **村正联动网**:鬼妖村正本体 + 灾厄(烬灭之刃)+ 诡厄巫法启示录(密特拉斯)+ 传奇怪物(圣骑)。没装对应 mod 时变体不可合成(创造/give 可拿)。
5. **诡厄巫法全家桶**:goety + goety_revelation + goety_cataclysm + goety_addition + 帕秋莉手册(黑暗之书教程)。启示录把 goety 延伸成完整流程。
6. **暮色全家桶**:暮色森林 + 暮色另类(魔改)+ 暮色风味乐事(暮色食材)+ 傀儡地牢(巨人武器用暮色材料)+ 地牢结构 mod。暮色是独立维度,建议配合 FTB 任务推进。
7. **冰火与龙**:冰与火之歌(驯龙/龙钢)+ dragonfight(末影龙强化)+ goety 龙息戒指。龙钢毕业装 + 驯龙骑乘是主世界核心玩法。
8. **灾厄 Boss 链**:cataclysm + goety_cataclysm + 村正烬灭之刃 + 罪业余烬(类魂 Boss)。灾厄 Boss 掉落腾炎/咒魂材料。
9. **神秘遗物体系**:enigmaticlegacy + enigmaticaddons + architectbypass + enigmaticdelicacy + curios + soulbound(死亡不掉落,配合七咒死亡惩罚)。七咒之戒强制佩戴是全局规则。
10. **装备品质全局**:quality_equipment 对所有装备生效(含 mod 装备),锻造台重铸;配合 tetra/vvaddon 属性拓展。
11. **战斗手感链**:bettercombat(双持)+ better_combat_reach_fix + playeranimator + 星月改革(剑格挡/伤害百分比化)+ simplyswords(特效武器)。
12. **存储物流链**:精致存储 + 铁箱子 + 精妙背包 + 区块载入器 + 传送石碑(仓库网络)。
13. **生成/战利品魔改链**:incontrol + badmobs + lootjs + lootr + champions + propertymodifier,配合 FTB 任务和 KubeJS 脚本,共同决定"哪里刷什么、掉什么"——这条链由整合包作者定制,玩家无需干预。

---

## 六、注意事项

1. **神赐物品的使用条件**:部分物品有硬性前置——无止之言要求七咒身份(本包默认强制佩戴七咒之戒,OK);炽铁剑合成自带火焰但**锻造升级/附魔继承需注意**;玻璃剑仅创造可用;大圣套 2.1 起无配方(终末圣堂限定,直接 give 绕过)。
2. **装备品质**:所有物品落地时带随机品质(quality_equipment),锻造台可用修复材料重铸;神赐装备品质不满意可重铸,不影响 ID。
3. **禁自然回血**:给玩家发治疗勋章 III / 治愈营火 / 女仆是维持生存的关键;神赐时注意发回血类物品。
4. **口渴系统**(thirst):需要喝水,药水/水瓶同样解渴。
5. **末地之眼**(endrem):要塞传送门被替换,集齐 12 种眼睛才能进末地;直接 give 12 种眼睛可跳过流程。
6. **末影龙强化**(dragonfight):末影龙有 4 阶段强化机制,单挑难度高,建议带龙钢/腾炎装再打。
7. **暮色森林维度**:需在传送门(4×4 水+花围边)跳入;暮色内 Boss 递进,炽铁装备要打完九头蛇才有材料。**注意:暮色另类(alternative_twilight)已魔改暮色生成/结构,攻略可能部分失效。**
8. **冰火龙钢套无护腿**(三件套),配任意护腿即可。
9. **天顶剑模式切换**:物品栏右键切射程(20/40/60/80/100 格),Ctrl+右键切目标,Shift+右键切是否打玩家——神赐后先按 Shift+右键把"打玩家"关掉,避免误伤队友。
10. **村正出鞘机制**:充能 100% 右键出鞘才进入强化状态,一段时间不攻击自动退出。
11. **七咒死亡惩罚**:被诅咒玩家死亡掉落灵魂水晶,配合 soulbound(灵魂绑定)可保装备;死亡后记得捡回灵魂水晶。
12. **女仆刷怪蛋**:1.1.5+ 版本生存模式无法自然获得(仅创造/交易),OP give 是唯一捷径;女仆 AI 对话配置见 02/04 文档。
13. **tetra 模块化武器**:give 只能给模块与材料,武器需在锻造台装配成型——想直接给成品,建议给"锻造之艺"材料包或成品模块(以游戏内 JEI 为准)。
14. **simplyswords 武器**:60+ 把特效武器 ID 未逐一收录,游戏内 JEI 搜索即可(give 格式 `simplyswords:<id>`)。
15. **脚本魔改**(KubeJS/OpenLoader/Paxi):本包大量配方/战利品经脚本改动,**网上攻略配方可能与本包实际不符**,一切以游戏内 JEI 为准。
16. **备份**:FTB 备份2 会自动备份存档,神赐发错东西无碍,可回档或直接用 `/clear` 清理。

---

## 附:参考来源

- MC百科 龙之冒险:新征程 更新日志(整合包 737):https://www.mcmod.cn/modpack/version/737.html
- MC百科 戈伯2(class 2547)、末影剑(item 286696)、龙之鞘翅(item 470032)、龙之胸甲(item 470034)
- MC百科 灾厄 腾炎套装(item 545536)、诡厄巫法 黑暗套装(item 753246)、星光破坏锤(item 219293)、无止之言(item 897621)
- MC百科 天顶剑(class 23975)、鬼妖村正(class 27665)、烬灭之刃(item 956415)
- MC百科 车万女仆 女仆刷怪蛋(item 186592)、女仆厨房(class 17633)、星月改革(class 17665)
- MC百科 暮色森林 炽铁剑(item 3972)、镜回 更新日志(class/version/16931)
- MC百科 Alex 的洞穴 射线枪(item 750162)
- 本机 mods 目录 jar 内 `assets/<modid>/lang/zh_cn.json|en_us.json` 与 `META-INF/mods.toml`(全部 give ID 的本地实证)
