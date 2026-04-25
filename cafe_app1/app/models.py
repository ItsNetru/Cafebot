from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("cooking", "Cooking"),
        ("delivering", "Delivering"),
        ("done", "Done"),
    ]

    user_id = models.IntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    items = models.TextField()
    total = models.IntegerField()
    address = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)