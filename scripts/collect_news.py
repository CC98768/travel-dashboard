#!/usr/bin/env python3
"""
每日全球旅游热点采集 - 纯搜索版
无需任何 AI API Key，100% 免费
DuckDuckGo 搜索 + 关键词规则过滤
"""
import json, os, sys, re, time, glob
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote

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

POSITIVE_KW = [
    'visa-free','visa','flight','route','growth','increase','new',
    'tourism','travel','免签','签证','航线','增长','旅游','优惠','便利',
    'recovery','reopen','recovered','开通','新增','放宽'
]
NEGATIVE_KW = [
    'terror','attack','war','sanction','earthquake','flood',
    '恐袭','战争','地震','制裁','洪水','负面'
]


def search_country(name, date_str):
    """搜索单个国家的旅游新闻"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        os.system(f"{sys.executable} -m pip install ddgs -q")
        from ddgs import DDGS
    
    ddgs = DDGS()
    results = []
    queries = [
        f'{name} travel visa tourism {date_str}',
        f'{name} 旅游 签证 {date_str}',
    ]
    for q in queries:
        try:
            hits = list(ddgs.text(q, max_results=5))
            for h in hits:
                results.append({
                    't': h.get('title',''),
                    'b': h.get('body',''),
                    'u': h.get('href','')
                })
            time.sleep(2)
        except: pass
    return results


def is_relevant(text):
    score = 0
    for kw in POSITIVE_KW:
        if kw.lower() in text.lower(): score += 1
    for kw in NEGATIVE_KW:
        if kw.lower() in text.lower(): score -= 3
    return score > 0


def classify(text):
    if any(k in text for k in ['签证','visa','免签']): return '签证政策'
    if any(k in text for k in ['航线','航班','flight','route']): return '航空交通'
    if any(k in text for k in ['增长','数据','growth','million']): return '行业数据'
    if any(k in text for k in ['活动','festival','event']): return '文旅活动'
    if any(k in text for k in ['优惠','discount']): return '旅行提示'
    return '目的地'


def make_baidu_url(title):
    return 'https://www.baidu.com/s?wd=' + quote(title)


def main():
    print(f"📡 全球旅游热点 (纯搜索版) - {DATE_STR}")
    print(f"   时效: {SEVEN_DAYS_AGO} ~ {DATE_STR}\n")

    countries_data = []
    for code, name in COUNTRIES.items():
        results = search_country(name, DATE_STR)
        print(f"  {name}: {len(results)} 条")

        relevant = [r for r in results if is_relevant(r['t'] + ' ' + r['b'])]
        
        events = []
        for i, r in enumerate(relevant[:10]):
            title = r['t'][:25] if r['t'] else f'{name}旅游动态'
            desc = r['b'][:60] if r['b'] else ''
            
            events.append({
                'rank': i + 1,
                'title': title,
                'category': classify(title + ' ' + desc),
                'summary': desc if len(desc) >= 20 else (title + ' - ' + desc),
                'source': 'DuckDuckGo',
                'impact': '关注后续发展',
                'source_url': make_baidu_url(title),
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
                'summary': f'暂无更多本周旅游热点，请搜索查看',
                'source': '系统',
                'impact': '暂无',
                'source_url': make_baidu_url(name + '旅游'),
                'key_figures': [],
                'travel_advisory': '',
                'tag': '新',
            })

        countries_data.append({'code': code, 'name': name, 'events': events[:10]})

    data = {'date': DATE_STR, 'countries': countries_data}

    # 保存
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    daily_dir = os.path.join(script_dir, 'daily')
    os.makedirs(daily_dir, exist_ok=True)

    out_path = os.path.join(daily_dir, f'{DATE_STR}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # manifest
    dates = []
    for fp in sorted(glob.glob(os.path.join(daily_dir, '2*.json'))):
        ds = os.path.basename(fp).replace('.json','')
        try:
            with open(fp,'r',encoding='utf-8-sig') as fh:
                d = json.load(fh)
            t = sum(len(c['events']) for c in d['countries'])
            dates.append({'date':ds,'countries':len(d['countries']),'events':t})
        except: pass
    with open(os.path.join(daily_dir,'manifest.json'),'w',encoding='utf-8') as f:
        json.dump({'available_dates':dates},f,ensure_ascii=False,indent=2)

    total = sum(len(c['events']) for c in data['countries'])
    print(f"\n✅ {DATE_STR} | {len(data['countries'])}国 | {total}条")


if __name__ == '__main__':
    main()
