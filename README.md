# Cattenbak

A scraper for cat.eduroam.org that generates discovery files for geteduroam

## Usage

1. Generate the files

		make

2. Upload the `disco` folder to a web server

Make sure that the files are served with the following header:

	Access-Control-Allow-Origin: *
	Cache-Control: public, max-age=3600, stale-while-revalidate=86400, stale-if-error=2592000
	X-Content-Type-Options: nosniff

You may also add a Content Security Policy

	Content-Security-Policy: default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none';


## Upload to Amazon S3

Make sure that you have installed the [AWS Command Line Interface](https://aws.amazon.com/cli/)
and that you have configuration to allow it to upload somewhere

	% cat ~/.aws/config
	[geteduroam]
	region=eu-central-1
	output=json
	%cat ~/.aws/config
	[geteduroam]
	aws_access_key_id = XXXXXXXXXXXXXXXXXXXX
	aws_secret_access_key = YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY


The generated file can be uploaded to S3 using

	make -B prod

## systemd timers

You can use systemd timers to periodically upload, as root:

	apt-get install php-cli php-curl python-pip make
	pip install awscli
	systemctl link $(pwd)/contrib/systemd/cattenbak.service
	systemctl enable $(pwd)/contrib/systemd/cattenbak.timer

As the geteduroam user

	cp contrib/gitconfig ~/.gitconfig
	git config user.name "$(hostname -f)"
	git config user.email "$(whoami)@$(hostname -f)"
	ssh-keygen -t ed25519 -C "$(hostname -f)"

Make sure that the key in \~/.ssh/id_ed25519.pub can be used to upload to this repo


## Contributing

After making changes, please run

	make camera-ready


## License

This software is released under the BSD-3-Clause, but uses a library under the AGPL-3.0.
Generated files are static files and are not affected by the AGPL-3.0,
even when hosted on a webserver.
