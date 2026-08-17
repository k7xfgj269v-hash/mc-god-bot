// night-vision.js — ludwigxu/PIGGOD 夜视自动补给（2026-08-17 按需新增）
// 死亡会清空效果，此脚本每秒检查一次，没了就自动补上（约 11.5 天）。
PlayerEvents.tick(event => {
    const p = event.player
    if (p.username !== 'ludwigxu' && p.username !== 'PIGGOD') return
    if (event.server.tick % 20 !== 0) return   // 每秒一次
    try {
        if (!p.potionEffects.isActive('minecraft:night_vision')) {
            p.potionEffects.add('minecraft:night_vision', 999999 * 20, 0)
        }
    } catch (e) {}
})
