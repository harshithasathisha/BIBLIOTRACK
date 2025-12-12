from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('profile/addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
]
