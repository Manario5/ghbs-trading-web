from typing import List, Dict

TIER_1: List[str] = [
    "1120", "2222", "1180", "1150", "1211",
    "2020", "7010", "2010", "7203", "4250",
    "1303", "2082", "1060", "2230", "1010",
    "6015", "8313", "1321", "1140", "7020",
    "1050", "1111", "2380", "2330", "2350",
    "1322", "2310", "1020", "1080", "8230",
]

TIER_2: List[str] = [
    "7202", "4200", "2290", "4013", "2382",
    "4264", "8010", "2200", "2083", "2280",
    "6017", "4263", "5110", "4030", "4009",
    "2223", "4325", "4002", "4190", "8210",
    "2320", "7030", "1831", "4240", "4005",
    "7040", "4300", "4164", "4142", "6018",
]

TIER_3: List[str] = [
    "6004", "2070", "2170", "4110", "4191",
    "2381", "4003", "4210", "4193", "2050",
    "4004", "4261", "8200", "2240", "4015",
    "4322", "4170", "1320", "8030", "2060",
]

WATCHLIST: List[str] = TIER_1 + TIER_2 + TIER_3

TIER_MAP: Dict[str, str] = {}
for t in TIER_1: TIER_MAP[t] = "TIER_1"
for t in TIER_2: TIER_MAP[t] = "TIER_2"
for t in TIER_3: TIER_MAP[t] = "TIER_3"

SECTOR_MAP: Dict[str, str] = {
    "1120": "Banks", "2222": "Energy", "1180": "Banks", "1150": "Banks",
    "1211": "Materials", "2020": "Materials", "7010": "Telecommunication Services",
    "2010": "Materials", "7203": "Software & Services", "4250": "Real Estate Mgmt & Dev't",
    "1303": "Capital Goods", "2082": "Utilities", "1060": "Banks", "2230": "Health Care Equipment & Svc",
    "1010": "Banks", "6015": "Consumer Services", "8313": "Insurance", "1321": "Materials",
    "1140": "Banks", "7020": "Telecommunication Services", "1050": "Banks", "1111": "Financial Services",
    "2380": "Energy", "2330": "Materials", "2350": "Materials", "1322": "Materials",
    "2310": "Materials", "1020": "Banks", "1080": "Banks", "8230": "Insurance",
    "7202": "Software & Services", "4200": "Consumer Discretionary Distribution & Retail",
    "2290": "Materials", "4013": "Health Care Equipment & Svc", "2382": "Energy", "4264": "Transportation",
    "8010": "Insurance", "2200": "Materials", "2083": "Utilities", "2280": "Food & Beverages",
    "6017": "Consumer Services", "4263": "Transportation", "5110": "Utilities", "4030": "Energy",
    "4009": "Health Care Equipment & Svc", "2223": "Materials", "4325": "Real Estate Mgmt & Dev't",
    "4002": "Health Care Equipment & Svc", "4190": "Consumer Discretionary Distribution & Retail",
    "8210": "Insurance", "2320": "Capital Goods", "7030": "Telecommunication Services",
    "1831": "Commercial & Professional Svc", "4240": "Consumer Discretionary Distribution & Retail",
    "4005": "Health Care Equipment & Svc", "7040": "Telecommunication Services", "4300": "Real Estate Mgmt & Dev't",
    "4164": "Consumer Staples Distribution & Retail", "4142": "Capital Goods", "6018": "Consumer Services",
    "6004": "Commercial & Professional Svc", "2070": "Pharma, Biotech & Life Science", "2170": "Materials",
    "4110": "Capital Goods", "4191": "Consumer Discretionary Distribution & Retail", "2381": "Energy",
    "4003": "Consumer Discretionary Distribution & Retail", "4210": "Media and Entertainment",
    "4193": "Consumer Discretionary Distribution & Retail", "2050": "Food & Beverages", 
    "4004": "Health Care Equipment & Svc", "4261": "Transportation", "8200": "Insurance",
    "2240": "Materials", "4015": "Pharma, Biotech & Life Science", "4322": "Real Estate Mgmt & Dev't",
    "4170": "Consumer Services", "1320": "Materials", "8030": "Insurance", "2060": "Materials",
}
