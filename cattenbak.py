#!/usr/bin/env python3
import requests
import json
import datetime
import argparse

cat_api = "https://cat.eduroam.org/new_test/user/API.php"
cat_download_api = "https://cat.eduroam.org/user/API.php"


def get_old_discovery_from_file(filename):
    try:
        with open(filename, "r") as fh:
            return json.load(fh)
    except json.decoder.JSONDecodeError as e:
        print(e)
        return None
    except FileNotFoundError as e:
        print(e)
        return None


def discovery_needs_refresh(old_discovery, new_discovery):
    return (
        old_discovery == None
        or "instances" not in old_discovery
        or not old_discovery["instances"] == new_discovery["instances"]
    )


def store_file(discovery, filename):
    with open(filename, "w") as fh:
        json.dump(
            discovery,
            fh,
            separators=(",", ":"),
            allow_nan=False,
            sort_keys=True,
            ensure_ascii=True,
        )
        fh.write("\r\n")


def get_preferred_name(names, country):
    if len(names) == 0:
        return None
    lang = {}
    for name in names:
        lang[name["lang"]] = name["value"]
    if "C" in lang:
        return lang["C"]
    elif country.lower() in lang:
        return lang[country.lower()]
    elif "en" in lang:
        return lang["en"]
    else:
        return names[0]["value"]


def get_profiles(idp):
    profiles = []
    if "profiles" in idp:
        profile_default = True
        for profile in idp["profiles"]:
            profile_name = get_preferred_name(profile["names"], idp["country"])
            if profile_name == None:
                profile_name = get_preferred_name(idp["names"], idp["country"])
            letswifi_url = ""
            redirect_url = ""
            if profile["redirect"]:
                if "#letswifi" in profile["redirect"]:
                    letswifi_url = profile["redirect"].split("#", 1)[0]
                else:
                    redirect_url = profile["redirect"]
            if letswifi_url:
                # todo: visit .well-known/letswifi.json for actual endpoints
                if letswifi_url[-1] != "/":
                    letswifi_url += "/"
                profiles.append(
                    {
                        "id": "letswifi_cat_%s" % (profile["id"]),
                        "name": profile_name,
                        "default": profile_default,
                        "eapconfig_endpoint": letswifi_url + "api/eap-config/",
                        "token_endpoint": letswifi_url + "oauth/token/",
                        "authorization_endpoint": letswifi_url + "oauth/authorize/",
                        "oauth": True,
                    }
                )
                profile_default = False
            elif redirect_url:
                profiles.append(
                    {
                        "id": "cat_%s" % (profile["id"]),
                        "redirect": redirect_url,
                        "name": profile_name,
                    }
                )
            else:
                profiles.append(
                    {
                        "id": "cat_%s" % (profile["id"]),
                        "cat_profile": int(profile["id"]),
                        "name": profile_name,
                        "eapconfig_endpoint": cat_download_api
                        + "?action=downloadInstaller&device=eap-generic&profile=%s"
                        % (profile["id"]),
                        "oauth": False,
                    }
                )
    return profiles


def generate(old_seq=None):
    candidate_seq = int(datetime.datetime.utcnow().strftime("%Y%m%d00"))
    if old_seq == None:
        # Use a high number so we have a better chance to be over
        # Let's hope this doesn't happen more than once a day ;)
        seq = candidate_seq + 80
    elif candidate_seq <= old_seq:
        seq = old_seq + 1
    else:
        seq = candidate_seq

    return {
        "version": 1,
        "seq": seq,
        "instances": instances(),
    }


def instances():
    instances = []

    r_list_everything = requests.get(
        cat_api + "?action=listIdentityProvidersWithProfiles"
    )
    data = r_list_everything.json()["data"]

    for idp in data:
        idp_name = get_preferred_name(data[idp]["names"], data[idp]["country"])

        geo = []
        if "geo" in data[idp]:
            for coords in data[idp]["geo"]:
                geo.append(
                    {
                        "lon": round(float(coords["lon"]), 3),
                        "lat": round(float(coords["lat"]), 3),
                    }
                )

        profiles = get_profiles(data[idp])

        if profiles:
            instances.append(
                {
                    "name": idp_name,
                    "country": data[idp]["country"],
                    "cat_idp": int(data[idp]["entityID"]),
                    "geo": geo,
                    "profiles": profiles,
                }
            )

    return sorted(instances, key=lambda idp: idp["name"])


def parse_args():
    parser = argparse.ArgumentParser(description="Generate geteduroam discovery files")
    parser.add_argument(
        "--file-path",
        nargs="?",
        metavar="FILE",
        dest="file_path",
        default="discovery.json",
        help="path where to write V1 discovery file to fileystem",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force writing file even if nothing changed",
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()

    old_discovery = get_old_discovery_from_file(args["file_path"])
    if not old_discovery or not "seq" in old_discovery:
        old_discovery = None

    discovery = generate(old_seq=old_discovery["seq"] if old_discovery else None)
    if args["force"] or discovery_needs_refresh(old_discovery, discovery):
        print("Storing discovery seq %s" % discovery["seq"])
        store_file(discovery, args["file_path"])

    else:
        print("Unchanged %d" % old_discovery["seq"])
