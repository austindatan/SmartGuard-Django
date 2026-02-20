from django.urls import path
from . import views

app_name = 'smartguard'

urlpatterns = [
    path('analytics/', views.analytics, name='analytics'),
]
