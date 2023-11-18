from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', register, name='register'),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path('profile/<str:username>/', profile, name="profile"),
    path('edit_profile/<str:username>/', edit_profile, name='edit_profile'),
    path("create_site/", create_site, name="create_site"),
    path('proxy_route/<str:user_site_name>/<path:routes_on_original_site>/', proxy_route, name='proxy_route'),

]