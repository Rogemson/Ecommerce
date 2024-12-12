from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import NewsletterForm
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem
from django import forms
from django.urls import reverse

def get_shared_context(request):
    data = cartData(request)
    return {
        'cartItems': data['cartItems'],
        'order': data['order'],
        'items': data['items'],
    }

def home_view(request):
    products = Product.objects.all()
    blogs = Blog.objects.all()[:5]
    latest_blog = blogs.first() 
    reviews = CustomerReview.objects.all()

    try:
        f = FeaturedProduct.objects.first()
    except FeaturedProduct.DoesNotExist:
        f = None  

    shared_context = get_shared_context(request)
    context = {
        'products': products,
        'blogs': blogs,
        'latest_blog': latest_blog,
        'reviews': reviews,
        'f': f,
        'page': 'home', 
    }
    context.update(shared_context)

    return render(request, 'store/home.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, "Invalid login credentials")
    
    return render(request, 'store/login.html')

@login_required
def view_profile(request):
    shared_context = get_shared_context(request)
    context = {'user': request.user, 'page': 'profile'}
    context.update(shared_context)
    return render(request, 'store/view-profile.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        user = request.user
        user.username = username
        user.email = email
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('view_profile')
    
    return render(request, 'store/update_profile.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer = Customer.objects.create(user=user) 
            login(request, user)
            return redirect('products')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'store/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def products(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/products.html', context)


def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    error_message = request.GET.get('error_message', None)

    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'error_message': error_message,
    }
    
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    if cartItems == 0:
        return redirect(f"{reverse('cart')}?error_message=Your cart is empty. Add items to proceed to checkout.")
    
    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    try:
        data = json.loads(request.body)
        productId = data['productId']
        action = data['action']
        quantity = int(data.get('quantity', 1))

        if quantity <= 0:
            return JsonResponse({'error': 'Quantity must be greater than zero'}, status=400)
        product = get_object_or_404(Product, id=productId)
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            if orderItem.quantity + quantity > product.quantity:
                return JsonResponse({'error': 'Not enough stock available'}, status=400)
            orderItem.quantity += quantity 

        elif action == 'remove':
            orderItem.quantity -= quantity 
            if orderItem.quantity <= 0:
                orderItem.delete() 
                return JsonResponse({'message': 'Item removed from cart'}, safe=False)
        orderItem.save()
        return JsonResponse({'message': 'Cart updated successfully'}, safe=False)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id
    
    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    for order_item in order.orderitem_set.all():
        product = order_item.product
        if product.quantity < order_item.quantity:
            return JsonResponse({
                'error': f'Not enough stock for {product.name}. Only {product.quantity} left.'
            }, status=400)
       
        product.quantity -= order_item.quantity
        if product.quantity < 0:
            product.quantity = 0
        product.save()
    return redirect('order_list')

def blog_list(request):
    blogs = Blog.objects.all()[:5] 
    latest_blog = blogs.first()
    return render(request, 'store/blog_list.html', {'blogs': blogs, 'latest_blog': latest_blog})

def subscribe_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if not NewsletterSubscriber.objects.filter(email=email).exists():
                form.save()
                messages.success(request, "You've successfully subscribed to the newsletter!")
            else:
                messages.warning(request, "This email is already subscribed!")
            return redirect('subscribe_newsletter')
    else:
        form = NewsletterForm()
    
    return render(request, 'store/subscribe_newsletter.html', {'form': form})

def payment_success(request):
    return render(request, 'store/payment_success.html')

def customer_reviews(request):
    reviews = CustomerReview.objects.all()
    return render(request, 'reviews.html', {'reviews': reviews})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        return redirect('home') 
    return render(request, 'store/delete_profile_confirm.html', {'user': request.user})

class FeaturedProductForm(forms.ModelForm):
    class Meta:
        model = FeaturedProduct
        fields = ['name', 'description', 'price', 'image']

def featured_product_view(request):
    try:
        f = FeaturedProduct.objects.first()
    except FeaturedProduct.DoesNotExist:
        f = None
    
    return render(request, 'featured_product.html', {'f': f})
        
def order_list(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered')
        return render(request, 'store/order_list.html', {'orders': orders})
    else:
        return render(request, 'store/order_list.html', {'orders': []})
        