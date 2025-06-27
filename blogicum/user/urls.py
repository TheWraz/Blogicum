from django.urls import path

from .views import profile_view, edit_profile


app_name = 'user'

urlpatterns = [
    path('<str:username>/', profile_view, name='profile'),
    path('<str:username>/edit/', edit_profile, name='edit_profile'),
]