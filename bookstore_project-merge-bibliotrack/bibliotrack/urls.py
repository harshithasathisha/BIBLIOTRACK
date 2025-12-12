from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('books/', include('books.urls')),
    path('orders/', include('orders.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('chat/', include('chat.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('', include('books.urls')),  # Root URL for book list
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
