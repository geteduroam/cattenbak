from cattenbak import (
	generate,
	geofilter,
	download_s3,
	upload_s3,
	get_old_discovery_from_url,
	discovery_needs_refresh,
)
import boto3
import os


def lambda_handler(event, context):
	s3 = boto3.client("s3")
	old_discovery = download_s3(s3, os.environ["s3_bucket"], os.environ["s3_geo_v1"])
	if not "seq" in old_discovery or old_discovery["seq"] == 0:
		print("WARNING: Unable to download old discovery from S3")
		print("Fallback to downloading from discovery URL")
		old_discovery = get_old_discovery_from_url()

	# This may crash, but in that case we have lost our seq,
	# so a crash is warranted
	discovery = generate(seq=old_discovery["seq"] + 1)

	if old_discovery:
		discovery["seq"] = max(discovery["seq"], old_discovery["seq"] + 1)
	if discovery_needs_refresh(old_discovery, discovery):
		print("Uploading discovery seq %s" % discovery.seq)
		upload_s3(s3, discovery, os.environ["s3_bucket"], os.environ["s3_geo_v1"])
		geofilter(discovery)
		upload_s3(s3, discovery, os.environ["s3_bucket"], os.environ["s3_plain_v1"])
	else:
		print("Unchanged %d" % old_discovery["seq"])
