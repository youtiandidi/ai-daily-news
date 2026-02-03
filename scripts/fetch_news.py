# -*- coding: utf-8 -*-
"""
AI 每日资讯抓取脚本
适用于 GitHub Actions 自动运行
"""

import feedparser
import requests
import json
import re
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ==================== 配置区 ====================

# 从环境变量读取配置
WXPUSHER_TOKEN = os.getenv("WXPUSHER_TOKEN", "")
WXPUSHER_UID = os.getenv("WXPUSHER_UID", "UID_hB2iGBSu4t8GlVO4rBPXst71tfzZ")
WXPUSHER_API_URL = "https://wxpusher.zjiecode.com/api/send/message"

# 智谱AI配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_MODEL = "glm-4-flash"

# RSS 源
RSS_SOURCES = [
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "limit": 12},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage?page=1", "limit": 12},
]

# 关键词
IMPORTANT_KEYWORDS = [
    "GPT", "Claude", "Gemini", "Llama", "Mistral", "OpenAI", "ChatGPT",
    "模型", "发布", "推出", "突破", "创新", "AI", "人工智能",
    "谷歌", "微软", "Meta", "英伟达", "NVIDIA", "DeepMind",
    "芯片", "GPU", "算力", "融资", "收购", "投资", "合作",
]

FILTER_KEYWORDS = ["招聘", "求职", "Hiring", "job", "课程", "培训", "tutorial", "周报"]

# 数据路径
DATA_DIR = Path("data")
SENT_FILE = DATA_DIR / "sent_articles.json"


# ==================== 工具函数 ====================

def ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(exist_ok=True)

def load_json(filepath):
    """加载JSON文件"""
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    """保存JSON文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_article_id(url, title):
    """生成文章唯一ID"""
    return hashlib.md5(f"{url}{title}".encode()).hexdigest()

def is_important(title, summary):
    """判断文章是否重要"""
    text = (title + " " + summary).lower()
    for kw in FILTER_KEYWORDS:
        if kw.lower() in text:
            return False
    for kw in IMPORTANT_KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def summarize_article(summary):
    """提取文章摘要"""
    if not summary:
        return "暂无摘要"
    summary = re.sub(r'<[^>]+>', '', summary).strip()
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', summary))
    if chinese_chars < 20:
        return "点击查看详情"
    if len(summary) > 150:
        summary = summary[:150] + "..."
    return summary

def translate_title_to_chinese(title):
    """简单的英文标题翻译"""
    if len(re.findall(r'[\u4e00-\u9fff]', title)) > len(title) * 0.3:
        return title

    trans = {
        "OpenAI": "OpenAI", "Google": "谷歌", "Meta": "Meta", "Microsoft": "微软",
        "NVIDIA": "英伟达", "Anthropic": "Anthropic", "DeepMind": "DeepMind",
        "GPT": "GPT", "GPT-4": "GPT-4", "Claude": "Claude", "Gemini": "Gemini",
        "Llama": "Llama", "Mistral": "Mistral", "ChatGPT": "ChatGPT",
        "AI": "AI", "LLM": "大语言模型", "Agent": "智能体",
        "announces": "发布", "launches": "推出", "releases": "发布",
        "new": "新", "model": "模型", "breakthrough": "突破",
        "research": "研究", "paper": "论文", "study": "研究",
    }

    zh_title = title
    for en, zh in sorted(trans.items(), key=lambda x: len(x[0]), reverse=True):
        zh_title = re.sub(r'\b' + re.escape(en) + r'\b', zh, zh_title, flags=re.IGNORECASE)

    zh_title = re.sub(r'\s+', ' ', zh_title).strip()
    return zh_title


# ==================== GLM-4 整理 ====================

def call_zhipu_ai(articles_text):
    """调用智谱GLM-4模型整理资讯"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """你是AI资讯分析助手。请严格按照以下格式输出今日资讯：

## 📰 今日重点

**1. 标题**：简要概括（30字以内）

**2. 标题**：简要概括（30字以内）

**3. 标题**：简要概括（30字以内）

## 📊 趋势分析

今日热点：[一句话总结]

## 🔮 发展预测

[基于当前趋势的1-2句话预测]

---
*本资讯由 GLM-4 Flash 模型整理*

⚠️ 注意事项：
1. 只输出3-5条最重要资讯
2. 每条概括严格控制在30字以内
3. 趋势分析用一句话总结
4. 预测用1-2句话
5. 必须严格按上述格式输出，不要添加其他内容"""

    data = {
        "model": ZHIPU_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请整理以下AI资讯：\n\n{articles_text}"}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        print("🤖 正在调用 GLM-4 模型整理资讯...")
        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("✅ GLM-4 整理完成")
                return content
            else:
                print(f"❌ GLM-4 响应异常: {result}")
                return None
        else:
            print(f"❌ GLM-4 调用失败: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ GLM-4 调用出错: {e}")
        return None


# ==================== 微信推送 ====================

def send_to_wechat(title, content):
    """发送消息到微信"""
    data = {
        "appToken": WXPUSHER_TOKEN,
        "content": f"### {title}\n\n{content}",
        "summary": title,
        "contentType": 3,
        "uids": [WXPUSHER_UID]
    }
    r = requests.post(WXPUSHER_API_URL, json=data, timeout=10)
    result = r.json()
    if result.get("code") == 1000:
        print(f"✅ 微信推送成功: {title}")
        return True
    else:
        print(f"❌ 微信推送失败: {result.get('msg')}")
        return False


# ==================== 主程序 ====================

def main():
    """主程序"""
    print("=" * 50)
    print("AI每日资讯 - GitHub Actions 版")
    print("=" * 50)

    # 检查配置
    if not WXPUSHER_TOKEN:
        print("❌ WXPUSHER_TOKEN 未设置")
        return False

    if not ZHIPU_API_KEY:
        print("❌ ZHIPU_API_KEY 未设置")
        return False

    ensure_data_dir()
    sent = load_json(SENT_FILE)
    all_new = []

    # 收集文章
    for source in RSS_SOURCES:
        limit = source.get("limit", 12)
        print(f"\n📰 抓取 {source['name']} (最多{limit}篇)...")

        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:limit]:
                url = entry.get("link", "")
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))

                if is_important(title, summary) and generate_article_id(url, title) not in sent:
                    all_new.append({
                        "source": source["name"],
                        "title": title,
                        "url": url,
                        "summary": summarize_article(summary)
                    })
                    sent[generate_article_id(url, title)] = {"sent_at": datetime.now().isoformat()}
        except Exception as e:
            print(f"   ⚠️  失败: {e}")

    save_json(SENT_FILE, sent)
    print(f"\n📊 获取 {len(all_new)} 篇重要文章")

    if not all_new:
        print("📭 没有新文章")
        return True

    # 构建文章文本供GLM-4分析
    articles_text = ""
    for i, a in enumerate(all_new[:15], 1):
        translated_title = translate_title_to_chinese(a['title'])
        articles_text += f"\n{i}. 【{a['source']}】{translated_title}\n   {a['summary']}\n   链接: {a['url']}\n"

    # 调用GLM-4整理
    glm4_content = call_zhipu_ai(articles_text)

    # 构建最终内容
    parts = []

    if glm4_content:
        parts.append(glm4_content)
    else:
        # 降级处理
        parts.append("## 📰 今日资讯\n")
        for a in all_new[:5]:
            parts.append(f"**{a['title']}**")
            parts.append(f"📌 {a['summary']}")
            parts.append(f"🔗 [查看详情]({a['url']})\n")

    # 添加所有链接
    if len(all_new) > 5:
        parts.append("\n## 📚 所有资讯链接\n")
        for a in all_new:
            parts.append(f"- [{a['title']}]({a['url']})")

    # 北京时间
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    title = f"AI每日资讯 - {now.strftime('%Y年%m月%d日')}"

    content = "\n".join(parts)

    # 发送到微信
    print("\n📤 发送到微信...")
    if send_to_wechat(title, content):
        print("✅ 发送成功!")
        return True
    else:
        print("❌ 发送失败")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
