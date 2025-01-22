import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError
from .logger import logger

#send image pre-signed url to model inference service, todo: get models pre-signed url to return.
def request_to_process_image(image_s3_key):
    presigned_url = cache.get(image_s3_key)
    if not presigned_url:
        try:
            presigned_url = generate_s3_presigned_for_image(image_s3_key)
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for key {image_s3_key}: {e}")
            return Response({'error': 'Unable to re-generate presigned URL'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    flask_service_url = settings.MODEL_INFERNECE_SERVICE_DOMAIN
    payload = {"presigned_url": presigned_url}
    try:
        response = requests.post(flask_service_url, json=payload)
        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response({"error": "Inference service returned an error", "details": response.text}, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to call inference service: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# generate s3 presigned url for image and save url in cache
def generate_s3_presigned_for_image(image_s3_key):
    try:
        s3_client = settings.AWS_S3_CLIENT
        image_pre_signed_url = s3_client.generate_presigned_url('get_object',
                                        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                'Key': image_s3_key},
                                        ExpiresIn=settings.AWS_PRESIGNED_URL_EXPIRATION)
        cache.set(image_s3_key, image_pre_signed_url, timeout=3600)
        return image_pre_signed_url
    except NoCredentialsError:
        logger.error("No AWS credentials found.")
        raise NoCredentialsError("AWS credentials are not available.")
    except ClientError as e:
        logger.error(f"S3 Client error while generating URL: {e}")
        raise ClientError(f"Failed to generate presigned URL: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error occurred during presigned URL generation.")
        raise Exception(f"An unexpected error occurred: {str(e)}")