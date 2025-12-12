from django.contrib import admin
from .models import UserInteraction, Recommendation

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'interaction_type', 'weight', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('timestamp',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'score', 'reason', 'created_at')
    list_filter = ('created_at', 'reason')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('created_at',)
