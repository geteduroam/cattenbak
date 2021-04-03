# Installation on EC2 instance

1. Set up an instance with Amazon Linux
	* A minimal instance is fine, but you need an external IPv4 address for S3 to work
	* Give the instance an IAM role so it can publish to S3

2. Install dependencies and cattenbak

		yum install git python3-pip
		git clone https://github.com/geteduroam/cattenbak.git
		cd cattenbak

	* The [../cattenbak.py] file contains some settings, `s3_bucket`, `s3_file` and `aws_session` that you can change if needed

3. Do a test-run

		make run

4. Install the timer
	* Modify `cattenbak-update.service` so the path is correct

		systemctl link `pwd`/cattenbak-update.service
		systemctl enable `pwd`/cattenbak-update.timer
