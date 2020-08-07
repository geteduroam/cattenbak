# Cattenbak

A scraper for cat.eduroam.org that generates discovery files for geteduroam

## Usage

1. Generate the files

		make

2. Upload the `disco` folder to a web server

Make sure that the files are served with the following header:

	Access-Control-Allow-Origin: *
	Cache-Control: must-revalidate
	X-Content-Type-Options: nosniff

You may also add a Content Security Policy

	Content-Security-Policy: default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none';


## Upload to Amazon S3

The generated file can be uploaded to S3 using

	make aws


## Contributing

After making changes, please run

	make camera-ready


## License

This software is released under the BSD-3-Clause, but uses a library under the AGPL-3.0.
Generated files are static files and are not affected by the AGPL-3.0,
even when hosted on a webserver.
