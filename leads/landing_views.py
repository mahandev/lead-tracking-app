
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from accounts.forms import CustomUserCreationForm
from .models import Client, Lead
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

def landing_page(request):
    """
    Beautiful landing page explaining the virtual phone service
    Redirects logged-in users to dashboard
    """
    
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    
    stats = {
        'total_calls_handled': 150000,
        'businesses_served': 1200,
        'average_response_time': '2.3 minutes',
        'missed_call_reduction': '95%'
    }
    
    features = [
        {
            'title': 'Instant Lead Capture',
            'description': 'Never miss a potential customer again. Every call is automatically captured and organized.',
            'icon': 'phone-call'
        },
        {
            'title': 'Real-time Analytics',
            'description': 'Get detailed insights into your call patterns, response times, and conversion rates.',
            'icon': 'bar-chart'
        },
        {
            'title': 'Smart Call Routing',
            'description': 'Intelligent routing ensures calls reach the right person at the right time.',
            'icon': 'route'
        },
        {
            'title': 'Call Recording & Playback',
            'description': 'Review important calls and improve your customer service quality.',
            'icon': 'mic'
        },
        {
            'title': 'Lead Management',
            'description': 'Track, categorize, and follow up on leads with our intuitive dashboard.',
            'icon': 'users'
        },
        {
            'title': 'Integration Ready',
            'description': 'Seamlessly integrate with your existing CRM and business tools.',
            'icon': 'link'
        }
    ]
    
    testimonials = [
        {
            'name': 'Sarah Johnson',
            'company': 'Johnson Realty',
            'text': 'VirtualPhone Pro helped us capture 40% more leads and reduced our response time dramatically.',
            'rating': 5
        },
        {
            'name': 'Mike Chen',
            'company': 'Chen Marketing Agency',
            'text': 'The analytics dashboard gives us insights we never had before. Game changer!',
            'rating': 5
        },
        {
            'name': 'Lisa Rodriguez',
            'company': 'Rodriguez Consulting',
            'text': 'Setup was incredibly easy and the call quality is crystal clear.',
            'rating': 5
        }
    ]
    
    context = {
        'stats': stats,
        'features': features,
        'testimonials': testimonials,
    }
    
    return render(request, 'landing/index.html', context)

def pricing_page(request):
    """
    Pricing page with different plans
    """
    plans = [
        {
            'name': 'Starter',
            'price': 29,
            'period': 'month',
            'features': [
                '1 Virtual Number',
                'Up to 100 calls/month',
                'Basic Analytics',
                'Email Support',
                'Call Recording (7 days)'
            ],
            'recommended': False
        },
        {
            'name': 'Professional',
            'price': 79,
            'period': 'month',
            'features': [
                '3 Virtual Numbers',
                'Up to 500 calls/month',
                'Advanced Analytics',
                'Priority Support',
                'Call Recording (30 days)',
                'CRM Integration',
                'Custom Reports'
            ],
            'recommended': True
        },
        {
            'name': 'Enterprise',
            'price': 199,
            'period': 'month',
            'features': [
                'Unlimited Virtual Numbers',
                'Unlimited calls',
                'Premium Analytics',
                '24/7 Phone Support',
                'Call Recording (1 year)',
                'Advanced Integrations',
                'Custom Development',
                'Dedicated Account Manager'
            ],
            'recommended': False
        }
    ]
    
    return render(request, 'landing/pricing.html', {'plans': plans})

def features_page(request):
    """
    Detailed features page
    """
    return render(request, 'landing/features.html')

def signup_with_redirect(request):
    """
    Custom signup view that redirects to dashboard setup
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Let\'s set up your virtual phone system.')
            return redirect('/dashboard/')  
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})
