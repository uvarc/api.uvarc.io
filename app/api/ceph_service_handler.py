import sys
import boto3
from botocore.config import Config


def create_bucket(access_key, secret_key, bucket_name):
    session = boto3.session.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    # Object Gateway URL
    s3client = session.client(
        's3',
        endpoint_url='https://machi-nas-s.hpc.virginia.edu:7480',
        config=Config()
    )
    # create [my-new-bucket]
    bucket = s3client.create_bucket(Bucket=bucket_name)


def main():
    args = sys.argv[1:]
    print("S3 access_key="+args[0])
    print("S3 secret_key="+args[1])
    print("Create Bucket Name="+args[1])
    create_bucket(args[0], args[1], args[2])


if __name__ == '__main__':
    main()
