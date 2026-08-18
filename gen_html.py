#!/usr/bin/env python3
"""Generate HTML dashboard from JSON data"""
import json

with open("travel_daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

today = data["today"]
window = data["window"]
data_json = json.dumps(data, ensure_ascii=False)

html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全球旅游热点看板 · {{DATE}}</title>
<style>
:root{--p:#2563eb;--pl:#dbeafe;--bg:#f1f5f9;--c:#fff;--t:#0f172a;--t2:#475569;--t3:#94a3b8;--b:#e2e8f0;--r:10px;--s:0 1px 3px rgba(0,0,0,.06);--sm:0 4px 12px rgba(0,0,0,.08)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--t);line-height:1.6;padding:20px}
.w{max-width:1000px;margin:0 auto}
.hd{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:16px}
.hd h1{font-size:20px;font-weight:700}.sub{font-size:12px;color:var(--t2);margin-top:2px}
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:#d1fae5;color:#065f46}
.badge .dot{width:6px;height:6px;border-radius:50%;background:#10b981}
.cal-wrap{background:var(--c);border-radius:var(--r);padding:14px 16px;margin-bottom:16px;box-shadow:var(--s);border:1px solid var(--b)}
.cal-title{font-size:13px;font-weight:600;color:var(--t2);margin-bottom:10px}
.cal-strip{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px}
.cal-day{min-width:52px;padding:8px 6px;border-radius:8px;text-align:center;cursor:pointer;border:1.5px solid var(--b);transition:.15s;user-select:none;flex-shrink:0}
.cal-day:hover{border-color:var(--p);background:var(--pl)}
.cal-day.active{background:var(--p);color:#fff;border-color:var(--p)}
.cal-day.today{border-color:#10b981;border-width:2px}
.cal-day .dow{font-size:10px;color:var(--t3);margin-bottom:2px}
.cal-day.active .dow{color:rgba(255,255,255,.8)}
.cal-day .dn{font-size:16px;font-weight:700}
.cal-day .dc{font-size:9px;color:var(--t3);margin-top:1px}
.cal-day.active .dc{color:rgba(255,255,255,.8)}
.sg{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}
.st{background:var(--c);border-radius:var(--r);padding:14px;text-align:center;box-shadow:var(--s);border:1px solid var(--b)}
.st .v{font-size:24px;font-weight:700;color:var(--p)}.st .l{font-size:11px;color:var(--t2);margin-top:2px}
.st.boom .v{color:#ef4444}.st.hot .v{color:#f97316}.st.new .v{color:#10b981}
.si{width:100%;padding:8px 12px;border:1px solid var(--b);border-radius:8px;font-size:13px;outline:none;margin-bottom:10px}
.si:focus{border-color:var(--p);box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.ch{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.cp{padding:5px 12px;border-radius:20px;border:1px solid var(--b);background:#fff;cursor:pointer;font-size:12px;transition:.15s;user-select:none}
.cp:hover{border-color:var(--p)}.cp.on{background:var(--pl);border-color:var(--p);color:var(--p);font-weight:600}
.legend{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;padding:8px 12px;background:#f8fafc;border-radius:8px;border:1px solid var(--b)}
.legend-item{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--t2)}
.legend-dot{width:8px;height:8px;border-radius:50%}
.cl{display:flex;flex-direction:column;gap:8px}
.cc{background:var(--c);border-radius:var(--r);border:1px solid var(--b);box-shadow:var(--s);overflow:hidden;transition:.2s}
.cc:hover{box-shadow:var(--sm)}
.chd{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;cursor:pointer;user-select:none}
.chd:hover{background:#f8fafc}.chd .left{display:flex;align-items:center;gap:10px}
.cf{font-size:22px;line-height:1}.cn{font-size:14px;font-weight:600}
.ct{font-size:11px;color:var(--t2);background:var(--bg);padding:2px 8px;border-radius:10px}
.ar{font-size:12px;color:var(--t3);transition:transform .2s}.cc.open .ar{transform:rotate(180deg)}
.cb{max-height:0;overflow:hidden;transition:max-height .3s ease}.cc.open .cb{max-height:10000px}
.ev{padding:12px 16px;border-top:1px solid #f1f5f9;display:flex;gap:12px;cursor:pointer;transition:.15s;position:relative}
.ev:first-child{border-top:none}.ev:hover{background:#f8fafc}
.er{width:28px;height:28px;min-width:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0;margin-top:2px}
.r1{background:linear-gradient(135deg,#f59e0b,#f97316)}.r2{background:linear-gradient(135deg,#94a3b8,#64748b)}.r3{background:linear-gradient(135deg,#d97706,#b45309)}.rn{background:var(--p)}
.eb{flex:1;min-width:0}.et{font-size:14px;font-weight:600;line-height:1.4;margin-bottom:4px}
.tg{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:6px}
.tc{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:500}
.tc-sc{background:#fef3c7;color:#92400e}
.es{font-size:12px;color:var(--t2);line-height:1.7;margin-bottom:6px}
.ei{font-size:11px;color:var(--p);background:var(--pl);padding:5px 10px;border-radius:6px;margin-bottom:6px;display:inline-block}
.esr{font-size:10px;color:var(--t3)}
.ev-tag{position:absolute;top:0;left:0;padding:2px 8px;font-size:10px;font-weight:700;color:#fff;border-radius:0 0 8px 0;z-index:1;line-height:1.4}
.ev-tag.boom{background:linear-gradient(135deg,#ef4444,#dc2626)}
.ev-tag.hot{background:linear-gradient(135deg,#f97316,#ea580c)}
.ev-tag.new{background:linear-gradient(135deg,#10b981,#059669)}
.mo{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,.5);z-index:1000;justify-content:center;align-items:flex-start;padding:40px 16px;overflow-y:auto;backdrop-filter:blur(4px)}.mo.show{display:flex}
.mc{background:var(--c);border-radius:14px;max-width:640px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.15);overflow:hidden;animation:su .2s ease}
@keyframes su{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.mt{padding:20px 24px 16px;border-bottom:1px solid var(--b);position:relative}
.mx{position:absolute;top:14px;right:16px;width:30px;height:30px;border-radius:50%;border:none;background:var(--bg);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;color:var(--t2)}.mx:hover{background:var(--b)}
.mrr{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.mr{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff}
.mct{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:14px;font-size:12px;font-weight:500;background:var(--pl);color:#1e40af}
.mtl{font-size:18px;font-weight:700;line-height:1.4}
.mb{padding:20px 24px}.ms{margin-bottom:18px}.ms:last-child{margin-bottom:0}
.msl{font-size:12px;font-weight:600;color:var(--t3);margin-bottom:8px}
.msc{font-size:14px;color:var(--t);line-height:1.8}
.kf{padding:8px 12px;background:var(--pl);border-radius:8px;font-size:13px;color:#1e40af;font-weight:500;margin-bottom:6px}
.mib{padding:12px 14px;background:#f0fdf4;border-radius:8px;border-left:3px solid #10b981;font-size:13px;line-height:1.7;color:#166534}
.ma{padding:10px 14px;border-radius:8px;font-size:13px;display:flex;align-items:center;gap:8px}
.ma.info{background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe}
.mf{padding:14px 24px;border-top:1px solid var(--b);display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:11px;color:var(--t3);flex-wrap:wrap}
.ft{text-align:center;padding:14px;font-size:11px;color:var(--t3);border-top:1px solid var(--b);margin-top:8px}
@media(max-width:600px){.sg{grid-template-columns:repeat(2,1fr)}.cal-day{min-width:44px}}
</style>
</head>
<body>
<div class="w">
<div class="hd"><div><h1>🌍 全球出入境旅游热点看板</h1><div class="sub">📅 数据窗口：{{WINDOW}} ｜ 自动采集 ｜ 25国×10条</div></div><div class="badge"><span class="dot"></span>实时看板</div></div>
<div class="cal-wrap"><div class="cal-title">📅 历史记录日历（点击切换日期）</div><div class="cal-strip" id="calstrip"></div></div>
<div class="sg"><div class="st"><div class="v" id="sc">-</div><div class="l">覆盖国家/地区</div></div><div class="st"><div class="v" id="sn">-</div><div class="l">当日要闻</div></div><div class="st boom"><div class="v" id="sb">-</div><div class="l">🔥 爆款</div></div><div class="st hot"><div class="v" id="sh">-</div><div class="l">📈 热门</div></div><div class="st new"><div class="v" id="sx">-</div><div class="l">✨ 最新</div></div></div>
<div class="legend"><div class="legend-item"><div class="legend-dot" style="background:#6366f1"></div>航线交通</div><div class="legend-item"><div class="legend-dot" style="background:#ec4899"></div>出入境政策</div><div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>本地生活</div><div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>旅游趋势</div><div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>景点活动</div><div class="legend-item"><div class="legend-dot" style="background:#8b5cf6"></div>文娱信息</div></div>
<input class="si" id="si" placeholder="🔍 搜索标题、摘要、国家…" oninput="render()">
<div class="ch" id="chips"></div>
<div class="cl" id="clist"></div>
<div class="ft">数据来源：WebSearch 自动采集 ｜ 更新时间：{{DATE}} ｜ 仅供参考，出行前请核实最新政策</div>
</div>
<div class="mo" id="mo" onclick="if(event.target===this)closeModal()"><div class="mc"><div class="mt"><button class="mx" onclick="closeModal()">✕</button><div class="mrr"><div class="mr" id="mr"></div><div><div class="mct" id="mct"></div></div></div><div class="mtl" id="mtl"></div></div><div class="mb"><div class="ms"><div class="msl">📝 摘要</div><div class="msc" id="msum"></div></div><div class="ms"><div class="msl">📊 关键数据</div><div id="mkf"></div></div><div class="ms"><div class="msl">💡 影响分析</div><div class="mib" id="mimp"></div></div><div class="ms"><div class="msl">📌 出行提示</div><div class="ma info" id="madv"></div></div></div><div class="mf"><span id="msrc"></span><a id="msl" href="#" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;background:var(--bg);border-radius:8px;font-size:12px;color:#2932e1;text-decoration:none;border:1px solid var(--b)">🔗 百度搜索详情</a></div></div></div>
<script>
var ALL_DATA={{DATA_JSON}};var dates=Object.keys(ALL_DATA.dates).sort().reverse();var curDate=ALL_DATA.today||dates[0];
var SC_MAP={'航线交通':{icon:'✈️',color:'#6366f1',bg:'#eef2ff'},'出入境政策':{icon:'📋',color:'#ec4899',bg:'#fdf2f8'},'本地生活':{icon:'🏙️',color:'#f59e0b',bg:'#fffbeb'},'旅游趋势':{icon:'📊',color:'#10b981',bg:'#ecfdf5'},'景点活动':{icon:'🏛️',color:'#3b82f6',bg:'#eff6ff'},'文娱信息':{icon:'🎭',color:'#8b5cf6',bg:'#f5f3ff'}};
function getItems(d){return(ALL_DATA.dates[d]&&ALL_DATA.dates[d].items)||[]}
function renderCal(){var h='',dow=['日','一','二','三','四','五','六'];dates.forEach(function(d){var dt=new Date(d+'T00:00:00'),n=getItems(d).length||ALL_DATA.dates[d].total_items||0,cls='cal-day'+(d===curDate?' active':'')+(d===dates[0]?' today':'');h+='<div class="'+cls+'" onclick="switchDate(\''+d+'\')"><div class="dow">周'+dow[dt.getDay()]+'</div><div class="dn">'+dt.getDate()+'日</div><div class="dc">'+n+'条</div></div>'});document.getElementById('calstrip').innerHTML=h}
function switchDate(d){curDate=d;renderCal();renderStats();renderChips();render()}
function renderStats(){var items=getItems(curDate),countries={};items.forEach(function(i){countries[i.country]=1});var tags={爆:0,热:0,新:0};items.forEach(function(i){tags[i.tag]=(tags[i.tag]||0)+1});document.getElementById('sc').textContent=Object.keys(countries).length||25;document.getElementById('sn').textContent=items.length||ALL_DATA.dates[curDate].total_items||250;document.getElementById('sb').textContent=tags['爆']||(ALL_DATA.dates[curDate].tag_summary||{}).爆||0;document.getElementById('sh').textContent=tags['热']||(ALL_DATA.dates[curDate].tag_summary||{}).热||0;document.getElementById('sx').textContent=tags['新']||(ALL_DATA.dates[curDate].tag_summary||{}).新||0}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function renderChips(){var items=getItems(curDate),cats=['全部'];items.forEach(function(i){var sc=i.sub_category||'旅游趋势';if(cats.indexOf(sc)<0)cats.push(sc)});var el=document.getElementById('chips');el.innerHTML='';cats.forEach(function(c){var b=document.createElement('span');b.className='cp'+(c==='全部'?' on':'');b.textContent=c;b.onclick=function(){document.querySelectorAll('.cp').forEach(function(x){x.classList.remove('on')});b.classList.add('on');render()};el.appendChild(b)});['爆','热','新'].forEach(function(t){var b=document.createElement('span');b.className='cp';b.textContent=t;b.style.borderColor=t==='爆'?'#ef4444':t==='热'?'#f97316':'#10b981';b.onclick=function(){document.querySelectorAll('.cp').forEach(function(x){x.classList.remove('on')});b.classList.add('on');renderFiltered(getItems(curDate).filter(function(i){return i.tag===t}))};el.appendChild(b)})}
function render(){var activeChip=document.querySelector('.cp.on'),curCat=activeChip?activeChip.textContent:'全部';renderFiltered(curCat==='全部'?getItems(curDate):getItems(curDate).filter(function(i){return(i.sub_category||'旅游趋势')===curCat}))}
function renderFiltered(items){var q=(document.getElementById('si').value||'').toLowerCase();if(q)items=items.filter(function(i){return(i.title+' '+i.summary+' '+i.country+' '+i.source).toLowerCase().indexOf(q)>=0});var byC={};items.forEach(function(i){if(!byC[i.country])byC[i.country]=[];byC[i.country].push(i)});var h='',fM={'中国':'🇨🇳','日本':'🇯🇵','韩国':'🇰🇷','泰国':'🇹🇭','新加坡':'🇸🇬','越南':'🇻🇳','马来西亚':'🇲🇾','印度':'🇮🇳','菲律宾':'🇵🇭','法国':'🇫🇷','意大利':'🇮🇹','西班牙':'🇪🇸','英国':'🇬🇧','德国':'🇩🇪','希腊':'🇬🇷','土耳其':'🇹🇷','瑞士':'🇨🇭','俄罗斯':'🇷🇺','美国':'🇺🇸','加拿大':'🇨🇦','墨西哥':'🇲🇽','巴西':'🇧🇷','澳大利亚':'🇦🇺','新西兰':'🇳🇿','阿联酋':'🇦🇪','印度尼西亚':'🇮🇩','埃及':'🇪🇬'};Object.keys(byC).sort().forEach(function(c){var ev=byC[c],fl=fM[c]||'🌍';h+='<div class="cc"><div class="chd" onclick="this.parentElement.classList.toggle(\'open\')"><div class="left"><span class="cf">'+fl+'</span><span class="cn">'+esc(c)+'</span><span class="ct">'+ev.length+'条</span></div><span class="ar">▼</span></div><div class="cb">';ev.forEach(function(e){var rc=e.tag==='爆'?'r1':e.tag==='热'?'r2':'rn',sc=e.sub_category||'旅游趋势',sm=SC_MAP[sc]||{icon:'',color:'#64748b',bg:'#f1f5f9'};var tc=e.tag==='爆'?'boom':e.tag==='热'?'hot':'new';h+='<div class="ev" onclick="openModal('+items.indexOf(e)+',\''+curDate+'\')"><div class="ev-tag '+tc+'">'+esc(e.tag)+'</div><div class="er '+rc+'">'+sm.icon+'</div><div class="eb"><div class="et">'+esc(e.title)+'</div><div class="tg"><span class="tc tc-sc" style="background:'+sm.bg+';color:'+sm.color+'">'+sm.icon+' '+esc(sc)+'</span></div><div class="es">'+esc(e.summary)+'</div><div class="ei">💡 '+esc(e.impact)+'</div><div class="esr">📎 '+esc(e.source)+' ｜ 📌 '+esc(e.travel_advisory)+'</div></div></div>'});h+='</div></div>'});if(!items.length)h='<div style="text-align:center;padding:40px;color:var(--t3)">暂无匹配结果</div>';document.getElementById('clist').innerHTML=h}
function openModal(idx,date){var items=getItems(date),e=items[idx];if(!e)return;var rc=e.tag==='爆'?'r1':e.tag==='热'?'r2':'rn',sc=e.sub_category||'旅游趋势',sm=SC_MAP[sc]||{icon:'📰',color:'#64748b',bg:'#f1f5f9'};document.getElementById('mr').className='mr '+rc;document.getElementById('mr').textContent=e.tag;document.getElementById('mct').innerHTML='<span style="background:'+sm.bg+';color:'+sm.color+';padding:2px 8px;border-radius:10px;font-size:11px">'+sm.icon+' '+esc(sc)+'</span>';document.getElementById('mtl').textContent=e.title;document.getElementById('msum').textContent=e.summary;var kfArr=Array.isArray(e.key_figures)?e.key_figures:[e.key_figures||'暂无数据'];document.getElementById('mkf').innerHTML=kfArr.map(function(f){return'<div class="kf">'+esc(f)+'</div>'}).join('');document.getElementById('mimp').textContent=e.impact;document.getElementById('madv').innerHTML='📌 '+esc(e.travel_advisory);document.getElementById('msrc').textContent='📎 '+e.source;document.getElementById('msl').href=e.source_url||'#';document.getElementById('mo').classList.add('show')}
function closeModal(){document.getElementById('mo').classList.remove('show')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeModal()});
renderCal();renderStats();renderChips();render();
</script>
</body>
</html>'''

html = html.replace('{{DATE}}', today).replace('{{WINDOW}}', window).replace('{{DATA_JSON}}', data_json)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Dashboard generated: index.html")
print(f"   Size: {len(html)} bytes ({len(html)/1024:.1f} KB)")
