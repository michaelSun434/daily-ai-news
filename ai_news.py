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

# 保存 HTML 到一个文件
def save_html(content):
    save_path = "index.html"  # GitHub Pages 默认主页
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 网页已更新: {save_path}")

# 主函数最后改成这样：
if __name__ == "__main__":
    news = fetch_news()
    summaries = summarize_news(news)

    html_content = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>每日AI新闻</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; }
h2 { color: #333; text-align: center; }
.news { margin-bottom: 20px;}
.news-title { font-weight: bold; font-size: 18px; }
.news-summary { margin: 5px 0; }
</style>
</head>
<body>
<h2>每日AI新闻</h2>
"""

    for s in summaries:
        html_content += f"""
<div class="news">
    <div class="news-title">{s['title']}</div>
    <div class="news-summary">{s['summary']}</div>
    <a href="{s['link']}" target="_blank">阅读原文</a>
</div>
"""

    html_content += "</body></html>"

    save_html(html_content)
