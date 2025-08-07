
from datetime import timezone
from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    
    def update(self, instance, validated_data):
        
        if validated_data.get('status') == 'contacted' and instance.status != 'contacted':
            
            if not instance.first_contacted_at:
                validated_data['first_contacted_at'] = timezone.now()
        return super().update(instance, validated_data)

    class Meta:
        model = Lead
        fields = [
            'id', 'customer_number', 'status', 'notes', 'created_at',
            'call_timestamp', 'call_duration', 'recording_url', 'first_contacted_at'
        ]
        
        read_only_fields = ['created_at']