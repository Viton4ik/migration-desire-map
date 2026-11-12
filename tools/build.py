"""fact_check.html + ZIP. Rerun after data.py and scenes.py: python3 tools/build.py"""
import csv, os, html, zipfile, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = list(csv.DictReader(open(os.path.join(ROOT, 'countries.csv')))); F = list(csv.DictReader(open(os.path.join(ROOT, 'facts.csv'))))
V = list(csv.DictReader(open(os.path.join(ROOT, 'voice_numbers.csv'))))
COL = {'MAGNET': '#1f9d55', 'PULL': '#7cc46a', 'STAY': '#9aa3ad', 'LEAVE': '#f08a24', 'EXIT': '#d7263d', 'LOCKED': '#222'}
Q = {'G': 'Gallup World Poll', 'S': 'other survey (media / barometer) - not Gallup', 'E': 'ESTIMATE from UN actual net migration', 'F': 'documented exit restriction'}
e = html.escape
cnt = collections.Counter(c['status'] for c in C); q = collections.Counter(c['quality'] for c in C)
fx = collections.defaultdict(list)
for f in F: fx[f['code']].append(f)
rows = []
for c in C:
    facts = '<br>'.join(f"<b>{e(f['fact_type'])}</b>: {e(f['value'])} <span class=m>[{e(f['period'])}, {e(f['source_ids'])}, {e(f['verification'])}]</span>" for f in fx[c['code']])
    rows.append(f"<tr><td>{c['order']}</td><td>{e(c['name'])}<div class=m>{c['code']} · {c['region_id']}</div></td><td><span class=b style='background:{COL[c['status']]}'>{e(c['status_label'])}</span></td><td class=q{c['quality']}>{e(Q[c['quality']])}</td><td>{e(c['basis'])}</td><td>{facts}</td></tr>")
src = open(os.path.join(ROOT, 'sources.txt')).read()
bad = [v for v in V if v['status'] != 'ok']
page = f"""<title>LEAVE vs MOVE TO Fact Check</title><meta name="claude:viewport-fit-sides" content="cover">
<style>
/* layout: single reading column, one wide scrollable registry table */
:root{{--bg:#fbfaf7;--fg:#1d2329;--muted:#66707a;--line:#e2e4e6;--soft:#f1f2f0;--accent:#1f6f8b;--body:"Source Sans 3",system-ui,sans-serif;--display:"Bricolage Grotesque",system-ui,sans-serif}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#14181c;--fg:#e6e8ea;--muted:#9aa3ac;--line:#2b3238;--soft:#1d2328;--accent:#6fb7d2;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#14181c;--fg:#e6e8ea;--muted:#9aa3ac;--line:#2b3238;--soft:#1d2328;--accent:#6fb7d2;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 var(--body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px}}
h1,h2{{font-family:var(--display);text-wrap:balance;line-height:1.15}}h1{{font-size:30px;margin:0 0 8px}}p,ul{{max-width:72ch}}a{{color:var(--accent)}}
.wrap{{overflow-x:auto}}table{{border-collapse:collapse;min-width:900px;width:100%;font-variant-numeric:tabular-nums}}td,th{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top;text-align:left}}th{{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}}
.b{{color:#fff;border-radius:10px;padding:2px 8px;font-weight:700;font-size:12px;white-space:nowrap}}.m{{color:var(--muted);font-size:12px}}.qE{{background:repeating-linear-gradient(45deg,transparent,transparent 6px,var(--soft) 6px,var(--soft) 12px)}}.qS{{outline:1px dashed var(--muted);outline-offset:-3px}}
pre{{white-space:pre-wrap;background:var(--soft);padding:12px;overflow-x:auto}}</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@700&family=Source+Sans+3:wght@400;700&display=swap">
<h1>Countries People Want to LEAVE vs MOVE TO - fact check</h1>
<p>Cut-off 2026-11-04. {len(C)} countries, {len(F)} facts. Statuses: {', '.join(f'{k} {v}' for k, v in cnt.items())}. Data quality: {', '.join(f'{Q[k]} {v}' for k, v in q.items())}.</p>
<p><b>Read this first.</b> Three survey metrics are mixed on purpose and never on one scale: % who want to leave (Gallup, barometers, national polls), Gallup PNMI (want in minus want out, % of adults), dream-destination share. Countries without any survey get a status from UN actual net migration and are shown hatched as an ESTIMATE. Other-survey countries are shown with a dotted outline. Verification: F = page opened and read, S = media table only, R = reference knowledge. Voice numbers not matched to a fact: {len(bad)}.</p>
<div class=wrap><table><tr><th>#</th><th>Country</th><th>Status</th><th>Data type</th><th>Basis</th><th>Facts</th></tr>{''.join(rows)}</table></div>
<h2>Sources</h2><pre>{e(src)}</pre>
<h2>Known limits</h2><ul><li>Survey years differ (2015-2017 to 2025); each chip shows its own period.</li><li>Question wording differs between Gallup, Arab Barometer ("considered emigrating"), Balkan Barometer ("considering living abroad"), MetroPOLL ("live or study abroad"), DIF/Razumkov ("if borders fully opened"), Gallup International ("if given paperwork").</li>
<li>Cuba 57%: Cubadata base is 1,090 answers, about 35% of the full 1,776 sample; shown as an independent poll.</li><li>Serbia and Montenegro: Balkan Barometer gives only a 40-50% range; the lower bound sets the status.</li>
<li>UN estimates for Turkmenistan, Cuba and other closed statistical systems may understate movement.</li><li>Henley passport counts come from a media table (S), recheck against henleyglobal.com before publishing.</li></ul>"""
open(os.path.join(ROOT, 'fact_check.html'), 'w').write(page)
files = ['project_brief.txt', 'project_status.txt', 'countries.csv', 'facts.csv', 'scenes.csv', 'voice_en.txt', 'voice_ru.txt', 'voice_numbers.csv', 'sources.txt',
         'fact_check.html', 'territories_and_exclusions.csv', 'stage1_data_sources.txt', 'env_check.txt', 'data_raw/un_wpp2024_net_migration.csv', 'tools/data.py', 'tools/scenes.py', 'tools/build.py']
with zipfile.ZipFile(os.path.join(ROOT, 'migration-desire-map_stage2.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(os.path.join(ROOT, f), 'migration-desire-map/' + f)
print('ok', len(rows), 'rows')
