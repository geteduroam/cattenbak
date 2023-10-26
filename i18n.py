from typing import List, Dict


def convertCatCountryToIsoCountry(country: str) -> str:
	# GEANT is its own country in CAT (used by IdP #796 and #797),
	# but these are named "guest IdP" and "guest IdP Android"
	# The actual "GÉANT Staff" profile has an NL country code,
	# so let's also convert those other GEANT profiles to NL
	if country == 'GEANT':
		return 'NL'

	# Otherwise use same country code as CAT
	return country


def getLanguagesForCountry(country: str) -> List[str]:
	d: Dict[str, List[str]] = {
		"AE": ["arb", "afb"],
		"AL": ["sq"],
		"AM": ["hy"],
		"AR": ["es"],
		"AT": ["de", "sl"],
		"AU": ["en"],
		"BD": ["bn"],
		"BE": ["nl", "fr"],
		"BG": ["bg"],
		"BR": ["pt"],
		"CA": ["en", "fr"],
		"CH": ["de", "fr", "it", "rm"],
		"CL": ["es"],
		"CO": ["es", "en"],
		"CR": ["es"],
		"CZ": ["cs"],
		"DE": ["de"],
		"DK": ["dk", "nb", "sv"],
		"EC": ["es"],
		"EE": ["et"],
		"ES": ["es", "ca"],
		"ET": ["aa", "am", "om", "so", "ti"],
		"FI": ["fi", "sv", "dk", "nb"],
		"FR": ["fr"],
		"GE": ["ka", "ab"],
		"GR": ["el"],
		"HR": ["hr"],
		"HU": ["hu"],
		"IE": ["en"],
		"IL": ["he"],
		"IS": ["is", "dk", "nb", "sv"],
		"IT": ["it"],
		"JP": ["jp"],
		"KE": ["sw", "en"],
		"KR": ["ko"],
		"KS": ["sq", "sr"], # Kosovo according to KREN (Kosovo NREN)
		"LA": ["lo"],
		"LK": ["si", "ta"],
		"LT": ["lt"],
		"LU": ["fr", "de"],
		"LV": ["lv"],
		"MA": ["arb", "zgh"],
		"MD": ["ro"],
		"ME": ["cnr"],
		"MK": ["mk", "sq"],
		"MT": ["mt", "en"],
		"MW": ["en", "ny"],
		"MX": ["es"],
		"MY": ["zsm", "en", "zh"],
		"NG": ["nb"],
		"NL": ["nl"],
		"NO": ["nb", "dk", "sv"],
		"NZ": ["en", "mi"],
		"OM": ["arb"],
		"PE": ["es"],
		"PH": ["fil", "en"],
		"PK": ["ur", "en"],
		"PL": ["pl"],
		"PT": ["pt"],
		"RO": ["ro"],
		"RS": ["rs"],
		"SE": ["sv", "dk", "nb"],
		"SG": ["en", "ms", "zh", "ta"],
		"SI": ["sl"],
		"SK": ["sk"],
		"TR": ["tr"],
		"UA": ["uk"],
		"UG": ["en", "sw"],
		"UK": ["en"],
		"US": ["en", "es"],
		"UY": ["es"],
		"XK": ["sq", "sr"], # Kosovo according to ISO rules (X means temporary)
		"ZA": ["en", "af", "zu", "xh", "nso", "tn", "st", "ts", "ss", "ve", "nr"],
		"ZM": ["en", "ny", "bem"],
	}
	if not country in d:
		raise Exception("Country %s unknown" % country)
	return d[country] if country in d else []
