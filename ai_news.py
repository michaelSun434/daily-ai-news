import feedparser
import openai
import os
import datetime

# ===== 配置 =====
rss_feeds = [
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/feed/",
    "https://syncedreview.com/feed/",   # 机器之心
    "http://www.qbitai.com/feed",       # 量子位
    "https://arxiv.org/rss/cs.LG",      # arXiv - 机器学习
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 从环境变量读取

# ===== 1. 抓取新闻 =====
def fetch_news():
    news_items = []
    for url in rss_feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:  # 每源取前3条
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "")
            })
    return news_items

# ===== 2. GPT 摘要 =====
def summarize_news(news_items):
    openai.api_key = OPENAI_API_KEY
    summaries = []
    for item in news_items:
        prompt = f"请用中文总结这则AI新闻，1-2句话，并说明对技术或投资可能的意义：\n标题：{item['title']}\n链接：{item['link']}"
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            summary_text = resp.choices[0].message.content.strip()
        except Exception as e:
            summary_text = f"【摘要失败】{e}"

        summaries.append({
            "title": item["title"],
            "summary": summary_text,
            "link": item["link"]
        })
    return summaries

# ===== 3. 保存为 index.html =====
def save_html(news_list):
    today = datetime.date.today()
    html_content = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>每日AI新闻 - {today}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }}
h1 {{ text-align: center; }}
.news {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ddd; }}
.news-title {{ font-weight: bold; font-size: 18px; }}
.news-summary {{ margin: 5px 0; color: #333; }}
a {{ color: #1a73e8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>每日AI新闻 ({today})</h1>
"""

    for n in news_list:
        html_content += f"""
<div class="news">
    <div class="news-title">{n['title']}</div>
    <div class="news-summary">{n['summary']}</div>
    <a href="{n['link']}" target="_blank">阅读原文</a>
</div>
"""

    html_content += "</body></html>"

    # 保存到仓库根目录（GitHub Pages默认读取的位置）
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 已生成 index.html")

# ===== 主流程 =====
if __name__ == "__main__":
    news = fetch_news()
    summaries = summarize_news(news)
    save_html(summaries)
