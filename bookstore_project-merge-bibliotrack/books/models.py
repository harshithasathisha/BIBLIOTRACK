from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    GENRE_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('mystery', 'Mystery'),
        ('romance', 'Romance'),
        ('sci-fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('self-help', 'Self-Help'),
        ('poetry', 'Poetry'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('thriller', 'Thriller'),
        ('comedy', 'Comedy'),
        ('adventure', 'Adventure'),
        ('children', 'Children'),
        ('young-adult', 'Young Adult'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300)
    isbn = models.CharField(max_length=13, unique=True, blank=True)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='other')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True)
    publication_date = models.DateField(blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    average_rating = models.FloatField(default=0.0)
    total_ratings = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['book', 'user']

    def __str__(self):
        return f"{self.user.username}'s review of {self.book.title}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'book']

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.book.title}"
