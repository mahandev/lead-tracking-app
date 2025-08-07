from django.db import models
from django.contrib.auth.models import User
import uuid 

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    business_name = models.CharField(max_length=200)
    webhook_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    virtual_number = models.CharField(max_length=20, unique=True, help_text="The virtual number assigned to this client")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='leads')
    customer_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp from our server when the lead was created.")
    call_timestamp = models.DateTimeField(help_text="Editable timestamp from the webhook for the actual call time.", null=True, blank=True)
    call_duration = models.IntegerField(default=0, help_text="Duration of the call in seconds.")
    recording_url = models.URLField(max_length=512, blank=True, null=True)
    first_contacted_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when status was first changed to 'Contacted'.")

    def __str__(self):
        return f"Lead from {self.customer_number} for {self.client.business_name}"