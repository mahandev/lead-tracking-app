
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Client, Lead

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'virtual_number', 'webhook_url_display', 'total_leads', 'created_at']
    list_filter = ['created_at']
    search_fields = ['business_name', 'user__username', 'virtual_number']
    readonly_fields = ['webhook_token', 'webhook_url_display', 'webhook_url_ngrok', 'created_at']
    
    fieldsets = (
        ('Business Information', {
            'fields': ('user', 'business_name', 'virtual_number')
        }),
        ('Webhook Configuration', {
            'fields': ('webhook_token', 'webhook_url_display', 'webhook_url_ngrok'),
            'description': 'Use these URLs to receive call notifications from your phone service provider.'
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def webhook_url_display(self, obj):
        url = f"http://127.0.0.1:8000/webhook/{obj.webhook_token}/"
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<input type="text" value="{}" readonly style="width: 400px; padding: 5px;" id="webhook-{}">'
            '<button onclick="copyToClipboard(\'webhook-{}\')" style="padding: 5px 10px;">Copy</button>'
            '</div>',
            url, obj.id, obj.id
        )
    webhook_url_display.short_description = 'Local Webhook URL'
    
    def webhook_url_ngrok(self, obj):
        url = f"https://4d87827f4691.ngrok-free.app/webhook/{obj.webhook_token}/"
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<input type="text" value="{}" readonly style="width: 400px; padding: 5px;" id="ngrok-{}">'
            '<button onclick="copyToClipboard(\'ngrok-{}\')" style="padding: 5px 10px;">Copy</button>'
            '</div>',
            url, obj.id, obj.id
        )
    webhook_url_ngrok.short_description = 'Ngrok Webhook URL'
    
    def total_leads(self, obj):
        return obj.leads.count()
    total_leads.short_description = 'Total Leads'
    
    class Media:
        js = ('admin/js/webhook_copy.js',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['customer_number', 'client', 'status', 'call_duration_display', 'call_timestamp', 'created_at']
    list_filter = ['status', 'client', 'call_timestamp', 'created_at']
    search_fields = ['customer_number', 'client__business_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Lead Information', {
            'fields': ('client', 'customer_number', 'status', 'notes')
        }),
        ('Call Details', {
            'fields': ('call_duration', 'recording_url', 'call_timestamp')
        }),
        ('Tracking', {
            'fields': ('first_contacted_at', 'created_at')
        }),
    )
    
    def call_duration_display(self, obj):
        if obj.call_duration == 0:
            return "Missed Call"
        elif obj.call_duration < 60:
            return f"{obj.call_duration}s"
        else:
            minutes = obj.call_duration // 60
            seconds = obj.call_duration % 60
            return f"{minutes}m {seconds}s"
    call_duration_display.short_description = 'Call Duration'