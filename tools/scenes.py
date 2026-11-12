"""Script, scenes, voice files and number check. Rerun: python3 tools/scenes.py"""
import csv, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = {c['code']: c for c in csv.DictReader(open(os.path.join(ROOT, 'countries.csv')))}
F = list(csv.DictReader(open(os.path.join(ROOT, 'facts.csv'))))
N = {k: sum(1 for c in C.values() if c['status'] == k) for k in ('MAGNET', 'PULL', 'STAY', 'LEAVE', 'EXIT', 'LOCKED')}

# (scene_id, region, codes counted in this scene, EN, RU, caption, reveal word, flight_pause_s before scene)
S = [
('SC01','R01',['CAN'],
 "If you could move to any country tomorrow, would you leave yours? Let's find out where people want out and where they want in, starting with the biggest magnet on the planet, Canada.",
 "Если бы завтра можно было переехать в любую страну, уехал бы ты из своей? Давай узнаем, откуда люди хотят уехать и куда хотят переехать, и начнём с самого сильного магнита на планете, Канады.",
 'Countries People Want to LEAVE vs MOVE TO','Canada',0),
('SC02','R01',[],
 "Green magnet, instantly. Gallup compares how many people want to move in with how many want to move out, and Canada scores plus 225 percent. In theory, its adult population would more than triple. Bring a warm coat.",
 "Зелёный магнит сразу. Gallup сравнивает, сколько людей хотят сюда переехать и сколько хотят уехать, и у Канады плюс 225 процентов. В теории её взрослое население выросло бы больше чем втрое. Берите тёплую куртку.",
 'PNMI +225% (Gallup 2023-2025)','225',0),
('SC03','R01',['USA'],
 "Right below, the USA, still the world's number one dream. 15 percent of everyone who wants to emigrate picks America first. But that's the lowest share in nearly two decades, and one in five Americans now say they'd like to leave themselves.",
 "Прямо под ней США, всё ещё мечта номер один в мире. 15 процентов всех, кто хочет эмигрировать, первым выбирают Америку. Но это самая низкая доля почти за двадцать лет, и каждый пятый американец теперь сам говорит, что хотел бы уехать.",
 "#1 dream: 15% of would-be migrants | 20% of Americans want to leave",'fifteen',0),
('SC04','R01',['MEX','GTM','BLZ','HND','SLV','NIC'],
 "Now south, where the arrows flip. Mexico, 20 percent want out. Guatemala, 32. Belize is a quiet exception: by UN estimates more people arrive than leave. Then Honduras, the hot spot. Half of all adults wanted to leave in 2023, though by 2025 that fell to 35. Next door, El Salvador at 34, and Nicaragua at 19.",
 "Теперь на юг, где стрелки разворачиваются. Мексика, 20 процентов хотят уехать. Гватемала, 32. Белиз тихое исключение: по оценке ООН приезжает больше людей, чем уезжает. Дальше Гондурас, горячая точка. В 2023 году уехать хотела половина взрослых, хотя к 2025 году доля упала до 35. По соседству Сальвадор, 34, и Никарагуа, 19.",
 'Honduras 50% (2023) -> 35% (2025)','Half',0),
('SC05','R01',['CRI','PAN','JAM','CUB','BHS'],
 "Costa Rica, 30. Panama, 21. Even the canal can't keep everyone. Into the Caribbean: Jamaica loses more people than it gains. Cuba is the big one. In an independent 2023 poll, more than half said they want to leave the island, and the US now partially suspends visas for Cubans. The Bahamas? Sun, sea, and most people staying put.",
 "Коста-Рика, 30. Панама, 21. Даже канал не всех удерживает. В Карибское море: Ямайка теряет больше людей, чем получает. Куба самый громкий случай. В независимом опросе 2023 года больше половины сказали, что хотят уехать с острова, а США теперь частично приостановили визы для кубинцев. Багамы? Солнце, море, и большинство остаётся дома.",
 'Cuba: independent poll 2023 | US partial entry ban','more than half',0),
('SC06','R01',['HTI','DOM','TTO'],
 "Haiti is where wanting and leaving collide. In Gallup's 2015 to 2017 survey, 63 percent wanted out, and today the US fully suspends entry for Haitians. Wanting to go isn't the same as being let in. Dominican Republic, 46 percent. Trinidad and Tobago, mostly staying.",
 "На Гаити желание и возможность сталкиваются лбами. В опросе Gallup 2015-2017 годов уехать хотели 63 процента, а сегодня США полностью закрыли въезд для гаитян. Хотеть уехать не значит, что тебя впустят. Доминиканская Республика, 46 процентов. Тринидад и Тобаго, в основном остаются.",
 'Haiti 63% (2015-2017) | US full entry ban','63',0),
('SC07','R02',['VEN','COL','ECU','PER','BOL','CHL','ARG','URY','PRY','BRA','SUR','GUY'],
 "Next stop, South America. Venezuela, 27 percent, partly because so many have already gone: the UN estimates it lost about 15 people per thousand every year from 2019 to 2023. Colombia, 36. Ecuador, 49, nearly half. Peru, 42. Bolivia, 36. Down south, Chile 35 and Argentina 34. Uruguay, 25. Paraguay is the calm one, just 17. Brazil, the giant, 23. Suriname, mostly staying. And Guyana, small but losing people fast by UN estimates.",
 "Следующая остановка, Южная Америка. Венесуэла, 27 процентов, отчасти потому что очень многие уже уехали: по оценке ООН она теряла около 15 человек на тысячу каждый год с 2019 по 2023. Колумбия, 36. Эквадор, 49, почти половина. Перу, 42. Боливия, 36. На юге Чили 35 и Аргентина 34. Уругвай, 25. Парагвай самый спокойный, всего 17. Бразилия, гигант, 23. Суринам, в основном остаются. И Гайана, маленькая, но по оценке ООН быстро теряет людей.",
 'Venezuela: -15 per 1,000 a year (UN, 2019-2023)','fifteen',0),
('SC08','R03',['PRT','ESP','FRA','GBR','IRL'],
 "Across the Atlantic, and the map turns green. Portugal, plus 125. Spain, plus 74. France, plus 44. The UK is still a top dream destination, picked by 4 percent of would-be migrants worldwide, even though nearly a quarter of Brits tell one poll they're thinking about moving abroad. Ireland, plus 138, the comeback kid: in 2015 to 2017 it was only plus 48.",
 "Через Атлантику, и карта зеленеет. Португалия, плюс 125. Испания, плюс 74. Франция, плюс 44. Великобритания всё ещё в числе стран мечты, её выбирают 4 процента желающих переехать по всему миру, хотя почти четверть британцев говорят в одном опросе, что думают о переезде за границу. Ирландия, плюс 138, возвращение года: в 2015-2017 было всего плюс 48.",
 'Ireland +48% -> +138%','138',1.2),
('SC09','R03',['ISL','NOR','SWE','FIN','DNK','NLD','BEL','LUX','DEU','CHE','AUT','ITA'],
 "Iceland and Norway, more arrivals than departures by UN estimates. Sweden plus 91, Finland plus 97, Denmark plus 129. Cold winters, warm numbers. The Netherlands plus 43, Belgium plus 48, and tiny Luxembourg, plus 150. Germany, plus 53. Switzerland, more in than out. Austria, plus 83. And Italy, plus 25, when ten years ago it was negative.",
 "Исландия и Норвегия, по оценке ООН приезжает больше, чем уезжает. Швеция плюс 91, Финляндия плюс 97, Дания плюс 129. Холодные зимы, тёплые цифры. Нидерланды плюс 43, Бельгия плюс 48, и крошечный Люксембург, плюс 150. Германия, плюс 53. Швейцария, приезжающих больше. Австрия, плюс 83. И Италия, плюс 25, хотя десять лет назад была в минусе.",
 'Luxembourg +150%','150',0),
('SC10','R04',['SVN','HRV','BIH','SRB','MNE','ALB','MKD','GRC','BGR'],
 "Next stop, the east, where the green fades. Slovenia plus 8, Croatia plus 7, nearly balanced. Then the Balkans. Bosnia, 38 percent have considered leaving. Serbia and Montenegro, 40 to 50 percent in the Balkan Barometer. Albania was at 60 percent in Gallup's 2015 to 2017 count. North Macedonia, 35. Greece and Bulgaria, almost even.",
 "Следующая остановка, восток, где зелень бледнеет. Словения плюс 8, Хорватия плюс 7, почти баланс. Дальше Балканы. Босния, 38 процентов думали об отъезде. Сербия и Черногория, от 40 до 50 процентов по Балканскому барометру. Албания была на 60 процентах в подсчёте Gallup 2015-2017. Северная Македония, 35. Греция и Болгария, почти ноль.",
 'Balkans: 35-60% considering leaving','Balkans',0),
('SC11','R04',['ROU','HUN','SVK','CZE','POL','LTU','LVA','EST','BLR','MDA','UKR'],
 "Romania, minus 22, and Hungary, minus 24, the lowest score in the EU. Slovakia and Czechia, slightly negative. Poland, minus 5. Lithuania and Latvia, minus 15 each, Estonia minus 6. Belarus and Moldova, losing people by UN estimates. And Ukraine: after years of war, 21 percent say they would leave if the borders fully opened.",
 "Румыния, минус 22, и Венгрия, минус 24, худший показатель в ЕС. Словакия и Чехия, немного в минусе. Польша, минус 5. Литва и Латвия, по минус 15, Эстония минус 6. Беларусь и Молдова, по оценке ООН теряют людей. И Украина: после лет войны 21 процент говорят, что уехали бы, если бы границы полностью открыли.",
 'Hungary -24% (lowest in EU) | Ukraine 21%','24',0),
('SC12','R05',['RUS','GEO','ARM','AZE','KAZ','KGZ','TJK','UZB','TKM','AFG'],
 "Next stop, Russia. Only 9 percent want to move abroad for good, the lowest Levada has ever recorded. Georgia, also 9. Armenia, 22. Azerbaijan, Kazakhstan, Tajikistan and Uzbekistan, roughly balanced by UN estimates. Kyrgyzstan and Turkmenistan, slightly more arrivals. And Afghanistan. After the Taliban returned, 53 percent wanted to leave, a Gallup record. Its passport opens just 22 countries without a visa, the weakest on Earth, and the US has fully banned entry.",
 "Следующая остановка, Россия. Всего 9 процентов хотят уехать за границу навсегда, это минимум за всю историю замеров Левады. Грузия, тоже 9. Армения, 22. Азербайджан, Казахстан, Таджикистан и Узбекистан, по оценке ООН примерно баланс. Кыргызстан и Туркменистан, приезжающих чуть больше. И Афганистан. После возвращения талибов уехать хотели 53 процента, рекорд Gallup. Его паспорт открывает без визы всего 22 страны, самый слабый на Земле, а США полностью запретили въезд.",
 'Afghanistan 53% | passport: 22 countries | US full ban','22',0),
('SC13','R06',['IRN','IRQ','KWT','BHR','QAT','ARE','OMN','YEM','SAU'],
 "Next stop, the Middle East. Iran, a third want to emigrate, and the US travel ban now covers it completely. Iraq, 35 percent. Kuwait, just 16. Then the Gulf flips everything. Bahrain, balanced. Qatar, the UAE and Oman pull people in, and the UAE's net migration is about 20 people per thousand a year. Yemen, war, a weak passport and a full US ban. Saudi Arabia, a top ten dream destination worldwide.",
 "Следующая остановка, Ближний Восток. Иран, треть хотят эмигрировать, и запрет США на въезд теперь распространяется на него полностью. Ирак, 35 процентов. Кувейт, всего 16. А дальше Залив всё переворачивает. Бахрейн, баланс. Катар, ОАЭ и Оман притягивают людей, у ОАЭ чистая миграция около 20 человек на тысячу в год. Йемен, война, слабый паспорт и полный запрет США. Саудовская Аравия, в десятке стран мечты в мире.",
 'UAE: +20 per 1,000 a year (UN)','twenty',0),
('SC14','R06',['JOR','SYR','TUR','CYP','LBN','ISR'],
 "Jordan, 42 percent. Syria, 46 percent in Gallup's 2015 to 2017 count, and its passport opens only 25 doors. Turkey, 39 percent would like to live or study abroad. Cyprus, plus 79. Lebanon, 38. Israel, slightly more arriving than leaving.",
 "Иордания, 42 процента. Сирия, 46 процентов в подсчёте Gallup 2015-2017, и её паспорт открывает всего 25 дверей. Турция, 39 процентов хотели бы жить или учиться за границей. Кипр, плюс 79. Ливан, 38. Израиль, приезжающих немного больше, чем уезжающих.",
 'Syria passport: 25 countries','25',0),
('SC15','R07',['EGY','LBY','TUN','DZA','MAR','MRT'],
 "Next stop, North Africa. Egypt, 13 percent considered leaving. Libya, 20. Tunisia, 46. Algeria, close to balanced. Morocco, 35. Mauritania, 41.",
 "Следующая остановка, Северная Африка. Египет, 13 процентов думали об отъезде. Ливия, 20. Тунис, 46. Алжир, почти баланс. Марокко, 35. Мавритания, 41.",
 '','Tunisia',0),
('SC16','R07',['SEN','GMB','GIN','SLE','LBR','CIV','MLI','BFA'],
 "And now West Africa, the most restless corner of the map. Senegal 42, Gambia 50, Guinea 44. Then Sierra Leone, 75 percent, and Liberia, 76, the highest numbers in this entire video. Three out of four adults would leave if they could, and Sierra Leone is now under a full US entry ban. Ivory Coast, 29. Mali and Burkina Faso, only 12 each, the lowest in Africa.",
 "А теперь Западная Африка, самый беспокойный угол карты. Сенегал 42, Гамбия 50, Гвинея 44. Дальше Сьерра-Леоне, 75 процентов, и Либерия, 76, самые высокие цифры во всём ролике. Трое из четырёх взрослых уехали бы, если бы могли, а Сьерра-Леоне теперь под полным запретом въезда в США. Кот-д'Ивуар, 29. Мали и Буркина-Фасо, всего по 12, минимум в Африке.",
 'Liberia 76% | Sierra Leone 75%','76',0),
('SC17','R07',['GHA','TGO','BEN','NGA','NER','TCD'],
 "Ghana, 65. Togo 45, Benin 32. Nigeria, 51, the biggest country on this map where most people want out. Niger 17, Chad 20.",
 "Гана, 65. Того 45, Бенин 32. Нигерия, 51, самая большая страна на этой карте, где большинство хочет уехать. Нигер 17, Чад 20.",
 'Nigeria 51%','51',0),
('SC18','R08',['CMR','GAB','COG','CAF','SDN','ERI'],
 "Next stop, Central and East Africa. Cameroon, 41. Gabon, 37. Congo, 54. The Central African Republic and Sudan, losing people fast by UN estimates. And Eritrea, the locked door. Most people can't get a passport or an exit visa, and national service is compulsory from 18 to 40. So here we don't mark what people want. We mark that they can't leave.",
 "Следующая остановка, Центральная и Восточная Африка. Камерун, 41. Габон, 37. Конго, 54. ЦАР и Судан, по оценке ООН быстро теряют людей. И Эритрея, запертая дверь. Большинство не может получить паспорт или выездную визу, а нацслужба обязательна с 18 до 40 лет. Поэтому здесь мы отмечаем не желание людей, а то, что уехать они не могут.",
 "Eritrea: CAN'T LEAVE",'locked',0),
('SC19','R08',['ETH','SOM','KEN','SSD','UGA','RWA'],
 "Ethiopia, 31. Somalia, 29. Kenya, 39. South Sudan shows more arrivals than departures by UN estimates. Uganda, 37. Rwanda, close to balanced.",
 "Эфиопия, 31. Сомали, 29. Кения, 39. Южный Судан по оценке ООН показывает больше приезжающих, чем уезжающих. Уганда, 37. Руанда, почти баланс.",
 '','Kenya',0),
('SC20','R09',['COD','AGO','NAM','BWA','ZAF','SWZ','ZWE','ZMB','MWI','TZA','MOZ','MDG'],
 "Next stop, the south. DR Congo, 41. Angola, balanced. Namibia 27, Botswana 30, South Africa 32. Eswatini, 45. Zimbabwe, 33. Zambia, mostly staying. Malawi, 37. Tanzania and Madagascar, only 14 each. Mozambique, 20.",
 "Следующая остановка, юг. ДР Конго, 41. Ангола, баланс. Намибия 27, Ботсвана 30, ЮАР 32. Эсватини, 45. Зимбабве, 33. Замбия, в основном остаются. Малави, 37. Танзания и Мадагаскар, всего по 14. Мозамбик, 20.",
 '','Eswatini',0),
('SC21','R10',['LKA','IND','PAK','NPL','BTN','BGD'],
 "Across the Indian Ocean. Sri Lanka, losing a few people by UN estimates. India: just 4 percent told Gallup International they'd rather live in another country. Pakistan is the twist. By UN estimates it loses people every year, yet in a Gallup Pakistan survey 71 percent said they would never leave, and its passport opens only 29 doors. Nepal and Bangladesh, losing people too, with passports among the ten weakest. Bhutan, balanced.",
 "Через Индийский океан. Шри-Ланка, по оценке ООН немного теряет людей. Индия: всего 4 процента сказали Gallup International, что предпочли бы жить в другой стране. Пакистан с подвохом. По оценке ООН он теряет людей каждый год, но в опросе Gallup Pakistan 71 процент сказали, что никогда не уедут, а его паспорт открывает всего 29 дверей. Непал и Бангладеш тоже теряют людей, и их паспорта в десятке самых слабых. Бутан, баланс.",
 'Pakistan: 71% would never leave | passport: 29','71',1.2),
('SC22','R10',['MMR','THA','LAO','KHM','VNM','MYS','SGP','IDN','PHL'],
 "Myanmar and Laos, both under a full US entry ban. Thailand and Cambodia, mostly staying. Vietnam, only 8 percent. Malaysia, more arrivals. Singapore, slightly more arrivals and the strongest passport on the planet, 192 destinations. Indonesia, staying. And the Philippines, 17 percent dream of living abroad.",
 "Мьянма и Лаос, обе под полным запретом въезда в США. Таиланд и Камбоджа, в основном остаются. Вьетнам, всего 8 процентов. Малайзия, приезжающих больше. Сингапур, приезжающих чуть больше и самый сильный паспорт на планете, 192 направления. Индонезия, остаются. И Филиппины, 17 процентов мечтают жить за границей.",
 'Singapore passport: 192','192',0),
('SC23','R11',['CHN','MNG','PRK','KOR','JPN'],
 "Next stop, East Asia. China, close to balanced by UN estimates. Mongolia, the same. North Korea: no poll, and no way out. Citizens can't leave without state permission, so it gets the lock. South Korea, slightly more arrivals and one of the strongest passports. Japan, 14 percent would rather live elsewhere, with a passport that opens 188 doors.",
 "Следующая остановка, Восточная Азия. Китай, по оценке ООН почти баланс. Монголия, так же. Северная Корея: ни опроса, ни выхода. Граждане не могут выехать без разрешения государства, поэтому здесь замок. Южная Корея, приезжающих чуть больше и один из самых сильных паспортов. Япония, 14 процентов предпочли бы жить в другом месте, а её паспорт открывает 188 дверей.",
 "North Korea: CAN'T LEAVE",'lock',0),
('SC24','R11',['PNG','SLB','AUS','NZL','FJI'],
 "Down to the Pacific. Papua New Guinea and the Solomon Islands, mostly staying. Australia, a top dream destination. New Zealand, plus 231 in Gallup's 2015 to 2017 count, which back then beat even Canada. And Fiji, losing people by UN estimates.",
 "Вниз к Тихому океану. Папуа - Новая Гвинея и Соломоновы острова, в основном остаются. Австралия, одна из стран мечты. Новая Зеландия, плюс 231 в подсчёте Gallup 2015-2017, тогда это было выше даже Канады. И Фиджи, по оценке ООН теряет людей.",
 'New Zealand +231% (2015-2017)','231',1.0),
('SC25','R11',[],
 f"So here's the final map. {N['MAGNET']} magnets, {N['PULL']} countries with more people moving in, {N['STAY']} where most people stay, {N['LEAVE']} where many want out, {N['EXIT']} where it's close to half or more, and {N['LOCKED']} where people simply can't leave. And notice the pattern: the places people most want to leave often have the passports that open the fewest doors. So, where would you go? Tell us in the comments.",
 f"Итак, финальная карта. {N['MAGNET']} магнитов, {N['PULL']} стран, куда переезжает больше людей, {N['STAY']}, где большинство остаётся, {N['LEAVE']}, где многие хотят уехать, {N['EXIT']}, где таких почти половина или больше, и {N['LOCKED']}, откуда люди просто не могут уехать. И заметь закономерность: откуда больше всего хотят уехать, у тех чаще всего паспорта, которые открывают меньше всего дверей. Так куда бы ты поехал? Пиши в комментариях.",
 'Final count','final',0),
]

def main():
    route = [c for s in S for c in s[2]]
    order = sorted(C, key=lambda k: int(C[k]['order']))
    assert sorted(route) == sorted(order), set(order) ^ set(route)
    assert len(route) == len(set(route))
    # keep countries.csv order == route order
    if route != order: print('ROUTE ORDER DIFFERS from countries.csv', [(a, b) for a, b in zip(route, order) if a != b][:5])
    regs = {}
    for c in route: regs[C[c]['region_id']] = regs.get(C[c]['region_id'], 0) + 1
    en = '\n\n'.join(s[3] for s in S); ru = '\n\n'.join(s[4] for s in S)
    open(os.path.join(ROOT, 'voice_en.txt'), 'w').write(en + '\n'); open(os.path.join(ROOT, 'voice_ru.txt'), 'w').write(ru + '\n')
    intro = re.split(r'(?<=[.?!])\s+', S[0][3]); assert len(intro) == 2, intro
    # scenes.csv
    rows, cnt = [], 0
    for i, s in enumerate(S):
        cnt += len(s[2]); nxt = S[i + 1] if i + 1 < len(S) else None
        boundary = 'yes' if nxt and nxt[1] != s[1] else ''
        rows.append(dict(scene_id=s[0], region_id=s[1], region=C[s[2][0]]['region'] if s[2] else '', countries=';'.join(s[2]),
            country_names=';'.join(C[c]['short_name'] for c in s[2]), statuses=';'.join(f"{c}={C[c]['status']}{'*' if C[c]['quality'] in 'ES' else ''}" for c in s[2]),
            map_action='camera flies to each country in order; on arrival flag fill + face + status colour/icon appear at once; number chip pops on the spoken number; estimate = hatched, other survey = dotted outline' if s[2] else ('hold on previous country, chip animates' if i < len(S) - 1 else 'outro: zoom out to full world in status colours, counters roll to final values'),
            camera='country-to-country fly, zoom by country size' if s[2] else 'hold / zoom out', caption_en=s[5], voice_en_exact=s[3], meaning_ru=s[4],
            fact_sources=';'.join(sorted({f['source_ids'] for f in F if f['code'] in s[2]})), counter_increment=len(s[2]), counter_after=cnt,
            reveal_on_word=s[6], silent_chip='yes: every counted country shows its number chip even if the voice skips it' if s[2] else '',
            flight_pause_s=s[7], boundary_after=boundary, est_duration_s=round(len(s[3].split()) / 2.6 + s[7], 1)))
    with open(os.path.join(ROOT, 'scenes.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # numbers in voice vs facts
    WORDNUM = {'Half': '50', 'a third': '33', 'one in five': '20', 'nearly a quarter': '23', 'more than half': '57', 'Three out of four': '75'}
    out, bad = [], []
    for s in S:
        nums = re.findall(r'\d+(?:\.\d+)?', s[3]) + [v for k, v in WORDNUM.items() if k in s[3]]
        for n in nums:
            hits = [f for f in F if f['code'] in s[2] + (['CAN'] if s[0] == 'SC02' else []) and re.search(r'(?<![\d.])[-+]?' + n + r'(?![\d])', f['value'] + ' ' + f['period'])]
            if not hits: hits = [f for f in F if f['code'] in s[2] and f['fact_type'] == 'un_net_migration' and abs(abs(float(f['value'].split()[0])) - float(n)) < 0.6]
            if not hits and s[0] == 'SC25': hits = [dict(fact_id='COUNT', code='ALL')]
            out.append(dict(scene_id=s[0], number=n, fact_ids=';'.join(h['fact_id'] for h in hits[:3]), countries=';'.join(sorted({h['code'] for h in hits})), status='ok' if hits else 'CHECK'))
            if not hits: bad.append((s[0], n))
    with open(os.path.join(ROOT, 'voice_numbers.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    words = len(en.split())
    print(dict(countries=len(route), regions=regs, words=words, est_min=round(words / 155, 1), scenes=len(S), numbers=len(out), unmatched=bad))

if __name__ == '__main__': main()
