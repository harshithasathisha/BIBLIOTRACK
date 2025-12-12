from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommendations_view, name='recommendations'),
    path('refresh/', views.refresh_recommendations, name='refresh_recommendations'),
    path('similar/<int:book_id>/', views.similar_books, name='similar_books'),
]
