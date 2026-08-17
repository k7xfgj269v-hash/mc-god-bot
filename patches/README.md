# 协议补丁 (protocol patches)

`mineflayer` + `@tcortega/minecraft-protocol-forge` 连 **Forge 1.20.1 (FML3) mod 服**时,
`npm install` 装出来的原版 `minecraft-protocol`/`protodef`/`minecraft-data`/`mineflayer`
有 4 处解析缺陷,会直接导致 bot 连不上(收不到 spawn / 30s keepalive 超时循环 / 断言崩连接)。
这些补丁就是那几处修复。

**重要**:`npm install` 会冲掉 node_modules 里的全部改动。重装后跑一次
`node patches/apply-patches.js` 即可恢复。

---

## 补丁清单

| 文件 | 改动 | 为什么 |
|---|---|---|
| `compression.js` | Decompressor 循环消费 + 二分找 zlib 流边界 | 原版每 chunk 只解第一个包;Forge 把多包合并发送,后续全丢 → bot 收不到 spawn |
| `fml3.json` | `ServerRegistry.snapshot` → `restBuffer` | Forge 握手时该字段结构与定义不符,原版解析会崩断连接流 |
| `protocol.json` | `declare_recipes.recipes` / `unlock_recipes.recipes1` / `entity_metadata.metadata` → `restBuffer` | mod 配方/解锁/实体 metadata 与原版结构不同;bot 不需要,restBuffer 直接吞掉 |
| `simple_inventory.js` (mineflayer) | `setQuickBarSlot` 非法槽位忽略而非断言 | Forge 错位包会发负值/超界 slot,原版 `assert.ok` 直接崩连接 |

## 噪音:用原生选项,不打补丁

mod 服把多包合并进一个 blob,加上 mod 包结构与原版定义不符,反序列化器会频繁
丢弃它解析不完的包——原版会打 "Chunk size is X but only Y was read" 日志或一坨
`PartialReadError` 堆栈。这些是正常保护不是错误(bot 不需要那些包),纯噪音。
`minecraft-protocol` 的 `hideErrors: true`(客户端选项,透传成 deserializer 的
`noErrorLogging`)能一次性压掉这两处,无需任何补丁;真错误仍会通过 `cb(e)` 照常抛出。
之前有一个 `serializer.js` 补丁专压 "Chunk size" 日志,已被这个原生选项取代而删除。

## 压缩层关键设计

`compression.js` 的 `findCompressedLength` 用二分找 zlib 流精确边界,
判定依据是 **「输出长度 == DataLength」的最小前缀**:

- 截断的 zlib 流会返回「部分/空输出」而**从不抛异常**(实测),所以不能用「解出成功」当边界
- 只有吃到流尾才给出完整长度;尾部多余字节被 `unzipSync` 忽略
- 外部分帧器(splitter)已保证每 chunk 是完整帧,帧内解不出的剩余字节是服务器多算的垃圾,丢弃即可

