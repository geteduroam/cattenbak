# Installation on EC2 instance

1. Set up an instance with Amazon Linux
	* A minimal instance is fine, but you need an external IPv4 address for S3 to work
	* Give the instance an IAM role so it can publish to S3

2. Install dependencies and cattenbak

		sudo yum install git python3-pip
		git clone https://github.com/geteduroam/cattenbak.git
		cd cattenbak


3. Do a test-run

		make run
		cattenbak/cattenbak.py --s3-bucket geteduroam-disco


4. Configure the timer
	* Modify `cattenbak-update.service` so the path and arguments are correct

			ExecStart=/opt/cattenbak/cattenbak.py --s3-bucket geteduroam-disco

5. Enable the timer

			systemctl link `pwd`/cattenbak-update.service
			systemctl enable `pwd`/cattenbak-update.timer
