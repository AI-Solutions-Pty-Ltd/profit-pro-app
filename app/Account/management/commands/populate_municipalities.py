from django.core.management.base import BaseCommand

from app.Account.models import Municipality


class Command(BaseCommand):
    help = "Populates the database with South African municipalities."

    def handle(self, *args, **options):
        municipalities_data = """
Western Cape 	 Breede Valley Local Municipality 	 WC025 	 Cape Winelands
Western Cape 	 Drakenstein Local Municipality 	 WC023 	 Cape Winelands
Western Cape 	 Langeberg Local Municipality 	 WC026 	 Cape Winelands
Western Cape 	 Stellenbosch Local Municipality 	 WC024 	 Cape Winelands
Western Cape 	 Witzenberg Local Municipality 	 WC022 	 Cape Winelands
Western Cape 	 Beaufort West Local Municipality 	 WC053 	 Central Karoo
Western Cape 	 Laingsburg Local Municipality 	 WC051 	 Central Karoo
Western Cape 	 Prince Albert Local Municipality 	 WC052 	 Central Karoo
Western Cape 	 Bitou Local Municipality 	 WC047 	 Garden Route
Western Cape 	 George Local Municipality 	 WC044 	 Garden Route
Western Cape 	 Hessequa Local Municipality 	 WC042 	 Garden Route
Western Cape 	 Kannaland Local Municipality 	 WC041 	 Garden Route
Western Cape 	 Knysna Local Municipality 	 WC048 	 Garden Route
Western Cape 	 Mossel Bay Local Municipality 	 WC043 	 Garden Route
Western Cape 	 Oudtshoorn Local Municipality 	 WC045 	 Garden Route
Western Cape 	 Cape Agulhas Local Municipality 	 WC033 	 Overberg
Western Cape 	 Overstrand Local Municipality 	 WC032 	 Overberg
Western Cape 	 Swellendam Local Municipality 	 WC034 	 Overberg
Western Cape 	 Theewaterskloof Local Municipality 	 WC031 	 Overberg
Western Cape 	 Bergrivier Local Municipality 	 WC013 	 West Coast
Western Cape 	 Cederberg Local Municipality 	 WC012 	 West Coast
Western Cape 	 Matzikama Local Municipality 	 WC011 	 West Coast
Western Cape 	 Saldanha Bay Local Municipality 	 WC014 	 West Coast
Western Cape 	 Swartland Local Municipality 	 WC015 	 West Coast
Western Cape 	 City of Cape Town Metropolitan Municipality 	 CPT
Northern Cape 	 Dikgatlong Local Municipality 	 NC092 	 Frances Baard
Northern Cape 	 Magareng Local Municipality 	 NC093 	 Frances Baard
Northern Cape 	 Phokwane Local Municipality 	 NC094 	 Frances Baard
Northern Cape 	 Sol Plaatje Local Municipality 	 NC091 	 Frances Baard
Northern Cape 	 Ga-Segonyana Local Municipality 	 NC452 	 John Taolo Gaetsewe
Northern Cape 	 Gamagara Local Municipality 	 NC453 	 John Taolo Gaetsewe
Northern Cape 	 Joe Morolong Local Municipality 	 NC451 	 John Taolo Gaetsewe
Northern Cape 	 Hantam Local Municipality 	 NC065 	 Namakwa
Northern Cape 	 Kamiesberg Local Municipality 	 NC064 	 Namakwa
Northern Cape 	 Karoo Hoogland Local Municipality 	 NC066 	 Namakwa
Northern Cape 	 Khâi-Ma Local Municipality 	 NC067 	 Namakwa
Northern Cape 	 Nama Khoi Local Municipality 	 NC062 	 Namakwa
Northern Cape 	 Richtersveld Local Municipality 	 NC061 	 Namakwa
Northern Cape 	 Emthanjeni Local Municipality 	 NC073 	 Pixley ka Seme
Northern Cape 	 Kareeberg Local Municipality 	 NC074 	 Pixley ka Seme
Northern Cape 	 Renosterberg Local Municipality 	 NC075 	 Pixley ka Seme
Northern Cape 	 Siyancuma Local Municipality 	 NC078 	 Pixley ka Seme
Northern Cape 	 Siyathemba Local Municipality 	 NC077 	 Pixley ka Seme
Northern Cape 	 Thembelihle Local Municipality 	 NC076 	 Pixley ka Seme
Northern Cape 	 Ubuntu Local Municipality 	 NC071 	 Pixley ka Seme
Northern Cape 	 Umsobomvu Local Municipality 	 NC072 	 Pixley ka Sem
Northern Cape 	 !Kheis Local Municipality 	 NC084 	 ZF Mgcawu
Northern Cape 	 Dawid Kruiper Local Municipality 	 NC087 	 ZF Mgcawu
Northern Cape 	 Kai !Garib Local Municipality 	 NC082 	 ZF Mgcawu
Northern Cape 	 Kgatelopele Local Municipality 	 NC086 	 ZF Mgcawu
Northern Cape 	 Tsantsabane Local Municipality 	 NC085 	 ZF Mgcawu
Eastern Cape 	 Matatiele Local Municipality 	 EC441 	 Alfred Nzo
Eastern Cape 	 Ntabankulu Local Municipality 	 EC444 	 Alfred Nzo
Eastern Cape 	 Umzimvubu Local Municipality 	 EC442 	 Alfred Nzo
Eastern Cape 	 Winnie Madikizela-Mandela Local Municipality 	 EC443 	 Alfred Nzo
Eastern Cape 	 Amahlathi Local Municipality 	 EC124 	 Amathole
Eastern Cape 	 Great Kei Local Municipality 	 EC123 	 Amathole
Eastern Cape 	 Mbhashe Local Municipality 	 EC121 	 Amathole
Eastern Cape 	 Mnquma Local Municipality 	 EC122 	 Amathole
Eastern Cape 	 Ngqushwa Local Municipality 	 EC126 	 Amathole
Eastern Cape 	 Raymond Mhlaba Local Municipality 	 EC129 	 Amathole
Eastern Cape 	 Dr AB Xuma Local Municipality 	 EC137 	 Chris Hani
Eastern Cape 	 Emalahleni Local Municipality 	 EC136 	 Chris Hani
Eastern Cape 	 Enoch Mgijima Local Municipality 	 EC139 	 Chris Hani
Eastern Cape 	 Intsika Yethu Local Municipality 	 EC135 	 Chris Hani
Eastern Cape 	 Inxuba Yethemba Local Municipality 	 EC131 	 Chris Hani
Eastern Cape 	 Sakhisizwe Local Municipality 	 EC138 	 Chris Hani
Eastern Cape 	 Elundini Local Municipality 	 EC141 	 Joe Gqabi
Eastern Cape 	 Senqu Local Municipality 	 EC142 	 Joe Gqabi
Eastern Cape 	 Walter Sisulu Local Municipality 	 EC145 	 Joe Gqabi
Eastern Cape 	 Ingquza Hill Local Municipality 	 EC153 	 OR Tambo
Eastern Cape 	 King Sabata Dalindyebo Local Municipality 	 EC157 	 OR Tambo
Eastern Cape 	 Kumkani Mhlontlo Local Municipality 	 EC156 	 OR Tambo
Eastern Cape 	 Nyandeni Local Municipality 	 EC155 	 OR Tambo
Eastern Cape 	 Port St Johns Local Municipality 	 EC154 	 OR Tambo
Eastern Cape 	 Blue Crane Route Local Municipality 	 EC102 	 Sarah Baartman
Eastern Cape 	 Dr Beyers Naudé Local Municipality 	 EC101 	 Sarah Baartman
Eastern Cape 	 Kou-Kamma Local Municipality 	 EC109 	 Sarah Baartman
Eastern Cape 	 Kouga Local Municipality 	 EC108 	 Sarah Baartman
Eastern Cape 	 Makana Local Municipality 	 EC104 	 Sarah Baartman
Eastern Cape 	 Ndlambe Local Municipality 	 EC105 	 Sarah Baartman
Eastern Cape 	 Sundays River Valley Local Municipality 	 EC106 	 Sarah Baartman
Free State 	 Mafube Local Municipality 	 FS205 	 Fezile Dabi
Free State 	 Metsimaholo Local Municipality 	 FS204 	 Fezile Dabi
Free State 	 Moqhaka Local Municipality 	 FS201 	 Fezile Dabi
Free State 	 Ngwathe Local Municipality 	 FS203 	 Fezile Dabi
Free State 	 Masilonyana Local Municipality 	 FS181 	 Lejweleputswa
Free State 	 Matjhabeng Local Municipality 	 FS184 	 Lejweleputswa
Free State 	 Nala Local Municipality 	 FS185 	 Lejweleputswa
Free State 	 Tokologo Local Municipality 	 FS182 	 Lejweleputswa
Free State 	 Tswelopele Local Municipality 	 FS183 	 Lejweleputswa
Free State 	 Dihlabeng Local Municipality 	 FS192 	 Thabo Mofutsanyana
Free State 	 Maluti-a-Phofung Local Municipality 	 FS194 	 Thabo Mofutsanyana
Free State 	 Mantsopa Local Municipality 	 FS196 	 Thabo Mofutsanyana
Free State 	 Nketoana Local Municipality 	 FS193 	 Thabo Mofutsanyana
Free State 	 Phumelela Local Municipality 	 FS195 	 Thabo Mofutsanyana
Free State 	 Setsoto Local Municipality 	 FS191 	 Thabo Mofutsanyana
Free State 	 Kopanong Local Municipality 	 FS162 	 Xhariep
Free State 	 Letsemeng Local Municipality 	 FS161 	 Xhariep
Free State 	 Mohokare Local Municipality 	 FS163 	 Xhariep
Gauteng 	 Emfuleni Local Municipality 	 GT421 	 Sedibeng
Gauteng 	 Midvaal Local Municipality 	 GT422 	 Sedibeng
Gauteng 	 Lesedi Local Municipality 	 GT423 	 Sedibeng
Gauteng 	 Mogale City Local Municipality 	 GT481 	 West Rand
Gauteng 	 Merafong City Local Municipality 	 GT484 	 West Rand
Gauteng 	 Rand West City Local Municipality 	 GT485 	 West Rand
Kwa-Zulu Natal 	 Dannhauser Local Municipality 	 KZN254 	 Amajuba
Kwa-Zulu Natal 	 eMadlangeni Local Municipality 	 KZN253 	 Amajuba
Kwa-Zulu Natal 	 Newcastle Local Municipality 	 KZN252 	 Amajuba
Kwa-Zulu Natal 	 Dr Nkosazana Dlamini Zuma Local Municipality 	 KZN436 	 Harry Gwala
Kwa-Zulu Natal 	 Greater Kokstad Local Municipality 	 KZN433 	 Harry Gwala
Kwa-Zulu Natal 	 Johannes Phumani Phungula Local Municipality 	 KZN434 	 Harry Gwala
Kwa-Zulu Natal 	 Umzimkhulu Local Municipality 	 KZN435 	 Harry Gwala
Kwa-Zulu Natal 	 KwaDukuza Local Municipality 	 KZN292 	 iLembe
Kwa-Zulu Natal 	 Mandeni Local Municipality 	 KZN291 	 iLembe
Kwa-Zulu Natal 	 Maphumulo Local Municipality 	 KZN294 	 iLembe
Kwa-Zulu Natal 	 Ndwedwe Local Municipality 	 KZN293 	 iLembe
Kwa-Zulu Natal 	 Mthonjaneni Local Municipality 	 KZN285 	 King Cetshwayo
Kwa-Zulu Natal 	 Nkandla Local Municipality 	 KZN286 	 King Cetshwayo
Kwa-Zulu Natal 	 uMfolozi Local Municipality 	 KZN281 	 King Cetshwayo
Kwa-Zulu Natal 	 uMhlathuze Local Municipality 	 KZN282 	 King Cetshwayo
Kwa-Zulu Natal 	 uMlalazi Local Municipality 	 KZN284 	 King Cetshwayo
Kwa-Zulu Natal 	 Ray Nkonyeni Local Municipality 	 KZN216 	 Ugu
Kwa-Zulu Natal 	 uMdoni Local Municipality 	 KZN212 	 Ugu
Kwa-Zulu Natal 	 uMuziwabantu Local Municipality 	 KZN214 	 Ugu
Kwa-Zulu Natal 	 Umzumbe Local Municipality 	 KZN213 	 Ugu
Kwa-Zulu Natal 	 Impendle Local Municipality 	 KZN224 	 uMgungundlovu
Kwa-Zulu Natal 	 Mkhambathini Local Municipality 	 KZN226 	 uMgungundlovu
Kwa-Zulu Natal 	 Mpofana Local Municipality 	 KZN223 	 uMgungundlovu
Kwa-Zulu Natal 	 Msunduzi Local Municipality 	 KZN225 	 uMgungundlovu
Kwa-Zulu Natal 	 Richmond Local Municipality 	 KZN227 	 uMgungundlovu
Kwa-Zulu Natal 	 uMngeni Local Municipality 	 KZN222 	 uMgungundlovu
Kwa-Zulu Natal 	 uMshwathi Local Municipality 	 KZN221 	 uMgungundlovu
Kwa-Zulu Natal 	 Big Five Hlabisa Local Municipality 	 KZN276 	 Umkhanyakude
Kwa-Zulu Natal 	 Jozini Local Municipality 	 KZN272 	 Umkhanyakude
Kwa-Zulu Natal 	 Mtubatuba Local Municipality 	 KZN275 	 Umkhanyakude
Kwa-Zulu Natal 	 uMhlabuyalingana Local Municipality 	 KZN271 	 Umkhanyakude
Kwa-Zulu Natal 	 Endumeni Local Municipality 	 KZN241 	 Umzinyathi
Kwa-Zulu Natal 	 Msinga Local Municipality 	 KZN244 	 Umzinyathi
Kwa-Zulu Natal 	 Nqutu Local Municipality 	 KZN242 	 Umzinyathi
Kwa-Zulu Natal 	 Umvoti Local Municipality 	 KZN245 	 Umzinyathi
Kwa-Zulu Natal 	 Alfred Duma Local Municipality 	 KZN238 	 Uthukela
Kwa-Zulu Natal 	 Inkosi Langalibalele Local Municipality 	 KZN237 	 Uthukela
Kwa-Zulu Natal 	 Okhahlamba Local Municipality 	 KZN235 	 Uthukela
Kwa-Zulu Natal 	 Abaqulusi Local Municipality 	 KZN263 	 Zululand
Kwa-Zulu Natal 	 eDumbe Local Municipality 	 KZN261 	 Zululand
Kwa-Zulu Natal 	 Nongoma Local Municipality 	 KZN265 	 Zululand
Kwa-Zulu Natal 	 Ulundi Local Municipality 	 KZN266 	 Zululand
Kwa-Zulu Natal 	 uPhongolo Local Municipality 	 KZN262 	 Zululand
Kwa-Zulu Natal 	 eThekwini Metropolitan Municipality 	 ETH
Limpopo 	 Blouberg Local Municipality 	 LIM351 	 Capricorn
Limpopo 	 Lepelle-Nkumpi Local Municipality 	 LIM355 	 Capricorn
Limpopo 	 Molemole Local Municipality 	 LIM353 	 Capricorn
Limpopo 	 Polokwane Local Municipality 	 LIM354 	 Capricorn
Limpopo 	 Ba-Phalaborwa Local Municipality 	 LIM334 	 Mopani
Limpopo 	 Greater Giyani Local Municipality 	 LIM331 	 Mopani
Limpopo 	 Greater Letaba Local Municipality 	 LIM332 	 Mopani
Limpopo 	 Greater Tzaneen Local Municipality 	 LIM333 	 Mopani
Limpopo 	 Maruleng Local Municipality 	 LIM335 	 Mopani
Limpopo 	 Elias Motsoaledi Local Municipality 	 LIM472 	 Sekhukhune
Limpopo 	 Ephraim Mogale Local Municipality 	 LIM471 	 Sekhukhune
Limpopo 	 Fetakgomo Tubatse Local Municipality 	 LIM476 	 Sekhukhune
Limpopo 	 Makhuduthamaga Local Municipality 	 LIM473 	 Sekhukhune
Limpopo 	 Collins Chabane Local Municipality 	 LIM345 	 Vhembe
Limpopo 	 Makhado Local Municipality 	 LIM344 	 Vhembe
Limpopo 	 Musina Local Municipality 	 LIM341 	 Vhembe
Limpopo 	 Thulamela Local Municipality 	 LIM343 	 Vhembe
Limpopo 	 Bela-Bela Local Municipality 	 LIM366 	 Waterberg
Limpopo 	 Lephalale Local Municipality 	 LIM362 	 Waterberg
Limpopo 	 Modimolle–Mookgophong Local Municipality 	 LIM368 	 Waterberg
Limpopo 	 Mogalakwena Local Municipality 	 LIM367 	 Waterberg
Limpopo 	 Thabazimbi Local Municipality 	 LIM361 	 Waterberg
Mpumalanga 	 Bushbuckridge Local Municipality 	 MP325 	 Ehlanzeni
Mpumalanga 	 Mbombela Local Municipality 	 MP326 	 Ehlanzeni
Mpumalanga 	 Nkomazi Local Municipality 	 MP324 	 Ehlanzeni
Mpumalanga 	 Thaba Chweu Local Municipality 	 MP321 	 Ehlanzeni
Mpumalanga 	 Albert Luthuli Local Municipality 	 MP301 	 Gert Sibande
Mpumalanga 	 Dipaleseng Local Municipality 	 MP306 	 Gert Sibande
Mpumalanga 	 Govan Mbeki Local Municipality 	 MP307 	 Gert Sibande
Mpumalanga 	 Lekwa Local Municipality 	 MP305 	 Gert Sibande
Mpumalanga 	 Mkhondo Local Municipality 	 MP303 	 Gert Sibande
Mpumalanga 	 Msukaligwa Local Municipality 	 MP302 	 Gert Sibande
Mpumalanga 	 Pixley ka Seme Local Municipality 	 MP304 	 Gert Sibande
Mpumalanga 	 Dr JS Moroka Local Municipality 	 MP316 	 Nkangala
Mpumalanga 	 Emakhazeni Local Municipality 	 MP314 	 Nkangala
Mpumalanga 	 Emalahleni Local Municipality 	 MP312 	 Nkangala
Mpumalanga 	 Steve Tshwete Local Municipality 	 MP313 	 Nkangala
Mpumalanga 	 Thembisile Hani Local Municipality 	 MP315 	 Nkangala
Mpumalanga 	 Victor Khanye Local Municipality 	 MP311 	 Nkangala
North-West 	 Kgetlengrivier Local Municipality 	 NW374 	 Bojanala Platinum
North-West 	 Madibeng Local Municipality 	 NW372 	 Bojanala Platinum
North-West 	 Moretele Local Municipality 	 NW371 	 Bojanala Platinum
North-West 	 Moses Kotane Local Municipality 	 NW375 	 Bojanala Platinum
North-West 	 Rustenburg Local Municipality 	 NW373 	 Bojanala Platinum
North-West 	 City of Matlosana Local Municipality 	 NW403 	 Dr Kenneth Kaunda
North-West 	 JB Marks Local Municipality 	 NW405 	 Dr Kenneth Kaunda
North-West 	 Maquassi Hills Local Municipality 	 NW404 	 Dr Kenneth Kaunda
North-West 	 Greater Taung Local Municipality 	 NW394 	 Dr Ruth Segomotsi Mompati
North-West 	 Kagisano-Molopo Local Municipality 	 NW397 	 Dr Ruth Segomotsi Mompati
North-West 	 Lekwa-Teemane Local Municipality 	 NW396 	 Dr Ruth Segomotsi Mompati
North-West 	 Mamusa Local Municipality 	 NW393 	 Dr Ruth Segomotsi Mompati
North-West 	 Naledi Local Municipality 	 NW392 	 Dr Ruth Segomotsi Mompati
North-West 	 Ditsobotla Local Municipality 	 NW384 	 Ngaka Modiri Molema
North-West 	 Mahikeng Local Municipality 	 NW383 	 Ngaka Modiri Molema
North-West 	 Ramotshere Moiloa Local Municipality 	 NW385 	 Ngaka Modiri Molema
North-West 	 Ratlou Local Municipality 	 NW381 	 Ngaka Modiri Molema
North-West 	 Tswaing Local Municipality 	 NW382 	 Ngaka Modiri Molema
"""

        self.stdout.write("Populating municipalities...")

        # Clear existing data to prevent duplicates on re-run
        Municipality.objects.all().delete()

        for line in municipalities_data.strip().split("\n"):
            parts = line.strip().split("\t")
            if len(parts) == 4:
                province = parts[0].strip()
                municipality_name = parts[1].strip()
                code = parts[2].strip()
                district = parts[3].strip()

                Municipality.objects.create(
                    province=province,
                    municipality_name=municipality_name,
                    code=code,
                    district=district,
                )
            elif len(parts) == 3:  # Handle cases where district is missing
                province = parts[0].strip()
                municipality_name = parts[1].strip()
                code = parts[2].strip()

                Municipality.objects.create(
                    province=province,
                    municipality_name=municipality_name,
                    code=code,
                    district="",  # Set district to empty string
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Skipping malformed line: {line}")
                )

        self.stdout.write(self.style.SUCCESS("Municipalities populated successfully!"))
