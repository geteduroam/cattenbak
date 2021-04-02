from cattenbak import (
	generate,
	download_s3,
	upload_s3,
	discovery_needs_refresh,
)
import boto3
import os


def lambda_handler(event, context):
	s3 = boto3.client("s3")
	old_discovery = download_s3(s3, os.environ["s3_bucket"], os.environ["s3_path"])
	old_serial = old_discovery["serial"] if "serial" in old_discovery else 0

	discovery = generate(old_serial=old_serial)

	if discovery_needs_refresh(old_discovery, discovery):
		print("Uploading discovery serial %s" % discovery["serial"])
		upload_s3(s3, discovery, os.environ["s3_bucket"], os.environ["s3_path"])
	else:
		print("Unchanged %d" % old_discovery["serial"])
