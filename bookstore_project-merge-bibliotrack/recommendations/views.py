from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Recommendation
from .recommendation_engine import recommendation_engine

@login_required
def recommendations_view(request):
    """Display personalized recommendations for the user"""
    # Get cached recommendations or generate new ones
    recommendations = Recommendation.objects.filter(user=request.user)\
        .select_related('book')[:12]  # Limit to 12 for display

    if not recommendations.exists():
        # Generate recommendations if none exist
        recs = recommendation_engine.generate_recommendations(request.user, top_k=12)
        recommendations = []
        for rec in recs:
            # Create temporary objects for display
            class TempRec:
                def __init__(self, book, score, reason):
                    self.book = book
                    self.score = score
                    self.reason = reason
            recommendations.append(TempRec(rec['book'], rec['score'], rec['reason']))

    context = {
        'recommendations': recommendations,
    }
    return render(request, 'recommendations/recommendations.html', context)

@require_POST
@login_required
def refresh_recommendations(request):
    """Refresh recommendations for the user"""
    try:
        recommendation_engine.refresh_recommendations(request.user)
        return JsonResponse({'success': True, 'message': 'Recommendations refreshed!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def similar_books(request, book_id):
    """Get similar books based on content"""
    from books.models import Book

    try:
        target_book = Book.objects.get(id=book_id)
        all_books = Book.objects.exclude(id=book_id)[:20]  # Limit for performance

        similarities = recommendation_engine._get_content_similarity(target_book, all_books)
        similar_books = sorted(
            [(book, score) for book, score in similarities.items() if score > 0.3],
            key=lambda x: x[1],
            reverse=True
        )[:6]  # Top 6 similar books

        data = {
            'similar_books': [
                {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'cover_url': book.cover_image.url if book.cover_image else None,
                    'similarity': round(score * 100, 1)
                }
                for book, score in similar_books
            ]
        }
        return JsonResponse(data)
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
