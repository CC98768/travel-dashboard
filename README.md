# 🌍 每日全球旅游热点看板

每日自动采集全球 25 个主要旅游国家 Top 10 旅游行业要闻，生成可交互的可视化看板。

## ✨ 功能

- **25 国 × 10 条 = 250 条** 每日旅游事件
- **智能采集**：DuckDuckGo 搜索 + Claude AI 智能分析过滤
- **±7 天时效**：自动过滤过期内容
- **内容过滤**：仅收录出入境利好，排除政治/财报/负面内容
- **标签系统**：🔴爆 / 🟠热 / 🔵新 自动标记
- **可视化日历**：点击任意历史日期查看当日事件
- **双信源链接**：百度搜索 + Google 搜索（国外）/ 官网（国内）
- **1500+ 历史事件**：全部内嵌，离线可查

## 🚀 自动更新机制

```
每天 09:00 (北京时间)
    ↓
GitHub Actions 自动触发 (云端 Ubuntu)
    ↓
DuckDuckGo 搜索各国旅游新闻
    ↓
Claude AI 智能分析:
  • ±7天时效过滤
  • 利好内容筛选
  • 自动分类 + 标签
  • 生成结构化 JSON
    ↓
generate.py 生成看板 (嵌入所有历史数据)
    ↓
git push → GitHub Pages 自动部署
```

**不依赖本机，关机也能自动运行。**

## 📁 仓库结构

```
├── .github/workflows/daily-update.yml  ← 每日自动触发
├── scripts/collect_news.py             ← 智能采集脚本
├── daily/                              ← 每日数据存档
│   ├── 2026-08-06.json
│   ├── ...
│   └── manifest.json                   ← 日历索引
├── index.html                          ← 看板主页
├── template.html                       ← HTML 模板
├── generate.py                         ← 看板生成脚本
├── requirements.txt                    ← Python 依赖
└── README.md
```

## 🔧 首次配置

### 1. 获取 Anthropic API Key

1. 访问 https://console.anthropic.com/
2. 注册/登录账号
3. 进入 **API Keys** 页面
4. 点击 **Create Key**，复制密钥

> 💰 费用预估：约 $0.5/天（使用 Claude Sonnet），每月约 $15

### 2. 设置 GitHub Secret

1. 进入你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: 粘贴你的 API Key
6. 点击 **Add secret**

### 3. 开启 GitHub Pages

1. **Settings** → **Pages**
2. Source: `main` / `/ (root)`
3. Save
4. 等待 1-2 分钟，访问: `https://你的用户名.github.io/仓库名/`

### 4. 手动测试

1. 进入仓库 **Actions** 标签页
2. 点击 **Daily Travel Dashboard Update**
3. 点击 **Run workflow** → **Run workflow**
4. 等待 5-10 分钟，查看结果

## 📊 数据格式

每条事件 9 个字段：

| 字段 | 说明 |
|------|------|
| title | 事件标题（20字内） |
| category | 分类（签证政策/目的地/航空交通/行业数据/文旅活动/旅行提示） |
| summary | 摘要（40-60字） |
| source | 来源媒体 |
| impact | 影响分析（20-30字） |
| source_url | 信源链接（百度搜索） |
| key_figures | 关键数据（数组） |
| travel_advisory | 出行提示（≤15字） |
| tag | 标签（爆/热/新） |

## 🌐 国家覆盖

| 地区 | 国家 |
|------|------|
| 🌏 亚洲 | 中国 日本 韩国 泰国 新加坡 马来西亚 越南 印度 |
| 🌍 欧洲 | 法国 意大利 西班牙 英国 德国 希腊 土耳其 瑞士 俄罗斯 |
| 🌎 美洲 | 美国 加拿大 墨西哥 巴西 阿根廷 |
| 🌐 其他 | 澳大利亚 新西兰 阿联酋 |

## 📄 License

MIT
