from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('send/', views.send_message, name='send_message'),
    path('messages/', views.get_messages, name='get_messages'),
    path('clear/', views.clear_chat, name='clear_chat'),
    path('history/', views.chat_history, name='chat_history'),
]
