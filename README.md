# 🌍 全球旅游热点看板

25国 × 10条 = 250条每日旅游要闻，RSS + 官网多源自动采集，GitHub Actions 每日更新，GitHub Pages 自动部署。

## ✨ 特性

- **多源采集**：RSS订阅（Reddit/Skift/The Points Guy等）+ 各国旅游局官网直接抓取
- **无需 API Key**：完全基于公开 RSS 和网页，不受 API 配额限制
- **精确信源**：每条新闻附带真实 source_url，可直接点击查看原文
- **历史日历**：支持30天历史数据回溯，点击日期切换查看
- **自动去重**：标题相似度算法 + 历史数据比对，确保每日不重复
- **配额校验**：6类分布（航线2+政策2+生活1+趋势2+景点2+文娱1）自动校验修复
- **标签多元化**：爆标签分散在不同类别，不集中在同一类
- **GitHub Pages**：自动生成静态看板，任何人可访问

## 🚀 快速开始

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub 上创建新仓库（例如：global-travel-dashboard）
git init
git remote add origin https://github.com/YOUR_USERNAME/global-travel-dashboard.git
```

### 2. 推送代码

```bash
cd global-travel-dashboard
git add .
git commit -m "🚀 初始化全球旅游热点看板"
git branch -M main
git push -u origin main
```

### 3. 启用 GitHub Pages

1. 进入仓库 → Settings → Pages
2. Source 选择 **Deploy from a branch**
3. Branch 选择 **gh-pages** / root
4. 保存后等待1-2分钟

### 4. 启用 GitHub Actions

1. 进入仓库 → Actions
2. 找到 "每日旅游热点采集" workflow
3. 点击 "Run workflow" 手动触发第一次运行
4. 之后每天北京时间 9:00 自动运行

## 📊 信源说明

### 数据源分类

| 层级 | 来源类型 | 示例 | 信源精准度 |
|---|---|---|---|
| **第一层** | RSS 订阅 | Reddit travel, Skift, The Points Guy | ⭐⭐⭐⭐⭐ 精确URL |
| **第二层** | 官方网站 | 各国旅游局/移民局官网 | ⭐⭐⭐⭐ 精确域名 |
| **第三层** | 综合整理 | 无法匹配具体源时的兜底 | ⭐⭐⭐ Google搜索链接 |

### 25国官方信源映射

每个国家都预配了权威信源URL：

- 🇨🇳 中国：国家移民管理局(nia.gov.cn)、民航局(caac.gov.cn)、文旅部(mct.gov.cn)
- 🇯🇵 日本：外务省(mofa.go.jp)、JNTO(jnto.go.jp)
- 🇹🇭 泰国：旅游局(tat.or.th)、移民局(immigration.go.th)、电子签(thaievisa.go.th)
- 🇺🇸 美国：国务院(travel.state.gov)、Brand USA(brandusa.com)
- 🇬🇧 英国：VisitBritain、UK Visas(gov.uk)
- ... 等25国全部配置

### 为什么有些信源是搜索链接？

部分新闻由 LLM 基于训练数据综合生成，无法追溯到单一网页。这种情况：
- `source_url` 存 Google 搜索链接（可搜索到相关信息）
- `source` 标注"综合整理"
- 随着 RSS 采集运行，真实 URL 占比会逐步提升至 70%+

## 📁 项目结构

```
global-travel-dashboard/
├── .github/workflows/
│   └── daily-update.yml    # GitHub Actions 工作流
├── scripts/
│   ├── collect.py           # 多源数据采集器
│   └── generate_dashboard.py # HTML 看板生成器
├── data/
│   ├── history.json         # 历史数据（自动维护）
│   └── today.json           # 最新数据快照
├── dashboard/
│   └── index.html           # 生成的看板（部署到Pages）
├── requirements.txt         # Python 依赖
└── README.md
```

## 🔧 自定义

### 添加新的 RSS 源

编辑 `scripts/collect.py` 中的 `RSS_SOURCES` 列表：

```python
{"name":"新源名称","url":"https://example.com/rss","lang":"en"},
```

### 修改采集时间

编辑 `.github/workflows/daily-update.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

### 添加新的国家

编辑 `scripts/collect.py` 中的 `COUNTRIES_25` 列表和 `OFFICIAL_SOURCES` 映射。

## ⚠️ 已知限制

1. **GitHub Actions 共享 IP**：直接爬取可能被某些网站限速（但 RSS 不受影响）
2. **官网结构变化**：官方网站页面改版可能导致抓取失败，需定期维护
3. **首次运行数据量**：第一次运行时历史为空，部分国家可能数据不足
4. **RSS 源时效**：部分 RSS 源可能停止更新，需定期检查

## 📜 License

MIT
