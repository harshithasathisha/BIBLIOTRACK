from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm, UserProfileForm, LoginForm
from .models import UserProfile, Address
from orders.models import Order, OrderItem

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('profile')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Get tab parameter
    active_tab = request.GET.get('tab', 'orders')

    # Get data for different tabs
    if active_tab == 'orders':
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]  # Recent 5 orders
        context_data = {'orders': orders}
    elif active_tab == 'personal':
        context_data = {}
    elif active_tab == 'addresses':
        addresses = Address.objects.filter(user=request.user).order_by('-created_at')
        context_data = {'addresses': addresses}
    else:
        context_data = {}

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect(reverse('profile') + f'?tab=personal')
        elif 'add_address' in request.POST:
            # Handle address addition
            name = request.POST.get('name')
            street_address = request.POST.get('street_address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            postal_code = request.POST.get('postal_code')
            phone = request.POST.get('phone')
            is_default = request.POST.get('is_default') == 'on'

            if name and street_address and city and state and postal_code:
                Address.objects.create(
                    user=request.user,
                    name=name,
                    street_address=street_address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    phone=phone,
                    is_default=is_default
                )
                messages.success(request, 'Address added successfully!')
                return redirect(reverse('profile') + f'?tab=addresses')
            else:
                messages.error(request, 'Please fill in all required fields.')
        elif 'update_personal' in request.POST:
            # Handle personal info update
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            messages.success(request, 'Personal information updated successfully!')
            return redirect(reverse('profile') + f'?tab=personal')

    form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'active_tab': active_tab,
        'initials': profile.get_initials(),
        **context_data
    }
    return render(request, 'accounts/profile.html', context)

@require_POST
@login_required
def delete_address(request, address_id):
    """Delete user address"""
    try:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        return JsonResponse({'success': True, 'message': 'Address deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def set_default_address(request, address_id):
    """Set address as default"""
    try:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        # This will trigger the save method to handle default logic
        address.is_default = True
        address.save()
        return JsonResponse({'success': True, 'message': 'Default address updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
