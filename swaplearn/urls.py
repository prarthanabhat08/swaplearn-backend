from django.urls import path
from . import views
from .views import get_user, update_profile

urlpatterns = [
    path('', views.home),

    path('api/add-user/', views.api_add_user),
    path('api/users/', views.api_get_users),
    path('api/login/', views.api_login),

    path('api/save-skills/', views.save_user_skills),
    path('api/user-skills/<int:user_id>/', views.get_user_skills),
    path('api/match/<int:user_id>/', views.find_matches),

    path('api/send-request/', views.send_request),

    path('api/requests/<int:user_id>/', views.get_requests),
    path('api/accept-request/', views.accept_request),
    path('api/reject-request/', views.reject_request),

    path('api/discover/<int:user_id>/', views.discover_users),

    path('api/chats/<int:user_id>/', views.get_chats),

    path('api/messages/<str:room_id>/', views.get_messages),
    path('api/send-message/', views.send_message),

    path('api/update-profile/', update_profile),
    path('api/get-user/<int:user_id>/', get_user),

    path('api/save_calendar_slots/', views.save_calendar_slots),
    path('api/get_calendar_slots/', views.get_calendar_slots),
    
    path('api/end_session/', views.end_session),
    
    path('api/get-profile/<int:user_id>/', views.get_profile),
]