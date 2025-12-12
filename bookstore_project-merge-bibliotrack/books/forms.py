from django import forms
from .models import Book, Review

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'description', 'genre', 'price',
                 'stock_quantity', 'cover_image', 'publication_date', 'publisher',
                 'page_count', 'language']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your review...'}),
        }

class VisualSearchForm(forms.Form):
    image = forms.ImageField(
        label='Upload an image to find similar books',
        help_text='Upload a book cover image to find visually similar books in our catalog.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'})
    )
