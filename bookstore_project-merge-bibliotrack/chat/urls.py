from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:book_id>/', views.book_club_chat, name='book_club_chat'),
    path('book/<int:book_id>/send/', views.send_message, name='send_message'),
    path('book/<int:book_id>/messages/', views.get_messages, name='get_messages'),
    path('book/<int:book_id>/comments/', views.book_comments, name='book_comments'),
    path('book/<int:book_id>/add-comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comment/<int:comment_id>/reply/', views.reply_to_comment, name='reply_to_comment'),
]
