#!/usr/bin/env node
/**
 * mc-god-bot 协议补丁应用脚本
 *
 * 每次 `npm install` 会把 node_modules 重装成原版,下面这些补丁全被冲掉,
 * 导致 bot 连不上 mod 服(FML3 握手失败/收不到 spawn/30s 超时循环)。
 * 跑一次本脚本即可把 patches/ 里的改动重新打回去。
 *
 * 用法:node patches/apply-patches.js
 * 说明:脚本会在打每个补丁前后做校验,失败会明确报错(不会半途破坏文件)。
 */
const fs = require('fs')
const path = require('path')

const ROOT = path.join(__dirname, '..')
// 目标 node_modules:默认本仓库安装目录;可被环境变量覆盖(补丁可能打进别的项目)
const NM = process.env.MC_NODE_MODULES || path.join(ROOT, 'node_modules')
const PATCHES = __dirname

function die (msg) {
  console.error('[FAIL] ' + msg)
  process.exit(1)
}

function copyFile (from, to, label) {
  const src = path.join(PATCHES, from)
  const dst = path.join(NM, to)
  if (!fs.existsSync(src)) die(label + ': patches/' + from + ' 不存在')
  fs.copyFileSync(src, dst)
  console.log('[OK] ' + label + ' -> node_modules/' + to)
}

// 1. 整文件替换:压缩层(循环消费多包)。
//    解析噪音(PartialReadError 堆栈 / "Chunk size" 日志)由客户端原生选项
//    hideErrors: true 压掉——原版 FullPacketParser 两处日志都被 noErrorLogging 把关,
//    无需再补丁 protodef serializer.js。
copyFile('compression.js', 'minecraft-protocol/src/transforms/compression.js', 'compression.js')

// 2. 精确字符串替换:fml3.json 的 ServerRegistry.snapshot -> restBuffer
// 注意:JSON 文件可能是 CRLF 行尾,用正则匹配 \n 以兼容 \r?\n
function esc (s) {
  // s 里的 \n 是真实换行符(0x0A),转成正则 `\r?\n` 以兼容 CRLF/LF 文件
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\n/g, '\\r?\\n')
}

function patchFile (rel, pairs, label) {
  const p = path.join(NM, rel)
  if (!fs.existsSync(p)) die(label + ': ' + rel + ' 不存在')
  let s = fs.readFileSync(p, 'utf8')
  let applied = 0
  for (const [old, neu] of pairs) {
    const re = new RegExp(esc(old))
    const neuRe = new RegExp(esc(neu))
    if (!re.test(s)) {
      // 找不到旧片段:可能是「已打过补丁」(幂等) 或文件结构变了
      if (neuRe.test(s)) { console.log('[SKIP] ' + label + ' (已打过)'); continue }
      die(label + ': 找不到目标片段 -> ' + old.slice(0, 60))
    }
    if ((s.match(re) || []).length > 1) die(label + ': 目标片段不唯一 -> ' + old.slice(0, 60))
    s = s.replace(re, neu)
    applied++
  }
  if (applied > 0) {
    fs.writeFileSync(p, s)
    console.log('[OK] ' + label)
  }
}

patchFile('@tcortega/minecraft-protocol-forge/src/client/data/fml3.json', [[
  '"name": "snapshot",\n                      "type": [\n                        "option",\n                        "forge_snapshot"\n                      ]',
  '"name": "snapshot",\n                      "type": "restBuffer"'
]], 'fml3 ServerRegistry.snapshot')

patchFile('minecraft-data/minecraft-data/data/pc/1.20/protocol.json', [
  ['"name": "metadata",\n              "type": "entityMetadata"',
   '"name": "metadata",\n              "type": "restBuffer"'],
  ['"name": "recipes1",\n              "type": [\n                "array",\n                {\n                  "countType": "varint",\n                  "type": "string"\n                }\n              ]',
   '"name": "recipes1",\n              "type": "restBuffer"'],
], 'protocol.json entity_metadata/unlock_recipes')

// declare_recipes 的 recipes 字段是超大数组,用括号配对替换整个 type
{
  const p = path.join(NM, 'minecraft-data/minecraft-data/data/pc/1.20/protocol.json')
  let s = fs.readFileSync(p, 'utf8')
  const markerRe = new RegExp(esc('"name": "recipes",\n              "type": ['))
  const patchedRe = new RegExp(esc('"name": "recipes",\n              "type": "restBuffer"'))
  if (!markerRe.test(s)) {
    if (patchedRe.test(s)) { console.log('[SKIP] protocol.json declare_recipes.recipes (已打过)') }
    else die('protocol.json declare_recipes: 找不到 recipes 字段')
  } else {
    const i = s.search(markerRe)
    const marker = s.slice(i)
    const arrStart = marker.indexOf('[')
    let depth = 0
    let j = arrStart
    for (; j < marker.length; j++) {
      if (marker[j] === '[') depth++
      else if (marker[j] === ']') {
        depth--
        if (depth === 0) break
      }
    }
    if (depth !== 0) die('protocol.json declare_recipes: 括号配对失败')
    const replacement = '"name": "recipes",\n              "type": "restBuffer"'
    s = s.slice(0, i) + replacement + marker.slice(j + 1)
    // 校验 JSON 合法
    try { JSON.parse(s) } catch (e) { die('protocol.json declare_recipes: 替换后 JSON 非法: ' + e.message) }
    fs.writeFileSync(p, s)
    console.log('[OK] protocol.json declare_recipes.recipes')
  }
}

// 3. mineflayer setQuickBarSlot:非法槽位忽略而非断言(Forge 错位包会发负值/超界 slot)
patchFile('mineflayer/lib/plugins/simple_inventory.js', [[
  'assert.ok(slot >= 0)\n    assert.ok(slot < 9)',
  'if (slot < 0 || slot >= QUICK_BAR_COUNT) return // Forge 错位包会发非法槽位,忽略'
]], 'mineflayer setQuickBarSlot')

console.log('\n全部补丁已应用。重启 bot: cd <repo> && pkill -f mc-god-bot; nohup node mc-god-bot.js >> /tmp/mc-god-bot.log 2>&1 &')
