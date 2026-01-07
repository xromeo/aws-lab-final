import json
import boto3
import logging
from botocore.exceptions import ClientError

# Logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global initialization
s3_client = boto3.client('s3')
BUCKET_NAME = "IMAGES_BUCKET"

def app_handler(event, context):
    """
    Main Lambda handler.
    Detects HTTP method for both REST API and HTTP API (API Gateway v1/v2).
    """
    request_context = event.get("requestContext", {})
    http_method = event.get("httpMethod") or request_context.get("http", {}).get("method")
    path_params = event.get("pathParameters") or {}

    logger.info(f"Processing {http_method} request")
    
    if http_method == "POST":
        return prepare_upload(event)
    
    if http_method == "GET" and "objectKey" in path_params:
        # Decode the object key in case it contains special characters
        from urllib.parse import unquote
        return download_redirect(unquote(path_params["objectKey"]))
    
    return error_response(404, "Route not found")

def prepare_upload(event):
    """
    Generates a pre-signed URL for direct upload to S3 (POST /files)
    """
    try:
        body = json.loads(event.get("body") or "{}")
        raw_filename = body.get("filename")

        if not raw_filename:
            return error_response(400, "Missing 'filename' in request body")

        # Security: prevent path traversal
        filename = os.path.basename(raw_filename)
        object_key = f"uploads/{filename}"
        content_type = body.get("contentType", "application/octet-stream")

        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': object_key,
                'ContentType': content_type
            },
            ExpiresIn=900  # 15 minutes
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "objectKey": object_key,
                "uploadUrl": upload_url
            })
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return error_response(500, "Could not generate upload URL")

def download_redirect(object_key):
    """
    Generates a pre-signed download URL and redirects the client
    (GET /files/{objectKey})
    """
    try:
        # Improvement: verify the object exists before generating the signed URL
        s3_client.head_object(Bucket=BUCKET_NAME, Key=object_key)

        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': object_key},
            ExpiresIn=3600  # 1 hour
        )

        logger.info(f"Redirecting user to download: {object_key}")
        
        return {
            "statusCode": 307,  # Temporary Redirect
            "headers": {
                "Location": signed_url,
                "Access-Control-Allow-Origin": "*"  # Useful for lab/demo environments
            },
            "body": ""
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            return error_response(404, f"File '{object_key}' not found")
        logger.error(f"S3 Error: {str(e)}")
        return error_response(500, "Internal S3 error")

def error_response(status, message):
    """
    Helper function for consistent error responses
    """
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
