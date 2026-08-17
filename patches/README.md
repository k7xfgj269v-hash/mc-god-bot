# 协议补丁 (protocol patches)

`mineflayer` + `@tcortega/minecraft-protocol-forge` 连 **Forge 1.20.1 (FML3) mod 服**时,
`npm install` 装出来的原版 `minecraft-protocol`/`protodef`/`minecraft-data` 有 4 处解析缺陷,
会直接导致 bot 连不上(收不到 spawn / 30s keepalive 超时循环)。这些补丁就是那 4 处修复。

**重要**:`npm install` 会冲掉 node_modules 里的全部改动。重装后跑一次
`node patches/apply-patches.js` 即可恢复。

---

## 补丁清单

| 文件 | 改动 | 为什么 |
|---|---|---|
| `compression.js` | Decompressor 循环消费 + 二分找 zlib 流边界 | 原版每 chunk 只解第一个包;Forge 把多包合并发送,后续全丢 → bot 收不到 spawn |
| `serializer.js` | `FullPacketParser._transform` 循环解析 chunk 内所有包 | 服务器把一批包压缩进一个 blob;原版反序列化器只吃第一个包、丢掉剩下并刷 "partial packet" 报错 |
| `fml3.json` | `ServerRegistry.snapshot` → `restBuffer` | Forge 握手时该字段结构与定义不符,原版解析会崩断连接流 |
| `protocol.json` | `declare_recipes.recipes` / `unlock_recipes.recipes1` / `entity_metadata.metadata` → `restBuffer` | mod 配方/解锁/实体 metadata 与原版结构不同;bot 不需要,restBuffer 直接吞掉 |

## 压缩层关键设计

`compression.js` 的 `findCompressedLength` 用二分找 zlib 流精确边界,
判定依据是 **「输出长度 == DataLength」的最小前缀**:

- 截断的 zlib 流会返回「部分/空输出」而**从不抛异常**(实测),所以不能用「解出成功」当边界
- 只有吃到流尾才给出完整长度;尾部多余字节被 `unzipSync` 忽略
- 外部分帧器(splitter)已保证每 chunk 是完整帧,帧内解不出的剩余字节是服务器多算的垃圾,丢弃即可
