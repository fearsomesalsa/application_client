from django.db import models


class Upload(models.Model):
    upload = models.FileField(upload_to="media")
