from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import Book, Review, Wishlist
from .forms import BookForm, ReviewForm, VisualSearchForm
from .visual_search import visual_search_engine
from .semantic_search import semantic_search_engine
from recommendations.recommendation_engine import recommendation_engine
from orders.models import Cart, Order, OrderItem
from accounts.models import User
import csv
from django.contrib.admin.views.decorators import staff_member_required
import logging

logger = logging.getLogger(__name__)

def book_list(request):
    books = Book.objects.all()
    genre = request.GET.get('genre')
    search = request.GET.get('search')
    sort = request.GET.get('sort', '-created_at')
    semantic_results = []
    use_semantic = False

    if genre:
        books = books.filter(genre=genre)

    if search:
        # First try exact/partial text search
        text_books = books.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(description__icontains=search)
        )

        # If text search returns few results (< 3), try semantic search
        if text_books.count() < 3:
            semantic_results = semantic_search_engine.search(search, limit=12)
            use_semantic = len(semantic_results) > 0

            if use_semantic:
                # Use semantic results, but exclude already found text matches
                text_book_ids = set(text_books.values_list('id', flat=True))
                semantic_books = [result['book'] for result in semantic_results if result['book'].id not in text_book_ids]
                books = list(text_books) + semantic_books
            else:
                books = text_books
        else:
            books = text_books

    if sort == 'price_low':
        books = books.order_by('price')
    elif sort == 'price_high':
        books = books.order_by('-price')
    elif sort == 'rating':
        books = books.order_by('-average_rating')
    elif sort == 'newest':
        books = books.order_by('-created_at')
    else:
        books = books.order_by(sort)

    # Handle pagination
    if isinstance(books, list):
        # For mixed results (text + semantic), paginate manually
        paginator = Paginator(books, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        # For QuerySet results
        paginator = Paginator(books, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    genres = Book.objects.values_list('genre', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'genres': genres,
        'current_genre': genre,
        'search_query': search,
        'current_sort': sort,
        'use_semantic': use_semantic,
        'semantic_results': semantic_results[:6] if use_semantic else [],  # Show top 6 semantic matches
    }
    return render(request, 'books/book_list_new.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all().order_by('-created_at')
    user_review = None
    in_wishlist = False

    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_wishlist = Wishlist.objects.filter(user=request.user, book=book).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        if 'add_review' in request.POST:
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.book = book
                review.user = request.user
                review.save()
                update_book_rating(book)
                # Track user interaction for recommendations
                recommendation_engine.update_user_interactions(request.user, book, 'review')
                messages.success(request, 'Review added successfully!')
                return redirect('book_detail', pk=pk)
        elif 'add_to_wishlist' in request.POST:
            Wishlist.objects.get_or_create(user=request.user, book=book)
            # Track user interaction for recommendations
            recommendation_engine.update_user_interactions(request.user, book, 'wishlist')
            messages.success(request, 'Book added to wishlist!')
            return redirect('book_detail', pk=pk)
        elif 'remove_from_wishlist' in request.POST:
            Wishlist.objects.filter(user=request.user, book=book).delete()
            messages.success(request, 'Book removed from wishlist!')
            return redirect('book_detail', pk=pk)

    form = ReviewForm()
    context = {
        'book': book,
        'reviews': reviews,
        'user_review': user_review,
        'form': form,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def wishlist_view(request):
    if request.method == 'POST' and 'remove_from_wishlist' in request.POST:
        book_id = request.POST.get('book_id')
        if book_id:
            Wishlist.objects.filter(user=request.user, book_id=book_id).delete()
            messages.success(request, 'Book removed from wishlist!')
        return redirect('wishlist')

    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('book')
    return render(request, 'books/wishlist.html', {'wishlist_items': wishlist_items})

def update_book_rating(book):
    reviews = book.reviews.all()
    if reviews.exists():
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        book.average_rating = round(avg_rating, 1)
        book.total_ratings = reviews.count()
    else:
        book.average_rating = 0.0
        book.total_ratings = 0
    book.save()

def visual_search_view(request):
    """Handle visual search by uploaded image"""
    visual_results = []
    form = VisualSearchForm()

    if request.method == 'POST':
        form = VisualSearchForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = request.FILES['image']
            try:
                visual_results = visual_search_engine.search_by_image(uploaded_image, top_k=12)
                if not visual_results:
                    messages.warning(request, 'No similar books found. Try uploading a clearer book cover image.')
                else:
                    messages.success(request, f'Found {len(visual_results)} visually similar books!')
            except Exception as e:
                logger.error(f"Visual search error: {e}")
                messages.error(request, 'An error occurred during visual search. Please try again.')

    context = {
        'form': form,
        'visual_results': visual_results,
    }
    return render(request, 'books/visual_search.html', context)

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with analytics and management features"""
    # Book statistics
    total_books = Book.objects.count()
    books_by_genre = Book.objects.values('genre').annotate(count=Count('id')).order_by('-count')
    top_rated_books = Book.objects.filter(average_rating__gt=0).order_by('-average_rating')[:10]
    recent_books = Book.objects.order_by('-created_at')[:10]

    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    recent_users = User.objects.order_by('-date_joined')[:10]

    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    total_revenue = Order.objects.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Review statistics
    total_reviews = Review.objects.count()
    average_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0

    # Handle backend test actions
    connection_status = 'connected'  # Assume connected for now
    book_count = total_books

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'test_connection':
            # Simple connection test - check if database is accessible
            try:
                Book.objects.count()
                connection_status = 'connected'
                messages.success(request, 'Backend connection test successful!')
            except Exception as e:
                connection_status = 'error'
                messages.error(request, f'Backend connection test failed: {str(e)}')

        elif action == 'seed_books':
            # Seed sample books
            try:
                sample_books = [
                    {
                        'title': 'The Great Gatsby',
                        'author': 'F. Scott Fitzgerald',
                        'isbn': '978-0-7432-7356-5',
                        'price': 12.99,
                        'stock_quantity': 25,
                        'genre': 'Fiction',
                        'description': 'A classic American novel set in the Jazz Age.',
                        'publication_year': 1925,
                    },
                    {
                        'title': 'To Kill a Mockingbird',
                        'author': 'Harper Lee',
                        'isbn': '978-0-06-112008-4',
                        'price': 14.99,
                        'stock_quantity': 20,
                        'genre': 'Fiction',
                        'description': 'A gripping tale of racial injustice and childhood innocence.',
                        'publication_year': 1960,
                    },
                    {
                        'title': '1984',
                        'author': 'George Orwell',
                        'isbn': '978-0-452-28423-4',
                        'price': 13.99,
                        'stock_quantity': 30,
                        'genre': 'Dystopian',
                        'description': 'A dystopian social science fiction novel.',
                        'publication_year': 1949,
                    },
                    {
                        'title': 'Pride and Prejudice',
                        'author': 'Jane Austen',
                        'isbn': '978-0-14-143951-8',
                        'price': 11.99,
                        'stock_quantity': 15,
                        'genre': 'Romance',
                        'description': 'A romantic novel of manners.',
                        'publication_year': 1813,
                    },
                    {
                        'title': 'The Catcher in the Rye',
                        'author': 'J.D. Salinger',
                        'isbn': '978-0-316-76948-0',
                        'price': 10.99,
                        'stock_quantity': 18,
                        'genre': 'Fiction',
                        'description': 'A controversial novel about teenage rebellion.',
                        'publication_year': 1951,
                    },
                ]

                books_created = 0
                for book_data in sample_books:
                    # Check if book already exists
                    if not Book.objects.filter(isbn=book_data['isbn']).exists():
                        Book.objects.create(**book_data)
                        books_created += 1

                if books_created > 0:
                    messages.success(request, f'Successfully seeded {books_created} sample books!')
                    # Update book count
                    book_count = Book.objects.count()
                else:
                    messages.info(request, 'Sample books already exist in the database.')

            except Exception as e:
                messages.error(request, f'Failed to seed books: {str(e)}')

        elif action == 'check_book_count':
            # Just refresh the count
            book_count = Book.objects.count()
            messages.info(request, f'Current book count: {book_count}')

    context = {
        'total_books': total_books,
        'books_by_genre': books_by_genre,
        'top_rated_books': top_rated_books,
        'recent_books': recent_books,
        'total_users': total_users,
        'active_users': active_users,
        'recent_users': recent_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 1),
        'connection_status': connection_status,
        'book_count': book_count,
    }
    return render(request, 'books/admin_dashboard.html', context)

@staff_member_required
def export_books_csv(request):
    """Export books data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Author', 'ISBN', 'Genre', 'Price', 'Stock',
        'Average Rating', 'Total Ratings', 'Created At'
    ])

    books = Book.objects.all().order_by('id')
    for book in books:
        writer.writerow([
            book.id,
            book.title,
            book.author,
            book.isbn,
            book.genre,
            book.price,
            book.stock_quantity,
            book.average_rating,
            book.total_ratings,
            book.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response

@staff_member_required
def export_users_csv(request):
    """Export users data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Username', 'Email', 'First Name', 'Last Name',
        'Date Joined', 'Is Active', 'Is Staff'
    ])

    users = User.objects.all().order_by('id')
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.is_active,
            user.is_staff,
        ])

    return response

@staff_member_required
def export_orders_csv(request):
    """Export orders data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'User', 'Status', 'Total Amount', 'Created At',
        'Shipping Address', 'Payment Method'
    ])

    orders = Order.objects.select_related('user').order_by('-created_at')
    for order in orders:
        writer.writerow([
            order.id,
            order.user.username,
            order.status,
            order.total_amount,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.shipping_address,
            order.payment_method,
        ])

    return response
