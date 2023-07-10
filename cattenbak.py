#!/usr/bin/env python3
import requests
import json
import datetime
import argparse
import urllib.parse
import sys
from typing import Optional, List, Any, Dict, Set

cat_api = "https://cat.eduroam.org/user/API.php"


def getProfilesFromCat() -> Dict:
	idp_names: Set[str] = set()
	instances: List[Any] = []

	r_List_everything = requests.get(
		cat_api + "?action=listIdentityProvidersWithProfiles"
	)
	data = r_List_everything.json()
	assert "status" in data
	assert "data" in data
	assert data["status"] == 1
	return data["data"]


def getLanguagesForCountry(country: str) -> List[str]:
	d: Dict[str, List[str]] = {
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
		"FI": ["fi", "sv", "dk", "nb"],
		"FR": ["fr"],
		"GE": ["ka", "ab"],
		"GEANT": [],
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
		"ZA": ["en", "af", "zu", "xh", "nso", "tn", "st", "ts", "ss", "ve", "nr"],
		"ZM": ["en", "ny", "bem"],

		"AE": [],
		"KS": [],
	}
	if not country in d:
		print("Country %s unknown" % country, file=sys.stderr)
	return d[country] if country in d else []


def getFirstCommonMember(list1: List[str], list2: List[str]) -> Optional[str]:
	for h in list1:
		if h in list2:
			return h
	return None


def getLocalisedName(
	names: List, preferredLanguage: str, country: str
) -> Optional[str]:
	if len(names) == 0:
		return None
	lang: Dict[str, str] = {}
	for name in names:
		lang[name["lang"]] = name["value"]
	if preferredLanguage in lang:
		return lang[preferredLanguage]
	elif "C" in lang:
		return lang["C"]
	elif "any" in lang:
		return lang["any"]
	elif (
		countryLang := getFirstCommonMember(
			getLanguagesForCountry(country), list(lang.keys())
		)
	) in lang:
		return lang[countryLang]
	elif "en" in lang:
		return lang["en"]
	else:
		return names[0]["value"]


def checkProfile(profile: Dict):
	return profile.name is not None and country is not None and profiles


def checkInstitution(profile: Dict):
	return profile.name is not None and country is not None and profiles


def generateInstitution(instData: Dict[str, Any], lang: str):
	return {
		"name": getLocalisedName(instData["names"], lang, instData["country"]),
		"country": instData["country"],
		"geo": list(
			map(lambda x: geoCompress(x), instData["geo"] if "geo" in instData else [])
		),
		"profiles": list(
			filter(
				lambda profile: not profile is None and checkProfile(profile),
				map(
					lambda x: generateProfile(
						x,
						lang,
						instData["country"],
					),
					instData["profiles"],
				),
			)
		),
	}


def generateProfile(catProfile: Dict, lang: str, country: str) -> Dict[str, str]:
	if catProfile["redirect"]:
		if "#letswifi" in catProfile["redirect"]:
			letswifi_url = urllib.parse.urlparse(catProfile["redirect"])._replace(
				fragment=""
			)
			return {
				"id": "cat_profile_%s" % catProfile["id"],
				"name": getLocalisedName(catProfile["names"], lang, country),
				"type": "letswifi",
				"letswifi_endpoint": letswifi_url.geturl(),
			}
		else:
			return {
				"id": "cat_profile_%s" % catProfile["id"],
				"name": getLocalisedName(catProfile["names"], lang, country),
				"type": "webview",
				"portal_endpoint": catProfile["redirect"],
			}
	else:
		return {
			"id": "cat_profile_%s" % catProfile["id"],
			"name": getLocalisedName(catProfile["names"], lang, country),
			"type": "eap-config",
			"eapconfig_endpoint": "%s?action=downloadInstaller&device=eap-generic&profile=%s"
			% (cat_api, catProfile["id"]),
			"mobileconfig_endpoint": "%s?action=downloadInstaller&device=apple_global&profile=%s"
			% (cat_api, catProfile["id"]),
		}


def geoCompress(geo: Dict) -> Dict:
	return {
		"lon": round(float(geo["lon"]), 3),
		"lat": round(float(geo["lat"]), 3),
	}


def generateDiscovery(catData: Dict, lang: str):
	return list(
		map(
			lambda x: generateInstitution(x[1], lang) | {"id": "cat_idp_%s" % x[0]},
			filter(lambda x: "profiles" in x[1], catData.items()),
		)
	)


def parseArgs() -> Dict[str, str]:
	parser = argparse.ArgumentParser(description="Generate geteduroam discovery files")
	parser.add_argument(
		"--file-path",
		nargs="?",
		metavar="FILE",
		dest="file_path",
		default=None,
		help="path where to write V2 discovery file to fileystem",
	)
	parser.add_argument(
		"-l",
		"--language",
		nargs="?",
		dest="lang",
		default="any",
		help="generate file for this language code",
	)
	return vars(parser.parse_args())


if __name__ == "__main__":
	args = parseArgs()
	discovery = generateDiscovery(getProfilesFromCat(), args["lang"])
	file = (
		"discovery-%s.json" % args["lang"]
		if args["file_path"] == None
		else args["file_path"]
	)
	with open(file, "w") as fh:
		json.dump(
			discovery,
			fh,
			separators=(",", ":"),
			allow_nan=False,
			sort_keys=True,
			ensure_ascii=True,
			check_circular=False,
		)
		fh.write("\r\n")
