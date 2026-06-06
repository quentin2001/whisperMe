import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from plyer import notification
from app.config import config

class PodcastNotifier:
    def __init__(self):
        self.smtp_server = config.get("smtp_server", "smtp.qq.com")
        self.smtp_port = config.get("smtp_port", 465)
        self.smtp_username = config.get("smtp_username", "")
        self.smtp_password = config.get("smtp_password", "")
        self.smtp_sender = config.get("smtp_sender", "")
        self.recipient_email = config.get("notification_email", "")
        self.enable_win_notification = config.get("enable_win_notification", True)
        
        print("✉️ [LOG] 初始化提醒通知模块完成")

    def send_desktop_notification(self, title: str, message: str):
        """
        触发 Windows 系统右下角气泡通知
        """
        if not self.enable_win_notification:
            return
            
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="whisperMe 本地播客处理中心",
                timeout=10
            )
            print("🔔 [LOG] Windows 桌面通知发送成功")
        except Exception as e:
            print(f"⚠️ [LOG 异常] 无法发送 Windows 桌面通知: {e}")

    def send_email_notification(self, podcast_title: str, podcast_name: str, task_id: str, summary_md: str, like_count: int, comment_count: int):
        """
        发送格式精美的卡片式 HTML 邮件通知
        """
        import re

        if not self.smtp_username or not self.smtp_password or not self.recipient_email:
            print("⚠️ [LOG 警告] 未配置完整的 SMTP 邮件信息 (账号、授权码或接收邮箱为空)，跳过邮件提醒。")
            return False

        try:
            next_kws = ['核心主旨', '目标受众', '含金量评级', '推荐等级', '核心观点', '议题提炼', '发言人', '听众口碑', '事实一致性', '1.', '2.', '3.', '4.', '5.']

            theme = convert_markdown_inline(extract_section(summary_md, ['核心主旨', '主旨'], next_kws))
            audience = convert_markdown_inline(extract_section(summary_md, ['目标受众', '受众'], next_kws))
            rating_desc = extract_section(summary_md, ['含金量评级与判定理由', '含金量评级', '评级'], next_kws)
            recommend = convert_markdown_inline(extract_section(summary_md, ['推荐等级', '收听建议', '推荐'], next_kws))

            # 提取含金量评级字母
            score = "A"
            score_match = re.search(r'评级为[：:\s]*\*{0,2}([A-D][\+\-]?)\*{0,2}', rating_desc)
            if score_match:
                score = score_match.group(1).replace("*", "").strip()
            else:
                score_match = re.search(r'[A-D][\+\-]?', rating_desc)
                if score_match:
                    score = score_match.group(0).replace("*", "").strip()

            rating_desc_clean = convert_markdown_inline(re.sub(r'因此，?评级为.*$', '', rating_desc).strip())

            # 提取发言人姓名
            host, guest = extract_speakers(summary_md, next_kws)

            # 格式化议题卡片
            topics_txt = extract_section(summary_md, ['核心观点与议题提炼', '核心观点与议题', '核心观点', '议题提炼'], next_kws)
            topics_html = format_markdown_to_html_cards(topics_txt)
            # 确定评级标签颜色
            rating_color = "#f7768e" # 红色/粉色表示 A/A+
            if "B" in score:
                rating_color = "#ff9e64" # 橙色表示 B
            elif "C" in score or "D" in score:
                rating_color = "#73daca" # 蓝色/绿色表示 C/D

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎙️ 播客总结卡片：【{podcast_title}】"
            msg["From"] = self.smtp_sender or self.smtp_username
            msg["To"] = self.recipient_email

            html_content = f"""
            <html>
            <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; padding: 20px; margin: 0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #121218; border: 1px solid #1f1f2e; border-radius: 14px; overflow: hidden; box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.7);">
                    
                    <!-- 渐变头部卡片 (使用 whisperMe 主题配色) -->
                    <div style="background: linear-gradient(135deg, #7aa2f7, #9d7cd8); padding: 30px 24px; text-align: left; position: relative;">
                        <div style="font-size: 11px; font-weight: bold; color: rgba(255, 255, 255, 0.85); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px;">
                            🎙️ {podcast_name} • AI 播客浓缩卡片
                        </div>
                        <h2 style="color: #ffffff; margin: 0 0 10px 0; font-size: 20px; font-weight: bold; line-height: 1.4;">
                            {podcast_title}
                        </h2>
                        <div style="font-size: 13px; color: rgba(255, 255, 255, 0.95);">
                            主持：<span style="font-weight: bold; color: #73daca;">{host}</span> &nbsp;&nbsp;|&nbsp;&nbsp; 嘉宾：<span style="font-weight: bold; color: #ff9e64;">{guest}</span>
                        </div>
                    </div>
                    
                    <div style="padding: 24px;">
                        <!-- 头部评分卡片与收听建议 -->
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                            <tr>
                                <td style="width: 100px; text-align: center; vertical-align: middle; background-color: #181820; border: 1px solid #262630; border-radius: 10px 0 0 10px; padding: 15px;">
                                    <div style="font-size: 10px; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">含金量评级</div>
                                    <div style="font-size: 36px; font-weight: 900; color: {rating_color}; line-height: 1;">{score}</div>
                                </td>
                                <td style="background-color: #1a1a24; border: 1px solid #262630; border-left: none; border-radius: 0 10px 10px 0; padding: 15px; vertical-align: top;">
                                    <div style="font-size: 11px; color: #bb9af2; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">🎯 核心收听建议</div>
                                    <div style="font-size: 13px; color: #e2e8f0; font-weight: bold; line-height: 1.4;">{recommend}</div>
                                    <div style="font-size: 12px; color: #a1a1aa; margin-top: 4px; line-height: 1.4;"><strong>适合人群：</strong>{audience}</div>
                                </td>
                            </tr>
                        </table>

                        <!-- 核心主旨卡片 -->
                        <div style="background-color: #181820; border: 1px solid #262630; border-radius: 10px; padding: 18px; margin-bottom: 24px;">
                            <div style="font-size: 13px; font-weight: bold; color: #7aa2f7; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">📖 播客核心速览</div>
                            <div style="font-size: 13px; line-height: 1.6; color: #d4d4d8;">{theme}</div>
                            {f'<div style="font-size: 12px; line-height: 1.5; color: #a1a1aa; margin-top: 10px; border-top: 1px solid #262630; padding-top: 8px;"><strong>评级理由：</strong>{rating_desc_clean}</div>' if rating_desc_clean else ''}
                        </div>

                        <!-- 观点/议题卡片列表 -->
                        <div style="margin-bottom: 24px;">
                            <div style="font-size: 13px; font-weight: bold; color: #9d7cd8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">💡 核心议题与精选金句</div>
                            {topics_html}
                        </div>

                        <!-- 社交互动热度 -->
                        <div style="display: flex; justify-content: space-between; align-items: center; background-color: #181820; border-radius: 8px; padding: 10px 15px; font-size: 12px; color: #a1a1aa; margin-bottom: 24px;">
                            <span>🔥 本集互动数据：👍 {like_count} 点赞 &nbsp;&nbsp;|&nbsp;&nbsp; 💬 {comment_count} 评论</span>
                            <span style="color: #73daca;">数据源：Bilibili / 小宇宙 FM</span>
                        </div>

                        <!-- 打开工作台按钮 -->
                        <div style="text-align: center; margin: 30px 0 10px 0;">
                            <a href="http://localhost:5173/task/{task_id}" style="display: inline-block; background: linear-gradient(90deg, #7aa2f7, #9d7cd8); color: #ffffff; text-decoration: none; font-weight: bold; font-size: 14px; padding: 12px 35px; border-radius: 30px; box-shadow: 0 4px 15px rgba(122, 162, 247, 0.45); letter-spacing: 0.5px;">
                                💻 打开工作台查看详情
                            </a>
                        </div>

                    </div>
                    
                    <!-- 页脚 -->
                    <div style="background-color: #0b0f19; padding: 20px; text-align: center; font-size: 11px; color: #52525b; border-top: 1px solid #181820;">
                        本邮件由 whisperMe 播客 AI 助手自动发送。请确保您的本地 Uvicorn 服务和 Vite 前端处于正常运行状态。
                    </div>

                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_content, "html"))

            # 4. 连接 SMTP 服务器并发送
            print(f"📡 [LOG] 正在建立 SMTP 连接: {self.smtp_server}:{self.smtp_port}...")
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.smtp_sender or self.smtp_username, self.recipient_email, msg.as_string())
            server.quit()
            
            print("✉️ [LOG] HTML 总结提醒邮件已成功发送！")
            return True
            
        except Exception as e:
            print(f"❌ [LOG 异常] 发送邮件失败: {e}")
            import traceback
            traceback.print_exc()
            return False

# 辅助解析与提取函数
def convert_markdown_inline(text):
    import re
    if not text:
        return ""
    # 将 markdown 粗体 **文字** 转换成 HTML 的 strong 加粗标签，并附加醒目的暖色高亮
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong style="color: #ff9e64;">\1</strong>', text)
    return text

def extract_section(text, keywords, next_keywords, default_val=''):
    import re
    for kw in keywords:
        pattern = r'(?:^|\n)(?:[\s\d\.\-#\*]*(?:' + re.escape(kw) + r')[ \t\*\:\：]*)([\s\S]*?)(?=\n(?:[\s\d\.\-#\*]*(?:' + '|'.join(next_keywords) + r'))|$)'
        match = re.search(pattern, text)
        if match:
            val = match.group(1).strip()
            # 保留星号以允许 inline markdown 渲染，只剥离开头的冒号、横杠与空格
            val = re.sub(r'^[:：\-\s]+', '', val).strip()
            return val
    return default_val

def format_markdown_to_html_cards(markdown_text):
    import re
    html = markdown_text.strip()
    html = html.replace("<", "&lt;").replace(">", "&gt;")
    
    parts = re.split(r'\n###\s+', "\n" + html)
    card_htmls = []
    
    intro = parts[0].strip()
    if intro and not intro.startswith("##"):
        intro_clean = convert_markdown_inline(intro)
        card_htmls.append(f"<p style='color: #d4d4d8; font-size: 14px; margin-bottom: 15px;'>{intro_clean}</p>")
        
    for part in parts[1:]:
        if not part.strip():
            continue
        lines = part.strip().split("\n")
        title = convert_markdown_inline(lines[0].strip())
        body = "\n".join(lines[1:]).strip()
        
        body_html = body
        body_html = re.sub(r'^\s*[\-\*]\s*\*\*([^*]+)\*\*[：:]*(.*)', r'<p style="margin: 6px 0; font-size: 13px; line-height: 1.5; color: #a1a1aa;"><strong style="color: #bb9af2;">\1：</strong>\2</p>', body_html, flags=re.MULTILINE)
        body_html = re.sub(r'^\s*[\-\*]\s*(.+)', r'<p style="margin: 6px 0; font-size: 13px; line-height: 1.5; color: #d4d4d8;">• \1</p>', body_html, flags=re.MULTILINE)
        body_html = convert_markdown_inline(body_html)
        body_html = body_html.replace("\n", "<br>")
        
        card = f"""
        <div style="background-color: #1e1e24; border: 1px solid #2d2d34; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 4px solid #9d7cd8;">
            <h4 style="color: #7aa2f7; margin: 0 0 10px 0; font-size: 14px; font-weight: bold;">{title}</h4>
            <div style="color: #d4d4d8;">{body_html}</div>
        </div>
        """
        card_htmls.append(card)
        
    return "\n".join(card_htmls)

def extract_speakers(summary_md, next_kws):
    import re
    sec3 = extract_section(summary_md, ['发言人画像与立场分析', '角色定位', '发言人'], next_kws)
    host = "未定位"
    guest = "未定位"
    
    for line in sec3.split('\n'):
        line_str = line.strip()
        if not line_str:
            continue
        if '主持人' in line_str or '主播' in line_str:
            bold_matches = re.findall(r'\*\*([^*]+)\*\*', line_str)
            if len(bold_matches) >= 2:
                host = bold_matches[1].strip()
            elif len(bold_matches) == 1:
                if line_str.startswith('**主持人') or line_str.startswith('**主播'):
                    colon_match = re.search(r'[：:]\s*(.*)', line_str)
                    if colon_match:
                        host = colon_match.group(1).strip()
                else:
                    host = bold_matches[0].strip()
            else:
                colon_match = re.search(r'[：:]\s*(.*)', line_str)
                if colon_match:
                    host = colon_match.group(1).strip()
                    
        elif '嘉宾' in line_str:
            bold_matches = re.findall(r'\*\*([^*]+)\*\*', line_str)
            if len(bold_matches) >= 2:
                guest = bold_matches[1].strip()
            elif len(bold_matches) == 1:
                if line_str.startswith('**嘉宾'):
                    colon_match = re.search(r'[：:]\s*(.*)', line_str)
                    if colon_match:
                        guest = colon_match.group(1).strip()
                else:
                    guest = bold_matches[0].strip()
            else:
                colon_match = re.search(r'[：:]\s*(.*)', line_str)
                if colon_match:
                    guest = colon_match.group(1).strip()
                    
    # 清理 Speaker_xx 等声纹分割临时标签后缀以及各种多余字符
    host = re.sub(r'\s*[\(\uff08][sS][pP][eE][aA][kK][eE][rR]_\d+[\uff09\)]', '', host).strip()
    guest = re.sub(r'\s*[\(\uff08][sS][pP][eE][aA][kK][eE][rR]_\d+[\uff09\)]', '', guest).strip()
    host = re.sub(r'^[\-\*\s]+', '', host).strip()
    guest = re.sub(r'^[\-\*\s]+', '', guest).strip()
    return host, guest
