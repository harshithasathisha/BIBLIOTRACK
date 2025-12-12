from django.db import models
from django.contrib.auth.models import User
from books.models import Book

class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('wishlist', 'Wishlist'),
        ('cart', 'Cart'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    weight = models.FloatField(default=1.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'book', 'interaction_type']

    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.book.title}"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    score = models.FloatField()
    reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'book']
        ordering = ['-score']

    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.book.title} ({self.score})"
