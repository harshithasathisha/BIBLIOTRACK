from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('<int:pk>/', views.book_detail, name='book_detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('visual-search/', views.visual_search_view, name='visual_search'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('export/books/csv/', views.export_books_csv, name='export_books_csv'),
    path('export/users/csv/', views.export_users_csv, name='export_users_csv'),
    path('export/orders/csv/', views.export_orders_csv, name='export_orders_csv'),
]
