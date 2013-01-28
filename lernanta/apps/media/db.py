from django.db import models

from drumbeat.models import ModelBase

class Image(ModelBase):

    image_file = models.FileField(upload_to="uploads/images")
    uploader_uri = models.CharField(max_length=256)
