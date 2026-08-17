#!/usr/bin/env python3
"""
每日全球旅游热点智能采集脚本 v2
================================
基于综合评分的角标分配系统

评分维度（满分 100 分）：
- 出行影响程度：0-40 分
- 时效性：0-25 分
- 公众热度：0-20 分
- 来源权威性：0-15 分

角标分配规则：
- 爆 (1 条/国): 总分≥75, 影响≥30, 时效≥15, 权威≥8, 热度≥10
- 热 (2 条/国): 总分≥55, 影响≥15, 时效≥10, 权威≥5
- 新 (7 条/国): 总分≥30, 时效≥3, 权威≥4
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 常量
TODAY = datetime.utcnow() + timedelta(hours=8)
DATE_STR = TODAY.strftime('%Y-%m-%d')
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f'daily-{DATE_STR}.json')

# 25 个国家
COUNTRIES = [
    ('CN', '中国'), ('JP', '日本'), ('KR', '韩国'), ('TH', '泰国'),
    ('SG', '新加坡'), ('MY', '马来西亚'), ('VN', '越南'), ('IN', '印度'),
    ('FR', '法国'), ('IT', '意大利'), ('ES', '西班牙'), ('GB', '英国'),
    ('DE', '德国'), ('GR', '希腊'), ('TR', '土耳其'), ('CH', '瑞士'),
    ('RU', '俄罗斯'), ('US', '美国'), ('CA', '加拿大'), ('MX', '墨西哥'),
    ('BR', '巴西'), ('AR', '阿根廷'), ('AU', '澳大利亚'), ('NZ', '新西兰'),
    ('AE', '阿联酋')
]


def is_negative_event(item: Dict) -> bool:
    """
    判断是否为负面事件（安全事故、灾害、景区限流等）
    负面事件不参与评分，直接排除
    """
    negative_keywords = [
        '事故', '灾害', '地震', '洪水', '火灾', '爆炸',
        '限流', '关闭', '暂停', '取消', '禁止', '警告',
        '危险', '安全提醒', '注意', '避免', '不建议'
    ]
    title = item.get('title', '').lower()
    summary = item.get('summary', '').lower()
    text = title + ' ' + summary
    
    # 官方政策收紧类保留（如签证材料调整、新增限制等）
    policy_keywords = ['签证', '材料', '调整', '新增', '政策', '规则']
    if any(k in text for k in policy_keywords):
        return False
    
    return any(k in text for k in negative_keywords)


def calculate_impact_score(item: Dict) -> int:
    """
    出行影响程度：0-40 分
    
    35-40: 国家级或跨国政策、主要国际航线、全国性大型旅游安排
    25-34: 主要城市、热门目的地、核心航司或区域性政策
    15-24: 单城市、单航线、重要节庆、景点/展会
    5-14: 当地生活、一般活动、小范围文娱
    0: 与出行决策关系弱
    """
    title = item.get('title', '').lower()
    summary = item.get('summary', '').lower()
    text = title + ' ' + summary
    
    # 国家级/跨国政策
    if any(k in text for k in ['签证政策', '免签', '签证便利', '出入境', '国际航线', '全国性']):
        if any(k in text for k in ['重大', '全面', '全国', '所有', '全部']):
            return 38
        return 35
    
    # 主要城市/区域政策
    if any(k in text for k in ['城市', '区域', '航司', '航空公司', '热门']):
        if any(k in text for k in ['重要', '主要', '核心']):
            return 30
        return 25
    
    # 单城市/单航线/重要节庆
    if any(k in text for k in ['城市', '航线', '航班', '节庆', '节日', '展会', '景点']):
        if any(k in text for k in ['重要', '热门', '著名']):
            return 22
        return 18
    
    # 当地生活/一般活动
    if any(k in text for k in ['生活', '活动', '文娱', '服务', '更新']):
        return 10
    
    # 与出行关系弱
    return 5


def calculate_freshness_score(item: Dict, now: datetime) -> int:
    """
    时效性：0-25 分
    
    25: 发布不超过 24 小时，或未来 3 天内生效
    20: 发布不超过 72 小时，或未来 7 天内生效
    15: 发布不超过 7 天，或未来 14 天内生效
    8: 发布不超过 14 天
    3: 发布不超过 30 天，且仍有效
    0: 超过 30 天、已失效，或时间无法核验
    """
    # 尝试从 item 中获取发布时间
    publish_date = item.get('publish_date')
    effective_date = item.get('effective_date')
    
    if not publish_date and not effective_date:
        # 无法核验时间
        return 0
    
    # 计算发布时间差
    if publish_date:
        if isinstance(publish_date, str):
            try:
                publish_dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
            except:
                publish_dt = None
        else:
            publish_dt = publish_date
        
        if publish_dt:
            days_diff = (now - publish_dt).days
            if days_diff <= 1:
                return 25
            elif days_diff <= 3:
                return 20
            elif days_diff <= 7:
                return 15
            elif days_diff <= 14:
                return 8
            elif days_diff <= 30:
                return 3
            else:
                return 0
    
    # 计算生效时间差
    if effective_date:
        if isinstance(effective_date, str):
            try:
                effective_dt = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
            except:
                effective_dt = None
        else:
            effective_dt = effective_date
        
        if effective_dt:
            days_until = (effective_dt - now).days
            if days_until <= 3:
                return 25
            elif days_until <= 7:
                return 20
            elif days_until <= 14:
                return 15
            elif days_until <= 30:
                return 3
            else:
                return 0
    
    return 0


def calculate_heat_score(item: Dict) -> int:
    """
    公众热度：0-20 分
    
    20: 搜索热度增长≥200%，或 5 家及以上独立权威媒体 24 小时内跟进
    15: 搜索热度增长≥100%，或 3-4 家独立权威渠道跟进
    10: 搜索热度增长≥30%，或 2 家独立权威渠道跟进
    5: 有 1 家权威渠道发布，但缺少持续热度证据
    0: 无可核验热度证据
    """
    # 尝试从 item 中获取热度指标
    media_count = item.get('media_count', 0)
    search_growth = item.get('search_growth', 0)
    
    # 基于权威媒体数量
    if media_count >= 5:
        return 20
    elif media_count >= 3:
        return 15
    elif media_count >= 2:
        return 10
    elif media_count >= 1:
        return 5
    else:
        # 基于搜索热度
        if search_growth >= 200:
            return 20
        elif search_growth >= 100:
            return 15
        elif search_growth >= 30:
            return 10
        elif search_growth > 0:
            return 5
        else:
            return 0


def calculate_authority_score(item: Dict) -> int:
    """
    来源权威性：0-15 分
    
    15: 政府部门、使领馆、边检/海关、机场/航司、铁路公司、景区官方、活动主办方
    12: 国家级主流媒体或国际通讯社
    8: 行业协会、权威旅游机构、区域主流媒体
    4: 经核验的本地媒体、商业旅游平台
    0: 无来源、转载链不清晰
    """
    source = item.get('source', '').lower()
    
    # 政府/官方机构
    if any(k in source for k in ['政府', '局', '使领馆', '海关', '边检', '机场', '航司', '航空', '铁路', '景区']):
        return 15
    
    # 国家级主流媒体
    if any(k in source for k in ['新华社', '央视', '人民', '国家', '官方', '通讯社', 'reuters', 'ap ', 'bbc']):
        return 12
    
    # 行业协会/权威机构
    if any(k in source for k in ['协会', '旅游局', '旅游发展', '官方旅游', 'agency', 'authority']):
        return 8
    
    # 本地媒体/商业平台
    if any(k in source for k in ['旅游', 'travel', 'trip', 'booking', '携程', '去哪儿', '马蜂窝']):
        return 4
    
    return 0


def calculate_score(item: Dict, now: datetime) -> Dict[str, int]:
    """
    计算综合评分
    返回评分分解和总分
    """
    impact = calculate_impact_score(item)
    freshness = calculate_freshness_score(item, now)
    heat = calculate_heat_score(item)
    authority = calculate_authority_score(item)
    
    total = impact + freshness + heat + authority
    
    return {
        'impact': impact,
        'freshness': freshness,
        'heat': heat,
        'authority': authority,
        'total': total
    }


def assign_tags_by_score(items: List[Dict], now: datetime) -> List[Dict]:
    """
    基于评分分配角标
    
    规则：
    - 爆 (1 条/国): 总分≥75, 影响≥30, 时效≥15, 权威≥8, 热度≥10
    - 热 (2 条/国): 总分≥55, 影响≥15, 时效≥10, 权威≥5
    - 新 (7 条/国): 总分≥30, 时效≥3, 权威≥4
    """
    # 先计算所有项目的评分
    for item in items:
        score_breakdown = calculate_score(item, now)
        item['score'] = score_breakdown['total']
        item['score_breakdown'] = {
            'impact': score_breakdown['impact'],
            'freshness': score_breakdown['freshness'],
            'heat': score_breakdown['heat'],
            'authority': score_breakdown['authority']
        }
    
    # 按总分排序
    items.sort(key=lambda x: x['score'], reverse=True)
    
    # 分配角标
    bo_count = 0
    re_count = 0
    xin_count = 0
    
    for item in items:
        total = item['score']
        impact = item['score_breakdown']['impact']
        freshness = item['score_breakdown']['freshness']
        heat = item['score_breakdown']['heat']
        authority = item['score_breakdown']['authority']
        
        # 爆：1 条/国
        if bo_count < 1 and total >= 75 and impact >= 30 and freshness >= 15 and authority >= 8 and heat >= 10:
            item['tag'] = '爆'
            item['tag_reason'] = f"总分{total}≥75, 影响{impact}≥30, 时效{freshness}≥15, 权威{authority}≥8, 热度{heat}≥10"
            bo_count += 1
        # 热：2 条/国
        elif re_count < 2 and total >= 55 and impact >= 15 and freshness >= 10 and authority >= 5:
            item['tag'] = '热'
            item['tag_reason'] = f"总分{total}≥55, 影响{impact}≥15, 时效{freshness}≥10, 权威{authority}≥5"
            re_count += 1
        # 新：7 条/国
        elif xin_count < 7 and total >= 30 and freshness >= 3 and authority >= 4:
            item['tag'] = '新'
            item['tag_reason'] = f"总分{total}≥30, 时效{freshness}≥3, 权威{authority}≥4, 新近有效资讯"
            xin_count += 1
        else:
            # 不符合任何角标条件
            item['tag'] = '未达标'
            item['tag_reason'] = f"总分{total}, 不满足爆/热/新门槛"
    
    return items


def validate_tag_thresholds(items: List[Dict]) -> bool:
    """
    验证角标配额是否满足
    
    必须满足：
    - 爆：1 条
    - 热：2 条
    - 新：7 条
    
    如果任一不满足，返回 False
    """
    bo_count = sum(1 for item in items if item.get('tag') == '爆')
    re_count = sum(1 for item in items if item.get('tag') == '热')
    xin_count = sum(1 for item in items if item.get('tag') == '新')
    
    if bo_count < 1:
        print(f"  ❌ 校验失败：'爆'条目不足（{bo_count}/1）")
        return False
    if re_count < 2:
        print(f"  ❌ 校验失败：'热'条目不足（{re_count}/2）")
        return False
    if xin_count < 7:
        print(f"  ❌ 校验失败：'新'条目不足（{xin_count}/7）")
        return False
    
    return True


def collect_country_data(code: str, name: str) -> List[Dict]:
    """
    采集单个国家的旅游热点数据
    返回至少 12-15 条候选数据
    """
    # 这里应该调用实际的新闻 API 或 Web 搜索
    # 返回候选数据列表
    # 示例数据（实际应替换为真实采集）
    return [
        {
            'title': f'{name}旅游政策调整',
            'summary': f'{name}发布新的旅游签证政策，简化申请流程。',
            'source': f'{name}政府旅游局',
            'publish_date': (TODAY - timedelta(hours=12)).isoformat(),
            'media_count': 5,
            'category': '签证政策'
        },
        {
            'title': f'{name}新增国际航线',
            'summary': f'{name}新增多条国际航线，提升旅游便利性。',
            'source': f'{name}航空公司',
            'publish_date': (TODAY - timedelta(hours=24)).isoformat(),
            'media_count': 3,
            'category': '航空交通'
        },
        # ... 更多候选数据
    ]


def process_country(code: str, name: str) -> Optional[Dict]:
    """
    处理单个国家的数据采集、评分和角标分配
    
    返回处理后的国家数据，如果校验失败返回 None
    """
    print(f"📍 处理 {name} ({code})...")
    
    # 1. 采集候选数据（至少 12-15 条）
    raw_items = collect_country_data(code, name)
    print(f"   采集 {len(raw_items)} 条候选数据")
    
    # 2. 排除负面事件
    eligible_items = [item for item in raw_items if not is_negative_event(item)]
    print(f"   排除负面后剩余 {len(eligible_items)} 条")
    
    if len(eligible_items) < 10:
        print(f"  ❌ 候选数据不足（{len(eligible_items)}/10），跳过")
        return None
    
    # 3. 评分并分配角标
    scored_items = assign_tags_by_score(eligible_items, TODAY)
    
    # 4. 验证角标配额
    if not validate_tag_thresholds(scored_items):
        print(f"  ❌ 角标配额校验失败，跳过")
        return None
    
    # 5. 选取前 10 条（爆 1 + 热 2 + 新 7）
    final_items = []
    for tag in ['爆', '热', '新']:
        tag_items = [item for item in scored_items if item.get('tag') == tag]
        if tag == '爆':
            final_items.extend(tag_items[:1])
        elif tag == '热':
            final_items.extend(tag_items[:2])
        elif tag == '新':
            final_items.extend(tag_items[:7])
    
    # 6. 格式化输出
    events = []
    for idx, item in enumerate(final_items, 1):
        events.append({
            'rank': idx,
            'title': item['title'],
            'category': item.get('category', '行业数据'),
            'summary': item['summary'],
            'source': item['source'],
            'impact': item.get('impact_analysis', ''),
            'source_url': item.get('source_url', ''),
            'key_figures': item.get('key_figures', []),
            'travel_advisory': item.get('travel_advisory', ''),
            'tag': item['tag'],
            'score': item['score'],
            'score_breakdown': item['score_breakdown'],
            'tag_reason': item['tag_reason']
        })
    
    return {
        'code': code,
        'name': name,
        'events': events
    }


def main():
    """
    主函数：采集所有国家数据并生成 JSON
    """
    print(f" 开始采集 {DATE_STR} 全球旅游热点")
    print(f"   目标：25 个国家，每国 10 条事件")
    print()
    
    countries_data = []
    
    for code, name in COUNTRIES:
        country_data = process_country(code, name)
        if country_data:
            countries_data.append(country_data)
        else:
            print(f"  ⚠️ {name} 校验失败，跳过")
    
    # 生成最终 JSON
    output = {
        'date': DATE_STR,
        'countries': countries_data
    }
    
    # 保存文件
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ 采集完成！")
    print(f"   文件：{OUTPUT_FILE}")
    print(f"   国家数：{len(countries_data)}")
    print(f"   事件数：{sum(len(c['events']) for c in countries_data)}")
    
    # 角标统计
    bo_count = sum(1 for c in countries_data for e in c['events'] if e.get('tag') == '爆')
    re_count = sum(1 for c in countries_data for e in c['events'] if e.get('tag') == '热')
    xin_count = sum(1 for c in countries_data for e in c['events'] if e.get('tag') == '新')
    
    print(f"   角标分布：爆{bo_count} 热{re_count} 新{xin_count}")


if __name__ == '__main__':
    main()
