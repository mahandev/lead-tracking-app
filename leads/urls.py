
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CallWebhookView, LeadViewSet, DashboardAnalyticsView, dashboard_view, logout_view
from .landing_views import landing_page, pricing_page, features_page


router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')

urlpatterns = [
    
    path('', landing_page, name='landing_page'),
    path('pricing/', pricing_page, name='pricing_page'),
    path('features/', features_page, name='features_page'),
    
    
    path('logout/', logout_view, name='logout'),
    
    
    path('dashboard/', dashboard_view, name='dashboard'),
    
    
    path('leads/', include(router.urls)),  
    path('analytics/', DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    
    
    path('webhook/<uuid:token>/', CallWebhookView.as_view(), name='call-webhook'),
]