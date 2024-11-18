from cattenbak import Cattenbak, sigil_v2, sigil_v3
import boto3
import brotlicffi as brotli
import os
import gzip
import json
from typing import Optional, List, Any, Dict, Set, Union


def lambda_handler(event, context) -> str:
	s3 = boto3.client("s3")
	bucket = os.environ["s3_bucket"]

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
	new_discovery = cattenbak.generateDiscovery(old_seq=old_seq)
	if seq := cattenbak.discoveryIsUpToDate(old_discovery, new_discovery):
		result = "Refresh not needed at seq %s\r\n" % (seq)
		print(result)  # Goes to CloudWatch
	else:
		result = "Updating to discovery seq %s" % new_discovery[sigil_v3]["seq"]
		print(result)  # Goes to CloudWatch
		if "s3_write_path_v2" in os.environ:
			discovery_v2 = {sigil_v2: new_discovery[sigil_v2]}
			upload_s3_json(
				s3,
				discovery_v2,
				bucket,
				os.environ["s3_write_path_v2"],
				"gzip",
			)
		if "s3_write_path_v3" in os.environ:
			discovery_v3 = {sigil_v3: new_discovery[sigil_v3]}
			upload_s3_json(
				s3,
				discovery_v3,
				bucket,
				os.environ["s3_write_path_v3"],
				"br",
			)

	return result  # Goes to Lambda UI when testing


def upload_s3_json(
	s3, discovery: Dict, s3_bucket: str, s3_file: str, compressor: str
) -> None:
	if compressor == "gzip":
		c = gzip
	elif compressor == "br":
		c = brotli
	else:
		raise Exception("Wrong compressor provided")
	discovery_body = c.compress(
		json.dumps(
			discovery,
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
		Body=discovery_body,
		CacheControl="public, max-age=900, s-maxage=300, stale-while-revalidate=86400, stale-if-error=2592000",
		ContentEncoding=compressor,
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
		c = None
		if "ContentEncoding" in response:
			if response["ContentEncoding"] == "gzip":
				c = gzip
			elif response["ContentEncoding"] == "br":
				c = brotli
			else:
				raise Exception(
					"Unknown ContentEncoding: " + response["ContentEncoding"]
				)
		return (
			json.loads(c.decompress(response["Body"].read()).decode("utf-8"))
			if c
			else response["Body"].read().decode("utf-8")
		)
	except json.decoder.JSONDecodeError as e:
		print(e)
		return None
