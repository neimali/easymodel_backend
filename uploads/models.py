from django.db import models
from django.contrib.auth.models import AbstractUser

# 自定义用户模型
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

# 图片模型
class Images(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,  # 用户删除时，删除关联的图片
        related_name="images",  # 可通过 user.images 查询用户的所有图片
    )
    s3_path = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"Image owned by {self.user.email} - Path: {self.s3_path}"
