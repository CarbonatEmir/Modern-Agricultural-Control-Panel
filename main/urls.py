#Tüm bağlantıları buradan sağlayacağız, views dahil
'''
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
'''
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('gecmis/', views.analiz_gecmisi, name='analiz_gecmisi'),
    path('kameralar/', views.kameralar, name='kameralar'),
    path('ayarlar/', views.ayarlar, name='ayarlar'),
    path('api/analiz-yap/', views.yapay_zeka_analiz_api, name='api_analiz'),
]