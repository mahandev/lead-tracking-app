from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from .serializers import LeadSerializer
from django.db.models import Count, Avg, F, DurationField
from .models import Client, Lead
from django.db.models.functions import TruncDate, Extract

@method_decorator(csrf_exempt, name='dispatch')
class CallWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request, token, *args, **kwargs):
        try:
            client = Client.objects.get(webhook_token=token)
        except Client.DoesNotExist:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        params = request.GET
        
        direction = params.get('Direction', '').lower()
        if direction != 'incoming':
            return Response({"message": "Only incoming calls are processed"}, status=status.HTTP_200_OK)
        
        call_sid = params.get('CallSid')
        customer_number = params.get('From')
        call_status = params.get('CallStatus', '').lower()
        
        if not call_sid or not customer_number:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        if call_status == 'completed':
            lead_status = 'contacted'
        elif call_status in ['no-answer', 'busy', 'failed']:
            lead_status = 'new'
        else:
            lead_status = 'new'
        
        call_duration = int(params.get('DialCallDuration', 0))
        recording_url = params.get('RecordingUrl')
        start_time_str = params.get('StartTime')
        
        call_timestamp = None
        if start_time_str:
            try:
                call_timestamp = parse_datetime(start_time_str)
            except:
                pass
        
        if not call_timestamp:
            call_timestamp = timezone.now()
        
        lead, created = Lead.objects.get_or_create(
            client=client,
            customer_number=customer_number,
            call_timestamp=call_timestamp,
            defaults={
                'status': lead_status,
                'call_duration': call_duration,
                'recording_url': recording_url,
            }
        )
        
        if not created:
            lead.status = lead_status
            lead.call_duration = call_duration
            if recording_url:
                lead.recording_url = recording_url
            lead.save()
        
        return Response({"message": "Lead processed", "created": created}, status=status.HTTP_200_OK)
    


class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer

    def get_queryset(self):
        return Lead.objects.filter(client__user=self.request.user).order_by('-call_timestamp')

class DashboardAnalyticsView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({"error": "Client profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        status_counts = Lead.objects.filter(client=client).values('status').annotate(count=Count('status'))
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        leads_over_time = Lead.objects.filter(client=client, call_timestamp__gte=thirty_days_ago)\
            .extra(select={'day': "DATE(call_timestamp)"})\
            .values('day').annotate(count=Count('id')).order_by('day')
            
        response_time_data = Lead.objects.filter(
            client=client,
            first_contacted_at__isnull=False
        ).aggregate(
            avg_response_time=Avg(F('first_contacted_at') - F('created_at'))
        )
        
        total_leads = Lead.objects.filter(client=client).count()
        total_missed = Lead.objects.filter(client=client, call_duration=0).count()
        
        avg_response_seconds = 0
        if response_time_data['avg_response_time']:
            avg_response_seconds = response_time_data['avg_response_time'].total_seconds()
            
        data = {
            'kpis': {
                'total_leads': total_leads,
                'total_missed_calls': total_missed,
                'avg_response_seconds': round(avg_response_seconds)
            },
            'leads_by_status': list(status_counts),
            'leads_over_time': list(leads_over_time)
        }
        
        return Response(data)
    

@login_required
def dashboard_view(request):
    if request.method == 'POST' and not hasattr(request.user, 'client'):
        business_name = request.POST.get('business_name')
        if business_name:
            Client.objects.create(
                user=request.user,
                business_name=business_name,
                virtual_number=f"+1-555-{request.user.id:04d}"
            )
            messages.success(request, f'Welcome to VirtualPhone Pro, {business_name}! Your virtual phone system is now active.')
    
    try:
        client = request.user.client
    except Client.DoesNotExist:
        return render(request, 'dashboard/setup_profile.html')

    days = int(request.GET.get('days', 30))
    date_from = timezone.now() - timedelta(days=days)
    
    leads_queryset = Lead.objects.filter(client=client)
    
    status_filter = request.GET.get('status')
    if status_filter:
        leads_queryset = leads_queryset.filter(status=status_filter)
    
    duration_filter = request.GET.get('duration')
    if duration_filter == '0':
        leads_queryset = leads_queryset.filter(call_duration=0)
    elif duration_filter == '1-30':
        leads_queryset = leads_queryset.filter(call_duration__range=(1, 30))
    elif duration_filter == '31-120':
        leads_queryset = leads_queryset.filter(call_duration__range=(31, 120))
    elif duration_filter == '121+':
        leads_queryset = leads_queryset.filter(call_duration__gt=120)
    
    search_filter = request.GET.get('search')
    if search_filter:
        leads_queryset = leads_queryset.filter(customer_number__icontains=search_filter)

    status_counts = list(leads_queryset.values('status').annotate(count=Count('status')))

    leads_over_time_data = leads_queryset.filter(call_timestamp__gte=date_from)\
        .annotate(day=TruncDate('call_timestamp'))\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')

    leads_over_time = {
        "labels": [item['day'].strftime('%b %d') for item in leads_over_time_data],
        "data": [item['count'] for item in leads_over_time_data]
    }
    
    total_leads = leads_queryset.count()
    converted_leads = leads_queryset.filter(status='converted').count()
    missed_calls = leads_queryset.filter(call_duration=0).count()
    
    response_time_data = leads_queryset.filter(
        first_contacted_at__isnull=False
    ).aggregate(
        avg_response_time=Avg(F('first_contacted_at') - F('created_at'))
    )
    
    avg_response_seconds = 0
    if response_time_data['avg_response_time']:
        avg_response_seconds = response_time_data['avg_response_time'].total_seconds()
    
    all_leads = leads_queryset.order_by('-call_timestamp')
    
    analytics = {
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0,
        'missed_calls': missed_calls,
        'missed_call_rate': (missed_calls / total_leads * 100) if total_leads > 0 else 0,
        'avg_response_time_minutes': avg_response_seconds / 60 if avg_response_seconds > 0 else 0,
        'avg_call_duration': leads_queryset.filter(call_duration__gt=0).aggregate(
            avg_duration=Avg('call_duration')
        )['avg_duration'] or 0
    }

    duration_ranges = [
        ('0-30s', 0, 30),
        ('31-60s', 31, 60),
        ('1-2m', 61, 120),
        ('2-5m', 121, 300),
        ('5m+', 301, 999999)
    ]
    
    duration_data = []
    for label, min_dur, max_dur in duration_ranges:
        if max_dur == 999999:
            count = leads_queryset.filter(call_duration__gte=min_dur).count()
        else:
            count = leads_queryset.filter(call_duration__range=(min_dur, max_dur)).count()
        duration_data.append({'label': label, 'count': count})
    
    hourly_data = leads_queryset.exclude(call_timestamp__isnull=True)\
        .annotate(hour=Extract('call_timestamp', 'hour'))\
        .values('hour')\
        .annotate(count=Count('id'))\
        .order_by('hour')
    
    hourly_pattern = {str(hour): 0 for hour in range(24)}
    for item in hourly_data:
        hourly_pattern[str(item['hour'])] = item['count']
    
    business_hours = ['6', '8', '10', '12', '14', '16', '18', '20']
    hourly_chart_data = {
        'labels': [f"{int(h)}:00" for h in business_hours],
        'data': [hourly_pattern[h] for h in business_hours]
    }

    context = {
        'client': client,
        'all_leads': all_leads,
        'status_counts_json': json.dumps(status_counts),
        'leads_over_time_json': json.dumps(leads_over_time),
        'duration_data_json': json.dumps(duration_data),
        'hourly_data_json': json.dumps(hourly_chart_data),
        'analytics': analytics,
        'current_filters': {
            'days': days,
            'status': status_filter,
            'duration': duration_filter,
            'search': search_filter
        }
    }
    return render(request, 'dashboard/enhanced_dashboard.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('landing_page')