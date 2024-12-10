from cattenbak import Cattenbak, sigil_v2, sigil_v3
import boto3
import os
import gzip
import json
from typing import Optional, List, Any, Dict, Set, Union


def lambda_handler(event, context) -> str:
	s3 = boto3.client("s3")
	bucket = os.environ["s3_bucket"]
	cache_control = os.environ["cache_control"]
	minimal_app_version = os.environ["minimal_app_version"]

	legacy_provider_hosts = []
	if "legacy_provider_hosts" in os.environ:
		legacy_provider_hosts = os.environ["legacy_provider_hosts"].split(",")
	legacy_stub = os.environ["legacy_stub"] if "legacy_stub" in os.environ else None
	cattenbak = Cattenbak(
		legacy_provider_hosts=legacy_provider_hosts,
		legacy_stub=legacy_stub,
	)

	old_discovery = download_s3_json(s3, bucket, os.environ["s3_read_path_v3"])
	try:
		old_seq = old_discovery[sigil_v3]["seq"]
	except:
		old_seq = None
	new_discovery = cattenbak.generateDiscovery(
		old_seq=old_seq, minimal_app_version=minimal_app_version
	)
	if seq := cattenbak.discoveryIsUpToDate(old_discovery, new_discovery):
		result = "Refresh not needed at seq %s\r\n" % (seq)
		print("%s\n" % result)  # Goes to CloudWatch
	else:
		result = "Updating to discovery seq %s" % new_discovery[sigil_v3]["seq"]
		print("%s\n" % result)  # Goes to CloudWatch
		if "s3_write_path_v2" in os.environ:
			discovery_v2 = {sigil_v2: new_discovery[sigil_v2]}
			upload_s3_json(
				s3,
				data=discovery_v2,
				s3_bucket=bucket,
				s3_file=os.environ["s3_write_path_v2"],
				cache_control=cache_control,
			)
		if "s3_write_path_v3" in os.environ:
			discovery_v3 = {sigil_v3: new_discovery[sigil_v3]}
			upload_s3_json(
				s3,
				data=discovery_v3,
				s3_bucket=bucket,
				s3_file=os.environ["s3_write_path_v3"],
				cache_control=cache_control,
			)
		print("completed\n")  # Goes to CloudWatch

	return result  # Goes to Lambda UI when testing


def upload_s3_json(
	s3, data: Dict, s3_bucket: str, s3_file: str, cache_control: str
) -> None:
	data_body = gzip.compress(
		json.dumps(
			data,
			separators=(",", ":"),  # Prevent space after comma and colon
			allow_nan=False,
			sort_keys=True,  # Make output reproducable
			ensure_ascii=True,  # Compresses better
		).encode("ascii")
		+ b"\r\n"
	)
	result = s3.put_object(
		Bucket=s3_bucket,
		Key=s3_file,
		Body=data_body,
		CacheControl=cache_control,
		ContentEncoding="gzip",
		ContentType="application/json",
		ACL="public-read",
	)
	if result["ResponseMetadata"]["HTTPStatusCode"] != 200:
		raise Exception(
			"Wrong status code " + result["ResponseMetadata"]["HTTPStatusCode"]
		)


def download_s3_json(
	s3, s3_bucket: str, s3_file: str
) -> Optional[Dict[str, Union[List, str, int]]]:
	try:
		response = s3.get_object(
			Bucket=s3_bucket,
			Key=s3_file,
		)
	except s3.exceptions.NoSuchKey as e:
		print(e)
		return None
	except s3.exceptions.InvalidObjectState as e:
		print(e)
		return None

	try:
		compressed = False
		if "ContentEncoding" in response:
			if response["ContentEncoding"] == "gzip":
				compressed = True
			else:
				raise Exception(
					"Unknown ContentEncoding: " + response["ContentEncoding"]
				)
		return (
			json.loads(gzip.decompress(response["Body"].read()).decode("utf-8"))
			if compressed
			else response["Body"].read().decode("utf-8")
		)
	except json.decoder.JSONDecodeError as e:
		print(e)
		return None
