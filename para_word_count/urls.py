"""
URL configuration for para_word_count project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path

# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]


from django.contrib import admin
from django.urls import path, include
from para_word_count.user import views as user_view
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required

# Root redirect view
def root_redirect(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('home')
    else:
        from django.shortcuts import redirect
        return redirect('login')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    
    # REST Framework
    path('api-auth/', include('rest_framework.urls')),
    
    ##### user related path##########################
    path('user/', include('para_word_count.user.urls')),
    path('login/', user_view.Login, name='login'),
    path('logout/', auth.LogoutView.as_view(template_name='user/index.html'), name='logout'),
    path('register/', user_view.register, name='register'),
    path('home/', user_view.home, name='home'),
]