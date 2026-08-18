#!/usr/bin/env python3
"""
全球旅游热点看板 - 多源数据采集器 v2.0
修复：国家匹配（利用源上下文）、分类均衡、去重
"""

import json, os, re, time, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from difflib import SequenceMatcher

try:
    import feedparser
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ 缺少依赖: {e}\n请运行: pip install -r requirements.txt")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"
TODAY_FILE = DATA_DIR / "today.json"

COUNTRIES_25 = [
    "中国","日本","韩国","泰国","新加坡","越南","马来西亚","印度",
    "菲律宾","印度尼西亚","法国","意大利","西班牙","英国","德国",
    "希腊","土耳其","瑞士","俄罗斯","美国","加拿大","墨西哥",
    "巴西","澳大利亚","新西兰"
]

COUNTRY_EN = {
    "中国":"China","日本":"Japan","韩国":"South Korea","泰国":"Thailand",
    "新加坡":"Singapore","越南":"Vietnam","马来西亚":"Malaysia","印度":"India",
    "菲律宾":"Philippines","印度尼西亚":"Indonesia","法国":"France",
    "意大利":"Italy","西班牙":"Spain","英国":"UK","德国":"Germany",
    "希腊":"Greece","土耳其":"Turkey","瑞士":"Switzerland","俄罗斯":"Russia",
    "美国":"USA","加拿大":"Canada","墨西哥":"Mexico","巴西":"Brazil",
    "澳大利亚":"Australia","新西兰":"New Zealand"
}

CATEGORIES = ["航线交通","出入境政策","本地生活","旅游趋势","景点活动","文娱信息"]
SC_EXPECTED = {"航线交通":2,"出入境政策":2,"本地生活":1,"旅游趋势":2,"景点活动":2,"文娱信息":1}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TravelDashboard/1.0)"
}

# =============================================
# 信源定义
# =============================================

# RSS 源 + 预设国家（用于国家匹配）
RSS_SOURCES = [
    {"name":"Reddit r/travel","url":"https://www.reddit.com/r/travel/.rss","lang":"en","country_hint":None},
    {"name":"Reddit r/solotravel","url":"https://www.reddit.com/r/solotravel/.rss","lang":"en","country_hint":None},
    {"name":"Reddit r/backpacking","url":"https://www.reddit.com/r/backpacking/.rss","lang":"en","country_hint":None},
    {"name":"Reddit r/ChinaTravel","url":"https://www.reddit.com/r/ChinaTravel/.rss","lang":"en","country_hint":"中国"},
    {"name":"Reddit r/JapanTravel","url":"https://www.reddit.com/r/JapanTravel/.rss","lang":"en","country_hint":"日本"},
    {"name":"Reddit r/ThailandTourism","url":"https://www.reddit.com/r/ThailandTourism/.rss","lang":"en","country_hint":"泰国"},
    {"name":"Skift","url":"https://skift.com/feed/","lang":"en","country_hint":None},
    {"name":"The Points Guy","url":"https://thepointsguy.com/feed/","lang":"en","country_hint":None},
    {"name":"One Mile at a Time","url":"https://onemileatatime.com/feed/","lang":"en","country_hint":None},
]

# 各国官方信源URL映射
OFFICIAL_SOURCES = {
    "中国":[
        {"name":"中国政府网","url":"https://www.gov.cn/zhengce/","type":"出入境政策"},
        {"name":"文化和旅游部","url":"https://www.mct.gov.cn/whzx/whyw/","type":"旅游趋势"},
    ],
    "日本":[
        {"name":"JNTO","url":"https://www.jnto.go.jp/news/","type":"旅游趋势"},
    ],
    "韩国":[
        {"name":"韩国观光公社","url":"https://www.visitkorea.or.kr/","type":"旅游趋势"},
    ],
    "泰国":[
        {"name":"泰国旅游局TAT","url":"https://www.tat.or.th/","type":"旅游趋势"},
        {"name":"泰国电子签","url":"https://thaievisa.go.th/","type":"出入境政策"},
    ],
    "新加坡":[
        {"name":"新加坡旅游局STB","url":"https://www.stb.gov.sg/","type":"旅游趋势"},
        {"name":"新加坡ICA","url":"https://www.ica.gov.sg/","type":"出入境政策"},
    ],
    "越南":[
        {"name":"越南旅游局","url":"https://www.vietnam.travel/","type":"旅游趋势"},
    ],
    "马来西亚":[
        {"name":"马来西亚旅游局","url":"https://www.tourism.gov.my/","type":"旅游趋势"},
    ],
    "印度":[
        {"name":"印度旅游局","url":"https://www.incredibleindia.gov.in/","type":"旅游趋势"},
        {"name":"印度签证","url":"https://indianvisaonline.gov.in/","type":"出入境政策"},
    ],
    "菲律宾":[
        {"name":"菲律宾旅游局","url":"https://www.tourism.gov.ph/","type":"旅游趋势"},
    ],
    "印度尼西亚":[
        {"name":"印尼旅游部","url":"https://www.indonesia.travel/","type":"旅游趋势"},
    ],
    "法国":[
        {"name":"法国旅游局","url":"https://www.france.fr/","type":"旅游趋势"},
    ],
    "意大利":[
        {"name":"ENIT","url":"https://www.enit.it/","type":"旅游趋势"},
    ],
    "西班牙":[
        {"name":"Turespaña","url":"https://www.spain.info/","type":"旅游趋势"},
    ],
    "英国":[
        {"name":"VisitBritain","url":"https://www.visitbritain.com/","type":"旅游趋势"},
        {"name":"UK Visas","url":"https://www.gov.uk/browse/visas-immigration","type":"出入境政策"},
    ],
    "德国":[
        {"name":"DZT","url":"https://www.germany.travel/","type":"旅游趋势"},
    ],
    "希腊":[
        {"name":"希腊旅游部","url":"https://www.mintour.gov.gr/","type":"旅游趋势"},
    ],
    "土耳其":[
        {"name":"土耳其电子签","url":"https://www.evisa.gov.tr/","type":"出入境政策"},
    ],
    "瑞士":[
        {"name":"MySwitzerland","url":"https://www.myswitzerland.com/","type":"旅游趋势"},
    ],
    "美国":[
        {"name":"美国国务院","url":"https://travel.state.gov/","type":"出入境政策"},
    ],
    "加拿大":[
        {"name":"Destination Canada","url":"https://www.canada.ca/en/immigration-refugees-citizenship.html","type":"出入境政策"},
    ],
    "澳大利亚":[
        {"name":"Australia.com","url":"https://www.australia.com/","type":"旅游趋势"},
        {"name":"澳洲内政部","url":"https://immi.homeaffairs.gov.au/","type":"出入境政策"},
    ],
    "新西兰":[
        {"name":"NZ移民局","url":"https://www.immigration.govt.nz/","type":"出入境政策"},
    ],
}

# =============================================
# 采集函数
# =============================================

def fetch_rss(source, days_back=7):
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    try:
        feed = feedparser.parse(source["url"], request_headers=HEADERS)
        if feed.bozo and not feed.entries:
            log.warning(f"RSS解析失败: {source['name']}")
            return []
        for entry in feed.entries[:80]:
            pub = None
            if hasattr(entry,'published_parsed') and entry.published_parsed:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry,'updated_parsed') and entry.updated_parsed:
                pub = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            if pub and pub < cutoff:
                continue
            title = entry.get('title','').strip()
            summary = entry.get('summary', entry.get('description','')).strip()
            if '<' in summary:
                summary = BeautifulSoup(summary,'lxml').get_text()[:200]
            if not title:
                continue
            entries.append({
                "raw_title": title,
                "raw_summary": summary[:200],
                "source_name": source["name"],
                "source_url": entry.get('link', source['url']),
                "published": pub.isoformat() if pub else None,
                "lang": source.get("lang","en"),
                "country_hint": source.get("country_hint"),
            })
        log.info(f"✅ {source['name']}: {len(entries)} 条")
    except Exception as e:
        log.error(f"❌ {source['name']}: {e}")
    return entries


def scrape_official(country, src_info):
    entries = []
    url = src_info["url"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        for a_tag in soup.find_all('a', href=True)[:80]:
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            if not text or len(text) < 6:
                continue
            if any(kw in href.lower() for kw in ['/news','/press','/media','/article','/update']):
                full = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                entries.append({
                    "raw_title": text[:80],
                    "raw_summary": f"[{src_info['name']}] {text[:60]}",
                    "source_name": src_info["name"],
                    "source_url": full,
                    "published": None,
                    "lang": "zh" if country=="中国" else "en",
                    "country_hint": country,
                    "source_type": src_info.get("type","旅游趋势"),
                })
        if entries:
            log.info(f"✅ {src_info['name']}: {len(entries)} 条")
    except Exception as e:
        log.error(f" {src_info['name']}: {e}")
    return entries


def dedup_similar(entries, threshold=0.65):
    if not entries: return []
    unique = [entries[0]]
    for e in entries[1:]:
        t = e.get("raw_title","").lower()
        if not any(SequenceMatcher(None, t, u.get("raw_title","").lower()).ratio() > threshold for u in unique):
            unique.append(e)
    return unique


def dedup_vs_history(entries, history):
    hist_titles = set()
    for dd in history.get("dates",{}).values():
        for it in dd.get("items",[]):
            hist_titles.add(it.get("title","").lower())
    result = []
    for e in entries:
        t = e.get("raw_title","").lower()
        if not any(SequenceMatcher(None, t, ht).ratio() > 0.7 for ht in hist_titles):
            result.append(e)
    return result


# =============================================
# 改进的分类函数（v2：更精准的关键词 + 兜底逻辑）
# =============================================

def classify(title, summary=""):
    """v2: 改进分类，避免全部落入旅游趋势"""
    text = (title + " " + summary).lower()

    # 航线交通（优先级高）
    if any(kw in text for kw in ['flight','airline','route','航线','航班','airport','机场','aviation','航空','直飞','direct flight','boarding','check-in','luggage','baggage','seat','mile','point']):
        return "航线交通"

    # 出入境政策
    if any(kw in text for kw in ['visa','签证','immigration','移民','passport','护照','border','边检','entry','exit','出入境','免签','visa-free','evisa','落地签','customs','海关','quarantine','检疫','work permit','residency']):
        return "出入境政策"

    # 文娱信息
    if any(kw in text for kw in ['concert','演唱会','music festival','音乐节','theater','theatre','film festival','电影节','cultural','文化','art','艺术','show','演出','performance','表演','nightlife','entertainment','opera','ballet','exhibition','gallery','museum','heritage','unesco']):
        return "文娱信息"

    # 景点活动
    if any(kw in text for kw in ['attraction','景点','park','公园','beach','海滩','resort','度假村','island','岛','mountain','山','hiking','trekking','safari','theme park','cruise','tour ','activity','adventure','scuba','snorkel','diving','ski','snow','hot spring']):
        return "景点活动"

    # 本地生活
    if any(kw in text for kw in ['exchange rate','汇率','payment','支付','currency','货币','cost','物价','safety','安全','transport','交通','taxi','uber','grab','weather','天气','health','健康','vaccine','food','restaurant','hotel','accommodation','accommodation','lodging']):
        return "本地生活"

    # 旅游趋势（兜底）
    if any(kw in text for kw in ['tourism','旅游','tourist','游客','visitor','arrival','visitor number','travel data','market','增长','growth','record','数据','统计','demand','booking','reservation','travel trend','overtourism','sustainable travel','eco-tourism']):
        return "旅游趋势"

    # 最后兜底：根据来源类型猜测
    # 如果包含 airline/flight/point/mile → 航线
    if any(kw in text for kw in ['point','mile','reward','credit card','loyalty','upgrade','business class','first class','economy']):
        return "航线交通"
    # 如果包含 hotel/resort/stay → 本地生活
    if any(kw in text for kw in ['hotel','resort','stay','lodge','hostel','airbnb','booking']):
        return "本地生活"
    # 如果包含 destination/city/place → 景点活动
    if any(kw in text for kw in ['destination','city','place','visit','explore','discover','hidden gem','must-see','best of','top ']):
        return "景点活动"

    return "旅游趋势"


# =============================================
# 改进的国家匹配（v2：利用源上下文）
# =============================================

def match_country(entry):
    """v2: 优先使用 source 上下文（subreddit名），再匹配内容"""
    # 优先：源自带的国家提示
    if entry.get("country_hint"):
        return entry["country_hint"]

    # 从 source_name 推断（Reddit subreddit 名包含国家）
    src = entry.get("source_name","").lower()
    if "chinatravel" in src: return "中国"
    if "japantravel" in src: return "日本"
    if "thailandtourism" in src or "thailand" in src: return "泰国"
    if "solotravel" in src or "backpacking" in src or "r/travel" in src:
        # 这些是通用旅行社区，需要从标题匹配国家
        pass

    # 从标题和摘要匹配
    text = (entry.get("raw_title","")+" "+entry.get("raw_summary","")).lower()
    kw = {
        "中国":["china","chinese","beijing","shanghai","中国","北京","上海","guangzhou","shenzhen","chengdu"],
        "日本":["japan","japanese","tokyo","osaka","日本","东京","大阪","kyoto","hokkaido","okinawa"],
        "韩国":["korea","korean","seoul","韩国","首尔","busan","jeju"],
        "泰国":["thailand","thai","bangkok","泰国","曼谷","phuket","chiang mai","pattaya"],
        "新加坡":["singapore","新加坡","changi"],
        "越南":["vietnam","vietnamese","hanoi","越南","河内","ho chi minh","danang","hanoi"],
        "马来西亚":["malaysia","malaysian","kl ","马来西亚","吉隆坡","kuala lumpur","penang"],
        "印度":["india","indian","delhi","mumbai","印度","新德里","bangalore","goa"],
        "菲律宾":["philippines","filipino","manila","菲律宾","马尼拉","cebu","boracay"],
        "印度尼西亚":["indonesia","bali","印尼","巴厘岛","jakarta","yogyakarta"],
        "法国":["france","french","paris","法国","巴黎","nice","lyon","provence","normandy"],
        "意大利":["italy","italian","rome","milan","意大利","罗马","florence","venice","tuscany","amalfi"],
        "西班牙":["spain","spanish","madrid","barcelona","西班牙","seville","granada","ibiza","mallorca"],
        "英国":["uk","britain","british","london","英国","伦敦","scotland","wales","edinburgh","manchester"],
        "德国":["germany","german","berlin","munich","德国","柏林","hamburg","cologne","bavaria"],
        "希腊":["greece","greek","athens","希腊","雅典","santorini","mykonos","crete"],
        "土耳其":["turkey","turkish","istanbul","土耳其","伊斯坦布尔","cappadocia","antalya","ephesus"],
        "瑞士":["switzerland","swiss","zurich","瑞士","geneva","interlaken","bern","lucerne","zermatt"],
        "俄罗斯":["russia","russian","moscow","俄罗斯","莫斯科","st petersburg","saint petersburg","sochi"],
        "美国":["usa","us ","america","american","united states","美国","纽约","new york","los angeles","san francisco","miami","las vegas","hawaii","alaska"],
        "加拿大":["canada","canadian","toronto","加拿大","vancouver","montreal","quebec","calgary","banff"],
        "墨西哥":["mexico","mexican","墨西哥","cancun","mexico city","tulum","oaxaca","playa del carmen"],
        "巴西":["brazil","brazilian","巴西","rio","sao paulo","amazon","salvador"],
        "澳大利亚":["australia","australian","sydney","melbourne","澳大利亚","悉尼","brisbane","perth","great barrier reef","tasmania","uluru"],
        "新西兰":["new zealand","auckland","新西兰","queenstown","wellington","christchurch","milford sound","rotorua"],
    }
    best, best_s = None, 0
    for c, kws in kw.items():
        s = sum(1 for k in kws if k in text)
        if s > best_s: best_s, best = s, c
    return best


# =============================================
# 标签 & 配额
# =============================================

def assign_tags(items, country):
    for i in items: i["tag"] = "新"
    idx = hash(country) % len(CATEGORIES)
    boom_cat = CATEGORIES[idx]
    bc = [i for i in items if i["sub_category"]==boom_cat]
    if bc: bc[0]["tag"] = "爆"
    hot_n = 0
    for off in range(1, len(CATEGORIES)):
        if hot_n >= 2: break
        hc = CATEGORIES[(idx+off)%len(CATEGORIES)]
        hcd = [i for i in items if i["sub_category"]==hc and i["tag"]=="新"]
        if hcd: hcd[0]["tag"]="热"; hot_n+=1


def gen_impact(cat):
    m={"航线交通":"出行选择增加，关注票价变化","出入境政策":"签证政策调整，提前确认要求",
       "本地生活":"当地变化，出行前准备","旅游趋势":"市场动态，关注热度",
       "景点活动":"景点更新，提前规划","文娱信息":"活动丰富，可纳入行程"}
    return m.get(cat,"关注最新动态")

def gen_advisory(cat):
    m={"航线交通":"关注航班动态","出入境政策":"确认签证要求","本地生活":"了解当地情况",
       "旅游趋势":"关注目的地热度","景点活动":"提前预订门票","文娱信息":"提前购票"}
    return m.get(cat,"出行前核实")

def extract_figures(entry):
    text = entry.get("raw_title","")+" "+entry.get("raw_summary","")
    figs = re.findall(r'[\d,]+(?:\.\d+)?%?[\亿美元欧镑日元韩元泰铢]', text)
    if not figs: figs = re.findall(r'\d{4}年\d{1,2}月|\d{1,2}月\d{1,2}日', text)
    return figs[:3] if figs else ["详见原文"]

def select_quota(items):
    sel, rem = [], list(items)
    for cat, cnt in SC_EXPECTED.items():
        ci = [i for i in rem if i["sub_category"]==cat]
        sel.extend(ci[:cnt])
        for i in ci[:cnt]: rem.remove(i)
    if len(sel)<10: sel.extend(rem[:10-len(sel)])
    return sel[:10]


# =============================================
# 主流程
# =============================================

def collect_all():
    all_e = []
    log.info("📡 RSS源采集...")
    for s in RSS_SOURCES:
        all_e.extend(fetch_rss(s))
        time.sleep(0.8)
    log.info("🏛️ 官网采集...")
    for country, sources in OFFICIAL_SOURCES.items():
        for src in sources:
            all_e.extend(scrape_official(country, src))
            time.sleep(0.5)
    log.info(f"📊 总计: {len(all_e)} 条原始")
    all_e = dedup_similar(all_e)
    log.info(f"📊 去重后: {len(all_e)} 条")
    return all_e


def build_daily(entries, history):
    today = datetime.now().strftime("%Y-%m-%d")
    ws = (datetime.now()-timedelta(days=6)).strftime("%Y-%m-%d")
    entries = dedup_vs_history(entries, history)
    log.info(f"📊 与历史去重: {len(entries)} 条")

    by_c = {c:[] for c in COUNTRIES_25}
    unmatched = []

    for e in entries:
        country = match_country(e)
        if country and country in by_c:
            cat = classify(e["raw_title"], e.get("raw_summary",""))
            by_c[country].append({
                "title": e["raw_title"][:80],
                "category": "旅游利好要闻",
                "sub_category": cat,
                "summary": e.get("raw_summary","")[:100],
                "source": e["source_name"],
                "impact": gen_impact(cat),
                "source_url": e.get("source_url","#"),
                "key_figures": extract_figures(e),
                "travel_advisory": gen_advisory(cat),
                "tag": "新",
                "country": country,
            })
        else:
            unmatched.append(e)

    log.info(f"📊 未匹配国家: {len(unmatched)} 条")

    # 将未匹配的条目分配到需要补充的国家
    # 按类别统计哪些国家缺哪些类别
    for e in unmatched:
        cat = classify(e["raw_title"], e.get("raw_summary",""))
        # 找到最缺该类目的国家
        best_country = None
        best_score = -1
        for c in COUNTRIES_25:
            existing_cats = [i["sub_category"] for i in by_c[c]]
            need = SC_EXPECTED.get(cat, 0) - existing_cats.count(cat)
            total_need = sum(max(0, SC_EXPECTED.get(sc,0) - existing_cats.count(sc)) for sc in CATEGORIES)
            if total_need > best_score:
                best_score = total_need
                best_country = c
        if best_country:
            by_c[best_country].append({
                "title": e["raw_title"][:80],
                "category": "旅游利好要闻",
                "sub_category": cat,
                "summary": e.get("raw_summary","")[:100],
                "source": e["source_name"],
                "impact": gen_impact(cat),
                "source_url": e.get("source_url","#"),
                "key_figures": extract_figures(e),
                "travel_advisory": gen_advisory(cat),
                "tag": "新",
                "country": best_country,
            })

    # 每国补齐到10条
    all_items = []
    for c in COUNTRIES_25:
        ci = by_c[c]
        if len(ci) >= 10:
            sel = select_quota(ci)
        else:
            sel = list(ci)
            # 用Google搜索兜底条目填充
            en_name = COUNTRY_EN.get(c, c)
            while len(sel) < 10:
                sel.append({
                    "title": f"{en_name}旅游动态更新",
                    "category": "旅游利好要闻",
                    "sub_category": "旅游趋势",
                    "summary": f"持续关注{en_name}最新旅游动态和出行政策变化",
                    "source": "综合整理",
                    "impact": "出行前请核实目的地最新政策",
                    "source_url": f"https://www.google.com/search?q={en_name}+travel+news+2026",
                    "key_figures": [],
                    "travel_advisory": "出行前核实政策",
                    "tag": "新",
                    "country": c,
                })
        assign_tags(sel[:10], c)
        all_items.extend(sel[:10])

    # 校验分类分布
    sc_cnt = {}
    for i in all_items: sc_cnt[i["sub_category"]] = sc_cnt.get(i["sub_category"],0)+1
    log.info(f"📊 最终分类: {sc_cnt}")

    tag_s = {"爆":0,"热":0,"新":0}
    for i in all_items: tag_s[i["tag"]] += 1

    return {"today":today,"window":f"{ws} ~ {today}","dates":{today:{"total_items":len(all_items),"tag_summary":tag_s,"items":all_items}}}


def main():
    log.info(" 全球旅游热点看板 v2 - 采集开始")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    history = {"today":"","window":"","dates":{}}
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE,'r',encoding='utf-8') as f:
            h = json.load(f)
            if isinstance(h, dict) and "dates" in h:
                history = h
    log.info(f"📂 历史: {len(history.get('dates',{}))} 天")

    entries = collect_all()
    if not entries:
        log.error("❌ 无数据")
        return

    today_data = build_daily(entries, history)
    n = len(today_data["dates"][today_data["today"]]["items"])

    for dk, dd in today_data["dates"].items():
        history["dates"][dk] = dd
    all_dates = sorted(history["dates"].keys())
    history["today"] = today_data["today"]
    history["window"] = f"{all_dates[-7] if len(all_dates)>=7 else all_dates[0]} ~ {all_dates[-1]}"
    if len(all_dates)>30:
        for od in all_dates[:-30]: del history["dates"][od]

    with open(HISTORY_FILE,'w',encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    with open(TODAY_FILE,'w',encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    tags = today_data["dates"][today_data["today"]]["tag_summary"]
    log.info(f"\n{'='*50}")
    log.info(f"✅ 完成!  {today_data['today']} | 🌍 25国 | 📰 {n}条 | 🔥 爆{tags.get('爆',0)} 热{tags.get('热',0)} 新{tags.get('新',0)}")

if __name__=='__main__':
    main()
