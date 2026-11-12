"""Builds countries.csv, facts.csv, sources.txt, territories_and_exclusions.csv for
'Countries People Want to LEAVE vs MOVE TO'. Rerun: python3 tools/data.py"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CUTOFF = '2026-11-04'

SOURCES = {
 'S01': ('Gallup, "Desire to Migrate Remains at Record High" (2024-10-30), World Poll 2023, % adults who would like to move permanently to another country', 'https://news.gallup.com/poll/652748/desire-migrate-remains-record-high.aspx'),
 'S02': ('Gallup, "Desire to Move Permanently to U.S. at New Low" (2026-04-23), World Poll 2025: world 15%, preferred destinations', 'https://news.gallup.com/poll/708614/desire-migrate-drops-new-low.aspx'),
 'S03': ('Gallup, "How Migration Could Reshape Populations and Labor Forces" (2026-04-23), Potential Net Migration Index 2023-2025', 'https://news.gallup.com/poll/708680/migration-reshape-populations-labor-forces.aspx'),
 'S04': ('Arab Barometer Wave VIII press release (2024-08-15), % who considered emigrating, 2023-24', 'https://www.arabbarometer.org/media-news/press-release-migration-trends-in-the-middle-east-and-north-africa-revealed-in-latest-arab-barometer-survey/'),
 'S05': ('Arab Barometer Wave VII Migration Report, 2021-22', 'https://www.arabbarometer.org/wp-content/uploads/ABVII_Migration_Report-EN.pdf'),
 'S06': ('UN DESA, World Population Prospects 2024, crude net migration rate per 1,000 (estimates 2019-2023), official R package wpp2024 1.1-3', 'https://github.com/PPgp/wpp2024'),
 'S07': ('Levada Center, emigration sentiments, April 2025 (17-23 Apr 2025, n=1,617)', 'https://www.levada.ru/en/2025/05/28/sentiments-about-emigration-and-attitudes-towards-those-who-left-april-2025/'),
 'S08': ('Democratic Initiatives Foundation + Razumkov Centre, 29 Nov-14 Dec 2024 (n=1,518), via Nikvesti', 'https://nikvesti.com/en/news/public/300333-poll-21-percent-ukrainians-like-emigrate-borders-opened'),
 'S09': ('MetroPOLL "Turkey\'s Pulse", Oct 2023 (n=1,691), via Duvar English', 'https://www.duvarenglish.com/four-out-of-ten-people-in-turkey-want-to-live-abroad-survey-news-63229'),
 'S10': ('Social Weather Stations, December survey (n=1,200), via Malaya Business Insight', 'https://malaya.com.ph/news/17-of-filipinos-want-to-live-abroad'),
 'S11': ('Keyou Analytics telephone poll, Nov-Dec 2021 (n=1,300), via Iran Times (2021-12-31)', 'https://iran-times.com/third-of-iranians-want-to-emigrate'),
 'S12': ('CRRC Caucasus Barometer 2024, "Interested in permanent emigration?"', 'https://caucasusbarometer.org/en/cb2024/EMIGRAT/'),
 'S13': ('RCC Balkan Barometer 2023, via bne IntelliNews (2023-07-25)', 'https://www.intellinews.com/almost-half-western-balkan-citizens-consider-emigrating-as-eu-accession-hopes-fade-285455/'),
 'S14': ('Gallup, "More Than 750 Million Worldwide Would Migrate If They Could" (Dec 2018), World Poll 2015-2017', 'https://news.gallup.com/poll/245255/750-million-worldwide-migrate.aspx'),
 'S15': ('Gallup International Association, End of Year survey 2022 (57 countries), published 2023-02-04', 'https://www.gallup-international.com/survey-results-and-news/survey-result/one-in-three-global-citizens-want-to-immigrate'),
 'S16': ('Gallup, "As Taliban Returns, Majority of Afghans Seek Exit" (2022-04-04), 2021 data', 'https://news.gallup.com/poll/391499/taliban-returns-majority-afghans-seek-exit.aspx'),
 'S17': ('Currencies Direct "British Expat Report" (n>1,500 UK adults), via HRreview 2024-10-01', 'https://hrreview.co.uk/hr-news/future-of-work-hr-news/over-1-in-5-adults-are-considering-moving-abroad/377161'),
 'S18': ('Semafor on Gallup 2025: one in five Americans want to leave (2025-11-13)', 'https://www.semafor.com/article/11/13/2025/one-in-five-americans-want-to-leave-us-poll-finds'),
 'S19': ('NAFSA summary of Presidential Proclamations 10949 (2025-06-04) and 10998 (2025-12-16, eff. 2026-01-01)', 'https://www.nafsa.org/regulatory-information/proclamation-december-16-2025-travel-ban-effective-january-1-2026'),
 'S20': ('Henley Passport Index 2026 figures via AviationA2Z (2026-08-07)', 'https://aviationa2z.com/index.php/2026/08/07/10-strongest-and-weakest-passports-in-2026/'),
 'S21': ('UK Home Office CPIN Eritrea: national service and illegal exit (Dec 2025)', 'https://www.gov.uk/government/publications/eritrea-country-policy-and-information-notes/country-policy-and-information-note-national-service-and-illegal-exit-eritrea-december-2025-accessible'),
 'S22': ('Gallup migration interactive, World Poll 2015-2017 (152 countries); NZ PNMI 231% quoted on page', 'https://news.gallup.com/migration/interactive.aspx'),
 'S24': ('Cubadata independent poll, 23 Mar-8 Apr 2023 (n=1,776), via CubaNet', 'https://www.cubanet.org/noticias/el-575-de-los-cubanos-quiere-irse-de-la-isla-segun-encuesta/'),
 'S23': ('Geo News fact-check on Gallup Pakistan surveys, Dec 2023 (71% would not leave)', 'https://www.geo.tv/latest/555435-fact-check-gallup-pakistan-survey-does-not-show-94-of-pakistanis-want-to-leave-country'),
}

# ---- survey layers: code -> (value, source, period, tier) ; tier G = Gallup World Poll, S = other survey (media/barometer)
LEAVE = {}  # % who want to leave
def put(d, src, period, tier):
    for k, v in d.items(): LEAVE.setdefault(k, (v, src, period, tier))
put({'USA':20}, 'S18', '2025', 'G')
put({'MEX':20,'NIC':19,'SLV':34,'BRA':23,'COL':36,'VEN':27,'DOM':46,'HND':50,'PRY':17,'GTM':32,'PAN':21,'ARG':34,'CHL':35,'CRI':30,'URY':25,'BOL':36,'ECU':49,'PER':42,
 'GAB':37,'BFA':12,'GMB':50,'COD':41,'NAM':27,'UGA':37,'CIV':29,'NER':17,'TGO':45,'BWA':30,'MOZ':20,'MLI':12,'BEN':32,'ZWE':33,'NGA':51,'TCD':20,'COG':54,
 'SLE':75,'CMR':41,'GIN':44,'MDG':14,'TZA':14,'SWZ':45,'LBR':76,'MRT':41,'ZAF':32,'MWI':37,'KEN':39,'GHA':65,'SEN':42,'ETH':31,'SOM':29,'CAN':20}, 'S01', '2023', 'G')
put({'AFG':53}, 'S16', '2021', 'G')
put({'HTI':63,'ALB':60,'SYR':46}, 'S14', '2015-2017', 'G')
put({'TUN':46,'JOR':42,'LBN':38,'MAR':35,'KWT':16}, 'S04', '2023-24', 'S')
put({'IRQ':35,'LBY':20,'EGY':13}, 'S05', '2021-22', 'S')
put({'RUS':9}, 'S07', 'Apr 2025', 'S')
put({'UKR':21}, 'S08', 'Dec 2024', 'S')
put({'TUR':39}, 'S09', 'Oct 2023', 'S')
put({'PHL':17}, 'S10', 'Dec 2022', 'S')
put({'IRN':33}, 'S11', 'Nov-Dec 2021', 'S')
put({'ARM':22,'GEO':9}, 'S12', '2024', 'S')
put({'BIH':38,'MKD':35}, 'S13', '2023', 'S')
put({'JPN':14,'VNM':8,'IND':4}, 'S15', 'Aug-Oct 2022', 'S')
put({'SRB':40,'MNE':40}, 'S13', '2023', 'S')
put({'CUB':57}, 'S24', 'Mar-Apr 2023', 'S')
LEAVE_NOTE = {'UKR':'"would leave if borders fully opened"', 'TUR':'"would like to live or study abroad"', 'MAR':'considered emigrating', 'TUN':'considered emigrating',
 'JOR':'considered emigrating','LBN':'considered emigrating','KWT':'considered emigrating','IRQ':'considered emigrating','LBY':'considered emigrating','EGY':'considered emigrating',
 'JPN':'"would like to live in another country" (GIA)','VNM':'(GIA)','IND':'(GIA)','BIH':'considered living abroad','MKD':'considered living abroad','SRB':'40-50% considering living abroad (lower bound used)','MNE':'40-50% considering living abroad (lower bound used)','CUB':'57.5% of 1,090 answers (Cubadata, independent online poll; ~35% of the full 1,776 sample)'}
PNMI = {'LUX':150,'IRL':138,'DNK':129,'PRT':125,'FIN':97,'SWE':91,'AUT':83,'CYP':79,'ESP':74,'DEU':53,'BEL':48,'FRA':44,'NLD':43,'ITA':25,
 'SVN':8,'HRV':7,'GRC':-3,'POL':-5,'EST':-6,'BGR':-8,'CZE':-11,'SVK':-12,'LTU':-15,'LVA':-15,'ROU':-22,'HUN':-24,'CAN':225,'USA':37}
PNMI_OLD = {'NZL':(231,'S22','2015-2017')}
DREAM = {'USA':(15,'S02','2025'),'CAN':(9,'S02','2025'),'GBR':(4,'S02','2025'),'DEU':(6,'S14','2015-2017'),'FRA':(5,'S14','2015-2017'),
 'AUS':(5,'S14','2015-2017'),'SAU':(3,'S14','2015-2017'),'ESP':(3,'S14','2015-2017')}
EXTRA_CHIPS = {'GBR':('23% consider moving abroad within 5 years','S17','2024'), 'PAK':('71% say they would never leave','S23','Dec 2023'),
 'ALB':('Balkan Barometer 2023: 40-50% considering','S13','2023')}
LOCKED = {'PRK':('Citizens cannot leave without state permission','R'), 'ERI':('Most people cannot get passports or exit visas','S21')}
PASSPORT = {'SGP':192,'KOR':188,'JPN':188,'ARE':188,'NOR':186,'CHE':185,'GBR':184,'MYS':183,'USA':180,'ISL':180,
 'AFG':22,'SYR':25,'IRQ':28,'PAK':29,'YEM':30,'SOM':32,'NPL':34,'PRK':35,'BGD':35,'IRN':37}
US_BAN_FULL = 'AFG MMR TCD GNQ ERI HTI IRN LAO LBY MLI NER COG SLE SOM SSD SDN SYR YEM BFA'.split()
US_BAN_PART = 'AGO ATG BEN BDI CIV CUB DMA GAB GMB MWI MRT NGA SEN TZA TGO TON TKM VEN ZMB ZWE'.split()
SHORT = {'Dominican Republic':'Dominican Rep.','Trinidad and Tobago':'Trinidad & Tob.','Bosnia and Herzegovina':'Bosnia & Herz.','United Arab Emirates':'UAE',
 'Central African Republic':'CAR','Republic of the Congo':'Congo','Papua New Guinea':'Papua N. Guinea','Solomon Islands':'Solomon Isl.','United States':'USA'}
STATUSES = {
 'MAGNET': ('MAGNET', 'PNMI >= +50%, or (no PNMI) >= 3% of the world\'s would-be migrants name it as their dream destination'),
 'PULL':   ('MORE WANT IN', 'PNMI +10..+49%, or estimate: UN net migration >= +2 per 1,000 (2019-2023 avg)'),
 'STAY':   ('MOST STAY', '% wanting to leave < 20, or PNMI -9..+9%, or estimate: UN net migration -2..+2'),
 'LEAVE':  ('MANY WANT OUT', '% wanting to leave 20-39, or PNMI <= -10%, or estimate: UN net migration <= -2'),
 'EXIT':   ('MOST WANT OUT', '% wanting to leave >= 40 (any survey)'),
 'LOCKED': ('CAN\'T LEAVE', 'documented state ban on leaving / exit visas withheld; overrides other rules'),
}

def classify(code, un):
    if code in LOCKED: return 'LOCKED', 'exit ban', 'F'
    if code in PNMI and code not in ('USA',):
        p = PNMI[code]; s = 'MAGNET' if p >= 50 else 'PULL' if p >= 10 else 'STAY' if p > -10 else 'LEAVE'
        return s, f'PNMI {p:+d}% (Gallup 2023-2025)', 'G'
    if code == 'USA':
        return 'MAGNET', 'world #1 dream destination (15%), PNMI +37%', 'G'
    if code in PNMI_OLD:
        p = PNMI_OLD[code][0]; return ('MAGNET' if p >= 50 else 'PULL'), f'PNMI {p:+d}% (Gallup 2015-2017)', 'G'
    if code in DREAM and DREAM[code][0] >= 3:
        return 'MAGNET', f'{DREAM[code][0]}% of would-be migrants pick it ({DREAM[code][2]})', 'G'
    if code in LEAVE:
        v, src, per, tier = LEAVE[code]; s = 'EXIT' if v >= 40 else 'LEAVE' if v >= 20 else 'STAY'
        return s, f'{v}% want to leave ({per})', tier
    s = 'PULL' if un >= 2 else 'LEAVE' if un <= -2 else 'STAY'
    return s, f'estimate: UN net migration {un:+.1f} per 1,000 (2019-2023 avg)', 'E'

def main():
    base = list(csv.DictReader(open(os.path.join(ROOT, 'data_raw/un_wpp2024_net_migration.csv'))))
    add = {'USA': ('Canada', 840, 'United States', 'North America'), 'GMB': ('Senegal', 270, 'Gambia', 'Africa'), 'SWZ': ('South Africa', 748, 'Eswatini', 'Africa')}
    UNX = {'USA': None, 'GMB': None, 'SWZ': None}
    sys.path.insert(0, HERE)
    import pyreadr
    S = os.environ.get('WPP', '/tmp/claude-0/-home-claude/df0984ad-f311-5254-a0a3-609fbc0cd6b9/scratchpad/wpp2024/data/')
    misc = list(pyreadr.read_r(S + 'misc1dt.rda').values())[0]
    def un(mid):
        d = misc[misc.country_code == mid]; return round(d[(d.year >= 2019) & (d.year <= 2023)].cnmr.mean(), 2), round(d[d.year == 2023].cnmr.iloc[0], 2)
    rows = []
    for r in base:
        rows.append(r)
        for code, (after, mid, name, cont) in add.items():
            if r['name'] == after:
                a, b = un(mid)
                rows.append(dict(code=code, m49=mid, name=name, region_id=r['region_id'], region=r['region'], continent=cont, un_cnmr_avg_2019_2023=a, un_cnmr_2023=b))
    # Canada first, then USA (north to south), intro lands on Canada
    out, facts = [], []
    def fact(c, typ, val, date, per, src, ver, what):
        facts.append(dict(fact_id=f'F{len(facts)+1:03d}', country=c['name'], code=c['code'], region=c['region'], fact_type=typ, value=val, fact_date=date, period=per,
                          source_ids=src, urls=SOURCES[src][1] if src in SOURCES else '', verification=ver, what_it_confirms=what))
    for i, r in enumerate(rows, 1):
        code = r['code']; u = float(r['un_cnmr_avg_2019_2023'])
        st, basis, q = classify(code, u)
        lv = LEAVE.get(code); dr = DREAM.get(code); pn = PNMI.get(code) if code in PNMI else (PNMI_OLD[code][0] if code in PNMI_OLD else '')
        ban = 'full' if code in US_BAN_FULL else 'partial' if code in US_BAN_PART else ''
        c = dict(order=i, code=code, m49=r['m49'], name=r['name'], short_name=SHORT.get(r['name'], r['name'] if len(r['name']) <= 16 else r['name'][:15] + '.'),
                 region_id=r['region_id'], region=r['region'], continent=r['continent'], status=st, status_label=STATUSES[st][0], basis=basis, quality=q,
                 leave_pct=lv[0] if lv else '', leave_period=lv[2] if lv else '', leave_source=lv[1] if lv else '', leave_note=LEAVE_NOTE.get(code, ''),
                 pnmi=pn, dream_pct=dr[0] if dr else '', un_netmig_per1000_avg19_23=u, un_netmig_per1000_2023=r['un_cnmr_2023'],
                 passport_visa_free=PASSPORT.get(code, ''), us_entry_ban_2026=ban, locked_note=LOCKED[code][0] if code in LOCKED else '',
                 extra_chip=EXTRA_CHIPS[code][0] if code in EXTRA_CHIPS else '')
        out.append(c)
        if lv: fact(c, 'want_to_leave_pct', f'{lv[0]}% {LEAVE_NOTE.get(code, "")}'.strip(), lv[2], lv[2], lv[1], 'F', 'share of adults wanting to leave / move abroad (wording per source)')
        if code in PNMI: fact(c, 'pnmi', f'{PNMI[code]:+d}%', '2023-2025', '2023-2025', 'S03', 'F', 'Gallup Potential Net Migration Index')
        if code in PNMI_OLD: fact(c, 'pnmi', f'{PNMI_OLD[code][0]:+d}%', '2015-2017', '2015-2017', 'S22', 'F', 'Gallup PNMI (old period)')
        if dr: fact(c, 'dream_destination_pct', f'{dr[0]}%', dr[2], dr[2], dr[1], 'F', 'share of would-be migrants worldwide naming this country')
        fact(c, 'un_net_migration', f'{u:+.2f} per 1,000 (avg 2019-2023); 2023: {float(r["un_cnmr_2023"]):+.2f}', '2019-2023', 'estimate', 'S06', 'F', 'UN WPP 2024 crude net migration rate')
        if code in PASSPORT: fact(c, 'passport', f'{PASSPORT[code]} destinations', '2026', '2026', 'S20', 'S', 'Henley Passport Index 2026 (media table)')
        if ban: fact(c, 'us_entry_ban', ban, '2026-01-01', 'current at cut-off', 'S19', 'F', 'US entry suspension under Proclamation 10998')
        if code in LOCKED: fact(c, 'exit_restriction', LOCKED[code][0], CUTOFF, 'current', LOCKED[code][1], 'F' if LOCKED[code][1] != 'R' else 'R', 'state restriction on leaving')
        if code in EXTRA_CHIPS: e = EXTRA_CHIPS[code]; fact(c, 'extra_survey', e[0], e[2], e[2], e[1], 'F', 'additional survey figure (different wording)')
    EXTRA = [('HND','want_to_leave_pct','35% (2025)','2025','2025','S02','F','Honduras fell from above 50% to 35% in 2025'),
      ('USA','dream_destination_trend','15%, lowest in nearly two decades','2025','2025','S02','F','US share of would-be migrants at a new low'),
      ('IRL','pnmi_old','+48% (2015-2017)','2015-2017','2015-2017','S03','F','Ireland PNMI in the earlier period'),
      ('ITA','pnmi_old','-8% (2015-2017)','2015-2017','2015-2017','S03','F','Italy was negative in 2015-2017'),
      ('CAN','pnmi_old','+147% (2015-2017)','2015-2017','2015-2017','S03','F','Canada PNMI in 2015-2017 (lower than NZ 231)'),
      ('HUN','pnmi_rank','-24%, lowest of 27 EU countries','2023-2025','2023-2025','S03','F','derived from the EU table'),
      ('RUS','want_to_leave_trend','9%, lowest for the entire observation period','Apr 2025','Apr 2025','S07','F','Levada series minimum'),
      ('AFG','want_to_leave_trend','53%, record high','2021','2021','S16','F','Gallup record'),
      ('ERI','national_service','compulsory for citizens aged 18 to 40','Dec 2025','current','S21','F','UK Home Office CPIN'),
      ('LBR','derived_rank','76%, highest want-to-leave figure in the registry','2023','2023','S01','F','max of leave_pct in countries.csv'),
      ('MLI','derived_rank','12%, lowest Gallup figure in Africa (tie with Burkina Faso)','2023','2023','S01','F','min of African Gallup 2023 values'),
      ('NGA','derived_rank','51%: most populous country with leave_pct > 50','2023','2023','S01','R','population ranking is reference knowledge')]
    byc = {c['code']: c for c in out}
    for code, *rest in EXTRA: fact(byc[code], *rest)
    for f in ('countries.csv', 'facts.csv'):
        data = out if f == 'countries.csv' else facts
        with open(os.path.join(ROOT, f), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
    with open(os.path.join(ROOT, 'sources.txt'), 'w') as fh:
        fh.write(f'SOURCES - Countries People Want to LEAVE vs MOVE TO (cut-off {CUTOFF})\n\n')
        for k, (t, u) in SOURCES.items(): fh.write(f'{k}  {t}\n     {u}\n')
    with open(os.path.join(ROOT, 'territories_and_exclusions.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['name', 'code', 'type', 'reason', 'data_available'])
        for row in [('Malta', 'MLT', 'microstate', 'too small to read on the map', 'PNMI +67%'), ('Mauritius', 'MUS', 'island microstate', 'too small', 'Gallup 2023: 38%'),
                    ('Comoros', 'COM', 'island microstate', 'too small', 'Gallup 2023: 48%'), ('Palestine', 'PSE', 'territory / partially recognised', 'counted separately, not in country counter', 'Arab Barometer 2023-24: 25%'),
                    ('Kosovo', 'XKX', 'partially recognised', 'not in counter', 'Balkan Barometer 2023: 57%'), ('Western Sahara', 'ESH', 'disputed territory', 'not in counter', 'none'),
                    ('Taiwan', 'TWN', 'disputed status', 'not in route (kept from donor list)', 'none found'), ('Other microstates (Andorra, Monaco, Liechtenstein, San Marino, Vatican, Pacific/Caribbean island states)', '', 'microstate', 'too small', '')]:
            w.writerow(row)
    # coverage report
    from collections import Counter
    cnt = Counter(c['status'] for c in out); q = Counter(c['quality'] for c in out); reg = Counter(c['region_id'] for c in out); cont = Counter(c['continent'] for c in out)
    codes = [c['code'] for c in out]
    rep = dict(total=len(out), duplicates=len(codes) - len(set(codes)), statuses=dict(cnt), quality=dict(q), regions=dict(reg), continents=dict(cont))
    print(rep)
    return out, facts, rep

if __name__ == '__main__': main()
