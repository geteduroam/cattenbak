#!/usr/bin/env python3
import requests
import json
import gzip
import datetime
import boto3
import argparse

cat_api = "https://cat.eduroam.org/new_test/user/API.php"
cat_download_api = "https://cat.eduroam.org/user/API.php"
discovery_url = "https://discovery.eduroam.app/v1/discovery-geo.json"


def get_old_discovery_from_url():
    return requests.get(discovery_url).json()


def get_old_discovery_from_file(filename):
    try:
        with open(filename, "r") as fh:
            return json.load(fh)
    except json.decoder.JSONDecodeError:
        return {"seq": 0, "instances": [], "error": "json"}
    except FileNotFoundError:
        return {"seq": 0, "instances": [], "error": "file"}


def discovery_needs_refresh(old_discovery, new_discovery):
    return not old_discovery["instances"] == new_discovery["instances"]


def get_updated():
    return datetime.datetime.now().isoformat()


def upload_s3(s3, discovery, s3_bucket, s3_file):
    discovery_body = gzip.compress(
        json.dumps(
            discovery, separators=(",", ":"), allow_nan=False, ensure_ascii=True
        ).encode("ascii")
    )
    result = s3.put_object(
        Bucket=s3_bucket,
        Key=s3_file,
        Body=discovery_body,
        CacheControl="public, max-age=900, s-maxage=300, stale-while-revalidate=86400, stale-if-error=2592000",
        ContentEncoding="gzip",
        ContentType="application/json",
        ACL="public-read",
    )
    if result["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise Exception(
            "Wrong status code " + result["ResponseMetadata"]["HTTPStatusCode"]
        )


def download_s3(s3, s3_bucket, s3_file):
    response = s3.get_object(
        Bucket=s3_bucket,
        Key=s3_file,
    )
    try:
        return json.loads(gzip.decompress(response["Body"].read()).decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return {"seq": 0, "instances": [], "error": "json"}
    # except S3.Client.exceptions.NoSuchKey:
    #    return {"seq": 0, "instances": [], "error": "NoSuchKey"}
    # except S3.Client.exceptions.InvalidObjectState:
    #    return {"seq": 0, "instances": [], "error": "InvalidObjectState"}


def store_file(discovery, filename):
    with open(filename, "w") as fh:
        json.dump(
            discovery, fh, separators=(",", ":"), allow_nan=False, ensure_ascii=True
        )


def store_gzip_file(discovery, filename):
    with gzip.open(filename, "wb") as fh:
        fh.write(
            json.dumps(
                discovery, separators=(",", ":"), allow_nan=False, ensure_ascii=True
            ).encode("ascii")
        )


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


def generate(seq):
    return {
        "version": 1,
        "seq": seq,
        "updated": get_updated(),
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


def geofilter(discovery):
    for instance in discovery["instances"]:
        del instance["geo"]
        del instance["country"]
    return discovery


def parse_args():
    parser = argparse.ArgumentParser(description="Generate geteduroam discovery files")
    parser.add_argument(
        "--aws-session",
        nargs="?",
        metavar="SESSION",
        help="AWS session from ~/.aws to use",
    )
    parser.add_argument(
        "--s3-bucket", nargs="?", metavar="BUCKET", help="S3 bucket to upload to"
    )
    parser.add_argument(
        "--s3-file-plain-v1",
        nargs="?",
        metavar="PATH",
        dest="s3_plain_v1",
        default="v1/discovery.json",
        help="path for plain V1 discovery file",
    )
    parser.add_argument(
        "--s3-file-geo-v1",
        nargs="?",
        metavar="PATH",
        dest="s3_geo_v1",
        default="v1/discovery-geo.json",
        help="path for geolocation V1 discovery file",
    )
    parser.add_argument(
        "--discovery-plain",
        nargs="?",
        metavar="FILE",
        default="discovery.json",
        help="name of plain discovery file to write",
    )
    parser.add_argument(
        "--discovery-geo",
        nargs="?",
        metavar="FILE",
        default="discovery-geo.json",
        help="name of geolocation discovery file to write",
    )
    parser.add_argument("-n", dest="store", action="store_false")
    parser.add_argument(
        "-f", "--force", action="store_true", help="S3 bucket to upload to"
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()

    if args["s3_bucket"]:
        if args["aws_session"]:
            session = boto3.Session(profile_name=args["aws_session"])
        else:
            session = boto3.Session()
        s3 = session.client("s3")
        old_discovery = download_s3(s3, args["s3_bucket"], args["s3_geo_v1"])
    else:
        old_discovery = get_old_discovery_from_file(args["discovery_geo"])
    if not "seq" in old_discovery or old_discovery["seq"] == 0:
        old_discovery = get_old_discovery_from_url()

    discovery = generate(seq=old_discovery["seq"] + 1)
    if args["force"] or discovery_needs_refresh(old_discovery, discovery):
        if args["store"]:
            print("Storing discovery seq %s" % discovery["seq"])
            store_file(discovery, args["discovery_geo"])
            store_gzip_file(discovery, args["discovery_geo"] + ".gz")
        if args["s3_bucket"]:
            print("Uploading discovery seq %s" % discovery["seq"])
            upload_s3(s3, discovery, args["s3_bucket"], args["s3_geo_v1"])

        geofilter(discovery)
        if args["store"]:
            store_file(discovery, args["discovery_plain"])
            store_gzip_file(discovery, args["discovery_plain"] + ".gz")
        if args["s3_bucket"]:
            upload_s3(s3, discovery, args["s3_bucket"], args["s3_plain_v1"])
    else:
        print("Unchanged %d" % old_discovery["seq"])
