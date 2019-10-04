from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class Variant(models.Model):
  variant_id = models.BigIntegerField(primary_key=True)
  price = models.BigIntegerField(default=0)
  base_price = models.BigIntegerField(default=0)
  promotion_percent = models.FloatField(default=0)
  is_promoting = models.BooleanField(default=False)
