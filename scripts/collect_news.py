#!/usr/bin/env python3
"""
每日全球旅游热点智能采集 v8 - NewsData.io 版
NewsData.io API + Claude API 智能分析
免费额度 + 高质量数据

环境变量:
  NEWSDATA_API_KEY - NewsData.io API Key (必需)
  ANTHROPIC_API_KEY - Claude API Key (可选，用于智能分析)
"""
import json, os, sys, re, time, glob
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote

TODAY = datetime.utcnow() + timedelta(hours=8)
DATE_STR = TODAY.strftime('%Y-%m-%d')
SEVEN_DAYS_AGO = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')

NEWSDATA_API_KEY = os.environ.get('NEWSDATA_API_KEY', '')
if not NEWSDATA_API_KEY:
    print("❌ 未设置 NEWSDATA_API_KEY")
    sys.exit(1)

COUNTRIES = {
    'CN':'中国','JP':'日本','KR':'韩国','TH':'泰国','SG':'新加坡',
    'MY':'马来西亚','VN':'越南','IN':'印度','FR':'法国','IT':'意大利',
    'ES':'西班牙','GB':'英国','DE':'德国','GR':'希腊','TR':'土耳其',
    'CH':'瑞士','RU':'俄罗斯','US':'美国','CA':'加拿大','MX':'墨西哥',
    'BR':'巴西','AR':'阿根廷','AU':'澳大利亚','NZ':'新西兰','AE':'阿联酋'
}


def search_with_newsdata():
    """使用 NewsData.io API 搜索"""
    all_results = {}
    
    for code, name in COUNTRIES.items():
        # 构建搜索查询
        query = f"{name} travel OR tourism OR visa"
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={quote(query)}&language=en,zh&from={SEVEN_DAYS_AGO}&to={DATE_STR}"
        
        try:
            req = Request(url)
            resp = urlopen(req, timeout=30)
            data = json.loads(resp.read())
            
            results = []
            for article in data.get('results', [])[:10]:
                results.append({
                    'title': article.get('title', ''),
                    'body': article.get('description', ''),
                    'url': article.get('link', ''),
                    'source': article.get('source_id', ''),
                    'date': article.get('pubDate', '')
                })
            
            all_results[code] = results
            print(f"  {name}: {len(results)} 条")
            time.sleep(1)  # 避免频率限制
            
        except Exception as e:
            print(f"  ⚠️ {name}: {e}")
            all_results[code] = []
    
    return all_results


def analyze_results(search_results):
    """智能分析结果（如果有 Claude API Key）"""
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    
    if not ANTHROPIC_API_KEY:
        # 简单规则分析（无 AI）
        return simple_analyze(search_results)
    
    # 使用 Claude API 智能分析
    return claude_analyze(search_results, ANTHROPIC_API_KEY)


def simple_analyze(search_results):
    """简单规则分析（备用方案）"""
    countries_data = []
    
    for code, name in COUNTRIES.items():
        results = search_results.get(code, [])
        events = []
        
        for i, r in enumerate(results[:10]):
            title = r.get('title', '')[:25]
            desc = r.get('body', '')[:60]
            
            # 简单分类
            category = '目的地'
            if any(k in title+desc for k in ['visa', '签证', '免签']):
                category = '签证政策'
            elif any(k in title+desc for k in ['flight', '航线', '航班']):
                category = '航空交通'
            elif any(k in title+desc for k in ['growth', '增长', 'data', '数据']):
                category = '行业数据'
            
            events.append({
                'rank': i + 1,
                'title': title if title else f'{name}旅游动态',
                'category': category,
                'summary': desc if len(desc) >= 20 else (title + ' - ' + desc),
                'source': r.get('source', 'NewsData.io'),
                'impact': '关注后续发展',
                'source_url': f"https://www.baidu.com/s?wd={quote(title)}",
                'key_figures': [title[:30]],
                'travel_advisory': '关注最新动态',
                'tag': '爆' if i == 0 else ('热' if i < 3 else '新'),
            })
        
        # 补满 10 条
        while len(events) < 10:
            rank = len(events) + 1
            events.append({
                'rank': rank,
                'title': f'{name}旅游动态待更新',
                'category': '行业数据',
                'summary': '暂无更多本周旅游热点',
                'source': '系统',
                'impact': '暂无',
                'source_url': f"https://www.baidu.com/s?wd={quote(name+'旅游')}",
                'key_figures': [],
                'travel_advisory': '',
                'tag': '新',
            })
        
        countries_data.append({'code': code, 'name': name, 'events': events[:10]})
    
    return {'date': DATE_STR, 'countries': countries_data}


def claude_analyze(search_results, api_key):
    """使用 Claude API 智能分析"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # 准备搜索摘要
    summary = ""
    for code, items in search_results.items():
        summary += f"\n### {COUNTRIES[code]}\n"
        for i, r in enumerate(items, 1):
            summary += f"{i}. {r['title']}\n   {r['body'][:100]}\n"
    
    prompt = f"""你是旅游分析师。根据搜索结果，为每个国家整理 10 条旅游利好要闻。

要求：
- 仅收录{SEVEN_DAYS_AGO}至{DATE_STR}的事件
- 只收录：签证放宽/新航线/旅游优惠/正向数据/文旅活动
- rank1=tag:爆，rank2-3=tag:热，rank4-10=tag:新
- 不足 10 条用"本周暂无热点"占位

输出 JSON：
{{"date":"{DATE_STR}","countries":[{{"code":"CN","name":"中国","events":[{{"rank":1,"title":"标题","category":"签证政策/目的地/航空交通/行业数据/文旅活动/旅行提示","summary":"摘要","source":"来源","impact":"影响","source_url":"https://www.baidu.com/s?wd=...","key_figures":["数据"],"travel_advisory":"提示","tag":"爆/热/新"}}]}}]}}

搜索结果：
{summary}"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = message.content[0].text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group())
    
    # 如果 Claude 失败，回退到简单分析
    return simple_analyze(search_results)


def save_data(data):
    """保存数据"""
    sd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dd = os.path.join(sd, 'daily')
    os.makedirs(dd, exist_ok=True)
    
    with open(os.path.join(dd, f'{DATE_STR}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 更新 manifest
    dates = []
    for fp in sorted(glob.glob(os.path.join(dd, '2*.json'))):
        ds = os.path.basename(fp).replace('.json','')
        try:
            with open(fp,'r',encoding='utf-8-sig') as fh: d=json.load(fh)
            t = sum(len(c['events']) for c in d['countries'])
            dates.append({'date':ds,'countries':len(d['countries']),'events':t})
        except: pass
    
    with open(os.path.join(dd,'manifest.json'),'w',encoding='utf-8') as f:
        json.dump({'available_dates':dates},f,ensure_ascii=False,indent=2)
    
    print(f" manifest: {len(dates)} 天")


def main():
    print(f" 全球旅游热点 (NewsData.io) - {DATE_STR}")
    print("Step 1: NewsData.io 搜索...")
    results = search_with_newsdata()
    
    print("Step 2: 智能分析...")
    data = analyze_results(results)
    
    print("Step 3: 保存...")
    save_data(data)
    
    total = sum(len(c['events']) for c in data['countries'])
    print(f"✅ {DATE_STR} | {len(data['countries'])}国 | {total}条")


if __name__ == '__main__':
    main()
