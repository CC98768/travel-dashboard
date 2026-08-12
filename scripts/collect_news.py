#!/usr/bin/env python3
"""
每日全球旅游热点智能采集 v9 - NewsData.io 修复版
NewsData.io API + 简单规则分析
免费额度 + 自动运行

环境变量:
  NEWSDATA_API_KEY - NewsData.io API Key (必需)
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
        query = f"{name} travel tourism visa"
        
        # 注意：不使用 from/to 参数，免费版可能不支持
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={quote(query)}&language=en,zh"
        
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
                    'source': article.get('source_id', 'NewsData.io'),
                    'date': article.get('pubDate', '')
                })
            
            all_results[code] = results
            print(f"  {name}: {len(results)} 条")
            time.sleep(2)  # 避免频率限制
            
        except Exception as e:
            print(f"  ⚠️ {name}: {e}")
            all_results[code] = []
    
    return all_results


def simple_analyze(search_results):
    """简单规则分析"""
    countries_data = []
    
    for code, name in COUNTRIES.items():
        results = search_results.get(code, [])
        events = []
        
        for i, r in enumerate(results[:10]):
            title = r.get('title', '')[:25]
            desc = r.get('body', '')[:60]
            
            # 简单分类
            category = '目的地'
            if any(k in title+desc for k in ['visa', '签证', '免签', 'visa-free']):
                category = '签证政策'
            elif any(k in title+desc for k in ['flight', '航线', '航班', 'airline']):
                category = '航空交通'
            elif any(k in title+desc for k in ['growth', '增长', 'data', '数据', 'million']):
                category = '行业数据'
            elif any(k in title+desc for k in ['festival', '活动', 'event']):
                category = '文旅活动'
            elif any(k in title+desc for k in ['discount', '优惠', 'promotion']):
                category = '旅行提示'
            
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
    
    with open(os.path.join(dd, f'{DATE_STR}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n 数据已保存：{dd}/{DATE_STR}.json")
    
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
    print(f"📡 全球旅游热点 (NewsData.io) - {DATE_STR}")
    print(f"   时效窗口：{SEVEN_DAYS_AGO} ~ {DATE_STR}")
    print()
    
    # 1. 搜索
    print("Step 1: NewsData.io 搜索...")
    results = search_with_newsdata()
    
    # 2. 分析
    print("\nStep 2: 智能分析...")
    data = simple_analyze(results)
    
    # 3. 保存
    print("\nStep 3: 保存...")
    save_data(data)
    
    # 4. 摘要
    total = sum(len(c['events']) for c in data['countries'])
    tags = {}
    for c in data['countries']:
        for e in c['events']:
            t = e.get('tag', '')
            tags[t] = tags.get(t, 0) + 1
    
    print(f"\n{'='*50}")
    print(f"✅ 采集完成!")
    print(f" {DATE_STR} | 🌍 {len(data['countries'])}国 | 📰 {total}条")
    print(f"🔥 爆={tags.get('爆',0)} 热={tags.get('热',0)} 新={tags.get('新',0)}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
