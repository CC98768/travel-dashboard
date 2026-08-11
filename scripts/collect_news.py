#!/usr/bin/env python3
"""
每日全球旅游热点智能采集脚本 v3
================================
使用 DuckDuckGo 搜索 + Claude API 智能分析
全自动运行于 GitHub Actions，不依赖本机

环境变量:
  ANTHROPIC_API_KEY  - Anthropic API 密钥 (必需)

依赖:
  pip install anthropic duckduckgo-search
"""
import json, os, sys, time, re
from datetime import datetime, timedelta
from urllib.parse import quote

# ── 配置 ──
TODAY = datetime.utcnow() + timedelta(hours=8)  # UTC+8
DATE_STR = TODAY.strftime('%Y-%m-%d')
SEVEN_DAYS_AGO = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')

COUNTRIES = {
    'CN':'中国','JP':'日本','KR':'韩国','TH':'泰国','SG':'新加坡',
    'MY':'马来西亚','VN':'越南','IN':'印度','FR':'法国','IT':'意大利',
    'ES':'西班牙','GB':'英国','DE':'德国','GR':'希腊','TR':'土耳其',
    'CH':'瑞士','RU':'俄罗斯','US':'美国','CA':'加拿大','MX':'墨西哥',
    'BR':'巴西','AR':'阿根廷','AU':'澳大利亚','NZ':'新西兰','AE':'阿联酋'
}

SEARCH_GROUPS = [
    ('CN', ['中国 出入境 签证 旅游 最新 {date}', 'China visa entry exit travel {date}']),
    ('JP', ['日本 旅游 签证 航线 最新 {date}', 'Japan travel visa news {date}']),
    ('KR', ['韩国 旅游 签证 最新 {date}', 'Korea travel news {date}']),
    ('TH', ['泰国 旅游 签证 最新 {date}', 'Thailand travel news {date}']),
    ('SG', ['新加坡 旅游 最新 {date}', 'Singapore travel {date}']),
    ('MY', ['马来西亚 旅游 最新 {date}', 'Malaysia travel {date}']),
    ('VN', ['越南 旅游 最新 {date}', 'Vietnam travel {date}']),
    ('IN', ['印度 旅游 签证 最新 {date}', 'India travel visa {date}']),
    ('FR', ['法国 旅游 签证 最新 {date}', 'France travel {date}']),
    ('IT', ['意大利 旅游 最新 {date}', 'Italy travel {date}']),
    ('ES', ['西班牙 旅游 最新 {date}', 'Spain travel {date}']),
    ('GB', ['英国 旅游 签证 最新 {date}', 'UK Britain travel {date}']),
    ('DE', ['德国 旅游 最新 {date}', 'Germany travel {date}']),
    ('GR', ['希腊 旅游 最新 {date}', 'Greece travel {date}']),
    ('TR', ['土耳其 旅游 最新 {date}', 'Turkey travel {date}']),
    ('CH', ['瑞士 旅游 最新 {date}', 'Switzerland travel {date}']),
    ('RU', ['俄罗斯 旅游 签证 最新 {date}', 'Russia travel {date}']),
    ('US', ['美国 旅游 签证 最新 {date}', 'USA travel visa {date}']),
    ('CA', ['加拿大 旅游 最新 {date}', 'Canada travel {date}']),
    ('MX', ['墨西哥 旅游 最新 {date}', 'Mexico travel {date}']),
    ('BR', ['巴西 旅游 最新 {date}', 'Brazil travel {date}']),
    ('AR', ['阿根廷 旅游 最新 {date}', 'Argentina travel {date}']),
    ('AU', ['澳大利亚 旅游 最新 {date}', 'Australia travel {date}']),
    ('NZ', ['新西兰 旅游 最新 {date}', 'New Zealand travel {date}']),
    ('AE', ['阿联酋 迪拜 旅游 最新 {date}', 'UAE Dubai travel {date}']),
]


def search_news():
    """用 DuckDuckGo 搜索各国旅游新闻"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("安装 duckduckgo-search...")
        os.system(f"{sys.executable} -m pip install duckduckgo-search -q")
        from duckduckgo_search import DDGS

    all_results = {}
    ddgs = DDGS()

    for code, queries in SEARCH_GROUPS:
        name = COUNTRIES[code]
        results = []
        for q in queries:
            q = q.format(date=DATE_STR)
            try:
                hits = list(ddgs.text(q, max_results=8))
                for h in hits:
                    results.append({
                        'title': h.get('title', ''),
                        'body': h.get('body', ''),
                        'url': h.get('href', ''),
                    })
                print(f"  🔍 {name}: {len(hits)} 条 (query: {q[:40]}...)")
                time.sleep(1)  # 避免被限速
            except Exception as e:
                print(f"  ⚠️ {name} 搜索失败: {e}")

        all_results[code] = results[:15]  # 每国最多保留15条搜索结果
        print(f"  ✅ {name}: 共 {len(all_results[code])} 条搜索结果")

    return all_results


def analyze_with_claude(search_results):
    """用 Claude API 智能分析、过滤、结构化"""
    try:
        import anthropic
    except ImportError:
        print("安装 anthropic...")
        os.system(f"{sys.executable} -m pip install anthropic -q")
        import anthropic

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print("❌ 未设置 ANTHROPIC_API_KEY 环境变量!")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 准备搜索数据摘要
    search_summary = ""
    for code, results in search_results.items():
        name = COUNTRIES[code]
        search_summary += f"\n\n### {name} ({code})\n"
        for i, r in enumerate(results, 1):
            search_summary += f"{i}. [{r['title']}]({r['url']})\n   {r['body'][:150]}\n"

    prompt = f"""你是全球出入境旅游利好要闻分析师。今天是 {DATE_STR}。

请根据以下搜索结果，为每个国家整理 **恰好 10 条** 旅游热点事件。

## 严格要求

### 时效关卡
- 仅收录 {SEVEN_DAYS_AGO} 至 {DATE_STR} 之间的事件
- 超过此范围的一律排除
- 如果搜索结果中没有足够的新鲜事件，用"暂无更多本周热点"占位

### 内容过滤
✅ 只收录：签证放宽/免签/新航线/出入境便利化/旅游优惠/文旅活动/正向数据
❌ 排除：政治冲突/财报/安全事故/过期政策/通用趋势报告/负面舆情

### 标签规则
- rank 1 → tag: "爆"（每国仅1条，最重要的事件）
- rank 2-3 → tag: "热"（每国仅2条）
- rank 4-10 → tag: "新"

### 信源链接
- source_url 统一使用百度搜索链接：`https://www.baidu.com/s?wd=` + URL编码(事件标题+来源名)

### 输出格式
输出严格的 JSON，格式如下：
```json
{{
  "date": "{DATE_STR}",
  "countries": [
    {{
      "code": "CN",
      "name": "中国",
      "events": [
        {{
          "rank": 1,
          "title": "20字以内标题",
          "category": "签证政策/目的地/航空交通/行业数据/文旅活动/旅行提示",
          "summary": "40-60字摘要",
          "source": "来源媒体名称",
          "impact": "20-30字影响分析",
          "source_url": "https://www.baidu.com/s?wd=...",
          "key_figures": ["关键数据1", "关键数据2"],
          "travel_advisory": "10字以内提示",
          "tag": "爆/热/新"
        }}
      ]
    }}
  ]
}}
```

必须包含全部 25 个国家，每国恰好 10 条事件。
如果某国搜索结果不足，用"本周暂无更多热点"占位，但字段必须完整。
只输出 JSON，不要其他文字。

## 搜索结果
{search_summary}"""

    print(f"\n🤖 调用 Claude API 分析...")
    print(f"   搜索数据: {sum(len(v) for v in search_results.values())} 条")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    print(f"   Claude 响应: {len(response_text)} 字符")

    # 提取 JSON
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        print("❌ Claude 响应中未找到 JSON")
        sys.exit(1)

    data = json.loads(json_match.group())

    # 验证
    total = sum(len(c['events']) for c in data['countries'])
    print(f"   ✅ {len(data['countries'])} 国, {total} 条事件")

    return data


def save_data(data):
    """保存数据和更新 manifest"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    daily_dir = os.path.join(script_dir, 'daily')
    os.makedirs(daily_dir, exist_ok=True)

    # 保存当日数据
    out_path = os.path.join(daily_dir, f'{DATE_STR}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n📁 数据已保存: {out_path}")

    # 更新 manifest
    import glob as _glob
    dates = []
    for f in sorted(_glob.glob(os.path.join(daily_dir, '2*.json'))):
        ds = os.path.basename(f).replace('.json', '')
        try:
            with open(f, 'r', encoding='utf-8-sig') as fh:
                d = json.load(fh)
            t = sum(len(c['events']) for c in d['countries'])
            dates.append({'date': ds, 'countries': len(d['countries']), 'events': t})
        except:
            pass

    manifest = {'available_dates': dates}
    with open(os.path.join(daily_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"📋 manifest.json: {len(dates)} 天")

    return out_path


def main():
    print(f"📡 全球旅游热点智能采集 - {DATE_STR}")
    print(f"   时效窗口: {SEVEN_DAYS_AGO} ~ {DATE_STR}")
    print(f"   国家: {len(COUNTRIES)} 个")
    print()

    # 1. 搜索新闻
    print("📡 Step 1: 搜索新闻...")
    search_results = search_news()

    # 2. Claude 智能分析
    print("\n🤖 Step 2: Claude 智能分析...")
    data = analyze_with_claude(search_results)

    # 3. 保存
    print("\n💾 Step 3: 保存数据...")
    out_path = save_data(data)

    # 4. 摘要
    total = sum(len(c['events']) for c in data['countries'])
    tags = {}
    for c in data['countries']:
        for e in c['events']:
            t = e.get('tag', '')
            tags[t] = tags.get(t, 0) + 1

    print(f"\n{'='*50}")
    print(f"✅ 采集完成!")
    print(f"📅 {DATE_STR} | 🌍 {len(data['countries'])}国 | 📰 {total}条")
    print(f"🔥 爆={tags.get('爆',0)} 热={tags.get('热',0)} 新={tags.get('新',0)}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
