from cattenbak import (
	generate,
	discovery_needs_refresh,
)
import boto3
import os
import gzip
import json
from typing import Optional, List, Any, Dict, Set, Union
from typing_extensions import TypeGuard


def lambda_handler(event, context) -> str:
	s3 = boto3.client("s3")
	old_discovery = download_s3(s3, os.environ["s3_bucket"], os.environ["s3_path"])
	old_seq = (
		old_discovery["seq"]
		if old_discovery and isinstance(old_discovery["seq"], int)
		else None
	)

	discovery = generate(old_seq=old_seq)

	if (
		old_seq is None
		or not is_list_dict(old_discovery)
		or discovery_needs_refresh(old_discovery, discovery)
	):
		upload_s3(s3, discovery, os.environ["s3_bucket"], os.environ["s3_path"])
		result = "Uploaded discovery seq %s" % discovery["seq"]
	else:
		result = "Unchanged %d" % old_seq

	print(result)  # Goes to CloudWatch
	return result  # Goes to Lambda UI when testing


def upload_s3(s3, discovery: str, s3_bucket: str, s3_file: str) -> None:
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
) -> Optional[Dict[str, Union[List, int]]]:
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


def is_list_dict(val: Optional[Dict[str, Any]]) -> TypeGuard[Dict[str, List]]:
	return val is not None and all(isinstance(x, List) for x in val.values())
