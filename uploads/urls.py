from django.urls import path
from .views import UploadImageView, GenerateModelsView

urlpatterns = [
    path('upload_image/', UploadImageView.as_view(), name='upload-image'),
    path('generate_models/', GenerateModelsView.as_view(), name='generate-models')
]
