from django.db import models
from django.contrib.auth.models import User


class Site(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.URLField()


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    page_views = models.IntegerField(default=0)
    data_sent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)