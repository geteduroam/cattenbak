# Installation on AWS Lambda instance

1. Create an empty Lambda instance, and give it a role that can write to the correct S3 bucket

2. Run `make cattenbak.zip` and upload it to the Lambda function

3. Go to **Configuration** -> **General configuration** -> **Edit**

4. Set the timeout to at least 10 seconds

5. Add a trigger, **EventBridge (CloudWatch Events)**

6. Set the trigger to `rate(1 hour)`

7. Go to **Configuration** -> **Environment variables** -> **Edit**

8. Set the following variables

| Key         | Value                 |
|-------------|-----------------------|
| s3_bucket   | disco-geteduroam-app  |
| s3_path     | v1/discovery.json     |
