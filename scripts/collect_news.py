#!/usr/bin/env python3
"""
每日全球旅游热点采集 - Google News RSS 版
完全免费，无需 API Key
"""
import json, os, sys, time, glob, re
from datetime import datetime, timedelta
from urllib.parse import quote
import feedparser

TODAY = datetime.utcnow() + timedelta(hours=8)
DATE_STR = TODAY.strftime('%Y-%m-%d')
SEVEN_DAYS_AGO = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')

COUNTRIES = {
    'CN':'中国','JP':'日本','KR':'韩国','TH':'泰国','SG':'新加坡',
    'MY':'马来西亚','VN':'越南','IN':'印度','FR':'法国','IT':'意大利',
    'ES':'西班牙','GB':'英国','DE':'德国','GR':'希腊','TR':'土耳其',
    'CH':'瑞士','RU':'俄罗斯','US':'美国','CA':'加拿大','MX':'墨西哥',
    'BR':'巴西','AR':'阿根廷','AU':'澳大利亚','NZ':'新西兰','AE':'阿联酋'
}


def search_google_news(country_name):
    """使用 Google News RSS 搜索"""
    query = f"{country_name} travel tourism visa"
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        results = []
        
        for entry in feed.entries[:10]:
            # 提取标题和摘要
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            link = entry.get('link', '')
            
            results.append({
                'title': title,
                'body': summary,
                'url': link,
                'source': 'Google News',
                'date': entry.get('published', '')
            })
        
        return results
        
    except Exception as e:
        print(f"  ⚠️ {country_name}: {e}")
        return []


def analyze_results(all_results):
    """分析结果，生成结构化数据"""
    countries_data = []
    
    for code, name in COUNTRIES.items():
        results = all_results.get(code, [])
        events = []
        
        for i, r in enumerate(results[:10]):
            title = r.get('title', '')[:30]
            desc = r.get('body', '')[:80]
            
            # 简单分类
            category = '目的地'
            text = (title + ' ' + desc).lower()
            if any(k in text for k in ['visa', '签证', '免签', 'visa-free']):
                category = '签证政策'
            elif any(k in text for k in ['flight', '航线', '航班', 'airline']):
                category = '航空交通'
            elif any(k in text for k in ['growth', '增长', 'data', '数据', 'million']):
                category = '行业数据'
            elif any(k in text for k in ['festival', '活动', 'event']):
                category = '文旅活动'
            elif any(k in text for k in ['discount', '优惠', 'promotion']):
                category = '旅行提示'
            
            events.append({
                'rank': i + 1,
                'title': title if title else f'{name}旅游动态',
                'category': category,
                'summary': desc if len(desc) >= 30 else '暂无更多详情',
                'source': r.get('source', 'Google News'),
                'impact': '关注后续发展',
                'source_url': r.get('url', f"https://www.baidu.com/s?wd={quote(title)}"),
                'key_figures': [title[:30]],
                'travel_advisory': '关注最新动态',
                'tag': '爆' if i == 0 else ('热' if i < 3 else '新'),
            })
        
        # 补满 10 条
        while len(events) < 10:
            events.append({
                'rank': len(events) + 1,
                'title': f'{name}旅游动态待更新',
                'category': '行业数据',
                'summary': '暂无更多旅游热点',
                'source': '系统',
                'impact': '暂无',
                'source_url': f"https://www.baidu.com/s?wd={quote(name+'旅游')}",
                'key_figures': [],
                'travel_advisory': '',
                'tag': '新',
            })
        
        countries_data.append({'code': code, 'name': name, 'events': events[:10]})
    
    return {'date': DATE_STR, 'countries': countries_data}


def save_data(data):
    """保存数据"""
    sd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dd = os.path.join(sd, 'daily')
    os.makedirs(dd, exist_ok=True)
    
    output_file = os.path.join(dd, f'{DATE_STR}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n 数据已保存：{output_file}")
    
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
    print(f"📡 全球旅游热点 (Google News RSS) - {DATE_STR}")
    print()
    
    # 1. 搜索所有国家
    print("Step 1: Google News RSS 搜索...")
    all_results = {}
    for code, name in COUNTRIES.items():
        print(f"  搜索 {name}...")
        all_results[code] = search_google_news(name)
        print(f"    ✅ {len(all_results[code])} 条")
        time.sleep(0.5)
    
    # 2. 分析
    print("\nStep 2: 分析结果...")
    data = analyze_results(all_results)
    
    # 3. 保存
    print("\nStep 3: 保存...")
    save_data(data)
    
    # 4. 摘要
    total = sum(len(c['events']) for c in data['countries'])
    print(f"\n{'='*50}")
    print(f"✅ 完成! {DATE_STR} | {len(data['countries'])}国 | {total}条")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
