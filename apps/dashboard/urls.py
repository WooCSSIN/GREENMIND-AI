from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard Group
    path('dashboard/', include([
        path('', views.home_view, name='home'),
        path('catalog/', views.catalog_view, name='catalog'),
        path('simulator/', views.simulator_view, name='simulator'),
        path('monitoring/', views.monitoring_view, name='monitoring'),
        path('esg/', views.esg_view, name='esg'),
        path('health-check/', views.health_check_view, name='health_check'),
    ])),
]
