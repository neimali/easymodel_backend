from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings
import os
import uuid
import json
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from .utils import request_to_process_image, generate_s3_presigned_for_image
from .logger import logger
# Create your views here.

class UploadImageView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.s3_client = settings.AWS_S3_CLIENT  # Initialize S3 client once

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        MAX_FILE_SIZE_MB = 10 
        if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return Response({'error': 'File too large'}, status=status.HTTP_400_BAD_REQUEST)
        
        file_name = f"{uuid.uuid4()}-{file.name}"
        folder_name = 'user_images'
        image_s3_key = f"{folder_name}/{file_name}"

        #Upload image to AWS S3
        try:
            self.s3_client.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, image_s3_key, ExtraArgs={'ContentType': file.content_type})
        except boto3.exceptions.S3UploadFailedError as e:
            logger.error(f"Upload failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ClientError as e:
            logger.error(f"S3 Client error: {e}")
            return Response({'error': f"S3 Client error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        #generate image presigned url
        try:
            image_pre_signed_url = generate_s3_presigned_for_image(image_s3_key)
            return Response({'image_s3_key': image_s3_key},status=status.HTTP_201_CREATED)
        except NoCredentialsError:
            return Response({'error': 'AWS credentials are not available'}, status=status.HTTP_400_BAD_REQUEST)
        except ClientError as e:
            return Response({'error': f'Failed to generate presigned URL: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateModelsView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def post(self, request):
        data  = json.loads(request.body)
        image_s3_key = data['image_s3_key']
        response = request_to_process_image(image_s3_key)
        return response