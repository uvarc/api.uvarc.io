# shiny-build-api

A simple build API for DCOS-based Shiny apps

* [Resources](#resources)
  * [Generate Keys](#generate-keys)
  * [Add a User](#add-a-user)
  * [Delete a User](#delete-a-user)
* [Using the Keys](#using-the-keys)
  * [S3](#s3)
  * [SQS](#sqs)
* [Build and Deploy](#build-and-deploy)

## Resources

### Generate Keys

```/shiny/keys/{userid}/{apikey}```

An HTTP GET request of this resource returns a temporary set of credentials.

```
curl https://build.uvasomrc.io/shiny/keys/mst3k/51865a316af843df9a13ab7s8dk72cef
```

This endpoint verifies that the userid and apikey submitted by the user are registered and verified as matching. If confirmed as a match, the API generates a set of AWS keys under the AssumeRole function of STS. These tokens can be used for specific AWS operations and are valid for 900 seconds.

### Add a User

```/shiny/user/{userid}/{apikey}```

Available only to administrators. Submit a POST request to this endpoint with a JSON payload containing the `userid` of the user to create. An `apikey` will be returned to you.

Using `curl` this would look like this:

```
curl -i -H "Content-Type: application/json" -X POST -d '{"userid":"abc3z"}' https://build.uvasomrc.io/shiny/user/mst3k/51865a316af843df9a13ab7s8dk72cef
```

### Delete a user

```/shiny/user/{userid}/{apikey}```

Available only to administrators. Like the above method, an HTTP DELETE request will remove the user specified in your JSON payload:

```
curl -i -H "Content-Type: application/json" -X DELETE -d '{"userid":"abc3z"}' https://build.uvasomrc.io/shiny/user/mst3k/51865a316af843df9a13ab7s8dk72cef
```

### Logging

The three API calls above are logged to a DynamoDB table named `shinyapi_log`.


## Using the Keys

The output of a key generation request will appear something like this:
```
{
  "access_key": "ASIAW5BKWSI57EU6FQWQ",
  "secret_key": "FtIyGpWnD5rKhMc5iNBBF3NbiLz+BoZXScQnWLfc",
  "session_token": "FQoGZXIvYXdzEK7//////////wEaDAXTbvFiraPFDY2uJiL2AdTAHer0ggLtD00QQHPQp4BQW7cibnfyN/XF8teoPAguiJU2iJfVAQBPhvLtt6qA59r3m+SisV3Gt7ny1Lb+YTy8RjzjbnvvXn37Lopx1DsbmRPjM++NPj8pr87aDrdD9qyMXj2/ojb2aXUUzgBWpAk8aQ9pLO7Idr1stHbHvjjp4CXnt0dcFocHAdx6+gW7Nt2ykywJYjLHgGpHyeJBF4WEVDYW5kt6GwjW0Ye1RmCSbP3s38FlAqEqwDgIWrfuyrDq23fXotzhzXxG6jAlyCJ6AGaEnoWDITBBZJ5ylX0w8ILB0tgy09OKlsbdjn4NkifEMttSYyiqwcPkBQ==",
  "status": "ok",
  "valid_for": "900s"
}
```

Parse that payload to populate the following local environment variables:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`
* `AWS_SESSION_TOKEN`

Your environment should also define a `AWS_DEFAULT_REGION` set as `us-east-1`.

### S3

Using these temporary credentials, your code can upload an object to the `shiny-build` bucket. Note that these credentials do not allow retrieving or listing objects. Your call should resemble this AWS CLI action:

```
aws s3 cp local_bundle.zip s3://dcos-shiny/
```

In R, a possible candidate for this process is the [**aws.s3**](https://www.rdocumentation.org/packages/aws.s3/versions/0.3.12) package.

### SQS

Using the temporary credentials, your code should also trigger a Shiny build and deployment by sending a message to SQS. While all SQS messages require a `message-body` to be defined, other fields can be defined and populated as part of the message. This is helpful for passing and parsing specific metdata about a job.
This may include fields like `jobid`, `userid`, the full path to an object in S3, etc.

```
aws sqs send-message --queue-url https://sqs.us-east-1.amazonaws.com/474683445819/shiny-build \
  --message-body "Here is a simple message I want to send." \
  --message-attributes '{"actual-parameter": {"StringValue": "actual-value", "DataType": "String"}, "another-parameter": {"StringValue": "another-value", "DataType": "String"}}'

```

In R, a possible candidate for this process is the [**aws.sqs**](https://www.rdocumentation.org/packages/aws.sqs/versions/0.1.10) package.


## Build and Deploy

With the ability to upload an archive to S3 and send an SQS message to trigger a build, the rest of the process is automated. A build daemon will catch the new SQS message, parse its metadata, and know what to do in order to build the Shiny app container, push it to a repository, and deploy it to DCOS.

1. User authors working Shiny application code.
2. User triggers the R build package, with `userid` and `apikey` properly configured.
3. R build package requests temporary keys.
4. R build package creates an archive, uploads to S3, and sends SQS message.
5. Shiny build API daemon catches the message and creates a deployed container.

Depending upon the size of the payloads involved, this entire process should take between 5-20 minutes for normal-sized applications.
