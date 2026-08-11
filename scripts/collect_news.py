#!/usr/bin/env python3
"""
每日全球旅游热点智能采集 v5 - Groq 版
DuckDuckGo 搜索 + Groq (Llama 3.1) 智能分析
全自动、免费、高质量
"""
import json, os, sys, re, time, glob
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote

TODAY = datetime.utcnow() + timedelta(hours=8)
DATE_STR = TODAY.strftime('%Y-%m-%d')
SEVEN_DAYS_AGO = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
if not GROQ_API_KEY:
    print("❌ 未设置 GROQ_API_KEY")
    sys.exit(1)

COUNTRIES = {
    'CN':'中国','JP':'日本','KR':'韩国','TH':'泰国','SG':'新加坡',
    'MY':'马来西亚','VN':'越南','IN':'印度','FR':'法国','IT':'意大利',
    'ES':'西班牙','GB':'英国','DE':'德国','GR':'希腊','TR':'土耳其',
    'CH':'瑞士','RU':'俄罗斯','US':'美国','CA':'加拿大','MX':'墨西哥',
    'BR':'巴西','AR':'阿根廷','AU':'澳大利亚','NZ':'新西兰','AE':'阿联酋'
}

SEARCH_QUERIES = [
    ('CN','中国 出入境 签证 旅游 {date}'), ('JP','日本 旅游 签证 {date}'),
    ('KR','韩国 旅游 {date}'), ('TH','泰国 旅游 {date}'),
    ('SG','新加坡 旅游 {date}'), ('MY','马来西亚 旅游 {date}'),
    ('VN','越南 旅游 {date}'), ('IN','印度 旅游 {date}'),
    ('FR','法国 旅游 {date}'), ('IT','意大利 旅游 {date}'),
    ('ES','西班牙 旅游 {date}'), ('GB','英国 旅游 {date}'),
    ('DE','德国 旅游 {date}'), ('GR','希腊 旅游 {date}'),
    ('TR','土耳其 旅游 {date}'), ('CH','瑞士 旅游 {date}'),
    ('RU','俄罗斯 旅游 {date}'), ('US','美国 旅游 签证 {date}'),
    ('CA','加拿大 旅游 {date}'), ('MX','墨西哥 旅游 {date}'),
    ('BR','巴西 旅游 {date}'), ('AR','阿根廷 旅游 {date}'),
    ('AU','澳大利亚 旅游 {date}'), ('NZ','新西兰 旅游 {date}'),
    ('AE','阿联酋 迪拜 旅游 {date}'),
]


def search_news():
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        os.system(f"{sys.executable} -m pip install duckduckgo-search -q")
        from duckduckgo_search import DDGS
    ddgs = DDGS()
    results = {}
    for code, q in SEARCH_QUERIES:
        name = COUNTRIES[code]
        hits = []
        try:
            hits = list(ddgs.text(q.format(date=DATE_STR), max_results=6))
            time.sleep(1)
        except: pass
        results[code] = [{'t':h.get('title',''),'b':h.get('body',''),'u':h.get('href','')} for h in hits]
        print(f"  🔍 {name}: {len(results[code])} 条")
    return results


def analyze_with_groq(search_results):
    summary = ""
    for code, items in search_results.items():
        summary += f"\n### {COUNTRIES[code]}\n"
        for i,r in enumerate(items,1):
            summary += f"{i}. {r['t']}\n   {r['b'][:100]}\n"

    prompt = f"""今天是{DATE_STR}，你是旅游分析师。根据搜索结果，为每个国家整理10条出入境旅游利好要闻。

要求：
- 仅收录{SEVEN_DAYS_AGO}至{DATE_STR}的事件
- 只收录：签证放宽/新航线/旅游优惠/正向数据/文旅活动
- 排除：政治/财报/安全/负面/过期内容
- rank1=tag:爆, rank2-3=tag:热, rank4-10=tag:新
- source_url统一用: https://www.baidu.com/s?wd= + URL编码(标题+来源)
- 不足10条用"本周暂无热点"占位，但字段必须完整

输出JSON（只输出JSON，不要其他文字）：
{{"date":"{DATE_STR}","countries":[{{"code":"CN","name":"中国","events":[{{"rank":1,"title":"标题","category":"签证政策/目的地/航空交通/行业数据/文旅活动/旅行提示","summary":"摘要","source":"来源","impact":"影响","source_url":"https://...","key_figures":["数据"],"travel_advisory":"提示","tag":"爆/热/新"}}]}}]}}

搜索结果：
{summary}"""

    url = 'https://api.groq.com/openai/v1/chat/completions'
    payload = json.dumps({
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 16000
    }).encode()
    req = Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GROQ_API_KEY}'
    })
    resp = urlopen(req, timeout=180)
    data = json.loads(resp.read())

    text = data['choices'][0]['message']['content']
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        print("❌ Groq 未返回 JSON")
        sys.exit(1)
    return json.loads(match.group())


def save_data(data):
    sd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dd = os.path.join(sd, 'daily')
    os.makedirs(dd, exist_ok=True)
    with open(os.path.join(dd, f'{DATE_STR}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
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
    print(f"📋 manifest: {len(dates)} 天")


def main():
    print(f"📡 全球旅游热点 (Groq) - {DATE_STR}")
    print("Step 1: 搜索...")
    results = search_news()
    print("Step 2: Groq 分析...")
    data = analyze_with_groq(results)
    print("Step 3: 保存...")
    save_data(data)
    total = sum(len(c['events']) for c in data['countries'])
    print(f"✅ {DATE_STR} | {len(data['countries'])}国 | {total}条")


if __name__ == '__main__':
    main()
