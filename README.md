# 🌍 每日全球旅游热点看板

每日自动采集全球 25 个主要旅游国家 Top 10 旅游行业要闻，生成可交互的可视化看板。

## 📊 功能

- **25 国 × 10 条 = 250 条** 旅游行业事件
- **8 个字段**：标题 / 分类 / 摘要 / 来源 / 影响分析 / 信源链接 / 关键数据 / 出行提示
- **搜索**：按国家名称或事件关键词搜索
- **筛选**：按洲际（亚洲/欧洲/美洲/其他）筛选
- **详情弹窗**：点击事件查看详细摘要、关键数据、影响分析、出行提示
- **信源链接**：
  - 🇨🇳 国内事件 → 🔍百度搜索 + 🏛️来源官网
  - 🌍 国外事件 → 🔍百度搜索 + 🌐Google 搜索

## 📁 仓库结构

```
├── index.html          # 看板主页（GitHub Pages 入口）
├── template.html       # HTML 模板（含样式和交互逻辑）
├── generate.py         # 看板生成脚本
├── daily/              # 每日数据存档
│   └── 2026-08-07.json # 按日期命名的 JSON 数据
├── .gitignore
└── README.md
```

## 🔄 每日更新流程

```
09:00 定时任务自动触发
    ↓
WebSearch 采集 25 国旅游要闻
    ↓
保存 daily/YYYY-MM-DD.json
    ↓
python3 generate.py -d daily/YYYY-MM-DD.json
    ↓
生成 index.html（自包含，数据内嵌）
    ↓
git push → GitHub Pages 自动部署
```

## 🚀 本地使用

```bash
# 生成看板
python3 generate.py -d daily/2026-08-07.json

# 指定输出文件
python3 generate.py -d daily/2026-08-07.json -o output.html

# 直接用浏览器打开
open index.html
```

## 📋 数据格式

```json
{
  "date": "2026-08-07",
  "countries": [
    {
      "code": "CN",
      "name": "中国",
      "events": [
        {
          "rank": 1,
          "title": "事件标题",
          "category": "行业数据",
          "summary": "40-60字摘要",
          "source": "来源媒体",
          "impact": "20-30字影响分析",
          "source_url": "信源链接",
          "key_figures": ["关键数据1", "关键数据2"],
          "travel_advisory": "出行提示"
        }
      ]
    }
  ]
}
```

## 🌐 国家覆盖

| 地区 | 国家 |
|------|------|
| 🌏 亚洲 | 中国 日本 韩国 泰国 新加坡 马来西亚 越南 印度 |
| 🌍 欧洲 | 法国 意大利 西班牙 英国 德国 希腊 土耳其 瑞士 俄罗斯 |
| 🌎 美洲 | 美国 加拿大 墨西哥 巴西 阿根廷 |
| 🌐 其他 | 澳大利亚 新西兰 阿联酋 |

## 📄 License

MIT
