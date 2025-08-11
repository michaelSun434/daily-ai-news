import feedparser
import openai
import datetime
from email.mime.text import MIMEText
import smtplib
import requests
import os

# ===== 配置部分 =====
rss_feeds = [
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/feed/",
    "https://syncedreview.com/feed/",   # 机器之心
    "http://www.qbitai.com/feed",       # 量子位
    "https://arxiv.org/rss/cs.LG",
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 从环境变量读取
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = os.getenv("EMAIL_TO")

WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")  # 可选：企业微信机器人 webhook

# ===== 1. 抓取新闻 =====
def fetch_news():
    news_items = []
    for url in rss_feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:  # 每源取 3 条
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "")
            })
    return news_items

# ===== 2. 用 GPT 摘要 =====
def summarize_news(news_items):
    openai.api_key = OPENAI_API_KEY
    summaries = []
    for item in news_items:
        prompt = f"以下是一则AI相关的新闻，请用中文简明总结，1-2句话，并分析可能的技术发展方向或投资机会：\n标题: {item['title']}\n链接: {item['link']}"
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            summary_text = resp.choices[0].message.content.strip()
        except Exception as e:
            summary_text = "【摘要失败】" + str(e)

        summaries.append({
            "title": item["title"],
            "summary": summary_text,
            "link": item["link"]
        })
    return summaries

# ===== 3. 邮件发送 =====
def send_email(content):
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = f"每日AI新闻 - {datetime.date.today()}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)  # 如果用Gmail
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, [EMAIL_TO], msg.as_string())
    server.quit()

# ===== 4. 企业微信推送（可选） =====
def send_wechat(text):
    if not WECHAT_WEBHOOK:
        return
    payload = {"msgtype": "text", "text": {"content": text}}
    requests.post(WECHAT_WEBHOOK, json=payload)

# ===== 主流程 =====
if __name__ == "__main__":
    news = fetch_news()
    summaries = summarize_news(news)

    html_content = "<h2>今日AI新闻</h2>"
    wechat_text = "【今日AI新闻】\n"

    for s in summaries:
        html_content += f"<p><b>{s['title']}</b><br>{s['summary']}<br><a href='{s['link']}'>阅读原文</a></p>"
        wechat_text += f"{s['title']}\n{s['summary']}\n{s['link']}\n\n"

    # 发邮件
    if EMAIL_USER and EMAIL_PASS and EMAIL_TO:
        send_email(html_content)
    # 发企业微信
    send_wechat(wechat_text)

    print("✅ 今日AI新闻已发送")
