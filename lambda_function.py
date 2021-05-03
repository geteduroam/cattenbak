from cattenbak import (
	generate,
	discovery_needs_refresh,
)
import boto3
import os
import gzip
import json


def lambda_handler(event, context):
	s3 = boto3.client("s3")
	old_discovery = download_s3(s3, os.environ["s3_bucket"], os.environ["s3_path"])
	old_serial = old_discovery["serial"] if old_discovery else None

	discovery = generate(old_serial=old_serial)

	result = ''
	if discovery_needs_refresh(old_discovery, discovery):
		upload_s3(s3, discovery, os.environ["s3_bucket"], os.environ["s3_path"])
		result = "Uploaded discovery serial %s" % discovery["serial"]
	else:
		result = "Unchanged %d" % old_discovery["serial"]

	print(result)  # Goes to CloudWatch
	return result  # Goes to Lambda UI when testing


def upload_s3(s3, discovery, s3_bucket, s3_file):
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


def download_s3(s3, s3_bucket, s3_file):
	try:
		response = s3.get_object(
			Bucket=s3_bucket,
			Key=s3_file,
		)
	except s3.exceptions.NoSuchKey as e:
		print(e)
		return None
	except s3.exceptions.InvalidObjectState:
		print(e)
		return None

	try:
		return json.loads(gzip.decompress(response["Body"].read()).decode("utf-8"))
	except json.decoder.JSONDecodeError as e:
		print(e)
		return None
