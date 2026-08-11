#!/usr/bin/env python3
"""
每日全球旅游热点看板生成脚本 v2
- 读取 daily/ 目录下所有历史 JSON 数据
- 将所有数据嵌入 HTML（永不丢失历史数据）
- 自动更新 manifest.json
- 输出自包含 index.html
"""
import json, os, sys, glob

def load_all_data(daily_dir):
    """加载 daily/ 目录下所有历史数据"""
    all_data = {}
    manifest_dates = []
    
    for f in sorted(glob.glob(os.path.join(daily_dir, '2*.json'))):
        ds = os.path.basename(f).replace('.json', '')
        try:
            with open(f, 'r', encoding='utf-8-sig') as fh:
                d = json.load(fh)
            total = sum(len(c['events']) for c in d['countries'])
            all_data[ds] = d
            manifest_dates.append({
                'date': ds,
                'countries': len(d['countries']),
                'events': total
            })
        except Exception as e:
            print(f"  ⚠️ 跳过 {ds}: {e}")
    
    return all_data, {'available_dates': manifest_dates}

def save_manifest(daily_dir, manifest):
    """保存 manifest.json"""
    path = os.path.join(daily_dir, 'manifest.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"📋 manifest.json: {len(manifest['available_dates'])} 天数据")

def generate(daily_dir, template_path, output_path):
    """生成自包含 HTML（嵌入所有历史数据）"""
    
    # 1. 加载所有历史数据
    print("📂 加载历史数据...")
    all_data, manifest = load_all_data(daily_dir)
    
    if not all_data:
        print("❌ 没有找到任何历史数据！")
        sys.exit(1)
    
    # 最新一天作为默认显示
    latest_date = max(all_data.keys())
    latest_data = all_data[latest_date]
    total_events = sum(len(c['events']) for c in latest_data['countries'])
    
    print(f"  ✅ {len(all_data)} 天数据")
    for d in manifest['available_dates']:
        print(f"     {d['date']}: {d['countries']}国 {d['events']}条")
    
    # 2. 保存 manifest
    save_manifest(daily_dir, manifest)
    
    # 3. 读取模板
    with open(template_path, 'r', encoding='utf-8') as f:
        tpl = f.read()
    
    # 4. 嵌入所有数据（替代 __DATA__ 占位符）
    data_block = f'''var ALL_DATA = {json.dumps(all_data, ensure_ascii=False)};
var MANIFEST = {json.dumps(manifest, ensure_ascii=False)};
var CURRENT_DATE = "{latest_date}";
var DATA = ALL_DATA[CURRENT_DATE];
var EMBEDDED_DATA = DATA;'''
    
    tpl = tpl.replace('var DATA = __DATA__;', data_block, 1)
    
    # 5. 替换日期占位符
    tpl = tpl.replace('__DATE__', latest_date)
    
    # 6. 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tpl)
    
    sz = os.path.getsize(output_path) // 1024
    print(f"\n✅ 看板已生成: {output_path} ({sz} KB)")
    print(f"   📅 {latest_date} | 🌍 {len(latest_data['countries'])}国 | 📰 {total_events}条")
    print(f"   📦 内嵌 {len(all_data)} 天历史数据（永不丢失）")

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='生成旅游热点看板（嵌入所有历史数据）')
    p.add_argument('-d', '--data', help='今日数据文件（可选，自动从 daily/ 加载所有）')
    p.add_argument('-o', '--output', help='输出文件路径')
    a = p.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    daily_dir = os.path.join(script_dir, 'daily')
    template_path = os.path.join(script_dir, 'template.html')
    output_path = a.output or os.path.join(script_dir, 'index.html')
    
    # 确保 daily 目录存在
    os.makedirs(daily_dir, exist_ok=True)
    
    # 如果指定了数据文件，先复制到 daily/
    if a.data and os.path.exists(a.data):
        import shutil
        basename = os.path.basename(a.data)
        if not basename.startswith('2'):
            # 需要读取日期
            with open(a.data, 'r', encoding='utf-8-sig') as f:
                d = json.load(f)
            basename = d.get('date', 'unknown') + '.json'
        dest = os.path.join(daily_dir, basename)
        shutil.copy2(a.data, dest)
        print(f"📁 数据已保存: {dest}")
    
    generate(daily_dir, template_path, output_path)
