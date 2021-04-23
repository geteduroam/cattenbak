from cattenbak import generate, geofilter, upload_s3
import boto3
import os

def lambda_handler(event, context):
	s3 = boto3.client('s3')
	discovery = generate()
	upload_s3(s3, discovery, os.environ['s3_bucket'], os.environ['s3_geo_v1'])
	geofilter(discovery)
	upload_s3(s3, discovery, os.environ['s3_bucket'], os.environ['s3_plain_v1'])
