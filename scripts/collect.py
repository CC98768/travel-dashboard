#!/usr/bin/env python3
"""
全球旅游热点看板 - 多源数据采集器 v3.0
Google News RSS 中文信源 + 原文抓取 + 数字提取 + 真实分析
"""

import json, os, re, time, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from difflib import SequenceMatcher

try:
    import feedparser
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"缺少依赖: {e}")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"
TODAY_FILE = DATA_DIR / "today.json"

COUNTRIES_25 = [
    ("中国","China 旅游 出入境"),
    ("日本","日本 観光 旅行"),
    ("韩国","韩国 旅游 Korea tourism"),
    ("泰国","泰国 旅游 Thailand tourism"),
    ("新加坡","新加坡 旅游 Singapore tourism"),
    ("越南","越南 旅游 Vietnam tourism"),
    ("马来西亚","马来西亚 旅游 Malaysia tourism"),
    ("印度","印度 旅游 India tourism"),
    ("菲律宾","菲律宾 旅游 Philippines tourism"),
    ("印度尼西亚","印尼 巴厘岛 旅游 Indonesia Bali"),
    ("法国","法国 旅游 France tourism"),
    ("意大利","意大利 旅游 Italy tourism"),
    ("西班牙","西班牙 旅游 Spain tourism"),
    ("英国","英国 旅游 UK Britain tourism"),
    ("德国","德国 旅游 Germany tourism"),
    ("希腊","希腊 旅游 Greece tourism"),
    ("土耳其","土耳其 旅游 Turkey tourism"),
    ("瑞士","瑞士 旅游 Switzerland tourism"),
    ("俄罗斯","俄罗斯 旅游 Russia tourism"),
    ("美国","美国 旅游 USA travel"),
    ("加拿大","加拿大 旅游 Canada tourism"),
    ("墨西哥","墨西哥 旅游 Mexico tourism"),
    ("巴西","巴西 旅游 Brazil tourism"),
    ("澳大利亚","澳大利亚 旅游 Australia travel"),
    ("新西兰","新西兰 旅游 New Zealand travel"),
]

CATEGORIES = ["航线交通","出入境政策","本地生活","旅游趋势","景点活动","文娱信息"]
SC_EXPECTED = {"航线交通":2,"出入境政策":2,"本地生活":1,"旅游趋势":2,"景点活动":2,"文娱信息":1}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TravelDashboard/3.0)"}

# =============================================
# 分类判断
# =============================================

def classify(title, summary=""):
    text = (title + " " + summary).lower()
    kw_map = {
        "航线交通": ['flight','airline','route','航线','航班','airport','机场','aviation','航空','直飞','open','新航线','airfare','ticket','boarding'],
        "出入境政策": ['visa','免签','签证','入境','border','passport','immigration','海关','通关','e-visa','落地签','permit','custom'],
        "本地生活": ['hotel','酒店','restaurant','餐饮','支付','payment','transport','交通','夜市','market','shopping','购物','住宿'],
        "景点活动": ['attraction','景区','museum','博物馆','temple','寺庙','park','公园','hiking','徒步','tour','游览','开放',' reopening'],
        "文娱信息": ['festival','节','concert','演唱会','event','活动','exhibition','展览','show','演出','celebration','文化','art','艺术'],
    }
    scores = {}
    for cat, kws in kw_map.items():
        scores[cat] = sum(1 for kw in kws if kw in text)
    scores["旅游趋势"] = max(0, 3 - max(scores.values()))  # default fallback
    return max(scores, key=scores.get)


# =============================================
# 从原文提取数字
# =============================================

def extract_figures_from_text(text):
    figures = []
    # Percentages
    pcts = re.findall(r'[\d.]+%', text)
    figures.extend(pcts[:2])
    # Money
    money = re.findall(r'[\d,]+(?:\.\d+)?[亿美元欧镑日元韩元泰铢澳元加元]', text)
    figures.extend(money[:2])
    # Passenger numbers
    pax = re.findall(r'[\d.]+[万千百]?[人次]', text)
    figures.extend(pax[:2])
    # Growth numbers
    growth = re.findall(r'(?:增长|增加|上升|提升|下降|减少|缩减)[\d.]+[%百分之]*', text[:300])
    figures.extend(growth[:2])
    # Dates
    dates = re.findall(r'\d{4}年\d{1,2}月(?:\d{1,2}日)?', text)
    figures.extend(dates[:2])
    # Generic large numbers with units
    nums = re.findall(r'[\d,]+(?:万|亿|百万)', text)
    figures.extend(nums[:2])
    
    # Deduplicate and limit
    seen = set()
    unique = []
    for f in figures:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique[:5] if unique else ['详见原文']


# =============================================
# 从原文生成影响分析
# =============================================

def gen_impact_from_content(title, summary, full_text, cat):
    # Try to extract the core message
    text = (title + " " + summary + " " + full_text).lower()
    
    # Pattern-based impact analysis
    if cat == "航线交通":
        if any(kw in text for kw in ['new','新增','开通','恢复','resume','launch']):
            return '新航线/新运力投入运营，旅客出行选择增加，关注初期促销票价'
        if any(kw in text for kw in ['取消','停飞','cancel','suspend','delay']):
            return '航线调整影响旅客出行计划，建议尽早改签或选择替代方案'
        if any(kw in text for kw in ['sale','促销','discount','优惠','低价']):
            return '票价优惠降低出行成本，适合灵活日期的旅客抓住窗口期'
        return '航空运力变化影响出行成本和便利性，建议比价后预订'
    
    elif cat == "出入境政策":
        if any(kw in text for kw in ['visa-free','免签','exempt','waive']):
            return '免签政策降低出行门槛，预计带动相关目的地客流显著增长'
        if any(kw in text for kw in ['restrict','限制','ban','禁令','收紧']):
            return '政策收紧增加出行复杂度，需提前确认最新要求并留足办理时间'
        if any(kw in text for kw in ['extend','延长','扩大','expand']):
            return '政策放宽利好跨境出行，商务和旅游往来更加便利'
        return '出入境政策调整，出行前务必确认最新要求'
    
    elif cat == "本地生活":
        if any(kw in text for kw in ['new','新','open','开业','推出','launch']):
            return '新设施/新服务提升当地旅游体验，值得纳入行程规划'
        if any(kw in text for kw in ['price','涨价','上涨','increase','rise']):
            return '当地消费成本上升，建议提前做好预算规划'
        return '当地生活服务变化，出行前了解最新情况'
    
    elif cat == "旅游趋势":
        numbers = re.findall(r'[\d.]+%', text)
        if numbers:
            return f'数据显示旅游市场变化明显（{numbers[0]}），旅客可根据趋势调整出行计划'
        return '旅游市场动态值得关注，影响目的地选择和出行时机'
    
    elif cat == "景点活动":
        if any(kw in text for kw in ['reopen','重新开放','升级','upgrade','renovat']):
            return '景区升级后体验提升，但需确认预约要求和最新开放信息'
        if any(kw in text for kw in ['limit','限流','预约','reservation','capacity']):
            return '限流措施保障游览品质，务必提前预约避免扑空'
        return '景点/活动信息更新，建议提前确认开放时间和门票政策'
    
    elif cat == "文娱信息":
        if any(kw in text for kw in ['ticket','票','booking','预订']):
            return '热门活动票务紧张，建议尽早购票并确认退改政策'
        return '文化娱乐活动丰富目的地体验，可纳入行程但需提前规划'
    
    return '关注最新动态，出行前核实相关信息'


# =============================================
# 从原文生成出行提示
# =============================================

def gen_advisory_from_content(title, summary, full_text, cat):
    text = (title + " " + summary + " " + full_text).lower()
    
    advisories = []
    
    # Check for time-sensitive info
    dates = re.findall(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{1,2}月)', text)
    if dates:
        advisories.append(f'注意关键时间节点：{dates[0]}')
    
    # Category-specific
    if cat == "航线交通":
        if 'sale' in text or '促销' in text:
            advisories.append('促销票限时限量，确认行程后尽快下单')
        advisories.append('关注航司官网获取最新航班动态')
    elif cat == "出入境政策":
        advisories.append('政策可能随时调整，出发前48小时再次确认')
        advisories.append('确保护照有效期不少于6个月')
    elif cat == "景点活动":
        if '预约' in text or 'reservation' in text:
            advisories.append('需提前在线预约，现场可能不售票')
        advisories.append('关注景区官方渠道获取最新开放信息')
    elif cat == "文娱信息":
        advisories.append('热门场次建议提前2-4周购票')
    else:
        advisories.append('出行前关注目的地官方旅游信息')
    
    return '；'.join(advisories[:3]) if advisories else '出行前核实最新信息'


# =============================================
# 抓取 Google News RSS
# =============================================

def fetch_google_news(country, query, max_per_source=50):
    entries = []
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    try:
        feed = feedparser.parse(url, request_headers=HEADERS)
        if feed.bozo and not feed.entries:
            log.warning(f"RSS解析失败: {country}")
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        
        for entry in feed.entries[:max_per_source]:
            pub = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if pub and pub < cutoff:
                continue
            
            title = entry.get('title', '').strip()
            summary_html = entry.get('summary', entry.get('description', '')).strip()
            if '<' in summary_html:
                try:
                    summary = BeautifulSoup(summary_html, 'lxml').get_text()[:200]
                except:
                    summary = summary_html[:200]
            else:
                summary = summary_html[:200]
            
            if not title:
                continue
            
            entries.append({
                "raw_title": title,
                "raw_summary": summary,
                "source_name": entry.get('source', {}).get('title', 'Google News'),
                "source_url": entry.get('link', ''),
                "published": pub.isoformat() if pub else None,
                "country_hint": country,
            })
        
        if entries:
            log.info(f"  {country}: {len(entries)} 条")
    except Exception as e:
        log.error(f"  {country}: {e}")
    return entries


# =============================================
# 抓取原文提取详情
# =============================================

def fetch_article_details(url, timeout=10):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)[:2000]
        return text
    except:
        return ""


# =============================================
# 去重
# =============================================

def dedup_similar(entries, threshold=0.65):
    if not entries:
        return []
    unique = [entries[0]]
    for e in entries[1:]:
        t = e.get("raw_title", "").lower()
        if not any(SequenceMatcher(None, t, u.get("raw_title", "").lower()).ratio() > threshold for u in unique):
            unique.append(e)
    return unique


def dedup_vs_history(entries, history):
    hist_titles = set()
    for dd in history.get("dates", {}).values():
        for it in dd.get("items", []):
            hist_titles.add(it.get("title", "").lower())
    result = []
    for e in entries:
        t = e.get("raw_title", "").lower()
        if not any(SequenceMatcher(None, t, ht).ratio() > 0.7 for ht in hist_titles):
            result.append(e)
    return result


# =============================================
# 标签分配
# =============================================

def assign_tags(items, country):
    for i in items:
        i["tag"] = "新"
    idx = hash(country) % len(CATEGORIES)
    boom_cat = CATEGORIES[idx]
    bc = [i for i in items if i["sub_category"] == boom_cat]
    if bc:
        bc[0]["tag"] = "爆"
    hot_n = 0
    for off in range(1, len(CATEGORIES)):
        if hot_n >= 2:
            break
        hc = CATEGORIES[(idx + off) % len(CATEGORIES)]
        hcd = [i for i in items if i["sub_category"] == hc and i["tag"] == "新"]
        if hcd:
            hcd[0]["tag"] = "热"
            hot_n += 1


def select_quota(items):
    sel, rem = [], list(items)
    for cat, cnt in SC_EXPECTED.items():
        ci = [i for i in rem if i["sub_category"] == cat]
        sel.extend(ci[:cnt])
        for i in ci[:cnt]:
            if i in rem:
                rem.remove(i)
    if len(sel) < 10:
        sel.extend(rem[:10 - len(sel)])
    return sel[:10]


# =============================================
# 主流程
# =============================================

def collect_all():
    all_entries = []
    for country, query in COUNTRIES_25:
        entries = fetch_google_news(country, query)
        all_entries.extend(entries)
        time.sleep(0.5)
    log.info(f"  RSS总计: {len(all_entries)} 条原始")
    all_entries = dedup_similar(all_entries)
    log.info(f"  去重后: {len(all_entries)} 条")
    return all_entries


def build_daily(entries, history):
    today = datetime.now().strftime("%Y-%m-%d")
    ws = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    
    entries = dedup_vs_history(entries, history)
    log.info(f"  与历史去重: {len(entries)} 条")

    by_c = {c[0]: [] for c in COUNTRIES_25}

    for e in entries:
        country = e.get("country_hint", "")
        if country and country in by_c:
            cat = classify(e["raw_title"], e.get("raw_summary", ""))
            
            # 尝试抓取原文获取详细信息
            full_text = ""
            if e.get("source_url") and e["source_url"] != "#":
                full_text = fetch_article_details(e["source_url"])
                time.sleep(0.3)
            
            # 从原文提取具体数字
            search_text = e["raw_summary"] + " " + full_text
            key_figures = extract_figures_from_text(search_text)
            
            # 基于实际内容生成影响分析
            impact = gen_impact_from_content(e["raw_title"], e["raw_summary"], full_text, cat)
            
            # 基于实际内容生成出行提示
            advisory = gen_advisory_from_content(e["raw_title"], e["raw_summary"], full_text, cat)
            
            by_c[country].append({
                "title": e["raw_title"][:80],
                "category": "旅游利好要闻",
                "sub_category": cat,
                "summary": e.get("raw_summary", "")[:150],
                "source": e["source_name"],
                "impact": impact,
                "source_url": e.get("source_url", "#"),
                "key_figures": key_figures,
                "travel_advisory": advisory,
                "tag": "新",
                "country": country,
            })

    # 每国选10条（不够10条的保留实际数量，不填充垃圾）
    all_items = []
    for c in COUNTRIES_25:
        country_name = c[0]
        ci = by_c.get(country_name, [])
        if len(ci) >= 10:
            sel = select_quota(ci)
        else:
            sel = ci  # 保留实际数量
        assign_tags(sel, country_name)
        all_items.extend(sel)

    sc_cnt = {}
    for i in all_items:
        sc_cnt[i["sub_category"]] = sc_cnt.get(i["sub_category"], 0) + 1
    log.info(f"  最终分类: {sc_cnt}")

    tag_s = {"爆": 0, "热": 0, "新": 0}
    for i in all_items:
        tag_s[i["tag"]] += 1

    return {"today": today, "window": f"{ws} ~ {today}", "dates": {today: {"total_items": len(all_items), "tag_summary": tag_s, "items": all_items}}}


def main():
    log.info(" 全球旅游热点看板 v3 - 采集开始")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    history = {"today": "", "window": "", "dates": {}}
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            h = json.load(f)
            if isinstance(h, dict) and "dates" in h:
                history = h
    log.info(f"  历史: {len(history.get('dates', {}))} 天")

    entries = collect_all()
    if not entries:
        log.error(" 无数据，保留历史数据不更新")
        return
    if len(entries) < 10:
        log.warning(f" 仅采集到{len(entries)}条，数据不足，保留历史数据不更新")
        return

    today_data = build_daily(entries, history)
    n = len(today_data["dates"][today_data["today"]]["items"])

    for dk, dd in today_data["dates"].items():
        history["dates"][dk] = dd
    all_dates = sorted(history["dates"].keys())
    history["today"] = today_data["today"]
    history["window"] = f"{all_dates[-7] if len(all_dates) >= 7 else all_dates[0]} ~ {all_dates[-1]}"
    if len(all_dates) > 30:
        for od in all_dates[:-30]:
            del history["dates"][od]

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    with open(TODAY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    tags = today_data["dates"][today_data["today"]]["tag_summary"]
    log.info(f"\n{'=' * 50}")
    log.info(f" 完成!  {today_data['today']} |  25国 |  {n}条 |  爆{tags.get('爆', 0)} 热{tags.get('热', 0)} 新{tags.get('新', 0)}")

if __name__ == '__main__':
    main()
