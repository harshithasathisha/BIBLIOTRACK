from django.contrib import admin
from .models import Book, Review, Wishlist

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'price', 'stock_quantity', 'average_rating')
    list_filter = ('genre', 'publisher', 'language', 'created_at')
    search_fields = ('title', 'author', 'isbn', 'description')
    readonly_fields = ('average_rating', 'total_ratings', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'isbn', 'description', 'genre')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Publication Details', {
            'fields': ('publication_date', 'publisher', 'page_count', 'language')
        }),
        ('Media', {
            'fields': ('cover_image',)
        }),
        ('Ratings', {
            'fields': ('average_rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('added_at',)
