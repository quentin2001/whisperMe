# whisperMe — 使用手册 & 配置指南 (User Guide)

本文件提供了 whisperMe 的详细配置说明与常见问题解答。

---

## 配置说明

配置文件为项目根目录下的 `config.json`。首次使用请复制模板：

```bash
cp config.example.json config.json
```

### ASR 语音转录

| 配置项 | 说明 |
|---|---|
| `asr_mode` | `local`（离线）或 `online`（在线 API） |
| `local_whisper_model_path` | 本地 Whisper 模型目录路径（`asr_mode=local` 时必填） |
| `hf_token` | HuggingFace Token，用于下载 PyAnnote 声纹模型 |
| `online_api_key` | 在线 ASR API Key（`asr_mode=online` 时必填） |
| `online_base_url` | 在线 ASR API 地址，默认 MiMo ASR |
| `online_model` | 在线 ASR 模型名称 |

### AI 总结

| 配置项 | 说明 |
|---|---|
| `summary_mode` | `local`（本地 Ollama）或 `online`（在线 LLM API） |
| `ollama_url` | Ollama 服务地址，默认 `http://localhost:11434` |
| `ollama_model` | 本地模型名称，默认 `qwen2.5:7b-instruct` |
| `online_summary_api_key` | 在线 LLM API Key（`summary_mode=online` 时必填） |
| `online_summary_base_url` | 在线 LLM API 地址，默认 OpenAI |
| `online_summary_model` | 在线 LLM 模型名称，默认 `gpt-4o-mini` |

### 消息通知

| 配置项 | 说明 |
|---|---|
| `enable_win_notification` | Windows 桌面通知开关，默认 `true` |
| `enable_email_notification` | 邮件通知开关，默认 `false` |
| `smtp_server` / `smtp_port` | SMTP 服务器及端口 |
| `smtp_username` / `smtp_password` | SMTP 登录凭据 |
| `smtp_sender` / `notification_email` | 发件人 / 收件人地址 |

---

## 网络代理配置

whisperMe 需要同时访问中国网站（小宇宙、Bilibili）和国际服务（Anthropic API、OpenAI API）。如果使用代理软件，需要配置分流规则。

### Clash Verge 分流配置

在 Clash Verge 的 **Profile Enhancement Rules** 中添加以下规则：

```yaml
prepend:
  # 中国网站（直连）
  - DOMAIN-SUFFIX,xiaoyuzhoufm.com,DIRECT
  - DOMAIN-SUFFIX,bilibili.com,DIRECT
  - DOMAIN-SUFFIX,bilivideo.com,DIRECT
  - DOMAIN-SUFFIX,bilivideo.cn,DIRECT
  - DOMAIN-SUFFIX,hf-mirror.com,DIRECT
  - DOMAIN-SUFFIX,modelscope.cn,DIRECT
  - DOMAIN-SUFFIX,xiaomimimo.com,DIRECT
  - DOMAIN-SUFFIX,alidns.com,DIRECT
  - DOMAIN-SUFFIX,alicdn.com,DIRECT
  - IP-CIDR,223.5.5.5/32,DIRECT
  - DOMAIN-SUFFIX,xmcdn.com,DIRECT
  - DOMAIN-SUFFIX,xyzcdn.net,DIRECT

append: []
delete: []
```

### 域名说明

| 域名 | 用途 | 路由 |
|------|------|------|
| `xiaoyuzhoufm.com` | 小宇宙 FM 音频下载 | DIRECT |
| `bilibili.com` / `bilivideo.com` | Bilibili 视频下载 | DIRECT |
| `hf-mirror.com` | HuggingFace 中国镜像（模型下载） | DIRECT |
| `modelscope.cn` | ModelScope 模型下载 | DIRECT |
| `xiaomimimo.com` | 小米 MiMo ASR（在线语音识别） | DIRECT |
| `anthropic.com` | Claude Code API | 代理 |
| `api.openai.com` | OpenAI API | 代理 |
| `github.com` | 版本更新检查 | 代理 |

### 验证配置

配置完成后，在 Clash Verge 中点击"应用"或重启软件。然后测试：

```bash
# 测试中国网站（应该直连，速度快）
curl -I https://www.bilibili.com

# 测试代理网站（应该通过代理）
curl -I https://api.anthropic.com
```

---

## 常见问题 (FAQ)

<details>
<summary><strong>Q: 没有 GPU 也能用吗？</strong></summary>
<br />
可以。设置 <code>asr_mode</code> 为 <code>online</code> 使用在线 API 转录，或保持 <code>local</code> 模式——显存不足时会自动降级到 CPU 运行，只是速度会慢一些。
</details>

<details>
<summary><strong>Q: 支持哪些播客平台？</strong></summary>
<br />
目前支持小宇宙 FM（单集链接和节目主页链接均可）和 Bilibili。输入节目主页链接时，会自动解析并转录最新一集。
</details>

<details>
<summary><strong>Q: 开了代理软件（Clash / V2Ray）后在线 API 连不上？</strong></summary>
<br />
whisperMe 内置了 DoH DNS 直连机制和 4 级自适应代理回溯策略，能自动穿透 Clash TUN / Fake-IP 模式下的 DNS 劫持和 SSL EOF 报错。如果仍有问题，请检查代理软件的规则配置。详细的分流配置请参考上方的<a href="#网络代理配置">网络代理配置</a>章节。
</details>

<details>
<summary><strong>Q: 如何获取 HuggingFace Token？</strong></summary>
<br />
访问 <a href="https://huggingface.co/settings/tokens">huggingface.co/settings/tokens</a>，创建一个 Read 权限的 Token，填入 <code>config.json</code> 的 <code>hf_token</code> 字段。该 Token 用于下载 PyAnnote 声纹识别模型。没有 Token 也可以使用——程序会自动切换到国内镜像站下载。
</details>

<details>
<summary><strong>Q: 配置文件会被上传到 GitHub 吗？</strong></summary>
<br />
不会。<code>config.json</code> 已被 <code>.gitignore</code> 排除，你的 API Key、密码等敏感信息不会进入版本控制。仓库中只保留脱敏的 <code>config.example.json</code> 作为模板。
</details>
