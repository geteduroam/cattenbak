from cattenbak import Cattenbak, sigil
import boto3
import os
import gzip
import json
from typing import Optional, List, Any, Dict, Set, Union


def lambda_handler(event, context) -> str:
	s3 = boto3.client("s3")
	cattenbak = Cattenbak(
		letswifi_stub=os.environ["letswifi_stub"] if "letswifi_stub" in os.environ else None
	)

	old_discovery = download_s3(s3, os.environ["s3_bucket"], os.environ["s3_read_path"])
	try:
		old_seq = old_discovery[sigil]["seq"]
	except:
		old_seq = None
	new_discovery = cattenbak.generateDiscovery(old_seq=old_seq)
	if seq := cattenbak.discoveryIsUpToDate(old_discovery, new_discovery):
		result = "Refresh not needed at seq %s\r\n" % (seq)
	else:
		upload_s3(s3, new_discovery, os.environ["s3_bucket"], os.environ["s3_write_path"])
		result = "Uploaded discovery seq %s" % new_discovery[sigil]["seq"]

	print(result)  # Goes to CloudWatch
	return result  # Goes to Lambda UI when testing


def upload_s3(s3, discovery: Dict, s3_bucket: str, s3_file: str) -> None:
	discovery_body = gzip.compress(
		json.dumps(
			discovery,
			separators=(",", ":"),
			allow_nan=False,
			sort_keys=True,
			ensure_ascii=True,
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


def download_s3(
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
		return json.loads(gzip.decompress(response["Body"].read()).decode("utf-8"))
	except json.decoder.JSONDecodeError as e:
		print(e)
		return None
