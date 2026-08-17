'use strict'

const [readVarInt, writeVarInt, sizeOfVarInt] = require('protodef').types.varint
const zlib = require('zlib')
const Transform = require('readable-stream').Transform

module.exports.createCompressor = function (threshold) {
  return new Compressor(threshold)
}

module.exports.createDecompressor = function (threshold, hideErrors) {
  return new Decompressor(threshold, hideErrors)
}

class Compressor extends Transform {
  constructor (compressionThreshold = -1) {
    super()
    this.compressionThreshold = compressionThreshold
  }

  _transform (chunk, enc, cb) {
    if (chunk.length >= this.compressionThreshold) {
      try {
        const newChunk = zlib.deflateSync(chunk)
        const buf = Buffer.alloc(sizeOfVarInt(chunk.length) + newChunk.length)
        const offset = writeVarInt(chunk.length, buf, 0)
        newChunk.copy(buf, offset)
        this.push(buf)
        return cb()
      } catch (err) {
        return cb(err)
      }
    } else {
      const buf = Buffer.alloc(sizeOfVarInt(0) + chunk.length)
      const offset = writeVarInt(0, buf, 0)
      chunk.copy(buf, offset)
      this.push(buf)
      return cb()
    }
  }
}

class Decompressor extends Transform {
  constructor (compressionThreshold = -1, hideErrors = false) {
    super()
    this.compressionThreshold = compressionThreshold
    this.hideErrors = hideErrors
  }

  _transform (chunk, enc, cb) {
    try {
      let offset = 0
      // 循环消费:一个帧(外部分帧后的 chunk)可能包含多个 [DataLength][Data] 包
      // (Forge 合并发送)。原版只处理第一个 → 后续包被丢弃 → bot 收不到 spawn。
      while (offset < chunk.length) {
        const { size, value, error } = readVarInt(chunk, offset)
        if (error || size <= 0) break          // 帧尾残渣,丢弃
        if (value === 0) {
          // 未压缩:无内层长度,整段交给 deserializer 按 [VarInt length] 拆
          this.push(chunk.slice(offset + size))
          return cb()
        }
        // 压缩:二分找 zlib 流精确边界。
        // 外部分帧器已保证 chunk 是完整帧,所以帧内的包必完整;
        // 若在当前数据内解不出 = 这里不是有效包(帧尾垃圾,如服务器长度多算了几字节) → 丢弃
        const clen = findCompressedLength(chunk, offset + size, value)
        if (clen <= 0) return cb()
        let newBuf
        try {
          newBuf = zlib.unzipSync(chunk.slice(offset + size, offset + size + clen), { finishFlush: 2 })
        } catch (err) {
          return cb(err)
        }
        if (newBuf.length !== value && !this.hideErrors) {
          console.error('uncompressed length should be ' + value + ' but is ' + newBuf.length)
        }
        this.push(newBuf)
        offset += size + clen
      }
      return cb()
    } catch (err) {
      if (!this.hideErrors) {
        console.error('decompressor error', err)
      }
      return cb()
    }
  }
}

// 二分找压缩流边界:返回压缩流占用字节数;-1 = 当前数据内找不到完整包
// 判定依据:对 zlib 流,截断前缀会返回「部分/空输出」(实测从不抛异常),只有吃到流尾才给出
// 完整长度;尾巴多余字节被 unzipSync 忽略。所以「输出长度 == DataLength」的最小前缀 = 精确边界。
function findCompressedLength (buf, start, targetLen) {
  const end = buf.length
  if (start >= end) return -1
  let lo = 1
  let hi = end - start
  let found = -1
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2)
    let out = null
    try {
      out = zlib.unzipSync(buf.slice(start, start + mid), { finishFlush: 2 })
    } catch (e) {
      out = null
    }
    if (out && out.length === targetLen) {
      found = mid
      hi = mid - 1 // 找到完整边界,试着找更短的
    } else {
      lo = mid + 1 // 截断(输出<targetLen)或流损坏,需要更多字节
    }
  }
  return found
}
