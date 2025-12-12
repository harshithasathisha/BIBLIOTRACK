import os
import tempfile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import Book, Review, Wishlist
from orders.models import Order, OrderItem
from .semantic_search import SemanticSearchEngine
from .visual_search import VisualSearchEngine
import logging

logger = logging.getLogger(__name__)

class BookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            isbn="1234567890123",
            description="A test book description",
            genre="Fiction",
            price=29.99,
            stock_quantity=10,
            publisher="Test Publisher",
            page_count=300,
            language="English"
        )

    def test_book_creation(self):
        """Test that a book can be created with all fields"""
        self.assertEqual(self.book.title, "Test Book")
        self.assertEqual(self.book.author, "Test Author")
        self.assertEqual(self.book.price, 29.99)
        self.assertEqual(self.book.stock_quantity, 10)

    def test_book_str_method(self):
        """Test the string representation of a book"""
        self.assertEqual(str(self.book), "Test Book by Test Author")

class BookViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            description="A test book",
            genre="Fiction",
            price=19.99
        )

    def test_book_list_view(self):
        """Test that book list view loads correctly"""
        response = self.client.get(reverse('book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")

    def test_book_detail_view(self):
        """Test that book detail view loads correctly"""
        response = self.client.get(reverse('book_detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")

    def test_book_search(self):
        """Test book search functionality"""
        response = self.client.get(reverse('book_list'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")

class ReviewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title="Review Test Book",
            author="Test Author",
            description="A book for review testing",
            genre="Fiction",
            price=15.99
        )

    def test_review_creation(self):
        """Test that a review can be created"""
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            rating=5,
            comment="Great book!"
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great book!")
        self.assertEqual(str(review), f"Review by {self.user.username} for {self.book.title}")

class WishlistTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='wishlistuser',
            email='wishlist@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title="Wishlist Book",
            author="Test Author",
            description="A book for wishlist testing",
            genre="Fiction",
            price=12.99
        )

    def test_wishlist_creation(self):
        """Test that a book can be added to wishlist"""
        wishlist_item = Wishlist.objects.create(
            user=self.user,
            book=self.book
        )
        self.assertEqual(wishlist_item.user, self.user)
        self.assertEqual(wishlist_item.book, self.book)

class SemanticSearchTest(TestCase):
    def setUp(self):
        # Create test books
        self.book1 = Book.objects.create(
            title="Python Programming",
            author="John Doe",
            description="Learn Python programming",
            genre="Technology",
            price=39.99
        )
        self.book2 = Book.objects.create(
            title="Django Web Development",
            author="Jane Smith",
            description="Build web apps with Django",
            genre="Technology",
            price=49.99
        )

    def test_semantic_search_initialization(self):
        """Test that semantic search engine initializes properly"""
        engine = SemanticSearchEngine()
        # Test that model is loaded (may be None if SentenceTransformer fails)
        # This is more of a smoke test
        self.assertIsInstance(engine, SemanticSearchEngine)

class VisualSearchTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Visual Search Book",
            author="Test Author",
            description="A book for visual search testing",
            genre="Fiction",
            price=25.99
        )

    def test_visual_search_initialization(self):
        """Test that visual search engine initializes properly"""
        engine = VisualSearchEngine()
        # Test that it's an instance
        self.assertIsInstance(engine, VisualSearchEngine)

class OrderTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='ordertest',
            email='order@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title="Order Test Book",
            author="Test Author",
            description="A book for order testing",
            genre="Fiction",
            price=19.99,
            stock_quantity=5
        )

    def test_order_creation(self):
        """Test that an order can be created"""
        order = Order.objects.create(
            user=self.user,
            total_amount=19.99,
            shipping_address="123 Test St",
            payment_method="card"
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, 19.99)
        self.assertEqual(order.status, 'pending')  # default status

    def test_order_item_creation(self):
        """Test that order items can be created"""
        order = Order.objects.create(
            user=self.user,
            total_amount=39.98,
            shipping_address="123 Test St"
        )
        order_item = OrderItem.objects.create(
            order=order,
            book=self.book,
            quantity=2,
            price=19.99
        )
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.book, self.book)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, 19.99)

class AdminDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        # Create some test data
        self.book = Book.objects.create(
            title="Admin Test Book",
            author="Test Author",
            description="A book for admin testing",
            genre="Fiction",
            price=29.99
        )

    def test_admin_dashboard_requires_staff(self):
        """Test that admin dashboard requires staff permissions"""
        # Test without login
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test with regular user
        regular_user = get_user_model().objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_admin_dashboard_access(self):
        """Test that admin can access dashboard"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")

class ExportTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        # Create test data
        self.book = Book.objects.create(
            title="Export Test Book",
            author="Test Author",
            isbn="1234567890123",
            description="A book for export testing",
            genre="Fiction",
            price=19.99,
            stock_quantity=10
        )
        self.user = get_user_model().objects.create_user(
            username='exportuser',
            email='export@example.com',
            password='testpass123'
        )

    def test_export_books_csv(self):
        """Test CSV export for books"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('export_books_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="books_export.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('Export Test Book', content)
        self.assertIn('Test Author', content)

    def test_export_users_csv(self):
        """Test CSV export for users"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('export_users_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="users_export.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('exportuser', content)
        self.assertIn('export@example.com', content)

    def test_export_orders_csv(self):
        """Test CSV export for orders"""
        # Create a test order
        order = Order.objects.create(
            user=self.user,
            total_amount=19.99,
            shipping_address="123 Export St",
            payment_method="card"
        )
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('export_orders_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="orders_export.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('exportuser', content)
        self.assertIn('19.99', content)
