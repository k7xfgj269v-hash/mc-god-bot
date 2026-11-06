# 车万女仆 TLM 1.5.3 AI 接入完整文档

> 适用版本:**Touhou Little Maid 1.5.3-forge+mc1.20.1**(Forge 1.20.1-47.2.0,2026-07-17 发布)
> 信息核实来源:TartaricAcid/TouhouLittleMaid 源码(1.20 分支)与 wiki、mcmod.cn、Modrinth、bbsmc.net 更新日志、社区教程(博客园/mcmod 专栏)。标注「未确认」的条目是查不到确切来源的细节,请以实际游戏内表现为准。
>
> 一句话总结:**TLM 本体不含任何 AI 模型**。它只负责把女仆的状态、游戏上下文和你的话发给外部 LLM API,并执行模型返回的「工具调用」(函数调用)。你需要自己准备 LLM 的 API Key(或本地模型),并把站点写进配置文件或直接在游戏里配。

---

## 一、AI 对话功能概述(函数调用、能做什么)

### 1.1 这套系统是怎么设计的

1.5.1 起女仆 AI 聊天按主流 LLM Agent 架构重做,1.5.2/1.5.3 又补了异步工具调用、Minecraft Wiki 查询和 DeepSeek v4 API 兼容。核心概念四个:

| 概念 | 作用 | 类比 |
|---|---|---|
| LLM(大语言模型) | 女仆的"大脑",外部 API,需要自己配 | 人脑 |
| Function Call(工具调用) | 模型返回结构化的调用请求,游戏执行后把结果喂回模型 | 手和脚 |
| Skill(技能/提示词包) | 一段 Markdown 文本,触发时注入对话上下文,教模型"该怎么用工具" | 说明书 |
| Context(上下文) | 女仆/世界的实时状态(血量、工作模式、维度、附近实体等) | 感知 |

对话流程(简化):

```
玩家输入 → 自动注入 Context(status/world)→ 发给 LLM
   ↓ 模型返回文本
女仆说话(气泡/可选 TTS 朗读)
   ↓ 模型返回 tool_calls
游戏执行对应工具 → 结果追加回消息历史 → 再问一次模型 → …(循环,直到模型给纯文本)
```

### 1.2 内置工具(Tool)与上下文(Context)

模组默认注册 7 个工具(可在游戏内用 `/tlm ai_chat tool` 查看当前完整列表):

| 工具 ID | 功能 |
|---|---|
| `use_skill` | 触发已注册的 Skill,做提示词注入或知识检索 |
| `query_game_context` | 按分类查询游戏上下文(装备、位置、附近实体等) |
| `switch_follow_state` | 切换女仆跟随/驻守状态 |
| `switch_work_task` | 切换女仆工作模式(支持指定攻击目标) |
| `switch_schedule` | 切换日程(白天/夜晚/全天工作) |
| `switch_sit` | 切换坐/站状态 |
| `query_minecraft_wiki` | 查询 Minecraft Wiki(1.5.2 新增,异步执行,气泡会显示"正在翻阅 Wiki…") |

默认上下文分类:`status`、`world` 两条**自动注入**;`equipment`、`user`、`effects`、`position`、`nearby_entities`(最多 20 个)按需由 `query_game_context` 查询。

### 1.3 能做什么(能力边界)

- **用自然语言指挥女仆干活**:切工作模式(1.5.0 起可在**全部**工作模式间切换,不再只限攻击模式)、开/关跟随、坐下、换日程、设定攻击目标——一句话的事,例如「去打那只僵尸」。
- **提问游戏知识**:女仆会查 Minecraft Wiki 回答合成表、机制类问题。
- **查询女仆自己**:通过工具问"你身上有什么""附近有什么生物",模型按需调工具,不会一股脑灌 token。
- **防御机制**:工具调用链有最大轮数上限(社区资料称 16 轮)与连续重复调用熔断(连续 2 次相同调用即停),防止无限循环烧 token;模型幻觉/调错工具时自动重试引导自纠;每次对话前校验消息历史结构(修复了 DeepSeek 高频 HTTP 400);女仆实体不存在时立刻终止会话。
- **上下文压缩**:对话历史按 token 数(默认阈值 48K,见第六章配置)压缩摘要,长任务连贯性更好;对话缓存命中率 1.5.1 从约 50% 提到约 85%,省钱省时间。
- **每个玩家独立 Token 限额**:服务端累计每个玩家的消耗 token,超过 `MaxTokensPerPlayer`(默认无上限)后拒绝对话。

### 1.4 已知不兼容

官方 1.5.1 日志声明:AI 重构后仅《车万女仆:纸短情长》(Epistalove)附属存在兼容性崩溃,其余附属均兼容。

---

## 二、接入 LLM(llm.json)

### 2.1 站点配置文件在哪

游戏目录下(以官方启动器为例):

```
.minecraft/versions/<版本名>/config/touhou_little_maid/sites/
├── llm.json   # LLM 站点
├── tts.json   # 语音合成站点
└── stt.json   # 语音识别站点
```

首次启动游戏后会自动生成这三个文件,里面是**内置默认站点**(DeepSeek、阿里云、硅基流动、豆包、智谱、MiniMax、Kimi、Gemini、Grok、OpenRouter、Player2、OpenAI 等)。

> 注意:网上不少老教程(2025 年及更早)教你改 `config-touhou_little_maid/available_sites.yml`,那是 **1.5.x 之前的旧格式**(`type: chat`、`api_key` 字段),**1.5.3 已废弃**,请直接改 `sites/*.json`。

### 2.2 修改后如何生效

- 命令热重载:`/tlm ai_chat reload`(需要 OP,权限等级 2)。等价于重启时做的 `AvailableSites.init()`,会重新读三个 json 并回写。
- 或者在游戏里右键女仆打开 AI 界面操作(见第四章),保存时立即生效。
- **坑**:文件读取出错(JSON 语法错误)时,游戏会记日志然后**把默认站点回写覆盖文件**,所以手改文件前先备份,改完立刻重载验证。

### 2.3 字段说明(通用 Site 字段,三个 json 通用)

每个站点是一个对象,站点 ID 作为键。字段(源码 `Site.java` 定义):

| 字段 | 必填 | 含义 |
|---|---|---|
| `id` | 是 | 站点唯一标识,不含空格/非英文字符 |
| `api_type` | 是 | 协议类型。**LLM 目前只有 `openai`**(OpenAI 兼容端点);STT 有 `player2/aliyun/siliconflow/tencent`;TTS 有 `player2/fish-audio/gpt-sovits/siliconflow/minimax/system` |
| `enabled` | 是 | 是否启用,关掉后在游戏里不显示 |
| `icon` | 是 | 图标贴图,默认 `touhou_little_maid:textures/gui/ai_chat/<id>.png` |
| `url` | 是 | API 端点地址 |
| `secret_key` | 是 | 密钥(OpenAI 风格站点会拼成 `Authorization: Bearer <secret_key>`) |
| `headers` | 是(可空对象) | 附加 HTTP 请求头(JSON 对象),如 OpenRouter 的 Referer |
| `models` | 是 | 模型列表(LLM/TTS 含义不同,见下) |
| `has_thinking_field` | 否,默认 false | 响应里是否带 thinking 字段(DeepSeek v4、豆包、智谱、Kimi 等国内推理模型需要,1.5.3 默认站已自动修正) |
| `secret_id` | 否 | 仅腾讯云 ASR 用 |
| `site_model` | 否 | 仅 MiniMax TTS 用:TTS 合成模型,与 `models`(那里是音色 voice_id)不同 |
| `eng_ser_vice_type` | 否 | 仅腾讯云 ASR:引擎服务类型,默认 `16k_zh` |
| `hot_word` | 否 | 仅腾讯云 ASR:热词,格式 `词|权重`,如 `slime|100,creeper|80` |

LLM 的 `models` 有两种写法:

```json
"models": [
  "deepseek-v4-flash",
  { "name": "gpt-5.2", "reasoning": true }
]
```

- 普通字符串 = 普通模型;
- 对象 = 推理模型(`reasoning: true`),请求时系统消息会用 OpenAI 新版的 `developer` 角色、并禁用 thinking 字段(如果站点开了 `has_thinking_field`)。
- `reasoning` 字段在文件里只有推理模型才会显式写出(`reasoning: false` 时序列化为普通字符串)。

### 2.4 完整真实示例(1.5.3 默认生成内容风格)

**llm.json** —— 填 Key 就能用的 DeepSeek 站点 + 一个本地 Ollama 站点 + 一个走中转的 OpenAI 兼容站点:

```json
{
  "deepseek": {
    "id": "deepseek",
    "api_type": "openai",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/deepseek.png",
    "url": "https://api.deepseek.com/chat/completions",
    "secret_key": "YOUR_DEEPSEEK_KEY",
    "has_thinking_field": true,
    "headers": {},
    "models": [
      "deepseek-v4-flash",
      "deepseek-v4-pro"
    ]
  },
  "ollama_local": {
    "id": "ollama_local",
    "api_type": "openai",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/ollama_local.png",
    "url": "http://127.0.0.1:11434/v1/chat/completions",
    "secret_key": "ollama",
    "has_thinking_field": false,
    "headers": {},
    "models": [
      "qwen3:8b"
    ]
  },
  "my_proxy": {
    "id": "my_proxy",
    "api_type": "openai",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/my_proxy.png",
    "url": "https://your-relay.example.com/v1/chat/completions",
    "secret_key": "YOUR_RELAY_KEY",
    "has_thinking_field": false,
    "headers": {
      "HTTP-Referer": "https://github.com/TartaricAcid/TouhouLittleMaid"
    },
    "models": [
      "gpt-5.2",
      { "name": "gpt-5.4", "reasoning": true }
    ]
  }
}
```

要点:

- 任何 OpenAI 兼容端点都能接:**url 直接写 `…/chat/completions`**(不要只写到 `/v1`)。Ollama 开 `OLLAMA_HOST` 后天然提供 `/v1/chat/completions`,所以本地模型直接这样配。
- `secret_key` 为空时,游戏里切到该站点会提示"DeepSeek API 密钥未配置"(默认提示文案就是引导注册 DeepSeek)。
- 国内推理模型(DeepSeek v4、豆包、智谱、Kimi、部分硅基流动模型)记得 `has_thinking_field: true`,否则可能报 400 或把思考内容当正文。
- MiniMax 站点的系统消息会被模组合并(该 API 不支持多条 system 消息),不用你操心。
- 1.5.3 内置默认站点清单(无需配置,填 Key 即用):DeepSeek `https://api.deepseek.com/chat/completions`、阿里云 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`、硅基流动 `https://api.siliconflow.cn/v1/chat/completions`、豆包 `https://ark.cn-beijing.volces.com/api/v3/chat/completions`、智谱 `https://open.bigmodel.cn/api/paas/v4/chat/completions`、MiniMax、Kimi `https://api.moonshot.cn/v1/chat/completions`、Gemini、Grok、OpenRouter、Player2(`http://127.0.0.1:4315/v1/chat/completions`,需本地装 Player2 App,见 3.4)。

### 2.5 其他相关配置(common 配置文件 [ai] 段)

游戏还提供一份 Forge 配置(通常位于 `config/touhou_little_maid/common.toml`,文件名以实际生成为准;未确认文件名),`[ai]` 段字段(源码 `AIConfig` 定义):

| 配置项 | 默认 | 说明 |
|---|---|---|
| `LLMEnabled` | true | AI 对话总开关 |
| `AutoGenSettingEnabled` | true | 人设缺失时自动生成角色设定文件 |
| `LLMProxyAddress` | 空 | LLM HTTP 代理,如 `127.0.0.1:1080`;**仅支持 HTTP 代理,不支持 SOCKS** |
| `MaidHistoryCompressTokenLimit` | 48 | 历史压缩阈值,单位 K token(1K=1024),范围 8~1024 |
| `MaxTokensPerPlayer` | 2147483647 | 单玩家累计 token 上限 |
| `TTSEnabled` | true | TTS 开关 |
| `TTSLanguage` | en_us | TTS 语言,会被女仆的设置覆盖 |
| `TTSProxyAddress` | 空 | TTS 代理(同样仅 HTTP) |
| `STTEnabled` | true | STT 开关 |
| `STTType` | player2 | STT 类型(player2/aliyun/siliconflow/tencent) |
| `STTMicrophone` | 空 | 麦克风设备名,空 = 默认设备 |
| `MaidCanChatDistance` | 12 | 语音聊天搜索女仆的半径(格) |
| `STTProxyAddress` | 空 | STT 代理(同样仅 HTTP) |

---

## 三、语音 STT/TTS 接入

### 3.1 总流程

按住 **X 键**(默认)对女仆说话 → 松开 → 音频发给 STT 站点识别成文字 → 文字作为消息发给 LLM → 回复文本发给 TTS 站点合成语音 → 客户端播放。三段链路彼此独立,各配各的站点。

### 3.2 STT(语音识别)——4 种服务商

| api_type | 默认端点 | 需要填的字段 | 说明 |
|---|---|---|---|
| `player2`(默认) | `http://127.0.0.1:4315/v1/stt` | headers 里带 `player2-game-key: TouhouLittleMaid` | 配合本地 Player2 App(见 3.4) |
| `siliconflow` | `https://api.siliconflow.cn/v1/audio/transcriptions` | `secret_key` + `model`(默认 `FunAudioLLM/SenseVoiceSmall`) | 推荐,便宜大碗 |
| `aliyun` | `https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr` | `secret_key` + `app_key`,可选 `vocabulary_id`、`customization_id`、`enable_punctuation_prediction`、`enable_inverse_text_normalization`、`enable_voice_detection`、`disfluency` | 阿里云智能语音交互 |
| `tencent` | `https://asr.tencentcloudapi.com` | `secret_id` + `secret_key` + `eng_ser_vice_type`(默认 `16k_zh`) + 可选 `hot_word`(热词,格式 `slime\|100,creeper\|80`) | 腾讯云 ASR,签名由模组自动算 |

**stt.json 完整示例**:

```json
{
  "siliconflow": {
    "id": "siliconflow",
    "api_type": "siliconflow",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/siliconflow.png",
    "url": "https://api.siliconflow.cn/v1/audio/transcriptions",
    "secret_key": "YOUR_SILICONFLOW_KEY",
    "model": "FunAudioLLM/SenseVoiceSmall"
  },
  "tencent": {
    "id": "tencent",
    "api_type": "tencent",
    "enabled": false,
    "icon": "touhou_little_maid:textures/gui/ai_chat/tencent.png",
    "url": "https://asr.tencentcloudapi.com",
    "secret_id": "YOUR_TENCENT_SECRET_ID",
    "secret_key": "YOUR_TENCENT_SECRET_KEY",
    "eng_ser_vice_type": "16k_zh",
    "hot_word": "slime|100,creeper|80"
  }
}
```

> 注意 STT 站点的 `models` 字段不存在,硅基流动的模型名在独立的 `model` 字段里;腾讯云用的是 `secret_id` 而非仅 `secret_key`。

### 3.3 TTS(语音合成)——6 种服务商

| api_type | 默认端点 | 关键字段 | 说明 |
|---|---|---|---|
| `system` | 无(本地) | 无 | 游戏内置朗读(Minecraft Narrator),纯客户端,不花钱不联网 |
| `player2` | `http://127.0.0.1:4315/v1/tts/speak` | `models` 是音色 UUID→名称表 | 配合 Player2 App,内置 10 个音色(中英日西法葡) |
| `fish-audio` | `https://api.fish.audio/v1/tts` | `secret_key` + `models`(音色表,默认含 Neuro-sama、纳西妲、芙宁娜、雷电、流萤等) | 1.5.3 修了 400 兼容问题 |
| `gpt-sovits` | `http://127.0.0.1:9880/tts` | `secret_key`(任意非空)、`ref_audio_path`(参考音频)、`prompt_text`、`prompt_lang`(zh/ja/en/auto)、`text_split_method`(cut0~cut5)、`aux_ref_audio_paths` | 本地克隆音色,需自己改 api 代码(见 3.5) |
| `siliconflow` | `https://api.siliconflow.cn/v1/audio/speech` | `secret_key` + `models`(音色表,键为「模型:音色」格式,如 `FunAudioLLM/CosyVoice2-0.5B:anna`,默认 anna/bella/claire/diana 四音色) | 硅基流动语音;请求体 `model` 固定为 `FunAudioLLM/CosyVoice2-0.5B`,`voice` 原样发送所选键(不解析冒号,源码确认) |
| `minimax` | `https://api.minimaxi.com/v1/t2a_v2` | `secret_key` + `site_model`(默认 `speech-2.8-turbo`)+ `models`(音色表,成熟女声/软妹/元气等) | 国内音质最好的之一 |

**tts.json 完整示例**(GPT-SoVITS 本地 + MiniMax 云端):

```json
{
  "gpt-sovits": {
    "id": "gpt-sovits",
    "api_type": "gpt-sovits",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/gpt-sovits.png",
    "url": "http://127.0.0.1:9880/tts",
    "secret_key": "anything",
    "ref_audio_path": "refer_wave/小狐狸/参考音频.wav",
    "prompt_text": "参考音频的文本内容",
    "prompt_lang": "zh",
    "text_split_method": "cut1",
    "aux_ref_audio_paths": [],
    "headers": {}
  },
  "minimax": {
    "id": "minimax",
    "api_type": "minimax",
    "enabled": false,
    "icon": "touhou_little_maid:textures/gui/ai_chat/minimax.png",
    "url": "https://api.minimaxi.com/v1/t2a_v2",
    "secret_key": "YOUR_MINIMAX_KEY",
    "site_model": "speech-2.8-turbo",
    "headers": {},
    "models": {
      "Chinese (Mandarin)_Mature_Woman": "成熟女声(中)",
      "Chinese (Mandarin)_Warm_Girl": "温暖少女(中)",
      "Japanese_DecisivePrincess": "坚定公主(日)"
    }
  },
  "system": {
    "id": "system",
    "api_type": "system",
    "enabled": true,
    "icon": "touhou_little_maid:textures/gui/ai_chat/system.png"
  }
}
```

要点:

- TTS 的 `models` 是 **音色名→显示名** 的映射(不是模型名),聊天界面里会显示显示名。
- TTS 语言遵循 ISO 639-1(`zh`/`ja`/`en` 等),由女仆 AI 设置里的语言选项控制,未指定时用 `TTSLanguage` 配置。**如果模型不支持对应语言,合成会失败或效果差**(比如本地小模型不会日语却要求日语输出)。
- 想在聊天界面里关掉朗读:把 TTS 站点选成「无」(1.5.1 起支持)。
- **硅基流动 TTS 请求体细节(源码 `TTSSiliconflowClient` 确认)**:请求 JSON 的 `model` 字段**固定为常量 `FunAudioLLM/CosyVoice2-0.5B`**(与配置无关);`voice` 字段 = 你选中的 models 字典的**整个 key 原样发送,不解析冒号**。所以 `models` 里写 `"FunAudioLLM/CosyVoice2-0.5B:anna": "anna"`,请求的 voice 就是 `"FunAudioLLM/CosyVoice2-0.5B:anna"`;写成 `"anna": "anna"` 则 voice 为 `"anna"`。其余固定参数:`response_format: opus`、`sample_rate: 48000`、`stream: false`、`speed: 1`、`gain: 0`。若实测 API 对 voice 报错,改 key 格式即可(改完 `/tlm ai_chat reload`)。

### 3.4 Player2 App(零配置方案)

TLM 默认把 `player2` 站点指向 `http://127.0.0.1:4315`,带 `player2-game-key: TouhouLittleMaid` 请求头。这是 **Player2 官方本地 App**(player2.game)提供的聚合服务:装好 App、登录后,它会同时在本地提供 OpenAI 格式的 chat、STT、TTS 三个 API,含 10 个预置音色。适合不想折腾多家 API 的用户。

### 3.5 本地 TTS 改造方案(GPT-SoVITS,社区教程)

TLM 原生只兼容 Fish Audio,接 GPT-SoVITS 需要改一行接口名(社区已验证的教程,博客园 chy-2003):

1. 复制 `api.py` 为 `api-tlm.py`;把 `@app.post("/")` 和 `@app.get("/")` 改成 `/tts`(TLM 访问的就是 `/tts`)。
2. 补全请求字段(语言、cut_punc、top_k 等,TLM 会传这些)。
3. 返回值改回 opus 格式(用 ffmpeg 转 `audio/opus`,否则长文本容易失败)。
4. 启动:`runtime\python.exe api-tlm.py -dr <参考音频> -dt <参考文本> -dl ja`,看到 `Uvicorn running on http://0.0.0.0:9880` 即成功。
5. 改好的 api-tlm.py 有现成版:https://gitee.com/chy-2003/share/blob/master/api-tlm.py

---

## 四、游戏内使用指南

### 4.1 怎么获得女仆(召唤)

1. 收集 **P 点(灵力)**:击杀生物、战利品箱都有掉落;P 点物品丢出去即可吸取。
2. 造 **祭坛**:由羊毛等方块搭建(1.5.0 起检测更宽松,右键中间两块羊毛即可,朝向不限;具体结构细节未确认,游戏内合成书/帕秋莉手册有图示)。
3. 手持 **御币(祓串/garakuto,博丽御币或风祝御币)** 右键祭坛,消耗 P 点生成女仆(1.5.0 起御币耐久 300→1200)。生成的第一个女仆以召唤者为默认主人。

### 4.2 打开 AI 对话界面

- **准星对准你自己的女仆,按 T(聊天键)**:经过服务端鉴权后打开 AI 聊天界面。1.5.1 起女仆原始 GUI 里的 AI 标签页已移除,所有 AI 设置都在这个面板。
- 界面里:底部输入框输入文字回车发送;按钮从左到右分别是——聊天记录、角色设定编辑、设置(站点配置)、**LLM 站点/模型选择**、**TTS 站点/模型选择**、**TTS 语言选择**;面板实时显示累计 Token 消耗。
- 输入框支持 **↑/↓ 键**调取历史输入。
- 女仆思考时气泡显示"少女思考中……",调用工具时实时显示"正在调用 xxx"。

### 4.3 切换站点 / 配置站点

- 普通玩家:聊天界面里直接点 LLM/TTS 按钮切换站点与模型(只限于已配置且 `enabled` 的站点)。
- **站点配置(增删改)需要 OP 权限**(单人/局域网房主自带;服务器需要权限等级 2):聊天界面 → 设置 → 🏠 站点配置 → 分别管理 LLM / TTS / 语音输入(STT)的站点与 STT 配置。支持完全在游戏内新建、编辑、删除站点,无需手改 JSON;修改即时生效。
- 服务端配置里的 `secret_key` 不会下发给客户端(仅服务端持有,请求由服务端发出)。

### 4.4 语音对话

- 默认键 **X**:按住开始录音,松开停止并发送(自动找 12 格内最近的女仆,`MaidCanChatDistance` 可改)。找不到女仆会提示"在你 X 个方块内没有可以交谈的女仆"。
- 先决条件:`LLMEnabled` 和 `STTEnabled` 均为 true,STT 站点启用,并且电脑有麦克风(否则提示"没有找到麦克风设备")。

### 4.5 常用指令(全部在 `/tlm` 下,需要 OP)

| 指令 | 作用 |
|---|---|
| `/tlm ai_chat reload` | 重载 `sites/*.json` 与技能文件(改完配置必备) |
| `/tlm ai_chat tool` | 列出当前所有可用工具 |
| `/tlm ai_chat context` | 列出所有可用游戏上下文分类 |
| `/tlm ai_chat skill` | 列出已加载的技能 |
| `/tlm ai_chat tokens get <玩家>` | 查看玩家累计消耗 token |
| `/tlm ai_chat tokens handle set/add/min <玩家> <数量>` | 设置/增加/扣减玩家 token 额度 |
| `/tlm power get/handle` | 查看/修改 P 点 |

### 4.6 人设(角色设定)文件

每个模型的角色设定是 YAML 文件,放在 `config/touhou_little_maid/settings/`(支持 8 层子目录)或资源包 `assets/<domain>/settings/`(1 层)。`model_id` 声明该人设作用于哪些站点模型(可多个)。`AutoGenSettingEnabled` 开启时,没配人设的模型第一次对话会自动生成。

```yaml
meta:
  version: 0
  author: "你的名字"
  model_id:
    - deepseek
  language: "zh_cn"
setting: |
  你是一只温柔的女仆,名字叫灵梦。
  说话时简短可爱,称呼主人为"主人"。
  可以执行主人要求的任何任务。
```

- `setting` 支持 PAPI 变量替换(如女仆血量、名字等)。
- 技能文件(Skill)格式与扩展开发细节见官方 wiki `docs/wiki/dev/ai/`(overview / tool / context / skill / task 五篇)。

### 4.7 联机时:谁配什么(请求发生在哪一侧,源码级结论)

按源码调用链逐一确认(1.20 分支 = 1.5.3):

| 请求 | 发生侧 | 依据(类/调用位置) |
|---|---|---|
| **LLM API 请求** | **服务器侧** | 聊天 UI(客户端 `AIChatScreen` 592 行)输入 → C2S 包 `SendUserChatMessage`(maidId+文本+clientInfo)→ 服务器 handler 校验女仆归属 → `MaidAIChatManager.chat(String, ChatClientInfo, ServerPlayer)` → `LLMOpenAIClient.chat()` 在服务器进程发 HTTP 请求 |
| **STT 语音识别** | **客户端侧** | `STTCallback` 标注 `@OnlyIn(Dist.CLIENT)`;`STTChatKey`(X 键)是客户端输入事件;源码注释原文:「客户端不需要同步 STT 站点信息,因为 STT 就是在客户端使用的」。识别出的文本再经 `SendUserChatMessage` 发到服务器走 LLM 流程 |
| **TTS 合成** | **服务器合成,音频下发客户端播放** | `TTSCallback.onSuccess` 检查 `maid.level instanceof ServerLevel`,合成出的音频字节经 `TTSAudioToClientMessage`(S2C)发给女仆主人;「系统 TTS」同理:服务端发 `TTSSystemAudioToClientMessage`,客户端用游戏朗读器播放 |
| **女仆模型文件** | **客户端加载,服务器只同步模型 ID** | 模型包是客户端资源包(`ClientPackDownloadManager`、`ModelDownloadGui` 均在 client 包);服务器经 `MaidModelMessage`(C2S)/`YsmMaidModelMessage` 只同步模型标识字符串 |

**实操含义**:

- 专用服务器联机时,**llm.json、tts.json 只需要服务器配**(密钥只在服务器进程,`ClientAvailableSitesSync` 同步到客户端的只有「站点 ID → 模型名」表,不含密钥);朋友不需要各自填 Key,直接选服务器上已配置的站点和模型即可。
- **STT 例外:每个客户端各自配置**(stt.json 在各自客户端的 config 目录,语音识别请求从自己电脑发出,Key 也留在自己机器)。
- 客户端不开 AI 设置权限(非 OP)也能聊天,只是不能增删改站点。

---

## 五、AI 附属扩展一览

| 扩展 | 作者/来源 | MC / Loader | 前置要求 | 核心功能 | 1.20.1 可用 |
|---|---|---|---|---|---|
| **女仆生存**(TLMMS, Maid-Survival) | mcmod.cn/class/29280,Modrinth `tlm-maid-survival` | 1.20.1~1.20.6 Forge | **TLM 1.5.3-forge+mc1.20.1**(必需,1.9.6 版依赖)+ 可选 Cloth Config API | 生存增强:女仆按环境自动切换主手物品;低血量自动回魂符(有代价 DEBUFF)、鞘翅虚空救援、下界合金防火、海龟壳水下呼吸;卡地形时搭桥/搭高/挖掘的路径辅助;拴绳栓动物互动;四个模式——冒险(战斗护主)、生存(农牧)、旁观者(穿墙飞行,需解锁,联动 YSM 动画)、创造(锁血免伤、授权后执行指令、用 TLM AI 观察环境) | ✅ |
| **朝夕相伴**(Companionship) | GitHub Re-Summer75/Touhou-Little-Maid-Companionship(分支 `1.20.1`) | 1.20.1 **Forge 47.4.0+** | **TLM >= 1.5.3**(必需) | 成长与等级、每只女仆独立的原版进度树、独立饥饿/健康/自动进食(零食柜)、面部追踪喂食等沉浸互动、VRM 弹簧骨二级物理、环境风场、渲染法线修正;**自由模式下的数据驱动意图 AI**(Utility 评分,15 个内置意图,Data Pack `maid_ai/` 定义,可用 `/tlmcompanionship ai explain <女仆>` 查看当前决策解释);配置在 `config/tlm_companionship/` | ✅ 当前 v0.1.0 测试期 |
| **遥控女仆**(Telepathic Maid) | mcmod.cn/class/22390,Modrinth/CurseForge `telepathic-maid` | 1.20.1~1.20.6 Forge/Fabric | **勤劳跟踪狂(Diligent Stalker)1.1.0**(必需,mcmod 19577);TLM 具体版本要求未确认 | 拍照 + 粘土雕像烧制 + 潜行右键绑定女仆 → 进入"遥操控"模式:共享女仆视角、WASD 直接操控移动、滚轮切任务、开女仆 GUI;任意距离(自动强制加载区块);不可跨维度。键位:R 退出/C 切换操控/V 切换视角模式/E 开女仆 GUI | ✅ |
| **Little-Maid-Harvest-Helper**(小女仆丰收助手) | GitHub niumadadi520/Little-Maid-Harvest-Helper | 1.20.1 **Forge 47.4.22** Java 17 | **TLM 1.5.3**(必需) | 给农场模式补"右键采摘":甜浆果、发光浆果及其他右键采摘类作物(按注册名关键词 `berry/fruit/vine` 等与成熟属性 `ripe/mature` 识别),收获后保留植株,掉落物进女仆库存 | ✅ |
| **MIMO 语音合成**(TouhouLittleMaid MiMo TTS) | mcmod.cn/class/29490,CurseForge | **NeoForge 1.21.1** | TLM 前置 | 小米 MiMo TTS:预置音色 + 语音克隆(参考音频放服务端 `config/touhou_little_maid/mimo-clone/`,Base64 ≤10MB)、语言跟随游戏语言、MP3 输出 | ❌ **无 1.20.1 Forge 版** |

**选装建议**:

- 想要"女仆更像活人、能自主决策" → 朝夕相伴(与 TLM 1.5.3 的 AI 工具体系互补,自由模式不干扰其他工作模式,边界有 GameTest 保证)。
- 想要"女仆在生存流程里不暴毙、自动换工具" → 女仆生存。
- 想"亲自上号操作女仆"(PVP、远距离挂机操作)→ 遥控女仆(注意它依赖勤劳跟踪狂,且不能跨维度)。
- 种浆果/果园向生存 → 丰收助手(小而专,单点补足农场模式缺陷)。
- 语音克隆想用小米 MiMo → 1.20.1 玩家暂无官方途径,可考虑 GPT-SoVITS 本地方案(3.5 节)。

---

## 六、常见问题与排查

**1. 提示"没有可用的 LLM/TTS/STT 站点"**
检查 `sites/*.json` 里对应文件存在、站点 `enabled: true`、文件 JSON 合法;然后 `/tlm ai_chat reload` 或重启。语法错误会被默认站点覆盖(见 2.2),务必先备份。

**2. 配了 Key 还是连不上/无响应**
- 确认 `url` 写的是完整的 `…/chat/completions` 路径;
- 确认 Key 有效(可在浏览器/Postman 里用 `curl -H "Authorization: Bearer YOUR_KEY" -X POST <url>` 试);
- 服务器在国内、API 在海外,或反过来的,检查 `LLMProxyAddress`/`TTSProxyAddress`/`STTProxyAddress`(只支持 HTTP 代理,不支持 SOCKS);
- 中转站响应慢导致 AI 无响应:TLM 无超时配置项,若中转慢建议选更快模型或换更近的节点;
- 服务端日志搜 `touhou_little_maid` 的 `Error in LLM Request Sending/Received`。

**3. DeepSeek / 国内模型报 HTTP 400**
1.5.3 已修复:消息历史发送前会校验结构,DeepSeek 站点自动 `has_thinking_field: true`。仍报 400 时:确认模型名没填旧的 `deepseek-chat`/`deepseek-reasoner`(2026-07-24 起官方弃用,游戏会自动修正为 `deepseek-v4-flash`/`deepseek-v4-pro`);确认人设文件 `model_id` 写的模型名与站点 models 一致。

**4. 模型不支持函数调用/不会用工具**
- 有些模型(尤其是某些本地小模型、纯推理模型如 deepseek-r1/qwq 系列)的输出格式与 TLM 不兼容(社区 issue #809 有记录),表现为女仆只会聊天、不干活或连续报错;
- 解法:换支持 function calling 的模型(推荐 DeepSeek v4、GLM、Qwen、GPT、Claude 等主流 API),本地部署建议 qwen3 系 4b/8b/32b(注意给 TTS 和光影留显存);
- 可在 `/tlm ai_chat tool` 确认工具列表非空,并在聊天气泡里看"正在调用 xxx"确认调用过程。

**5. 语音识别失败**
- "没有找到麦克风设备":检查系统麦克风权限,或设 `STTMicrophone` 指定设备;
- "在你 X 个方块内没有可以交谈的女仆":站近点或调大 `MaidCanChatDistance`;
- "你好像什么都没说":录音太短/太安静;
- SiliconFlow STT 422:1.5.1 已修复,升级即可。

**6. TTS 不出声**
- 检查 TTS 站点选的是不是「无」;检查 `TTSEnabled`、站点 `enabled`;
- 本地 TTS(GPT-SoVITS)要确认 `url` 是 `http://127.0.0.1:9880/tts` 且服务已启动;
- 语言不匹配:模型不支持所选语言(如本地模型不会日语却选了 ja),把语言选项改成模型支持的;
- Fish Audio 400:1.5.3 已修复,升级版本。

**7. Token 消耗异常/超限**
- 用 `/tlm ai_chat tokens get <玩家>` 查消耗;`MaxTokensPerPlayer` 限总消耗,`MaidHistoryCompressTokenLimit`(默认 48K token)控制历史压缩阈值;
- 工具调用链有轮数与连续重复熔断保护,正常不会无限循环;担心幻觉调用就把模型换强一点。

**8. 站点配置保存失败/被还原**
- 站点配置需要 OP;非 OP 玩家打开设置面板会提示"权限不足!";
- 服务端/客户端都要装 TLM 才能用 AI;LLM/TTS 请求在**服务器**发起、TTS 音频由服务器下发,所以专用服务器只需服务器配 llm.json/tts.json;**STT 在各自客户端**发起,联机玩家要用语音得在自己客户端配好 STT 站点(见 4.7);
- 文件被还原 = JSON 语法错误后默认值回写,备份 + 用在线 JSON 校验器先检查。

**9. 已知兼容雷区**
- 纸短情长(Epistalove)附属与 1.5.1+ AI 重构不兼容(官方声明);
- 旧教程的 `available_sites.yml` 格式已废弃,勿照抄;
- 多版本混装(1.20.1 客户端 + 1.21.1 服务端)不保证 AI 功能正常(未确认,官方未声明支持混搭)。

---

## 附:现成的脚本/工具

| 工具 | 用途 | 获取方式 |
|---|---|---|
| Player2 App | 本地一键聚合 LLM/STT/TTS 三合一服务,TLM 内置 player2 站点直连 | player2.game(需登录) |
| 游戏内模型下载 | TLM 主界面自带的模型包下载功能(非 AI 相关,但常被配套使用) | 游戏内模型下载按钮 |
| Ollama | 本地 LLM 部署,接 `http://127.0.0.1:11434/v1` | ollama.com |
| GPT-SoVITS 一键包 + api-tlm.py | 本地 TTS 克隆音色;api-tlm.py 是社区改好的 TLM 兼容版 | gitee.com/chy-2003/share/blob/master/api-tlm.py(教程:博客园 chy-2003) |
| 官方默认模型包 | TLM 默认模型/贴图资源 | 仓库 `default-model-pack` 分支 |
| 官方 wiki 文档 | AI 扩展开发(工具/上下文/技能/任务) | wiki 分支 `docs/wiki/dev/ai/` |

官方**没有**现成的批量配置脚本(未确认);`sites/*.json` 是纯 JSON,可自己写脚本按模板批量生成站点。

---

## 主要信息来源

- 官方仓库:TartaricAcid/TouhouLittleMaid(1.20 分支 = 1.5.3-forge+mc1.20.1,`ai/` 源码、`gradle.properties`、lang 文件)与 wiki 分支(`docs/wiki/dev/ai/`、1.5.3 更新日志)
- 更新日志汇总:bbsmc.net/mod/touhou-little-maid/changelog(1.5.0~1.5.3 各版本全文)
- mcmod.cn:女仆生存 class/29280、MIMO TTS class/29490、遥控女仆 class/22390、勤劳跟踪狂 class/19577
- Modrinth API:`tlm-maid-survival`(依赖 TLM 1.5.3)、`telepathic-maid`(依赖 Diligent Stalker)
- GitHub:Re-Summer75/Touhou-Little-Maid-Companionship(README/分支 1.20.1)、niumadadi520/Little-Maid-Harvest-Helper(README)
- 社区教程:博客园 chy-2003《车万女仆AI对话全本地部署方法》、mcmod 专栏 5989《本地部署一个思考很快的妹抖》、GitHub issue #809(本地 LLM 兼容问题)
