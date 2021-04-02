#!/usr/bin/python3
import requests
import json
import gzip
import datetime
import boto3

cat_api = 'https://cat.eduroam.org/user/API.php'
cat_download_api = "https://cat.eduroam.org/user/API.php"
s3_bucket = "eduroam-discovery"
s3_file = "discovery/v1/discovery.json"
aws_session = "default"
discovery_url = "https://discovery.eduroam.app/v1/discovery.json"


def get_seq():
    old_discovery = requests.get(discovery_url)
    return int(old_discovery.json()["seq"]) + 1


def get_updated():
    return datetime.datetime.now().isoformat()


def upload_s3(discovery):
    discovery_body = gzip.compress(
        json.dumps(discovery, separators=(",", ":")).encode("utf-8")
    )
    if aws_session:
        session = boto3.Session(profile_name=aws_session)
    else:
        session = boto3.Session()
    s3 = session.client("s3")
    s3.put_object(
        Bucket=s3_bucket,
        Key=s3_file,
        Body=discovery_body,
        CacheControl="public, max-age=3600, s-maxage=300, stale-while-revalidate=86400, stale-if-error=2592000",
        ContentEncoding="gzip",
        ContentType="application/json",
    )


def store_file(discovery, filename):
    with open(filename, "w") as fh:
        json.dump(discovery, fh)


def store_gzip_file(discovery, filename):
    with gzip.open(filename, "wb") as fh:
        fh.write(json.dumps(discovery, separators=(",", ":")).encode("utf-8"))


def get_preferred_name(names, country):
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
        return data[idp]["names"][0]["value"]


def get_profiles(idp):
    profiles = []
    if "profiles" in idp:
        for profile in idp["profiles"]:
            profile_name = get_preferred_name(profile["names"], idp["country"])
            letswifi_url = ""
            redirect_url = ""
            if profile["redirect"]:
                if "#letswifi" in profile["redirect"]:
                    letswifi_url = profile["redirect"].split("#", 1)[0]
                else:
                    redirect_url = profile["redirect"]
            if letswifi_url:
                # todo: visit .well-known/letswifi.json for actual endpoints
                profiles.append(
                    {
                        "id": "letswifi_cat_%s" % (profile["id"]),
                        "name": profile_name,
                        "default": True,
                        "eapconfig_endpoint": letswifi_url + "api/eap-config/",
                        "token_endpoint": letswifi_url + "oauth/token/",
                        "authorization_endpoint": letswifi_url + "oauth/authorize/",
                        "oauth": True,
                    }
                )
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
                        + "?action=downloadInstaller&device=eap-config&profile=%s"
                        % (profile["id"]),
                        "oauth": False,
                    }
                )
    return profiles


if __name__ == "__main__":
    seq = get_seq()
    discovery = {
        "version": 1,
        "seq": seq,
        "updated": get_updated(),
        "instances": [],
    }

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
            discovery["instances"].append(
                {
                    "name": idp_name,
                    "country": data[idp]["country"],
                    "cat_idp": int(data[idp]["entityID"]),
                    "geo": geo,
                    "profiles": profiles,
                }
            )

    # print(json.dumps(discovery))
    # upload_s3(discovery)
    # store_file(discovery, 'discovery.json')
    store_gzip_file(discovery, "discovery-%d.json" % (seq))
