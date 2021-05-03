# Installation on EC2 instance

1. Set up an instance with Amazon Linux
	* A minimal instance is fine, but you need an external IPv4 address for S3 to work
	* Give the instance an IAM role so it can publish to S3

2. Install dependencies and cattenbak

		sudo yum install git python3-pip
		git clone https://github.com/geteduroam/cattenbak.git
		cd cattenbak


3. Do a test-run

		make S3_URL=s3://geteduroam-disco/v1-test/discovery.json upload


4. Configure the timer
	* Modify `cattenbak-update.service` so the path and arguments are correct

			ExecStart=/usr/bin/make -b /home/ec2-user/cattenbak/Makefile S3_URL=s3://geteduroam-disco/v1/discovery.json upload

5. Enable the timer

			systemctl link `pwd`/cattenbak-update.service
			systemctl enable `pwd`/cattenbak-update.timer
