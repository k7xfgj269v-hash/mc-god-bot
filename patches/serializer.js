const Transform = require('readable-stream').Transform

class Serializer extends Transform {
  constructor (proto, mainType) {
    super({ writableObjectMode: true })
    this.proto = proto
    this.mainType = mainType
    this.queue = Buffer.alloc(0)
  }

  createPacketBuffer (packet) {
    return this.proto.createPacketBuffer(this.mainType, packet)
  }

  _transform (chunk, enc, cb) {
    let buf
    try {
      buf = this.createPacketBuffer(chunk)
    } catch (e) {
      return cb(e)
    }
    this.push(buf)
    return cb()
  }
}

class Parser extends Transform {
  constructor (proto, mainType) {
    super({ readableObjectMode: true })
    this.proto = proto
    this.mainType = mainType
    this.queue = Buffer.alloc(0)
  }

  parsePacketBuffer (buffer) {
    return this.proto.parsePacketBuffer(this.mainType, buffer)
  }

  _transform (chunk, enc, cb) {
    this.queue = Buffer.concat([this.queue, chunk])
    while (true) {
      let packet
      try {
        packet = this.parsePacketBuffer(this.queue)
      } catch (e) {
        if (e.partialReadError) { return cb() } else {
          e.buffer = this.queue
          this.queue = Buffer.alloc(0)
          return cb(e)
        }
      }

      this.push(packet)
      this.queue = this.queue.slice(packet.metadata.size)
    }
  }
}

class FullPacketParser extends Transform {
  constructor (proto, mainType, noErrorLogging = false) {
    super({ readableObjectMode: true })
    this.proto = proto
    this.mainType = mainType
    this.noErrorLogging = noErrorLogging
  }

  parsePacketBuffer (buffer) {
    return this.proto.parsePacketBuffer(this.mainType, buffer)
  }

  _transform (chunk, enc, cb) {
    // Forge 服务器会把多个包合并压缩进同一个 blob,解压层解出的是「多包拼接」,
    // 原版只解析第一个包就把剩下的丢掉 → 丢包。这里循环解析 chunk 内所有包。
    let offset = 0
    try {
      while (offset < chunk.length) {
        const packet = this.parsePacketBuffer(chunk.slice(offset))
        if (packet.metadata.size <= 0) break // 安全:消耗 0 字节说明解析卡住,停止防死循环
        this.push(packet)
        offset += packet.metadata.size
      }
    } catch (e) {
      if (e.partialReadError) {
        if (!this.noErrorLogging) {
          console.log(e.stack)
        }
        return cb()
      } else {
        return cb(e)
      }
    }
    cb()
  }
}

module.exports = {
  Serializer,
  Parser,
  FullPacketParser
}
