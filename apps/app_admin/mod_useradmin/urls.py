from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    # User Admin
    path('', views.user_list, name='useradmin_list'),
    path('create/', views.user_create, name='useradmin_create'),
    path('<int:user_id>/edit/', views.user_edit, name='useradmin_edit'),
    path('<int:user_id>/delete/', views.user_delete, name='useradmin_delete'),
    path('bulk/', views.user_bulk, name='useradmin_bulk'),
]
