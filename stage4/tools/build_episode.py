"""Build data/episode.js from the verified registry, the region plan and the REAL word timestamps.

Inputs
  ../countries.csv (stage 2 registry), sync/words.json (aligned words of the real WAV: [{w,start,end}]),
  sync/script_words.json (voice_en.txt words mapped onto the audio by tools/align.py).
Output
  data/episode.js and sync/sync_table.csv (line, country, audio key moment, map event moment, check).
Every map time comes from a word time; nothing is spread evenly or estimated from word counts.
"""
import csv, json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
ROOT = os.environ.get('LOVEHATE_ROOT', '/mnt/project-files/countries-love-hate-usa')
FPS = 30

ISO = {  # alpha3 -> (ISO numeric used by Natural Earth/world-atlas, flag file)
    'CAN': ('124', 'ca'), 'MEX': ('484', 'mx'), 'GTM': ('320', 'gt'), 'BLZ': ('084', 'bz'), 'HND': ('340', 'hn'),
    'SLV': ('222', 'sv'), 'NIC': ('558', 'ni'), 'CRI': ('188', 'cr'), 'PAN': ('591', 'pa'), 'JAM': ('388', 'jm'),
    'CUB': ('192', 'cu'), 'BHS': ('044', 'bs'), 'HTI': ('332', 'ht'), 'DOM': ('214', 'do'), 'TTO': ('780', 'tt'),
    'VEN': ('862', 've'), 'COL': ('170', 'co'), 'ECU': ('218', 'ec'), 'PER': ('604', 'pe'), 'BOL': ('068', 'bo'),
    'CHL': ('152', 'cl'), 'ARG': ('032', 'ar'), 'URY': ('858', 'uy'), 'PRY': ('600', 'py'), 'BRA': ('076', 'br'),
    'SUR': ('740', 'sr'), 'GUY': ('328', 'gy'),
    'PRT': ('620', 'pt'), 'ESP': ('724', 'es'), 'FRA': ('250', 'fr'), 'GBR': ('826', 'gb'), 'IRL': ('372', 'ie'),
    'ISL': ('352', 'is'), 'NOR': ('578', 'no'), 'SWE': ('752', 'se'), 'FIN': ('246', 'fi'), 'DNK': ('208', 'dk'),
    'NLD': ('528', 'nl'), 'BEL': ('056', 'be'), 'LUX': ('442', 'lu'), 'DEU': ('276', 'de'), 'CHE': ('756', 'ch'),
    'AUT': ('040', 'at'), 'ITA': ('380', 'it'),
    'SVN': ('705', 'si'), 'HRV': ('191', 'hr'), 'BIH': ('070', 'ba'), 'SRB': ('688', 'rs'), 'MNE': ('499', 'me'),
    'ALB': ('008', 'al'), 'MKD': ('807', 'mk'), 'GRC': ('300', 'gr'), 'BGR': ('100', 'bg'), 'ROU': ('642', 'ro'),
    'HUN': ('348', 'hu'), 'SVK': ('703', 'sk'), 'CZE': ('203', 'cz'), 'POL': ('616', 'pl'), 'LTU': ('440', 'lt'),
    'LVA': ('428', 'lv'), 'EST': ('233', 'ee'), 'BLR': ('112', 'by'), 'MDA': ('498', 'md'), 'UKR': ('804', 'ua'),
    'RUS': ('643', 'ru'), 'GEO': ('268', 'ge'), 'ARM': ('051', 'am'), 'AZE': ('031', 'az'), 'KAZ': ('398', 'kz'),
    'KGZ': ('417', 'kg'), 'TJK': ('762', 'tj'), 'UZB': ('860', 'uz'), 'TKM': ('795', 'tm'), 'AFG': ('004', 'af'),
    'IRN': ('364', 'ir'), 'IRQ': ('368', 'iq'), 'KWT': ('414', 'kw'), 'BHR': ('048', 'bh'), 'QAT': ('634', 'qa'),
    'ARE': ('784', 'ae'), 'OMN': ('512', 'om'), 'YEM': ('887', 'ye'), 'SAU': ('682', 'sa'), 'JOR': ('400', 'jo'),
    'SYR': ('760', 'sy'), 'TUR': ('792', 'tr'), 'CYP': ('196', 'cy'), 'LBN': ('422', 'lb'), 'ISR': ('376', 'il'),
    'EGY': ('818', 'eg'), 'LBY': ('434', 'ly'), 'TUN': ('788', 'tn'), 'DZA': ('012', 'dz'), 'MAR': ('504', 'ma'),
    'MRT': ('478', 'mr'), 'SEN': ('686', 'sn'), 'GIN': ('324', 'gn'), 'SLE': ('694', 'sl'), 'LBR': ('430', 'lr'),
    'CIV': ('384', 'ci'), 'MLI': ('466', 'ml'), 'BFA': ('854', 'bf'), 'GHA': ('288', 'gh'), 'TGO': ('768', 'tg'),
    'BEN': ('204', 'bj'), 'NGA': ('566', 'ng'), 'NER': ('562', 'ne'), 'TCD': ('148', 'td'),
    'CMR': ('120', 'cm'), 'GAB': ('266', 'ga'), 'COG': ('178', 'cg'), 'CAF': ('140', 'cf'), 'SDN': ('729', 'sd'),
    'ERI': ('232', 'er'), 'ETH': ('231', 'et'), 'SOM': ('706', 'so'), 'KEN': ('404', 'ke'), 'SSD': ('728', 'ss'),
    'UGA': ('800', 'ug'), 'RWA': ('646', 'rw'),
    'COD': ('180', 'cd'), 'AGO': ('024', 'ao'), 'NAM': ('516', 'na'), 'BWA': ('072', 'bw'), 'ZAF': ('710', 'za'),
    'ZWE': ('716', 'zw'), 'ZMB': ('894', 'zm'), 'MWI': ('454', 'mw'), 'TZA': ('834', 'tz'), 'MOZ': ('508', 'mz'),
    'MDG': ('450', 'mg'),
    'LKA': ('144', 'lk'), 'IND': ('356', 'in'), 'PAK': ('586', 'pk'), 'NPL': ('524', 'np'), 'BTN': ('064', 'bt'),
    'BGD': ('050', 'bd'), 'MMR': ('104', 'mm'), 'THA': ('764', 'th'), 'LAO': ('418', 'la'), 'KHM': ('116', 'kh'),
    'VNM': ('704', 'vn'), 'MYS': ('458', 'my'), 'SGP': ('702', 'sg'), 'IDN': ('360', 'id'), 'PHL': ('608', 'ph'),
    'CHN': ('156', 'cn'), 'MNG': ('496', 'mn'), 'PRK': ('408', 'kp'), 'KOR': ('410', 'kr'), 'JPN': ('392', 'jp'),
    'PNG': ('598', 'pg'), 'SLB': ('090', 'sb'), 'AUS': ('036', 'au'), 'NZL': ('554', 'nz'), 'FJI': ('242', 'fj'),
}
GREEN = {'c1': '#7cf0a8', 'c2': '#1fa65a', 'ink': '#ffffff'}
RED = {'c1': '#ff6a6a', 'c2': '#c0182b', 'ink': '#ffffff'}

# Region plan R01 (scenes SC001-SC006). 'at' = phrase in voice_en.txt whose FIRST word start triggers the action.
# Reactions are game illustrations picked from the dated event, not claims about how people feel.
R01 = {
    'id': 'R01', 'name': 'North America & Caribbean', 'scenes': 'SC001-SC006',
    'shots': [
        {'ids': ['CAN'], 'arrive_at': 'in Canada', 'first': True},
        {'ids': ['MEX'], 'arrive_at': 'Mexico goes grey'},
        {'ids': ['GTM', 'BLZ', 'HND', 'SLV'], 'arrive_at': 'Guatemala, Belize'},
        {'ids': ['NIC', 'CRI'], 'arrive_at': 'Nicaragua flashes'},
        {'ids': ['PAN'], 'arrive_at': 'And Panama'},
        {'ids': ['JAM'], 'arrive_at': 'Jamaica, easy grey'},
        {'ids': ['CUB'], 'arrive_at': 'the first red swords'},
        {'ids': ['BHS', 'HTI', 'DOM'], 'arrive_at': 'Bahamas, Haiti'},
        {'ids': ['TTO'], 'arrive_at': 'Trinidad and Tobago. Four', 'zmax': 14},
    ],
    'stops': [
        {'code': 'CAN', 'at': 'Canada.', 'reaction': 'disappointed', 'tag': 'NATO 1949', 'scene': 'SC001', 'events': [
            {'kind': 'poll', 'at': '33 percent of Canadians', 'big': '33%', 'down': True, 'sub': '57% in 2023',
             'rival': {'at': 'China got 44', 'text': 'CHINA 44%'}}]},
        {'code': 'MEX', 'at': 'Mexico goes grey', 'reaction': 'awkward', 'tag': 'No alliance', 'scene': 'SC003', 'events': [
            {'kind': 'history', 'at': '1846 to 1848', 'text': 'WAR 1846-1848'},
            {'kind': 'stamp', 'at': 'declined to simply renew', 'text': 'USMCA', 'sub': 'NOT RENEWED AS-IS · JUL 2026'},
            {'kind': 'poll', 'at': '40 percent, China 59', 'big': '40%', 'sub': 'CHINA 59%', 'side': -1,
             'color': '#8C96A3', 'dark': '#3d444d'}]},
        {'code': 'GTM', 'at': 'Guatemala, Belize', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC004'},
        {'code': 'BLZ', 'at': 'Belize, Honduras', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC004'},
        {'code': 'HND', 'at': 'Honduras, El Salvador', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC004'},
        {'code': 'SLV', 'at': 'El Salvador: grey', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC004'},
        {'code': 'NIC', 'at': 'Nicaragua flashes', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC004', 'events': [
            {'kind': 'sanction', 'at': 'sanctions list', 'text': 'US SANCTIONS'}]},
        {'code': 'CRI', 'at': 'Costa Rica, calm', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC004'},
        {'code': 'PAN', 'at': 'Panama: grey today', 'reaction': 'shocked', 'tag': 'No alliance', 'scene': 'SC004', 'events': [
            {'kind': 'history', 'at': 'December 1989', 'text': 'US INVASION 1989'}]},
        {'code': 'JAM', 'at': 'Jamaica, easy grey', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC005'},
        {'code': 'CUB', 'at': 'the first red swords', 'reaction': 'angry', 'tag': 'US embargo', 'scene': 'SC005', 'events': [
            {'kind': 'timeline', 'side': 1, 'steps': [
                {'at': '1961, the embargo', 'year': '1961', 'label': 'TIES CUT'},
                {'at': 'more than six decades', 'year': '60+ YRS', 'label': 'EMBARGO'},
                {'at': '2015. Then', 'year': '2015', 'label': 'EMBASSIES REOPEN'},
                {'at': '2026 the US started', 'year': '2026', 'label': 'OIL TANKERS BLOCKED', 'c1': '#ff6a6a', 'c2': '#c0182b', 'ink': '#ffffff'}]}]},
        {'code': 'BHS', 'at': 'Bahamas, Haiti', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC006'},
        {'code': 'HTI', 'at': 'Haiti, Dominican', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC006'},
        {'code': 'DOM', 'at': 'Dominican Republic, Trinidad', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC006'},
        {'code': 'TTO', 'at': 'Trinidad and Tobago. Four', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC006', 'events': [
            {'kind': 'sticker', 'at': 'zero drama', 'text': '0 DRAMA', 'dx': -260, 'dy': -230}]},
    ],
    'end_after': 'Next stop, South America.',
}

# Region plan R02 (scenes SC007-SC012). Polls only where the voice says the number.
R02 = {
    'id': 'R02', 'name': 'South America', 'scenes': 'SC007-SC012',
    'shots': [
        {'ids': ['VEN'], 'arrive_at': 'Venezuela, and buckle'},
        {'ids': ['COL'], 'arrive_at': 'Colombia gets a green'},
        {'ids': ['ECU', 'PER'], 'arrive_at': 'Ecuador, grey. In'},
        {'ids': ['BOL'], 'arrive_at': 'Bolivia, grey, but'},
        {'ids': ['CHL'], 'arrive_at': 'Chile, grey. Argentina', 'span': [150, 95]},
        {'ids': ['ARG'], 'arrive_at': 'Argentina, green handshake'},
        {'ids': ['URY', 'PRY'], 'arrive_at': 'Uruguay, Paraguay, quick'},
        {'ids': ['BRA'], 'arrive_at': 'Brazil, green handshake too'},
        {'ids': ['SUR', 'GUY'], 'arrive_at': 'Suriname and Guyana close'},
    ],
    'stops': [
        {'code': 'VEN', 'at': 'Venezuela, and buckle', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC007', 'events': [
            {'kind': 'history', 'at': 'January 3, 2026', 'text': 'US OPERATION · 3 JAN 2026'},
            {'kind': 'stamp', 'at': 'embassy reopened in March', 'text': 'EMBASSY', 'sub': 'REOPENED · MAR 2026', 'color': '#1d8a4a', 'side': -1},
            {'kind': 'sanction', 'at': 'Sanctions are still', 'text': 'SANCTIONS STILL ON', 'dy': 300}]},
        {'code': 'COL', 'at': 'Colombia gets a green', 'reaction': 'wink', 'tag': 'MNNA 2022', 'scene': 'SC008', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '2025 Washington sanctioned', 'year': '2025', 'label': 'PRESIDENT SANCTIONED', **RED},
                {'at': 'August 2026', 'year': 'AUG 2026', 'label': 'NEW PRESIDENT'},
                {'at': 'billion dollars', 'year': '$1 BILLION', 'label': 'SECURITY AID', **GREEN}]}]},
        {'code': 'ECU', 'at': 'Ecuador, grey. In', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC009', 'events': [
            {'kind': 'stamp', 'at': 'said no to foreign', 'text': 'NO FOREIGN BASES', 'sub': 'REFERENDUM · NOV 2025', 'side': -1}]},
        {'code': 'PER', 'at': 'Peru turns green', 'reaction': 'happy', 'tag': 'MNNA 2026', 'scene': 'SC009', 'events': [
            {'kind': 'poll', 'at': '51 percent favorable', 'big': '51%', 'color': '#2FA05A', 'dark': '#14532d', 'side': 1}]},
        {'code': 'BOL', 'at': 'Bolivia, grey, but', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC010', 'events': [
            {'kind': 'stamp', 'at': 'ambassadors returned', 'text': 'AMBASSADORS BACK', 'sub': 'NOV 2025 · AFTER 17 YEARS', 'color': '#1d8a4a'}]},
        {'code': 'CHL', 'at': 'Chile, grey. Argentina', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC010'},
        {'code': 'ARG', 'at': 'Argentina, green handshake', 'reaction': 'happy', 'tag': 'MNNA 1998', 'scene': 'SC010'},
        {'code': 'URY', 'at': 'Uruguay, Paraguay, quick', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC011'},
        {'code': 'PRY', 'at': 'Paraguay, quick wave', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC011'},
        {'code': 'BRA', 'at': 'Brazil, green handshake too', 'reaction': 'happy', 'tag': 'MNNA 2019', 'scene': 'SC011', 'events': [
            {'kind': 'sanction', 'at': 'tariff fight in 2025', 'text': 'TARIFF FIGHT 2025', 'end_at': 'Lula visited'},
            {'kind': 'stamp', 'at': 'Lula visited the White House', 'text': 'WHITE HOUSE VISIT', 'sub': 'LULA · MAY 2026', 'color': '#1d8a4a', 'end_at': 'And Brazil is the closest'},
            {'kind': 'poll', 'at': 'US 47, China', 'big': '47%', 'color': '#2FA05A', 'dark': '#14532d', 'side': -1,
             'rival': {'at': 'China 46. Photo', 'text': 'CHINA 46%'}},
            {'kind': 'sticker', 'at': 'Photo finish', 'text': 'PHOTO FINISH', 'dx': 340, 'dy': 140}]},
        {'code': 'SUR', 'at': 'Suriname and Guyana close', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC012'},
        {'code': 'GUY', 'at': 'Guyana close out', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC012'},
    ],
    'end_after': 'cross the Atlantic.',
}
# Region plan R03 (scenes SC013-SC019). Poll colours: under 35% red, 35-49% grey, 50%+ green.
POLL_GREY = {'color': '#8C96A3', 'dark': '#3d444d'}
POLL_GREEN = {'color': '#2FA05A', 'dark': '#14532d'}
R03 = {
    'id': 'R03', 'name': 'Western & Northern Europe', 'scenes': 'SC013-SC019',
    'shots': [
        {'ids': ['PRT', 'ESP'], 'arrive_at': 'Portugal, blue shield', 'minfly': 2.3, 'dip': 0.45},
        {'ids': ['FRA'], 'arrive_at': 'France, blue shield. France'},
        {'ids': ['GBR', 'IRL'], 'arrive_at': 'The United Kingdom. British'},
        {'ids': ['ISL', 'NOR'], 'arrive_at': 'Iceland and Norway'},
        {'ids': ['SWE', 'FIN'], 'arrive_at': 'Sweden only joined'},
        {'ids': ['DNK'], 'arrive_at': 'Denmark, blue shield'},
        {'ids': ['NLD', 'BEL', 'LUX'], 'arrive_at': 'Netherlands, Belgium'},
        {'ids': ['DEU'], 'arrive_at': 'Germany fought America'},
        {'ids': ['CHE', 'AUT'], 'arrive_at': 'Switzerland and Austria'},
        {'ids': ['ITA'], 'arrive_at': 'Italy, blue shield'},
    ],
    'stops': [
        {'code': 'PRT', 'at': 'Portugal, blue shield', 'reaction': 'happy', 'tag': 'NATO 1949', 'scene': 'SC013'},
        {'code': 'ESP', 'at': 'Spain, blue shield too', 'reaction': 'awkward', 'tag': 'NATO 1982', 'scene': 'SC013', 'events': [
            {'kind': 'history', 'at': 'war in 1898', 'text': 'WAR 1898', 'end_at': 'Only 30 percent'},
            {'kind': 'poll', 'at': '30 percent of Spaniards', 'big': '30%'}]},
        {'code': 'FRA', 'at': 'France, blue shield. France', 'reaction': 'awkward', 'tag': 'NATO 1949', 'scene': 'SC014', 'events': [
            {'kind': 'stamp', 'at': '1778, the original', 'text': 'ALLIANCE 1778', 'sub': 'THE ORIGINAL FRIENDSHIP', 'color': '#1d8a4a', 'side': -1},
            {'kind': 'poll', 'at': '27 percent. Long', 'big': '27%'}]},
        {'code': 'GBR', 'at': 'The United Kingdom. British', 'reaction': 'chill', 'tag': 'NATO 1949', 'scene': 'SC015', 'events': [
            {'kind': 'history', 'at': 'burned the White House', 'text': 'WHITE HOUSE BURNED 1814', 'end_at': 'Today: NATO founder'},
            {'kind': 'poll', 'at': '41 percent favorable', 'big': '41%', **POLL_GREY}]},
        {'code': 'IRL', 'at': 'Ireland stays outside', 'reaction': 'chill', 'tag': 'Not in NATO', 'scene': 'SC015'},
        {'code': 'ISL', 'at': 'Iceland and Norway', 'reaction': 'calm', 'tag': 'NATO 1949', 'scene': 'SC016'},
        {'code': 'NOR', 'at': 'Norway, NATO founders', 'reaction': 'happy', 'tag': 'NATO 1949', 'scene': 'SC016'},
        {'code': 'SWE', 'at': 'Sweden only joined', 'reaction': 'disappointed', 'tag': 'NATO 2024', 'scene': 'SC016', 'events': [
            {'kind': 'poll', 'at': '19 percent. Finland', 'big': '19%', 'sub': 'LOWEST IN THE EU', 'side': -1}]},
        {'code': 'FIN', 'at': 'Finland joined in 2023', 'reaction': 'wink', 'tag': 'NATO 2023', 'scene': 'SC016', 'events': [
            {'kind': 'sticker', 'at': 'Two brand new shields', 'text': '2 NEW SHIELDS', 'dx': 0, 'dy': 200}]},
        {'code': 'DNK', 'at': 'Denmark, blue shield', 'reaction': 'nervous', 'tag': 'NATO 1949', 'scene': 'SC017', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'January 2026, Washington', 'year': 'JAN 2026', 'label': 'TARIFF THREATS OVER GREENLAND', **RED},
                {'at': 'September they signed', 'year': 'SEP 2026', 'label': 'SECURITY DEAL SIGNED', **GREEN}]},
            {'kind': 'sticker', 'at': 'Crisis parked', 'text': 'CRISIS PARKED', 'dx': 0, 'dy': 220}]},
        {'code': 'NLD', 'at': 'Netherlands, Belgium', 'reaction': 'disappointed', 'tag': 'NATO 1949', 'scene': 'SC018', 'events': [
            {'kind': 'poll', 'at': '25 percent. Germany', 'big': '25%', 'side': -1}]},
        {'code': 'BEL', 'at': 'Belgium, Luxembourg', 'reaction': 'calm', 'tag': 'NATO 1949', 'scene': 'SC018'},
        {'code': 'LUX', 'at': 'Luxembourg, three', 'reaction': 'happy', 'tag': 'NATO 1949', 'scene': 'SC018'},
        {'code': 'DEU', 'at': 'Germany fought America', 'reaction': 'awkward', 'tag': 'NATO 1955', 'scene': 'SC018', 'events': [
            {'kind': 'history', 'at': 'two world wars', 'text': 'WORLD WARS I & II', 'end_at': 'Now: 27 percent'},
            {'kind': 'poll', 'at': '27 percent favorable. Switzerland', 'big': '27%'}]},
        {'code': 'CHE', 'at': 'Switzerland and Austria', 'reaction': 'chill', 'tag': 'Neutral', 'scene': 'SC019'},
        {'code': 'AUT', 'at': 'Austria, neutral', 'reaction': 'calm', 'tag': 'Neutral', 'scene': 'SC019'},
        {'code': 'ITA', 'at': 'Italy, blue shield', 'reaction': 'awkward', 'tag': 'NATO 1949', 'scene': 'SC019', 'events': [
            {'kind': 'poll', 'at': '31 percent. Next', 'big': '31%'}]},
    ],
    'end_after': 'Next, the east.',
}
# Region plan R04 (scenes SC020-SC025). Ends before "Next stop, the biggest country on Earth" (Russia opens R05).
R04 = {
    'id': 'R04', 'name': 'Central & Eastern Europe', 'scenes': 'SC020-SC025',
    'shots': [
        {'ids': ['SVN', 'HRV'], 'arrive_at': 'Slovenia and Croatia'},
        {'ids': ['BIH', 'SRB'], 'arrive_at': 'Bosnia and Herzegovina, grey'},
        {'ids': ['MNE', 'ALB', 'MKD'], 'arrive_at': 'Montenegro, Albania'},
        {'ids': ['GRC'], 'arrive_at': 'Greece, blue shield'},
        {'ids': ['BGR', 'ROU'], 'arrive_at': 'Bulgaria and Romania'},
        {'ids': ['HUN'], 'arrive_at': 'Hungary, a shield'},
        {'ids': ['SVK', 'CZE'], 'arrive_at': 'Slovakia, Czechia'},
        {'ids': ['POL'], 'arrive_at': 'Poland, shield, and'},
        {'ids': ['LTU', 'LVA', 'EST'], 'arrive_at': 'Lithuania, Latvia'},
        {'ids': ['BLR'], 'arrive_at': 'Belarus flashes yellow'},
        {'ids': ['MDA', 'UKR'], 'arrive_at': 'Moldova, grey. Ukraine'},
    ],
    'stops': [
        {'code': 'SVN', 'at': 'Slovenia and Croatia', 'reaction': 'happy', 'tag': 'NATO 2004', 'scene': 'SC020'},
        {'code': 'HRV', 'at': 'Croatia, both NATO', 'reaction': 'wink', 'tag': 'NATO 2009', 'scene': 'SC020'},
        {'code': 'BIH', 'at': 'Bosnia and Herzegovina, grey', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC020', 'short': 'Bosnia & Herz.'},
        {'code': 'SRB', 'at': 'Serbia, grey, with', 'reaction': 'awkward', 'tag': 'No alliance', 'scene': 'SC020', 'events': [
            {'kind': 'history', 'at': 'NATO bombed Yugoslavia', 'text': 'NATO BOMBING 1999'}]},
        {'code': 'MNE', 'at': 'Montenegro, Albania', 'reaction': 'happy', 'tag': 'NATO 2017', 'scene': 'SC021'},
        {'code': 'ALB', 'at': 'Albania and North', 'reaction': 'wink', 'tag': 'NATO 2009', 'scene': 'SC021'},
        {'code': 'MKD', 'at': "North Macedonia, NATO's", 'reaction': 'happy', 'tag': 'NATO 2020', 'scene': 'SC021'},
        {'code': 'GRC', 'at': 'Greece, blue shield', 'reaction': 'calm', 'tag': 'NATO 1952', 'scene': 'SC021', 'events': [
            {'kind': 'poll', 'at': '37 percent. Bulgaria', 'big': '37%', **POLL_GREY}]},
        {'code': 'BGR', 'at': 'Bulgaria and Romania', 'reaction': 'happy', 'tag': 'NATO 2004', 'scene': 'SC022'},
        {'code': 'ROU', 'at': 'Romania, shields', 'reaction': 'wink', 'tag': 'NATO 2004', 'scene': 'SC022'},
        {'code': 'HUN', 'at': 'Hungary, a shield', 'reaction': 'shocked', 'tag': 'NATO 1999', 'scene': 'SC022', 'events': [
            {'kind': 'poll', 'at': '58 percent, the warmest', 'snap': 'fifty', 'big': '58%', 'sub': 'WARMEST IN THE EU',
             'color': '#2FA05A', 'dark': '#14532d'}]},
        {'code': 'SVK', 'at': 'Slovakia, Czechia', 'reaction': 'calm', 'tag': 'NATO 2004', 'scene': 'SC023'},
        {'code': 'CZE', 'at': 'Czechia, shields', 'reaction': 'chill', 'tag': 'NATO 1999', 'scene': 'SC023'},
        {'code': 'POL', 'at': 'Poland, shield, and', 'reaction': 'happy', 'tag': 'NATO 1999', 'scene': 'SC023', 'events': [
            {'kind': 'sticker', 'at': 'one of only six', 'text': '1 OF ONLY 6', 'dx': 0, 'dy': 230},
            {'kind': 'poll', 'at': '49 to 39', 'big': '49%', **POLL_GREY, 'rival': {'at': '39. Lithuania', 'text': 'CHINA 39%'}}]},
        {'code': 'LTU', 'at': 'Lithuania, Latvia', 'reaction': 'happy', 'tag': 'NATO 2004', 'scene': 'SC024'},
        {'code': 'LVA', 'at': 'Latvia, Estonia', 'reaction': 'calm', 'tag': 'NATO 2004', 'scene': 'SC024'},
        {'code': 'EST', 'at': 'Estonia, three', 'reaction': 'wink', 'tag': 'NATO 2004', 'scene': 'SC024'},
        {'code': 'BLR', 'at': 'Belarus flashes yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC024', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '2022, and sanctions', 'year': '2022', 'label': 'US EMBASSY CLOSED', **RED},
                {'at': 'March 2026, Washington', 'year': 'MAR 2026', 'label': 'SOME SANCTIONS EASED'},
                {'at': '250 political prisoners', 'year': '250', 'label': 'POLITICAL PRISONERS FREED', **GREEN}]},
            {'kind': 'sticker', 'at': 'Small thaw', 'text': 'SMALL THAW', 'dx': 0, 'dy': 230}]},
        {'code': 'MDA', 'at': 'Moldova, grey. Ukraine', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC025'},
        {'code': 'UKR', 'at': 'Ukraine, grey on paper', 'reaction': 'nervous', 'tag': 'No treaty', 'scene': 'SC025', 'events': [
            {'kind': 'stamp', 'at': 'minerals deal with Washington', 'text': 'MINERALS DEAL', 'sub': 'WITH THE US · APR 2025', 'color': '#1d8a4a', 'side': -1},
            {'kind': 'sanction', 'at': 'The war with Russia', 'text': 'WAR GOES ON', 'dy': 300}]},
    ],
    'end_after': 'talks keep stalling.',
}
# Region plan R05 (scenes SC026-SC028). Ends after the Kabul embassy line; "Next door, Iran" opens R06.
R05 = {
    'id': 'R05', 'name': 'Russia, Caucasus & Central Asia', 'scenes': 'SC026-SC028',
    'shots': [
        {'ids': ['RUS'], 'arrive_at': 'Russia. Yellow', 'fly_at': 'the biggest country on Earth', 'minfly': 2.4, 'dip': 0.3, 'wFrac': 0.85},
        {'ids': ['GEO', 'ARM', 'AZE'], 'arrive_at': 'Georgia, Armenia'},
        {'ids': ['KAZ', 'KGZ', 'TJK', 'UZB', 'TKM'], 'arrive_at': 'Kazakhstan, Kyrgyzstan', 'fly_at': 'Across the Caspian', 'minfly': 1.2},
        {'ids': ['AFG'], 'arrive_at': 'Then Afghanistan'},
    ],
    'stops': [
        {'code': 'RUS', 'at': 'Russia. Yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC026', 'flagFit': 'stretch', 'events': [
            {'kind': 'sanction', 'at': 'Rosneft and Lukoil', 'text': 'ROSNEFT + LUKOIL · OCT 2025', 'end_at': 'Allies in World'},
            {'kind': 'stamp', 'at': 'Allies in World War', 'text': 'WWII ALLIES', 'sub': 'THEN RIVALS', 'color': '#2F6FE0', 'end_at': 'The presidents met'},
            {'kind': 'stamp', 'at': 'met in Alaska', 'text': 'ALASKA SUMMIT', 'sub': 'AUG 2025', 'color': '#2F6FE0', 'side': -1},
            {'kind': 'sanction', 'at': 'no peace deal', 'text': 'NO PEACE DEAL YET', 'dy': 300}]},
        {'code': 'GEO', 'at': 'Georgia, Armenia', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'ARM', 'at': 'Armenia, Azerbaijan', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'AZE', 'at': 'Azerbaijan: grey', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'KAZ', 'at': 'Kazakhstan, Kyrgyzstan', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'KGZ', 'at': 'Kyrgyzstan, Tajikistan', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'TJK', 'at': 'Tajikistan, Uzbekistan', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'UZB', 'at': 'Uzbekistan, Turkmenistan', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC027'},
        {'code': 'TKM', 'at': 'Turkmenistan. Five', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC027', 'events': [
            {'kind': 'sticker', 'at': 'no drama. Then', 'text': 'NO DRAMA', 'dx': 0, 'dy': 230}]},
        {'code': 'AFG', 'at': 'Then Afghanistan', 'reaction': 'angry', 'tag': 'Embassy closed', 'scene': 'SC028', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '2001 to 2021', 'year': '2001-2021', 'label': "AMERICA'S WAR", **RED},
                {'at': '2012, a status', 'year': '2012', 'label': 'MAJOR NON-NATO ALLY', **GREEN},
                {'at': '2022. The US', 'year': '2022', 'label': 'STATUS REVOKED', **RED},
                {'at': 'closed since 2021', 'year': 'SINCE 2021', 'label': 'US EMBASSY CLOSED', **RED}]}]},
    ],
    'end_after': 'closed since 2021.',
}
# Region plan R06 (scenes SC029-SC035). Ends after "the whole survey."; "Into Africa." opens R07.
# UAE: the voice says "since 2025" (both recognisers), the verified fact is Sep 2024 -> no year on the map tag.
R06 = {
    'id': 'R06', 'name': 'Middle East', 'scenes': 'SC029-SC035',
    'shots': [
        {'ids': ['IRN'], 'arrive_at': 'Iran. The darkest', 'fly_at': 'Next door, Iran', 'minfly': 1.2},
        {'ids': ['IRQ'], 'arrive_at': 'Iraq, yellow'},
        {'ids': ['KWT', 'BHR', 'QAT', 'ARE'], 'arrive_at': 'Kuwait, Bahrain'},
        {'ids': ['OMN', 'YEM'], 'arrive_at': 'Oman, grey, and'},
        {'ids': ['SAU', 'JOR'], 'arrive_at': 'Saudi Arabia, the newest'},
        {'ids': ['SYR'], 'arrive_at': 'Syria, yellow, but'},
        {'ids': ['TUR'], 'arrive_at': 'Turkey, NATO shield'},
        {'ids': ['CYP', 'LBN', 'ISR'], 'arrive_at': 'Cyprus, grey'},
    ],
    'stops': [
        {'code': 'IRN', 'at': 'Iran. The darkest', 'reaction': 'angry', 'tag': 'No relations', 'scene': 'SC029', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'April 1980 after', 'year': 'APR 1980', 'label': 'RELATIONS CUT', **RED},
                {'at': 'February 28, 2026', 'year': '28 FEB 2026', 'label': 'WAR BEGINS', **RED},
                {'at': 'October 2026 the Strait', 'year': 'OCT 2026', 'label': 'HORMUZ STILL IN CRISIS', **RED}]}]},
        {'code': 'IRQ', 'at': 'Iraq, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC030', 'events': [
            {'kind': 'history', 'at': 'US war that began', 'text': 'IRAQ WAR 2003'}]},
        {'code': 'KWT', 'at': 'Kuwait, Bahrain', 'reaction': 'nervous', 'tag': 'MNNA 2004', 'scene': 'SC030', 'forceMicro': True},
        {'code': 'BHR', 'at': 'Bahrain, Qatar', 'reaction': 'nervous', 'tag': 'MNNA 2002', 'scene': 'SC030'},
        {'code': 'QAT', 'at': 'Qatar: green', 'reaction': 'shocked', 'tag': 'MNNA 2022', 'scene': 'SC030', 'events': [
            {'kind': 'history', 'at': 'hit by Iranian strikes', 'text': 'ALL 3 HIT BY IRAN · 2026', 'end_at': 'The UAE, a major'}]},
        {'code': 'ARE', 'at': 'The UAE, a major', 'reaction': 'calm', 'tag': 'Major Defense Partner', 'scene': 'SC030', 'short': 'UAE'},
        {'code': 'OMN', 'at': 'Oman, grey, and', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC031', 'events': [
            {'kind': 'stamp', 'at': 'mediated the US ceasefire', 'text': 'MEDIATOR', 'sub': 'US-HOUTHI CEASEFIRE · MAY 2025', 'color': '#1d8a4a', 'end_at': 'Yemen, yellow, after'}]},
        {'code': 'YEM', 'at': 'Yemen, yellow, after', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC031', 'events': [
            {'kind': 'sanction', 'at': 'weeks of US strikes', 'text': 'US STRIKES · SPRING 2025'}]},
        {'code': 'SAU', 'at': 'Saudi Arabia, the newest', 'reaction': 'happy', 'tag': 'MNNA 2026', 'scene': 'SC032', 'events': [
            {'kind': 'stamp', 'at': 'designated a major non-NATO', 'text': 'NEWEST HANDSHAKE', 'sub': 'MNNA SIGNED · JAN 2026', 'color': '#1d8a4a', 'side': -1}]},
        {'code': 'JOR', 'at': 'Jordan, a partner', 'reaction': 'calm', 'tag': 'MNNA 1996', 'scene': 'SC032'},
        {'code': 'SYR', 'at': 'Syria, yellow, but', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC033', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '2012. After Assad', 'year': '2012', 'label': 'US EMBASSY CLOSED', **RED},
                {'at': 'lifted sanctions', 'year': 'LIFTED', 'label': 'US SANCTIONS'},
                {'at': 'repeal the Caesar', 'year': 'REPEALED', 'label': 'CAESAR ACT'},
                {'at': '2026 the State Department', 'year': '2026', 'label': 'EMBASSY REOPENING PLANNED', **GREEN}]}]},
        {'code': 'TUR', 'at': 'Turkey, NATO shield', 'reaction': 'disappointed', 'tag': 'NATO 1952', 'scene': 'SC034', 'events': [
            {'kind': 'stamp', 'at': 'sanctioned its defense', 'text': 'SANCTIONED', 'sub': 'DEFENSE AGENCY · 2020', 'side': -1, 'end_at': 'And in the 2026 survey'},
            {'kind': 'poll', 'at': '13 percent favorable', 'big': '13%', 'sub': 'LOWEST IN SURVEY'},
            {'kind': 'sticker', 'at': "doesn't guarantee a hug", 'text': 'SHIELD ≠ HUG', 'dx': 0, 'dy': 230}]},
        {'code': 'CYP', 'at': 'Cyprus, grey', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC035'},
        {'code': 'LBN', 'at': 'Lebanon, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC035', 'forceMicro': True},
        {'code': 'ISR', 'at': 'Israel, green handshake', 'reaction': 'happy', 'tag': 'MNNA 1987', 'scene': 'SC035', 'events': [
            {'kind': 'poll', 'at': '81 percent favorable', 'snap': 'eighty', 'big': '81%', 'sub': 'HIGHEST IN SURVEY',
             'color': '#2FA05A', 'dark': '#14532d', 'side': -1}]},
    ],
    'end_after': 'the whole survey.',
}
# Region plan R07 (scenes SC036-SC040). Opens with "Into Africa."; ends after "On we go." ("Cameroon, Gabon" opens R08).
R07 = {
    'id': 'R07', 'name': 'North & West Africa', 'scenes': 'SC036-SC040',
    'shots': [
        {'ids': ['EGY'], 'arrive_at': 'Egypt, green handshake', 'fly_at': 'Into Africa'},
        {'ids': ['LBY', 'TUN', 'DZA'], 'arrive_at': 'Libya, yellow, the'},
        {'ids': ['MAR'], 'arrive_at': 'Morocco, green handshake, and'},
        {'ids': ['MRT', 'SEN', 'GIN', 'SLE', 'LBR', 'CIV', 'MLI'], 'arrive_at': 'Mauritania, Senegal', 'fly_at': 'West Africa, fast'},
        {'ids': ['BFA', 'GHA', 'TGO', 'BEN', 'NGA'], 'arrive_at': 'Burkina Faso, grey'},
        {'ids': ['NER', 'TCD'], 'arrive_at': 'Niger, grey, but'},
    ],
    'stops': [
        {'code': 'EGY', 'at': 'Egypt, green handshake', 'reaction': 'happy', 'tag': 'MNNA 1987', 'scene': 'SC036'},
        {'code': 'LBY', 'at': 'Libya, yellow, the', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC036', 'events': [
            {'kind': 'sanction', 'at': 'operated from Tunisia', 'text': 'US EMBASSY IN TUNIS · SINCE 2014', 'end_at': 'Tunisia, green handshake. Algeria'}]},
        {'code': 'TUN', 'at': 'Tunisia, green handshake. Algeria', 'reaction': 'happy', 'tag': 'MNNA 2015', 'scene': 'SC036'},
        {'code': 'DZA', 'at': 'Algeria, grey', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC036'},
        {'code': 'MAR', 'at': 'Morocco, green handshake, and', 'reaction': 'happy', 'tag': 'MNNA 2004', 'scene': 'SC037', 'events': [
            {'kind': 'stamp', 'at': 'the oldest friend', 'text': 'OLDEST FRIEND', 'sub': 'ON THIS MAP', 'color': '#1d8a4a', 'end_at': 'Morocco recognized the'},
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '1777, and their', 'year': '1777', 'label': 'RECOGNIZED THE US', **GREEN},
                {'at': '1786 treaty is', 'year': '1786', 'label': 'TREATY OF FRIENDSHIP', **GREEN},
                {'at': 'longest unbroken relationship', 'year': 'UNBROKEN', 'label': 'LONGEST IN US HISTORY', **GREEN}]}]},
        {'code': 'MRT', 'at': 'Mauritania, Senegal', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'SEN', 'at': 'Senegal, Guinea', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'GIN', 'at': 'Guinea, Sierra', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'SLE', 'at': 'Sierra Leone, Liberia', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'LBR', 'at': 'Liberia, Côte', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'CIV', 'at': "Côte d'Ivoire: all grey", 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC038'},
        {'code': 'MLI', 'at': 'Mali flashes yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC038', 'events': [
            {'kind': 'sanction', 'at': 'its own US sanctions', 'text': 'US SANCTIONS PROGRAM'}]},
        {'code': 'BFA', 'at': 'Burkina Faso, grey', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC039'},
        {'code': 'GHA', 'at': 'Ghana, grey but', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC039', 'events': [
            {'kind': 'poll', 'at': '68 percent favorable', 'snap': 'sixty', 'big': '68%', 'sub': 'TOP IN AFRICA', **POLL_GREEN, 'end_at': 'Togo, Benin, grey'}]},
        {'code': 'TGO', 'at': 'Togo, Benin, grey', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC039'},
        {'code': 'BEN', 'at': 'Benin, grey. Nigeria', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC039'},
        {'code': 'NGA', 'at': 'Nigeria: 63 percent', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC039', 'events': [
            {'kind': 'poll', 'at': '63 percent. Niger', 'snap': 'sixty', 'big': '63%', **POLL_GREEN}]},
        {'code': 'NER', 'at': 'Niger, grey, but', 'reaction': 'awkward', 'tag': 'No alliance', 'scene': 'SC040', 'events': [
            {'kind': 'stamp', 'at': 'withdrew from its bases', 'text': 'US TROOPS LEFT', 'sub': 'WITHDRAWAL · 2024', 'color': '#5f6873', 'end_at': 'Chad, grey. On'}]},
        {'code': 'TCD', 'at': 'Chad, grey. On', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC040'},
    ],
    'end_after': 'On we go.',
}
# Region plan R08 (scenes SC041-SC043). Ends after "Uganda and Rwanda, grey."; "DR Congo" opens R09.
R08 = {
    'id': 'R08', 'name': 'Central & East Africa', 'scenes': 'SC041-SC043',
    'shots': [
        {'ids': ['CMR', 'GAB', 'COG'], 'arrive_at': 'Cameroon, Gabon'},
        {'ids': ['CAF', 'SDN'], 'arrive_at': 'The Central African Republic'},
        {'ids': ['ERI', 'ETH', 'SOM'], 'arrive_at': 'Eritrea, Ethiopia'},
        {'ids': ['KEN', 'SSD', 'UGA', 'RWA'], 'arrive_at': 'Kenya, green handshake'},
    ],
    'stops': [
        {'code': 'CMR', 'at': 'Cameroon, Gabon', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC041'},
        {'code': 'GAB', 'at': 'Gabon, Republic', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC041'},
        {'code': 'COG', 'at': 'Republic of the Congo: grey', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC041', 'short': 'Rep. of the Congo'},
        {'code': 'CAF', 'at': 'Central African Republic, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC041', 'short': 'C. African Rep.', 'events': [
            {'kind': 'sanction', 'at': 'a US sanctions program. Sudan', 'text': 'US SANCTIONS PROGRAM', 'end_at': 'Sudan, yellow, the'}]},
        {'code': 'SDN', 'at': 'Sudan, yellow, the', 'reaction': 'shocked', 'tag': 'Embassy closed', 'scene': 'SC041', 'events': [
            {'kind': 'history', 'at': 'closed during the 2023', 'text': 'EMBASSY CLOSED · 2023 WAR'}]},
        {'code': 'ERI', 'at': 'Eritrea, Ethiopia', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC042'},
        {'code': 'ETH', 'at': 'Ethiopia, grey. Somalia', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC042'},
        {'code': 'SOM', 'at': 'Somalia, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC042', 'events': [
            {'kind': 'sanction', 'at': 'a US sanctions program, and', 'text': 'US SANCTIONS PROGRAM', 'end_at': 'and US troops fought'},
            {'kind': 'history', 'at': 'fought in Mogadishu', 'text': 'MOGADISHU 1993'}]},
        {'code': 'KEN', 'at': 'Kenya, green handshake', 'reaction': 'happy', 'tag': 'MNNA 2024', 'scene': 'SC043', 'events': [
            # the voice says "62 percent" (Parakeet and Whisper), the verified Pew figure is 63 -> no poll chip here
            {'kind': 'stamp', 'at': 'ally since 2024', 'text': 'NEW HANDSHAKE', 'sub': 'MAJOR NON-NATO ALLY · 2024', 'color': '#1d8a4a', 'side': -1, 'end_at': 'South Sudan, yellow'}]},
        {'code': 'SSD', 'at': 'South Sudan, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC043', 'events': [
            {'kind': 'sanction', 'at': 'sanctions. Uganda', 'text': 'US SANCTIONS'}]},
        {'code': 'UGA', 'at': 'Uganda and Rwanda', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC043'},
        {'code': 'RWA', 'at': 'Rwanda, grey', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC043'},
    ],
    'end_after': 'Uganda and Rwanda, grey.',
}
# Region plan R09 (scenes SC044-SC046). Ends after "one ocean ahead."; the Indian Ocean flight opens R10.
R09 = {
    'id': 'R09', 'name': 'Southern Africa', 'scenes': 'SC044-SC046',
    'shots': [
        {'ids': ['COD'], 'arrive_at': 'DR Congo, yellow'},
        {'ids': ['AGO', 'NAM', 'BWA'], 'arrive_at': 'Angola, Namibia'},
        {'ids': ['ZAF'], 'arrive_at': 'South Africa, yellow. Washington'},
        {'ids': ['ZWE', 'ZMB', 'MWI', 'TZA', 'MOZ', 'MDG'], 'arrive_at': 'Zimbabwe, Zambia'},
    ],
    'stops': [
        {'code': 'COD', 'at': 'DR Congo, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC044', 'events': [
            {'kind': 'sanction', 'at': 'sanctions. Angola', 'text': 'US SANCTIONS'}]},
        {'code': 'AGO', 'at': 'Angola, Namibia', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC044'},
        {'code': 'NAM', 'at': 'Namibia, Botswana', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC044'},
        {'code': 'BWA', 'at': 'Botswana, grey', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC044'},
        {'code': 'ZAF', 'at': 'South Africa, yellow. Washington', 'reaction': 'disappointed', 'tag': 'G20 dispute', 'scene': 'SC045', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'skipped the G20', 'year': '2025', 'label': 'US SKIPS G20 IN SOUTH AFRICA', **RED},
                {'at': "wouldn't invite", 'year': '2026', 'label': 'NOT INVITED TO US G20', **RED}]},
            {'kind': 'poll', 'at': '35 percent. Zimbabwe', 'big': '35%', **POLL_GREY}]},
        {'code': 'ZWE', 'at': 'Zimbabwe, Zambia', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC046'},
        {'code': 'ZMB', 'at': 'Zambia, Malawi', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC046'},
        {'code': 'MWI', 'at': 'Malawi, Tanzania', 'reaction': 'wink', 'tag': 'No alliance', 'scene': 'SC046'},
        {'code': 'TZA', 'at': 'Tanzania, Mozambique', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC046'},
        {'code': 'MOZ', 'at': 'Mozambique, and finally', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC046'},
        {'code': 'MDG', 'at': 'Madagascar. Six grey', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC046'},
    ],
    'end_after': 'one ocean ahead.',
}
# Region plan R10 (scenes SC047-SC053). Opens with 1.0 s inserted silence for the Indian Ocean flight; ends after
# "of any country surveyed."; "China." opens R11.
R10 = {
    'id': 'R10', 'name': 'South & Southeast Asia', 'scenes': 'SC047-SC053',
    'shots': [
        {'ids': ['LKA'], 'arrive_at': 'Sri Lanka, grey', 'minfly': 2.3, 'dip': 0.45},
        {'ids': ['IND'], 'arrive_at': 'India, green handshake'},
        {'ids': ['PAK'], 'arrive_at': 'Pakistan: a green'},
        {'ids': ['NPL', 'BTN'], 'arrive_at': 'Nepal, grey. And'},
        {'ids': ['BGD', 'MMR'], 'arrive_at': 'Bangladesh, grey'},
        {'ids': ['THA', 'LAO', 'KHM', 'VNM'], 'arrive_at': 'Thailand, blue shield'},
        {'ids': ['MYS', 'SGP', 'IDN'], 'arrive_at': 'Malaysia, 19 percent'},
        {'ids': ['PHL'], 'arrive_at': 'The Philippines. They'},
    ],
    'stops': [
        {'code': 'LKA', 'at': 'Sri Lanka, grey', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC047', 'events': [
            {'kind': 'poll', 'at': '42 percent. India', 'snap': 'forty', 'big': '42%', **POLL_GREY}]},
        {'code': 'IND', 'at': 'India, green handshake', 'reaction': 'happy', 'tag': 'Major Defense Partner', 'scene': 'SC047', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '2025 US tariffs', 'year': '2025', 'label': 'US TARIFFS HIT 50%', **RED},
                {'at': 'February 2026 a deal', 'year': 'FEB 2026', 'label': 'DEAL CUTS THEM TO 18%', **GREEN}]},
            {'kind': 'poll', 'at': 'the US 45, China', 'big': '45%', **POLL_GREY, 'rival': {'at': 'China 23', 'text': 'CHINA 23%'}}]},
        {'code': 'PAK', 'at': 'Pakistan: a green', 'reaction': 'awkward', 'tag': 'MNNA 2004', 'scene': 'SC048', 'events': [
            {'kind': 'poll', 'at': 'only 15 percent', 'big': '15%', 'rival': {'at': 'China at 90', 'text': 'CHINA 90%'}},
            {'kind': 'sticker', 'at': 'Paper friends', 'text': 'PAPER FRIENDS', 'dx': 0, 'dy': 230}]},
        {'code': 'NPL', 'at': 'Nepal, grey. And', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC049'},
        {'code': 'BTN', 'at': 'Bhutan and the United', 'reaction': 'chill', 'tag': 'No formal ties', 'scene': 'SC049', 'events': [
            {'kind': 'stamp', 'at': 'never had formal', 'text': 'NEVER', 'sub': 'NO FORMAL TIES · NO EMBASSY', 'color': '#5f6873', 'end_at': 'Not hate. Just'},
            {'kind': 'sticker', 'at': 'Not hate. Just', 'text': 'JUST NEVER'}]},
        {'code': 'BGD', 'at': 'Bangladesh, grey', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC050', 'events': [
            {'kind': 'poll', 'at': '26 percent. Myanmar', 'snap': 'twenty-six', 'big': '26%', 'end_at': 'Myanmar, yellow'}]},
        {'code': 'MMR', 'at': 'Myanmar, yellow', 'reaction': 'nervous', 'tag': 'US sanctions', 'scene': 'SC050', 'events': [
            {'kind': 'sanction', 'at': 'under a US sanctions', 'text': 'US SANCTIONS PROGRAM'}]},
        {'code': 'THA', 'at': 'Thailand, blue shield', 'reaction': 'calm', 'tag': 'Treaty 1954', 'scene': 'SC051', 'events': [
            {'kind': 'poll', 'at': '36 percent. Laos', 'big': '36%', **POLL_GREY, 'end_at': 'Laos, grey, and'}]},
        {'code': 'LAO', 'at': 'Laos, grey, and', 'reaction': 'shocked', 'tag': 'No alliance', 'scene': 'SC051', 'events': [
            {'kind': 'stamp', 'at': 'the most heavily bombed', 'text': 'MOST BOMBED', 'sub': 'PER PERSON, IN HISTORY', 'end_at': 'from US bombing between'},
            {'kind': 'history', 'at': 'from US bombing between', 'text': 'US BOMBING 1964-1973', 'end_at': 'Cambodia, grey. And'}]},
        {'code': 'KHM', 'at': 'Cambodia, grey. And', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC051'},
        {'code': 'VNM', 'at': 'Vietnam: a war', 'reaction': 'happy', 'tag': 'Strategic partner', 'scene': 'SC051', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'a war enemy', 'year': 'WAR', 'label': 'ENEMY FOR YEARS', **RED},
                {'at': 'since 2023 a comprehensive', 'year': '2023', 'label': 'COMPREHENSIVE STRATEGIC PARTNER', **GREEN}]}]},
        {'code': 'MYS', 'at': 'Malaysia, 19 percent', 'reaction': 'awkward', 'tag': 'No alliance', 'scene': 'SC052', 'events': [
            {'kind': 'poll', 'at': '19 percent. Singapore', 'big': '19%', 'side': -1, 'end_at': 'Indonesia, 29'}]},
        {'code': 'SGP', 'at': 'Singapore, 34', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC052', 'events': [
            {'kind': 'poll', 'at': '34. Indonesia', 'big': '34%', 'end_at': 'Indonesia, 29'}]},
        {'code': 'IDN', 'at': 'Indonesia, 29', 'reaction': 'awkward', 'tag': 'No alliance', 'scene': 'SC052', 'events': [
            {'kind': 'poll', 'at': '29. All grey', 'big': '29%'},
            {'kind': 'sticker', 'at': 'China scores far higher', 'text': 'CHINA HIGHER', 'dx': 0, 'dy': 230}]},
        {'code': 'PHL', 'at': 'The Philippines. They', 'reaction': 'happy', 'tag': 'Treaty 1951', 'scene': 'SC053', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '1899 to 1902', 'year': '1899-1902', 'label': 'WAR WITH THE US', **RED},
                {'at': 'since 1951, 56', 'year': '1951', 'label': 'DEFENSE TREATY'}]},
            {'kind': 'poll', 'at': '56 percent favorable', 'big': '56%', **POLL_GREEN, 'side': -1},
            {'kind': 'stamp', 'at': 'the highest confidence', 'text': 'TOP CONFIDENCE', 'sub': 'IN THE US PRESIDENT', 'color': '#2F6FE0'}]},
    ],
    'end_after': 'of any country surveyed.',
}
# Region plan R11 (scenes SC054-SC060): East Asia, Oceania, then the final count and the two maps. Ends with the episode.
R11 = {
    'id': 'R11', 'name': 'East Asia & Oceania', 'scenes': 'SC054-SC060',
    'shots': [
        {'ids': ['CHN'], 'arrive_at': 'China. Yellow'},
        {'ids': ['MNG'], 'arrive_at': 'Mongolia, grey. North'},
        {'ids': ['PRK'], 'arrive_at': 'North Korea, red swords'},
        {'ids': ['KOR', 'JPN'], 'arrive_at': 'South Korea, blue shield'},
        {'ids': ['PNG', 'SLB'], 'arrive_at': 'Papua New Guinea', 'minfly': 1.6, 'dip': 0.35},
        {'ids': ['AUS'], 'arrive_at': 'Australia, blue shield'},
        {'ids': ['NZL'], 'arrive_at': 'New Zealand, green'},
        {'ids': ['FJI'], 'arrive_at': 'Fiji, grey, our'},
    ],
    'stops': [
        {'code': 'CHN', 'at': 'China. Yellow', 'reaction': 'awkward', 'tag': 'US sanctions', 'scene': 'SC054', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'sanctions on Chinese military', 'year': 'SANCTIONS', 'label': 'MILITARY COMPANIES', **RED},
                {'at': 'a tariff war', 'year': 'TARIFFS', 'label': 'TRADE WAR', **RED},
                {'at': 'Korean War Chinese troops', 'year': '1950-53', 'label': 'KOREAN WAR', **RED},
                {'at': 'September 2026 Xi', 'year': 'SEP 2026', 'label': 'STATE DINNER', **GREEN},
                {'at': 'extended to January', 'year': 'TRUCE', 'label': 'EXTENDED TO JANUARY', **GREEN}]},
            {'kind': 'sticker', 'at': 'Rivals with a dinner', 'text': 'DINNER RIVALS', 'dx': 0, 'dy': 230}]},
        {'code': 'MNG', 'at': 'Mongolia, grey. North', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC055'},
        {'code': 'PRK', 'at': 'North Korea, red swords', 'reaction': 'angry', 'tag': 'Never recognized', 'scene': 'SC055', 'events': [
            {'kind': 'stamp', 'at': 'never recognized it', 'text': 'NEVER RECOGNIZED', 'sub': 'NO EMBASSY · NO AMBASSADOR', 'side': -1, 'end_at': 'Trump and Kim met'},
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': '1950 to 1953', 'year': '1950-1953', 'label': 'KOREAN WAR', **RED},
                {'at': 'met three times', 'year': '2018-2019', 'label': 'TRUMP-KIM: 3 MEETINGS'},
                {'at': 'another meeting is coming', 'year': 'NEXT?', 'label': 'ANOTHER MEETING PROMISED'}]},
            {'kind': 'sticker', 'at': 'Still no embassy', 'text': 'NO EMBASSY', 'dx': 0, 'dy': 230}]},
        {'code': 'KOR', 'at': 'South Korea, blue shield', 'reaction': 'happy', 'tag': 'Treaty 1953', 'scene': 'SC056', 'events': [
            {'kind': 'poll', 'at': '45 percent. Japan', 'big': '45%', **POLL_GREY, 'side': -1, 'end_at': 'Japan gave the US'}]},
        {'code': 'JPN', 'at': 'Japan: an enemy', 'reaction': 'happy', 'tag': 'Treaty 1951', 'scene': 'SC056', 'events': [
            {'kind': 'timeline', 'fit': True, 'steps': [
                {'at': 'enemy in World War', 'year': 'WWII', 'label': 'ENEMY', **RED},
                {'at': 'now a treaty ally', 'year': 'NOW', 'label': 'TREATY ALLY', 'c1': '#79a8ff', 'c2': '#2F6FE0', 'ink': '#ffffff'}]},
            {'kind': 'poll', 'at': 'the US 50 percent', 'snap': 'fifty', 'big': '50%', **POLL_GREEN, 'sub': '2ND-BIGGEST GAP', 'rival': {'at': 'China just 11', 'text': 'CHINA 11%'}}]},
        {'code': 'PNG', 'at': 'Papua New Guinea', 'reaction': 'calm', 'tag': 'No alliance', 'scene': 'SC057', 'short': 'Papua New Guinea'},
        {'code': 'SLB', 'at': 'Solomon Islands, grey', 'reaction': 'chill', 'tag': 'No alliance', 'scene': 'SC057'},
        {'code': 'AUS', 'at': 'Australia, blue shield', 'reaction': 'disappointed', 'tag': 'ANZUS 1951', 'scene': 'SC057', 'events': [
            {'kind': 'poll', 'at': 'just 24 percent', 'big': '24%', 'sub': 'LOW FOR AN ALLY'}]},
        {'code': 'NZL', 'at': 'New Zealand, green', 'reaction': 'happy', 'tag': 'MNNA 1996', 'scene': 'SC058'},
        {'code': 'FJI', 'at': 'Fiji, grey, our', 'reaction': 'happy', 'tag': 'No alliance', 'scene': 'SC058', 'forceMicro': True},
    ],
    'outro': {
        'start': 'So, the final count', 'total': '156 countries. 36',
        'rows': [['ALLY', '36 treaty allies'], ['PARTNER', '18 major partners'], ['NORMAL', '79 normal relationships'],
                 ['FRICTION', '18 with sanctions'], ['HOSTILE', ['4 with red swords', 'four']], ['NOTIES', 'Plus one friendly']],
        'red': [['CUB', 'Cuba, Afghanistan'], ['AFG', 'Afghanistan, Iran'], ['IRN', 'Iran and North'], ['PRK', 'North Korea. Plus']],
        'never': [['BTN', 'one friendly country']],
        'twist': 'The real twist?', 'left': 'Love on paper', 'right': 'love in the polls', 'maps': 'two different maps',
        'tur': 'Turkey is a NATO', 'tur13': '13 percent, while', 'gha': 'Ghana has no alliance', 'gha68': 'gives 68', 'question': 'Which number surprised',
    },
    'end_after': 'Which number surprised you most?',
}
PLANS = [R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11]

norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def load_words():
    # word times of the source WAV, moved onto the edited timeline (inserted silences, sync/audio_edits.json)
    sys.path.insert(0, HERE); from audio_edit import src2edit
    W = json.load(open(os.path.join(PROJ, 'sync', 'script_words.json')))  # [{w, start, end, i}] script order
    for w in W:
        w['src_start'], w['src_end'] = w['start'], w['end']; w['start'], w['end'] = round(src2edit(w['start']), 3), round(src2edit(w['end']), 3)
    return W


def finder(words):
    toks = [norm(x['w']) for x in words]
    cursor = [0]

    def find(phrase, from_cursor=True):
        q = [norm(x) for x in phrase.split() if norm(x)]
        for i in range(cursor[0] if from_cursor else 0, len(toks) - len(q) + 1):
            if toks[i:i + len(q)] == q:
                return i
        raise KeyError(phrase)
    return find, cursor


def snap(word, near_src):
    from audio_edit import src2edit
    A = json.load(open(os.path.join(PROJ, 'sync', 'parakeet_words.json')))['words']
    c = [w for w in A if norm(w['w']) == norm(word) and abs(w['start'] - near_src) < 1.5]
    w = min(c, key=lambda w: abs(w['start'] - near_src))
    return src2edit(w['start']), src2edit(w['end'])


OUTRO = {}


def main():
    words = load_words()
    find, cursor = finder(words)
    reg = {r['code']: r for r in csv.DictReader(open(os.path.join(ROOT, 'countries.csv')))}
    rows = []
    # intro: the two sentences of paragraph 1
    i_s1_end = find('hate it?') + 2
    i_s2 = i_s1_end
    i_s2_end = find('in Canada.') + 2
    intro = {'s1': [words[0]['start'], words[i_s1_end - 1]['end']], 's2': [words[i_s2]['start'], words[i_s2_end - 1]['end']]}
    rows.append(['R01', 'intro-1', '', words[0]['w'] + ' .. ' + words[i_s1_end - 1]['w'], intro['s1'][0], intro['s1'][1], 'title + theme emblem', 0.0])
    rows.append(['R01', 'intro-2', 'CAN', 'Let\'s .. Canada.', intro['s2'][0], intro['s2'][1], 'fly-in, arrive Canada', None])

    stops, shots, regions = [], [], []
    n0 = 0
    for plan in PLANS:
        rid, t_reg0 = plan['id'], n0 / FPS
        r_stops, r_shots = [], []
        for st in plan['stops']:
            i = find(st['at']); cursor[0] = i
            num, flag = ISO[st['code']]
            r = reg[st['code']]
            w0 = words[i]
            stop = {**({'flagFit': st['flagFit']} if 'flagFit' in st else {}), **({'forceMicro': True} if st.get('forceMicro') else {}), **({'short': st['short']} if 'short' in st else {}), 'code': st['code'], 'id': num, 'flag': flag, 'name': r['name'], 'status': r['status'], 'tag': st['tag'],
                    'reaction': st['reaction'], 'scene': st['scene'], 'region': rid, 'wordT': round(w0['start'], 3), 'events': []}
            for ev in st.get('events', []):
                e = {k: v for k, v in ev.items() if k not in ('at', 'steps', 'rival', 'end_at')}
                if 'at' in ev:
                    j = find(ev['at']); t0, t1 = words[j]['start'], words[j]['end']
                    if 'snap' in ev:
                        t0, t1 = snap(ev['snap'], words[j]['src_start'])
                    e['t'] = round(t0, 3)
                    rows.append([rid, st['scene'], st['code'], ev['at'], t0, t1, ev['kind'] + ' chip', e['t']])
                if 'end_at' in ev:   # leave the screen when the voice moves on to the next fact
                    e['end'] = round(words[find(ev['end_at'])]['start'] - 0.1, 3)
                if 'rival' in ev:
                    j = find(ev['rival']['at']); e['rival'] = {'t': round(words[j]['start'], 3), 'text': ev['rival']['text']}
                    rows.append([rid, st['scene'], st['code'], ev['rival']['at'], words[j]['start'], words[j]['end'], 'rival chip', e['rival']['t']])
                if 'steps' in ev:
                    e['steps'] = []
                    for sp in ev['steps']:
                        j = find(sp['at']); d = {k: v for k, v in sp.items() if k != 'at'}; d['t'] = round(words[j]['start'], 3)
                        e['steps'].append(d)
                        rows.append([rid, st['scene'], st['code'], sp['at'], words[j]['start'], words[j]['end'], 'timeline ' + sp['year'], d['t']])
                    e['t'] = e['steps'][0]['t']
                stop['events'].append(e)
            r_stops.append(stop)

        # shots: arrive just before the line about them starts; fly as soon as the previous line has ended
        cursor[0] = next(i for i, w in enumerate(words) if w['start'] >= t_reg0 - 0.01)
        for k, sh in enumerate(plan['shots']):
            j = find(sh['arrive_at']); cursor[0] = j
            line_t = words[j]['start']
            if sh.get('first'):
                fly, arrive = intro['s2'][0] + 0.35, line_t - 0.05   # parallel to sentence 2, on Canada by its end
            else:
                # fly as soon as the previous line has ended (never while it is still about the old place) and never
                # before this region's first frame: the flight into a region belongs to that region
                prev_end = words[j - 1]['end']
                fly = max(prev_end - 0.02, line_t - 1.6, t_reg0)
                if 'fly_at' in sh:   # take off on an earlier phrase that already leads to the place ("the biggest country")
                    fly = max(words[find(sh['fly_at'], from_cursor=False)]['start'], t_reg0)
                arrive = max(line_t + 0.05, fly + sh.get('minfly', 0.9))   # long hops (an ocean) get a longer flight
            ids = [ISO[c][0] for c in sh['ids']]
            r_shots.append({'ids': ids, 'codes': sh['ids'], 'region': rid, 'flyStart': round(fly, 3), 'arrive': round(arrive, 3),
                            **{k: sh[k] for k in ('zmax', 'span', 'wFrac', 'pad', 'dip', 'box') if k in sh}})
        if 'outro' in plan:   # final count + two maps: whole world, then the split screen (times from the words)
            O = plan['outro']; at = lambda ph: words[find(ph)]['start']
            def at_snap(spec):
                if isinstance(spec, list):
                    j = find(spec[0]); return snap(spec[1], words[j]['src_start'])[0]
                return at(spec)
            out = {'t0': round(at(O['start']), 3)}
            cursor[0] = find(O['start'])
            out['total'] = round(at(O['total']), 3)
            out['rows'] = [{'status': k, 't': round(at_snap(ph), 3)} for k, ph in O['rows']]
            cursor[0] = find(O['start'])
            out['red'] = [{'id': ISO[c][0], 'name': reg[c]['name'], 't': round(at(ph), 3), **({'dy': 50} if c == 'IRN' else {})} for c, ph in O['red']]   # Iran's pin below, Afghanistan's above
            out['never'] = [{'id': ISO[c][0], 'name': reg[c]['name'], 't': round(at(ph), 3)} for c, ph in O['never']]
            for k in ('twist', 'left', 'right', 'maps', 'tur', 'tur13', 'gha', 'gha68', 'question'):
                out[k] = round(at(O[k]), 3)
            out['turkey'], out['ghana'] = ISO['TUR'][0], ISO['GHA'][0]
            out['polls'] = [{'id': ISO[c][0], 'v': int(r['pew_us'])} for c, r in reg.items() if r['pew_us']]
            r_shots.append({'ids': [], 'codes': [], 'region': rid, 'overview': True, 'flyStart': out['t0'], 'arrive': round(out['t0'] + 2.2, 3)})
            for r in [['outro', 'final count'], *[[x['status'], 'count row'] for x in out['rows']]]:
                pass
            rows.append([rid, 'SC059', '', O['start'], out['t0'], None, 'camera pulls out to the whole world', out['t0']])
            rows.append([rid, 'SC059', '', O['total'], out['total'], None, 'scoreboard: 156 countries', out['total']])
            for (k, ph), x in zip(O['rows'], out['rows']):
                rows.append([rid, 'SC059', '', ph if isinstance(ph, str) else ph[0], x['t'], None, 'scoreboard row ' + k, x['t']])
            for (c, ph), x in zip(O['red'], out['red']):
                rows.append([rid, 'SC059', c, ph, x['t'], None, 'red pulse', x['t']])
            rows.append([rid, 'SC059', 'BTN', O['never'][0][1], out['never'][0]['t'], None, 'white glow', out['never'][0]['t']])
            for k, ev in (('left', 'split: alliance map'), ('right', 'split: poll map'), ('maps', 'title: two different maps'), ('tur', 'Turkey: NATO ally'),
                          ('tur13', 'Turkey: 13%'), ('gha', 'Ghana: no alliance'), ('gha68', 'Ghana: 68%'), ('question', 'question card')):
                rows.append([rid, 'SC060', '', O[k], out[k], None, ev, out[k]])
            OUTRO.update(out)
        # base activation: as the camera approaches (never later than the spoken name)
        for stop in r_stops:
            sh = next(s for s in r_shots if stop['id'] in s['ids'])
            if stop['id'] == sh['ids'][0]:   # first country of a shot: reveal while the camera is still arriving
                stop['activate'] = round(max(sh['flyStart'] + 0.3, min(stop['wordT'], sh['arrive'] - 0.3)), 3)
            else:                            # the others: on their spoken name
                stop['activate'] = round(stop['wordT'] - 0.08, 3)
            rows.append([rid, stop['scene'], stop['code'], stop['name'], stop['wordT'], None, 'fill+glow+face+status', stop['activate']])

        # region boundary: after the closing sentence and its natural tail, before the next line
        q = plan['end_after'].split()
        k = find(plan['end_after']); last = k + len(q) - 1
        cursor[0] = last + 1
        end_word = words[last]
        nxt = words[last + 1] if last + 1 < len(words) else None
        # chosen on the SOURCE audio (so inserted silence never moves an already delivered cut), then mapped
        tail_src = end_word['src_end'] + 0.35
        if nxt:
            tail_src = min(tail_src, (end_word['src_end'] + nxt['src_start']) / 2)
        else:   # the last region never runs past the end of the recording
            import wave
            wv = wave.open(os.path.join(PROJ, 'audio', 'voice_en_source.wav')); tail_src = min(tail_src, wv.getnframes() / wv.getframerate())
            tail_src = int(tail_src * FPS) / FPS
        from audio_edit import src2edit_before
        n_end = int(round(src2edit_before(round(tail_src * FPS) / FPS) * FPS))
        region = {'id': rid, 'name': plan['name'], 'scenes': plan['scenes'], 'n0': n0, 'n1': n_end,
                  't0': n0 / FPS, 't1': n_end / FPS, 'countries': len(r_stops), 'lastWord': end_word, 'nextWord': nxt}
        regions.append(region); stops += r_stops; shots += r_shots
        json.dump({'region': region, 'shots': r_shots}, open(os.path.join(PROJ, 'sync', 'region_%s.json' % rid), 'w'), indent=1)
        print(rid, 'stops', len(r_stops), 'shots', len(r_shots), 'frames [%d, %d)' % (n0, n_end), 'len %.3f s' % ((n_end - n0) / FPS))
        n0 = n_end

    ep = {
        'title': 'Countries That LOVE vs HATE the USA', 'size': [1920, 1080], 'fps': FPS, 'seed': 20261024,
        'totalCountries': 156, 'duration': n0 / FPS,
        'audio': {'file': 'audio/voice_en_edited.wav', 'preview': 'audio/voice_en_edited.wav', 'source': 'audio/voice_en_source.wav', 'sampleRate': 24000},
        'intro': intro, 'subject': {'id': '840', 'flag': 'us'},
        'statuses': STATUSES, 'shots': shots, 'stops': stops, 'regions': regions,
        'techChecks': TECH, **({'outro': OUTRO} if OUTRO else {}),
    }
    js = ('// GENERATED by tools/build_episode.py from countries.csv + the real WAV word timestamps. Edit the plan there.\n'
          'window.EPISODE = ' + json.dumps(ep, ensure_ascii=False, indent=1) + ';\n')
    open(os.path.join(PROJ, 'data', 'episode.js'), 'w').write(js)
    # keep the check results already written for rows whose timing did not change
    tbl = os.path.join(PROJ, 'sync', 'sync_table.csv')
    old = {}
    if os.path.exists(tbl):
        for r in csv.DictReader(open(tbl)):
            old[(r['scene'], r['country'], r['line_or_keyword'], r['map_event'], r['map_frame'])] = r.get('check', '')
    with open(tbl, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['region', 'scene', 'country', 'line_or_keyword', 'audio_start_s', 'audio_end_s', 'map_event', 'map_event_s', 'map_frame', 'check'])
        for r in rows:
            fr = '' if r[7] is None else int(round(r[7] * FPS))
            w.writerow([r[0], r[1], r[2], r[3], '' if r[4] is None else round(r[4], 3), '' if r[5] is None else round(r[5], 3), r[6],
                        '' if r[7] is None else round(r[7], 3), fr, old.get((r[1], r[2], r[3], r[6], str(fr)), '')])


STATUSES = {
    "ALLY": {"label": "TREATY ALLY", "color": "#2F6FE0", "dark": "#1b47a6", "icon": "shield"},
    "PARTNER": {"label": "MAJOR PARTNER", "color": "#2FA05A", "dark": "#1d7240", "icon": "handshake"},
    "NORMAL": {"label": "NORMAL TIES", "color": "#8C96A3", "dark": "#5f6873", "icon": "dot"},
    "FRICTION": {"label": "SANCTIONS / CRISIS", "color": "#F2B705", "dark": "#b58700", "icon": "bolt"},
    "HOSTILE": {"label": "HOSTILE", "color": "#E0283B", "dark": "#9c1424", "icon": "swords"},
    "NOTIES": {"label": "NEVER FORMAL TIES", "color": "#B9C2CC", "dark": "#7d8794", "icon": "dotted"},
}
TECH = [
    {"kind": "longname", "id": "140", "flag": "cf", "name": "Central African Republic", "status": "FRICTION", "tag": "US sanctions program"},
    {"kind": "micro", "id": "780", "flag": "tt", "name": "Trinidad and Tobago", "status": "NORMAL", "tag": "No alliance", "faceBacking": True},
    {"kind": "enclave", "id": "710", "flag": "za", "name": "South Africa", "status": "FRICTION", "tag": "G20 exclusion 2025-26"},
    {"kind": "complexflag", "id": "070", "flag": "ba", "name": "Bosnia and Herzegovina", "status": "NORMAL", "tag": "No alliance"},
]

if __name__ == '__main__':
    main()
