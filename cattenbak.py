#!/usr/bin/env python3
import requests
import json
import gzip
import datetime
import boto3
import argparse

cat_api = "https://cat.eduroam.org/new_test/user/API.php"
cat_download_api = "https://cat.eduroam.org/user/API.php"


def get_old_discovery_from_file(filename):
    try:
        with open(filename, "r") as fh:
            return json.load(fh)
    except json.decoder.JSONDecodeError:
        return {"serial": 0, "instances": [], "error": "json"}
    except FileNotFoundError:
        return {"serial": 0, "instances": [], "error": "file"}


def discovery_needs_refresh(old_discovery, new_discovery):
    return (
        old_discovery == None
        or "instances" not in old_discovery
        or not old_discovery["instances"] == new_discovery["instances"]
    )


def upload_s3(s3, discovery, s3_bucket, s3_file):
    discovery_body = gzip.compress(
        json.dumps(
            discovery, separators=(",", ":"), allow_nan=False, sort_keys=True, ensure_ascii=True
        ).encode("ascii")
        + b"\r\n"
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
    try:
        response = s3.get_object(
            Bucket=s3_bucket,
            Key=s3_file,
        )
    except s3.exceptions.NoSuchKey:
       return {"serial": 0, "instances": [], "error": "NoSuchKey"}
    except s3.exceptions.InvalidObjectState:
       return {"serial": 0, "instances": [], "error": "InvalidObjectState"}

    try:
        return json.loads(gzip.decompress(response["Body"].read()).decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return {"serial": 0, "instances": [], "error": "json"}


def store_file(discovery, filename):
    with open(filename, "w") as fh:
        json.dump(
            discovery, fh, separators=(",", ":"), allow_nan=False, sort_keys=True, ensure_ascii=True
        )
        fh.write("\r\n")


def store_gzip_file(discovery, filename):
    with gzip.open(filename, "wb") as fh:
        fh.write(
            json.dumps(
                discovery, separators=(",", ":"), allow_nan=False, sort_keys=True, ensure_ascii=True
            ).encode("ascii")
            + b"\r\n"
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


def generate(old_serial=None):
    candidate_serial = int(datetime.datetime.utcnow().strftime("%Y%m%d00"))
    if old_serial == None:
        # Use a high number so we have a better chance to be over
        # Let's hope this doesn't happen more than once a day ;)
        serial = candidate_serial + 80
    elif candidate_serial <= old_serial:
        serial = old_serial + 1
    else:
        serial = candidate_serial

    return {
        "version": 1,
        "serial": serial,
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
        "--aws-session",
        nargs="?",
        metavar="SESSION",
        help="AWS session from ~/.aws to use",
    )
    parser.add_argument(
        "--s3-bucket", nargs="?", metavar="BUCKET", help="S3 bucket to upload to"
    )
    parser.add_argument(
        "--s3-path",
        nargs="?",
        metavar="PATH",
        dest="s3_path",
        default="v1/discovery.json",
        help="path where to write V1 discovery file in S3",
    )
    parser.add_argument(
        "--file-path",
        nargs="?",
        metavar="FILE",
        dest="file_path",
        default="discovery.json",
        help="path where to write V1 discovery file to fileystem",
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
        old_discovery = download_s3(s3, args["s3_bucket"], args["s3_path"])
    else:
        old_discovery = get_old_discovery_from_file(args["file_path"])
    if not "serial" in old_discovery:
        old_discovery = {"serial":0}

    discovery = generate(old_serial=old_discovery["serial"])
    if args["force"] or discovery_needs_refresh(old_discovery, discovery):
        if args["store"]:
            print("Storing discovery serial %s" % discovery["serial"])
            store_file(discovery, args["file_path"])
            store_gzip_file(discovery, args["file_path"] + ".gz")
        if args["s3_bucket"]:
            print("Uploading discovery serial %s" % discovery["serial"])
            upload_s3(s3, discovery, args["s3_bucket"], args["s3_path"])

    else:
        print("Unchanged %d" % old_discovery["serial"])
