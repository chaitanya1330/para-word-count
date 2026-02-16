from django.contrib import admin
from django.urls import path, include
from para_word_count.user import views as user_view
from django.contrib.auth import views as auth


def root_redirect(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('home')
    else:
        from django.shortcuts import redirect
        return redirect('login')


class CustomLogoutView(auth.LogoutView):
    http_method_names = ['get', 'post', 'options']


urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('user/', include('para_word_count.user.urls')),
    path('login/', user_view.Login, name='login'),
    path('logout/', user_view.Login, name='logout'),
    path('register/', user_view.register, name='register'),
    path('home/', user_view.home, name='home'),
]