from django.urls import path
from . import views

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:book_id>/', views.update_cart_item, name='update_cart_item'),

    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),

    # Order URLs
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('track-order/', views.order_tracking, name='order_tracking'),
]
