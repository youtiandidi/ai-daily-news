# AI 每日资讯监控

> 每天 8:00 自动推送 AI 行业重要资讯到微信，由 GLM-4 模型智能整理。

## 功能特性

- ✅ 自动抓取量子位、Hacker News 等资讯源
- ✅ 智能筛选重要 AI 资讯
- ✅ GLM-4 模型自动整理和分析
- ✅ 每天 8:00 推送到微信
- ✅ 电脑关机也能运行

## 快速开始

### 1. Fork 本仓库

点击右上角 Fork 按钮

### 2. 配置 Secrets

进入你 Fork 的仓库：
- Settings → Secrets and variables → Actions
- 点击 "New repository secret" 添加以下密钥：

| Secret 名称 | 值 | 获取方式 |
|-------------|-----|----------|
| `WXPUSHER_TOKEN` | 你的 AppToken | https://wxpusher.zjiecode.com/ |
| `WXPUSHER_UID` | 你的 UID | 同上 |
| `ZHIPU_API_KEY` | 你的 API Key | https://open.bigmodel.cn/ |

### 3. 启用 Actions

- 进入 Actions 标签
- 点击 "I understand my workflows, go ahead and enable them"
- 在左侧选择 "AI Daily News"
- 点击 "Run workflow" 手动测试

### 4. 自动运行

配置完成后，程序将**每天 UTC 00:00（北京时间 08:00）**自动运行。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python scripts/fetch_news.py
```

## 文件结构

```
├── .github/workflows/
│   └── daily-news.yml      # GitHub Actions 配置
├── scripts/
│   └── fetch_news.py       # 主程序
├── data/
│   └── sent_articles.json  # 已发送记录
└── README.md
```

## 常见问题

**Q: 如何修改推送时间？**
A: 编辑 `.github/workflows/daily-news.yml` 中的 cron 表达式。

**Q: 如何添加更多资讯源？**
A: 编辑 `scripts/fetch_news.py` 中的 `RSS_SOURCES` 配置。

**Q: 如何停止推送？**
A: 在 Actions 页面禁用 workflow，或删除 Secrets。

## License

MIT
