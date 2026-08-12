#!/usr/bin/env python3
"""
每日全球旅游热点智能采集 v7 - Hugging Face 版
DuckDuckGo 搜索 + Hugging Face (Qwen 2.5 72B) 智能分析
免费 + 自动 + 质量较好

环境变量:
  HF_TOKEN - Hugging Face API Token (必需)
"""
import json, os, sys, re, time, glob
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote

TODAY = datetime.utcnow() + timedelta(hours=8)
DATE_STR = TODAY.strftime('%Y-%m-%d')
SEVEN_DAYS_AGO = (TODAY - timedelta(days=7)).strftime('%Y-%m-%d')

HF_TOKEN = os.environ.get('HF_TOKEN', '')
if not HF_TOKEN:
    print("❌ 未设置 HF_TOKEN")
    sys.exit(1)

COUNTRIES = {
    'CN':'中国','JP':'日本','KR':'韩国','TH':'泰国','SG':'新加坡',
    'MY':'马来西亚','VN':'越南','IN':'印度','FR':'法国','IT':'意大利',
    'ES':'西班牙','GB':'英国','DE':'德国','GR':'希腊','TR':'土耳其',
    'CH':'瑞士','RU':'俄罗斯','US':'美国','CA':'加拿大','MX':'墨西哥',
    'BR':'巴西','AR':'阿根廷','AU':'澳大利亚','NZ':'新西兰','AE':'阿联酋'
}

SEARCH_QUERIES = [
    ('CN', ['中国 出入境 签证 旅游 {date}', 'China visa travel {date}']),
    ('JP', ['日本 旅游 签证 {date}', 'Japan travel visa {date}']),
    ('KR', ['韩国 旅游 {date}', 'Korea travel {date}']),
    ('TH', ['泰国 旅游 {date}', 'Thailand travel {date}']),
    ('SG', ['新加坡 旅游 {date}', 'Singapore travel {date}']),
    ('MY', ['马来西亚 旅游 {date}', 'Malaysia travel {date}']),
    ('VN', ['越南 旅游 {date}', 'Vietnam travel {date}']),
    ('IN', ['印度 旅游 {date}', 'India travel {date}']),
    ('FR', ['法国 旅游 {date}', 'France travel {date}']),
    ('IT', ['意大利 旅游 {date}', 'Italy travel {date}']),
    ('ES', ['西班牙 旅游 {date}', 'Spain travel {date}']),
    ('GB', ['英国 旅游 {date}', 'UK travel {date}']),
    ('DE', ['德国 旅游 {date}', 'Germany travel {date}']),
    ('GR', ['希腊 旅游 {date}', 'Greece travel {date}']),
    ('TR', ['土耳其 旅游 {date}', 'Turkey travel {date}']),
    ('CH', ['瑞士 旅游 {date}', 'Switzerland travel {date}']),
    ('RU', ['俄罗斯 旅游 {date}', 'Russia travel {date}']),
    ('US', ['美国 旅游 签证 {date}', 'USA travel visa {date}']),
    ('CA', ['加拿大 旅游 {date}', 'Canada travel {date}']),
    ('MX', ['墨西哥 旅游 {date}', 'Mexico travel {date}']),
    ('BR', ['巴西 旅游 {date}', 'Brazil travel {date}']),
    ('AR', ['阿根廷 旅游 {date}', 'Argentina travel {date}']),
    ('AU', ['澳大利亚 旅游 {date}', 'Australia travel {date}']),
    ('NZ', ['新西兰 旅游 {date}', 'New Zealand travel {date}']),
    ('AE', ['阿联酋 迪拜 旅游 {date}', 'UAE Dubai travel {date}']),
]


def search_news():
    """搜索新闻"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        os.system(f"{sys.executable} -m pip install ddgs -q")
        from ddgs import DDGS
    
    ddgs = DDGS()
    results = {}
    
    for code, queries in SEARCH_QUERIES:
        name = COUNTRIES[code]
        hits = []
        for q in queries:
            q = q.format(date=DATE_STR)
            try:
                hits.extend(list(ddgs.text(q, max_results=4)))
                time.sleep(1)
            except: pass
        results[code] = [{'t':h.get('title',''),'b':h.get('body',''),'u':h.get('href','')} for h in hits[:10]]
        print(f"  {name}: {len(results[code])} 条")
    
    return results


def analyze_with_hf(search_results):
    """调用 Hugging Face API (Qwen 2.5 72B)"""
    summary = ""
    for code, items in search_results.items():
        summary += f"\n### {COUNTRIES[code]}\n"
        for i,r in enumerate(items,1):
            summary += f"{i}. {r['t']}\n   {r['b'][:100]}\n"
        if not items:
            summary += f"(暂无搜索结果)\n"

    prompt = f"""今天是{DATE_STR}，你是旅游分析师。为每个国家整理 10 条出入境旅游利好要闻。

要求：
- 仅收录{SEVEN_DAYS_AGO}至{DATE_STR}的事件
- 只收录：签证放宽/新航线/旅游优惠/正向数据/文旅活动
- 排除：政治/财报/安全/负面/过期内容
- rank1=tag:爆，rank2-3=tag:热，rank4-10=tag:新
- source_url 用：https://www.baidu.com/s?wd= + URL 编码 (标题)
- 不足 10 条用"本周暂无热点"占位，但字段必须完整

输出 JSON（只输出 JSON）：
{{"date":"{DATE_STR}","countries":[{{"code":"CN","name":"中国","events":[{{"rank":1,"title":"标题","category":"签证政策/目的地/航空交通/行业数据/文旅活动/旅行提示","summary":"摘要","source":"来源","impact":"影响","source_url":"https://...","key_figures":["数据"],"travel_advisory":"提示","tag":"爆/热/新"}}]}}]}}

搜索结果：
{summary}"""

    print("\n 调用 Hugging Face API (Qwen 2.5 72B)...")
    
    url = 'https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct'
    payload = json.dumps({
        "inputs": prompt,
        "parameters": {"max_new_tokens": 4000, "temperature": 0.3}
    }).encode()
    
    req = Request(url, data=payload, headers={
        'Authorization': f'Bearer {HF_TOKEN}',
        'Content-Type': 'application/json'
    })
    
    try:
        resp = urlopen(req, timeout=180)
        result = json.loads(resp.read())
        text = result[0].get('generated_text', '')
    except Exception as e:
        print(f"  HF API 错误：{e}")
        sys.exit(1)
    
    # 提取 JSON
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        print("  HF 未返回 JSON")
        sys.exit(1)
    
    return json.loads(match.group())


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
    print(f"📡 全球旅游热点 (Hugging Face) - {DATE_STR}")
    print("Step 1: 搜索...")
    results = search_news()
    
    print("Step 2: HF 分析...")
    data = analyze_with_hf(results)
    
    print("Step 3: 保存...")
    save_data(data)
    
    total = sum(len(c['events']) for c in data['countries'])
    print(f"✅ {DATE_STR} | {len(data['countries'])}国 | {total}条")


if __name__ == '__main__':
    main()
