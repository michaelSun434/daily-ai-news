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

MAX_NEWS = 20
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 从 GitHub Secrets 读取

def fetch_news():
    """抓取多来源新闻"""
    items = []
    for url in rss_feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "")
            })
    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique_items.append(item)
    return unique_items[:MAX_NEWS]

def summarize_with_investment(news_items):
    """用 GPT 做摘要 + 投资分析"""
    openai.api_key = OPENAI_API_KEY
    summaries = []
    for item in news_items:
        prompt = f"""以下是一则AI相关新闻，请用简体中文输出：
1. 摘要（1-2句）
2. 投资分析（1句话，说明可能的技术或商业影响）
标题：{item['title']}
链接：{item['link']}
"""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            text = resp.choices[0].message.content.strip()
        except Exception as e:
            text = f"【摘要生成失败】{e}"

        summaries.append({
            "title": item['title'],
            "summary": text,
            "link": item['link']
        })
    return summaries

def save_html_with_style(news_list):
    """生成 HTML 页面"""
    today = datetime.date.today()
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>每日AI新闻与投资分析 - {today}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 900px; margin: auto; padding: 20px; background: #fafafa; }}
h1 {{ text-align: center; color: #333; }}
.news {{ margin-bottom: 20px; padding: 15px; border-radius: 8px; background: #fff; box-shadow: 0 0 5px rgba(0,0,0,0.1); }}
.news-title {{ font-weight: bold; font-size: 18px; color: #1a73e8; }}
.news-summary {{ margin-top: 8px; white-space: pre-line; }}
a {{ color: #1a73e8; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>每日AI新闻与投资分析 ({today})</h1>
"""

    for n in news_list:
        html += f"""
<div class="news">
    <div class="news-title"><a href="{n['link']}" target="_blank">{n['title']}</a></div>
    <div class="news-summary">{n['summary']}</div>
</div>
"""

    html += "</body></html>"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html 已生成")

if __name__ == "__main__":
    news = fetch_news()
    summaries = summarize_with_investment(news)
    save_html_with_style(summaries)
