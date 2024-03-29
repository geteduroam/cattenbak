# Installation on AWS Lambda instance (manual)

1. Create an empty Lambda instance, and give it a role that can write to the correct S3 bucket

2. Run `make cattenbak.zip` and upload it to the Lambda function, this can also be done with `make deploy`

3. Go to **Configuration** -> **General configuration** -> **Edit**

4. Set the timeout to at least 10 seconds

5. Add a trigger, **EventBridge (CloudWatch Events)**

6. Set the trigger to `rate(1 hour)`

7. Go to **Configuration** -> **Environment variables** -> **Edit**

8. Set the following variables (remove `-staging` when going for production)

| Key               | Value                       |
|-------------------|-----------------------------|
| **s3_bucket**     | `geteduroam-disco`          |
| **s3_read_path**  | `v1/discovery.json`         |
| **s3_write_path** | `v1-staging/discovery.json` |
