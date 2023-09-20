#!/usr/bin/env python3
import requests
import json
import datetime
import argparse
import urllib.parse
import sys
from typing import Optional, List, Any, Dict, Set
from i18n import getLanguagesForCountry, convertCatCountryToIsoCountry

cat_api = "https://cat.eduroam.org/user/API.php"
user_agent = "geteduroam-cattenbak/2.0.0"
sigil = "http://letswifi.app/discovery#v2"


def getProfilesFromCat() -> Dict:
	idp_names: Set[str] = set()
	instances: List[Any] = []

	r_List_everything = requests.get(
		cat_api + "?action=listIdentityProvidersWithProfiles",
		# The CAT API does not return application/json, but rather text/html,
		# but the content is still a JSON payload
		headers={'User-Agent': user_agent, 'Accept': 'application/json'},
		allow_redirects=False,
		timeout=3,
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


class Cattenbak:
	def __init__(self, letswifi_stub: str=None, stubless_hosts: List[str]=[]):
		self.letswifi_stub = ""
		if letswifi_stub is None:
			self.letswifi_stub = ""
		if letswifi_stub:
			stub_url = urllib.parse.urlparse(letswifi_stub)
			if not stub_url.scheme == 'https':
				raise ValueError("letswifi_stub must be an https:// URL prefix");
		if letswifi_stub and letswifi_stub[-1] != "/":
			self.letswifi_stub = letswifi_stub + "/"
		else:
			self.letswifi_stub = letswifi_stub

		self.stubless_hosts = [] if stubless_hosts is None else stubless_hosts


	def getLocalisedName(
		self,
		names: List[Dict[str,str]], country: str
	) -> Optional[Dict[str, str]]:
		# If returning a Dict, it MUST contain an "any" language

		if len(names) == 0:
			return None
		if len(names) == 1:
			return {"any": names[0]["value"]}

		names = list(filter(lambda n: n["value"], names))
		if len(names) == 0:
			return None
		if len(names) == 1:
			return {"any": names[0]["value"]}

		languageDict = dict(map(lambda name: (name["lang"], name["value"]), names))
		if "any" in languageDict.keys():
			pass
		elif "C" in languageDict.keys():
			languageDict["any"] = languageDict.pop("C")
		elif "" in languageDict.keys():
			languageDict["any"] = languageDict.pop("")

		countryLangs = getLanguagesForCountry(country)
		nonEnglishCountryLangs = list(filter(lambda l: not l == "en", countryLangs))
		nonEnglishLanguageDict = {k: v for k, v in languageDict.items() if not k in ["any", "en"]}
		if nonEnglishCountryLangs and "en" in languageDict.keys() and "any" in languageDict.keys() and not languageDict["any"] in nonEnglishLanguageDict.values():
			# Is there a language for this country that isn't set yet?
			localLanguage = ''
			for language in nonEnglishCountryLangs:
				if not language in languageDict.keys():
					localLanguage = language
					break

			if localLanguage:
				# Here someone has set multiple languages, at least "en" and "any",
				# but they have not set a language that is local to their own country! Weird..
				# This could be because CAT doesn't allow you to set any language
				# that CAT itself is not translated in.  So it could be a way to put both languages anyway,
				# but it's not correct.  It's far more likely that they meant to do this:
				englishName = languageDict.pop("en")
				localName = languageDict.pop("any")
				languageDict["any"] = englishName
				languageDict[localLanguage] = localName

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


	def hasDuplicateNames(self, institution: Dict):
		for profile1 in institution["profiles"]:
			for profile2 in institution["profiles"]:
				if not profile1 == profile2 and profile1["name"] == profile2["name"]:
					return True
				if not profile1 == profile2 and not getFirstCommonMember(profile1["name"].values(), profile2["name"].values()) is None:
					return True
		return False


	def handleDuplicateNames(self, institution: Dict):
		result = dict(
			institution,
			profiles=list(map(
				lambda profile: dict(
					profile,
					name=None if not profile["id"][:12] == "cat_profile_" else self.addIdToNames(
						profile["name"] if profile["name"] else institution["name"],
						"#" + profile["id"][12:]
					),
				),
				institution["profiles"],
			))
		)
		return result


	def addIdToNames(self, names: Dict, id: str):
		return {k: v + " (" + id + ")" for k, v in names.items()}


	def checkProfile(self, profile: Dict):
		return not profile is None # and not profile["name"] is None and ("any" in profile["name"].keys() or not profile["name"])


	def checkInstitution(self, institution: Dict):
		return not institution["name"] is None and institution["profiles"] # and not institution["country"] is None


	def generateInstitution(self, instData: Dict[str, Any]) -> Dict[str,Any]:
		country = convertCatCountryToIsoCountry(instData["country"])
		name = self.getLocalisedName(instData["names"], convertCatCountryToIsoCountry(country))

		return {
			"name": name,
			"country": convertCatCountryToIsoCountry(country),
			"geo": list(
				map(lambda x: self.geoCompress(x), instData["geo"] if "geo" in instData else [])
			),
			"profiles": list(
				filter(
					lambda profile: self.checkProfile(profile),
					map(
						lambda catProfile: self.generateProfile(
							catProfile=catProfile,
							country=convertCatCountryToIsoCountry(country),
							parentName=name
						),
						instData["profiles"],
					),
				)
			),
		}


	def generateProfile(self, catProfile: Dict, country: str, parentName: Dict[str,str] = None) -> Optional[Dict[str, str]]:
		name = self.getLocalisedName(catProfile["names"], country)
		if name == parentName or not name:
			name = {}

		if catProfile["redirect"]:
			redirect_url = urllib.parse.urlparse(catProfile["redirect"])
			if not redirect_url.scheme:
				# If we use the scheme variable in urlparse, it will set the hostname as path
				# So we have to do this a bit more old fashioned
				redirect_url = urllib.parse.urlparse("http://" + catProfile["redirect"])
			if not redirect_url.scheme == 'https' and not redirect_url.scheme == 'http':
				return None
			frag = redirect_url.fragment.split("&")
			if "letswifi" in frag:
				if not redirect_url.scheme == 'https':
					# We only support HTTPS!
					return None
				if redirect_url.query:
					# We're not supporting this anymore!
					return None
				endpoint = redirect_url._replace(fragment="").geturl()
				if self.letswifi_stub:
					use_stub = True
					for stubless_host in self.stubless_hosts:
						stubless_host = stubless_host
						if stubless_host[0] == ".":
							if redirect_url.hostname.endswith(stubless_host):
								use_stub = False
								break
						else:
							if redirect_url.hostname == stubless_host:
								use_stub = False
								break
					if use_stub:
						endpoint = self.letswifi_stub + endpoint[8:]
				return {
					"id": "cat_profile_%s" % catProfile["id"],
					"name": name,
					"type": "letswifi",
					"letswifi_endpoint": endpoint,
				}
			else:
				return {
					"id": "cat_profile_%s" % catProfile["id"],
					"name": name,
					"type": "webview",
					"webview_endpoint": redirect_url.geturl(),
				}
		else:
			return {
				"id": "cat_profile_%s" % catProfile["id"],
				"name": name,
				"type": "eap-config",
				"eapconfig_endpoint": "%s?action=downloadInstaller&device=eap-generic&profile=%s"
				% (cat_api, catProfile["id"]),
				"mobileconfig_endpoint": "%s?action=downloadInstaller&device=apple_global&profile=%s"
				% (cat_api, catProfile["id"]),
			}


	def geoCompress(self, geo: Dict) -> Dict:
		# See https://xkcd.com/2170/
		return {
			"lon": round(float(geo["lon"]), 3),
			"lat": round(float(geo["lat"]), 3),
		}


	def generateInstituteList(self, catData: Dict) -> List:
		return list(
			map(
				# We add the CAT ID behind every profile name if there are duplicate profile names
				# This also applies to the profiles within the institution that are not duplicate
				lambda institution: self.handleDuplicateNames(institution) if self.hasDuplicateNames(institution) else institution,
				filter(
					# Filter out generated institutions
					lambda institution: self.checkInstitution(institution),
					map(
						# Generate our institution struct, and add an "id" so we can match it back to CAT
						lambda x: dict(self.generateInstitution(x[1]), id="cat_idp_%s" % x[0]),

						# Filter out institutions without profiles, returned by the CAT API
						filter(lambda x: "profiles" in x[1], catData.items()),
					)
				)
			)
		)


	def generateDiscovery(self, old_seq=None) -> Dict:
		def seq(old_seq: int = None) -> str:
			candidate_seq = int(datetime.datetime.utcnow().strftime("%Y%m%d00"))
			if old_seq is None:
				# Use a high number so we have a better chance to be over
				# Let's hope this doesn't happen more than once a day ;)
				seq = candidate_seq + 80
			elif candidate_seq <= old_seq:
				seq = old_seq + 1
			else:
				seq = candidate_seq

			return seq

		institutions = self.generateInstituteList(getProfilesFromCat())
		return {
			sigil: {
				"seq": seq(old_seq),
				"institutions": institutions,
				"apps": {},
			}
		}


	def discoveryIsUpToDate(self, old_discovery: Optional[Dict], new_discovery: Dict) -> Optional[int]:
		if old_discovery is None:
			return None
		if not sigil in old_discovery:
			return None

		old_discovery = old_discovery[sigil]
		new_discovery = new_discovery[sigil]

		old_institutions = old_discovery["institutions"] if "institutions" in old_discovery else None
		new_institutions = new_discovery["institutions"] if "institutions" in new_discovery else None

		assert isinstance(new_institutions, List)
		if not isinstance(old_institutions, List) or old_institutions is None or new_institutions is None:
			return None

		if old_institutions == new_institutions:
			return old_discovery["seq"]
		return None


def parseArgs() -> Dict[str, str]:
	parser = argparse.ArgumentParser(description="Generate geteduroam discovery files")
	parser.add_argument(
		"--file-path",
		nargs="?",
		metavar="FILE",
		dest="file_path",
		default="discovery.json",
		help="path where to write V2 discovery file to fileystem",
	)
	parser.add_argument(
		"--letswifi-stub",
		nargs="?",
		metavar="URL",
		dest="letswifi_stub",
		default=None,
		help="url prefix to put in front of the actual letswifi url"
	)
	parser.add_argument(
		"--stubless-host",
		action="extend",
		nargs="+",
		type=str,
		metavar="HOST",
		dest="stubless_host",
		help="hostname that won't get prefixed with the stub"
	)
	return vars(parser.parse_args())


if __name__ == "__main__":
	args = parseArgs()
	file = args["file_path"]
	cattenbak = Cattenbak(
		letswifi_stub=args["letswifi_stub"],
		stubless_hosts=args["stubless_host"]
	)
	old_discovery = {}
	try:
		with open(file, "r") as f:
			old_discovery = json.load(f)
			new_discovery = cattenbak.generateDiscovery(old_seq=old_discovery[sigil]["seq"])
	except:
		print("Cannot read old discovery\r\n", file=sys.stderr)
		new_discovery = cattenbak.generateDiscovery()
	if seq := cattenbak.discoveryIsUpToDate(old_discovery, new_discovery):
		print("Refresh not needed at seq %s\r\n" % (seq), file=sys.stderr)
	else:
		with open(file, "w") as fh:
			json.dump(
				new_discovery,
				fh,
				separators=(",", ":"), # remove frivulous space
				allow_nan=False,
				sort_keys=True, # reproducable output
				ensure_ascii=True, # compresses better
				check_circular=False,
			)
			fh.write("\r\n")
