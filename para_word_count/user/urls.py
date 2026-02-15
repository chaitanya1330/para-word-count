from django.urls import path, include
from django.conf import settings
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('api/save-paragraph/', views.save_paragraph_api, name='save_paragraph_api'),
    path('api/search-word/', views.search_word_api, name='search_word_api'),
]