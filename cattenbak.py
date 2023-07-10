#!/usr/bin/env python3
import requests
import json
import datetime
import argparse
import urllib.parse
import sys
from typing import Optional, List, Any, Dict, Set
from i18n import getLanguagesForCountry

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


def getFirstCommonMember(list1: List[str], list2: List[str]) -> Optional[str]:
	for h in list1:
		if h in list2:
			return h
	return None


def getLocalisedName(
	names: List[str], country: str
) -> Optional[Dict[str, str]]:
	# If returning a Dict, it MUST contain an "any" language
	if len(names) == 0:
		return None
	if len(names) == 1:
		return {"any": names[0]["value"]}
	languageDict = dict(map(lambda name: (name["lang"], name["value"]), names))
	if "C" in languageDict.keys():
		languageDict["any"] = languageDict.pop("C")

	countryLangs = getLanguagesForCountry(country)
	nonEnglishCountryLangs = list(filter(lambda l: not l == "en", countryLangs))
	if nonEnglishCountryLangs and "en" in languageDict.keys() and "any" in languageDict.keys() and getFirstCommonMember(nonEnglishCountryLangs, languageDict.keys()) is None:
		# Here someone has set multiple languages, at least "en" and "any",
		# but they have not set a language that is local to their own country! Weird..
		# This could be because CAT doesn't allow you to set any language
		# that CAT itself is not translated in.  So it could be a way to put both languages anyway,
		# but it's not correct.  It's far more likely that they meant to do this:
		englishName = languageDict.pop("en")
		localName = languageDict.pop("any")
		languageDict["any"] = englishName
		languageDict[nonEnglishCountryLangs[0]] = localName

	if not "any" in languageDict.keys():
		countryLangs.insert(0, "en")
		countryLangs.append(names[0]["lang"]) # use the first language as "any"
		for countryLang in countryLangs:
			if countryLang in languageDict.keys():
				languageDict["any"] = languageDict.pop(countryLang)
				break # break out of the for loop, we found a good candidate for "any"
		assert "any" in languageDict.keys()

	# Remove duplicates, where "any" and other languages are the same
	return {k: v for k, v in languageDict.items() if k == "any" or not v == languageDict["any"]}


def checkProfile(profile: Dict):
	return not profile["name"] is None and "any" in profile["name"].keys()


def checkInstitution(profile: Dict):
	return not profile["name"] is None and not profile["country"] is None and profile["profiles"]


def generateInstitution(instData: Dict[str, Any]):
	return {
		"name": getLocalisedName(instData["names"], instData["country"]),
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
						instData["country"],
					),
					instData["profiles"],
				),
			)
		),
	}


def generateProfile(catProfile: Dict, country: str) -> Optional[Dict[str, str]]:
	if catProfile["redirect"]:
		redirect_url = urllib.parse.urlparse(catProfile["redirect"])
		if not redirect_url.scheme == 'https' and not redirect_url.scheme == 'http':
			return None
		frag = redirect_url.fragment.split("&")
		if "letswifi" in frag:
			return {
				"id": "cat_profile_%s" % catProfile["id"],
				"name": getLocalisedName(catProfile["names"], country),
				"type": "letswifi",
				"letswifi_endpoint": redirect_url._replace(fragment="").geturl(),
			}
		else:
			return {
				"id": "cat_profile_%s" % catProfile["id"],
				"name": getLocalisedName(catProfile["names"], country),
				"type": "webview",
				"portal_endpoint": catProfile["redirect"],
			}
	else:
		return {
			"id": "cat_profile_%s" % catProfile["id"],
			"name": getLocalisedName(catProfile["names"], country),
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


def generateDiscovery(catData: Dict):
	return list(
		filter(
			lambda x: checkInstitution(x),
			map(
				lambda x: generateInstitution(x[1]) | {"id": "cat_idp_%s" % x[0]},
				filter(lambda x: "profiles" in x[1], catData.items()),
			)
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
	return vars(parser.parse_args())


if __name__ == "__main__":
	args = parseArgs()
	discovery = generateDiscovery(getProfilesFromCat())
	file = (
		"discovery.json"
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
