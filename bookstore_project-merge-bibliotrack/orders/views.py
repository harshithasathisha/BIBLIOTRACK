from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid
import razorpay

from .models import Cart, CartItem, Order, OrderItem
from books.models import Book

@login_required
def cart_view(request):
    """Display user's shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('book').all()

    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
    tax = subtotal * Decimal('0.08')  # 8% tax
    total = subtotal + shipping + tax

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'orders/cart.html', context)

@require_POST
@login_required
def add_to_cart(request, book_id):
    """Add book to cart"""
    try:
        book = get_object_or_404(Book, id=book_id)

        # Check if book is in stock
        if book.stock_quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Book is out of stock'})

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            book=book,
            defaults={'quantity': 1}
        )

        if not item_created:
            # Update quantity if item already exists
            if cart_item.quantity >= book.stock_quantity:
                return JsonResponse({'success': False, 'error': 'Not enough stock available'})
            cart_item.quantity += 1
            cart_item.save()

        cart.updated_at = timezone.now()
        cart.save()

        return JsonResponse({
            'success': True,
            'message': f'{book.title} added to cart',
            'cart_count': cart.items.count()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def remove_from_cart(request, book_id):
    """Remove book from cart"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, book_id=book_id)

        cart_item.delete()
        cart.updated_at = timezone.now()
        cart.save()

        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart.items.count()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def update_cart_item(request, book_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Quantity must be at least 1'})

        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, book_id=book_id)

        # Check stock availability
        if quantity > cart_item.book.stock_quantity:
            return JsonResponse({'success': False, 'error': 'Not enough stock available'})

        cart_item.quantity = quantity
        cart_item.save()
        cart.updated_at = timezone.now()
        cart.save()

        # Calculate new totals
        subtotal = sum(item.total_price for item in cart.items.all())
        shipping = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
        tax = subtotal * Decimal('0.08')
        total = subtotal + shipping + tax

        return JsonResponse({
            'success': True,
            'item_total': float(cart_item.total_price),
            'subtotal': float(subtotal),
            'shipping': float(shipping),
            'tax': float(tax),
            'total': float(total)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def checkout_view(request):
    """Display checkout page"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('book').all()

    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart')

    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    shipping = Decimal('5.00')
    tax = subtotal * Decimal('0.08')
    total = subtotal + shipping + tax

    # Razorpay integration
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        'amount': int(total * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1'
    })

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'orders/checkout.html', context)

@require_POST
@login_required
def process_checkout(request):
    """Process checkout and create order"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.select_related('book').all()

        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})

        # Get form data
        shipping_address = request.POST.get('shipping_address', '').strip()
        payment_id = request.POST.get('payment_id', '').strip()

        if not shipping_address:
            return JsonResponse({'success': False, 'error': 'Shipping address is required'})

        # Calculate totals
        subtotal = sum(item.total_price for item in cart_items)
        shipping = Decimal('5.00')
        tax = subtotal * Decimal('0.08')
        total = subtotal + shipping + tax

        # Generate unique order number
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            total_amount=total,
            shipping_address=shipping_address,
            payment_id=payment_id,
            status='confirmed'
        )

        # Create order items and update stock
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                quantity=cart_item.quantity,
                price=cart_item.book.price
            )

            # Update book stock
            cart_item.book.stock_quantity -= cart_item.quantity
            cart_item.book.save()

        # Clear cart
        cart.items.all().delete()

        return JsonResponse({
            'success': True,
            'order_number': order_number,
            'message': f'Order {order_number} placed successfully!'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('book').all()

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_tracking(request):
    """Display order tracking page"""
    order_number = request.GET.get('order', '').strip().upper()

    if not order_number:
        # Show search form
        context = {
            'order': None,
            'search_performed': False,
        }
        return render(request, 'orders/order_tracking.html', context)

    try:
        order = Order.objects.select_related('user').get(
            order_number=order_number,
            user=request.user
        )
        order_items = order.items.select_related('book').all()

        # Define timeline stages
        stages = [
            {'name': 'Order Placed', 'status': 'completed', 'date': order.created_at.date()},
            {'name': 'Processing', 'status': 'completed' if order.status in ['processing', 'shipped', 'out_for_delivery', 'delivered'] else 'pending'},
            {'name': 'Shipped', 'status': 'completed' if order.status in ['shipped', 'out_for_delivery', 'delivered'] else 'pending'},
            {'name': 'Out for Delivery', 'status': 'completed' if order.status in ['out_for_delivery', 'delivered'] else 'pending'},
            {'name': 'Delivered', 'status': 'completed' if order.status == 'delivered' else 'pending'},
        ]

        context = {
            'order': order,
            'order_items': order_items,
            'stages': stages,
            'search_performed': True,
        }
        return render(request, 'orders/order_tracking.html', context)

    except Order.DoesNotExist:
        messages.error(request, f'Order {order_number} not found or access denied.')
        context = {
            'order': None,
            'search_performed': True,
            'error': f'Order {order_number} not found.',
        }
        return render(request, 'orders/order_tracking.html', context)
