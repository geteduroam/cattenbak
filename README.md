# Cattenbak

A scraper for cat.eduroam.org that generates discovery files for geteduroam

## Usage

1. Optionally, create a virtual environment

	python3 -m venv /opt/cattenbak-venv
	source /opt/cattenbak-venv/bin/activate

2. Install cattenbak's dependencies via

	make cattenbak                  		# Without venv
	pip3 install -r requirements.txt		# With venv

... or make sure you use the system python3 and install the correct packages.

1. Modify cattenbak.py to generate the right output

Make sure that the files are served with the following headers:

	Access-Control-Allow-Origin: *
	Access-Control-Allow-Methods: GET, HEAD
	Cache-Control: public, max-age=900, s-maxage=300, stale-while-revalidate=86400, stale-if-error=2592000
	X-Content-Type-Options: nosniff

You may also add a Content Security Policy

	Content-Security-Policy: default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none';

Note: Amazon does not support `X-Content-Type-Options` or `Content-Security-Policy` in S3 or Cloudfront
without using a Lambda@Edge function.  These headers are recommended but not required.

The `Access-Control-*` headers can be set using CORS configuration in S3.
These are necessary to read the discovery file from a browser using JavaScript.


## Upload to Amazon S3

The cattenbak.py script uploads to S3 via the upload_s3() function using the boto3 library.

Make sure that you have the AWS configuration files, or set the correct environment variables with credentials.

	% cat ~/.aws/config
	[geteduroam]
	region=eu-central-1
	output=json
	% cat ~/.aws/config
	[geteduroam]
	aws_access_key_id = XXXXXXXXXXXXXXXXXXXX
	aws_secret_access_key = YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY

Make sure that the S3 bucket has the following CORS configuration

	[
		{
			"AllowedHeaders": ["*"],
			"AllowedMethods": ["GET", "HEAD"],
			"AllowedOrigins": ["*"],
			"ExposeHeaders": []
		}
	]


## systemd timers

You can use systemd timers to periodically generate/upload, as root:

	systemctl link $(pwd)/cattenbak-update.service
	systemctl enable $(pwd)/cattenbak-update.timer


## Contributing

After making changes, please use black for syntax corrections.


## License

See COPYING
