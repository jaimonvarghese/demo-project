from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Shop, User, Wishlist
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta


def home(request):
    featured_products = Product.objects.all()[:8]
    categories = Category.objects.filter(parent__isnull=True)
    shops = Shop.objects.filter(is_verified=True)[:4]
    
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_obj = Wishlist.objects.filter(user=request.user).first()
        if wishlist_obj:
            wishlist_product_ids = list(wishlist_obj.products.values_list('id', flat=True))

    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'shops': shops,
        'wishlist_product_ids': wishlist_product_ids,
    })


def products(request):
    all_products = Product.objects.all()
    categories = Category.objects.filter(parent__isnull=True)
    
    # Filtering
    category_id = request.GET.get('category')
    shop_id = request.GET.get('shop')
    search_q = request.GET.get('q', '')
    sort = request.GET.get('sort', 'default')

    if category_id:
        all_products = all_products.filter(category_id=category_id)
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            category_id = None
    
    if shop_id:
        all_products = all_products.filter(shop_id=shop_id)

    if search_q:
        all_products = all_products.filter(p_name__icontains=search_q)

    if sort == 'price_asc':
        all_products = all_products.order_by('price')
    elif sort == 'price_desc':
        all_products = all_products.order_by('-price')
    else:
        all_products = all_products.order_by('-created_at')

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_obj = Wishlist.objects.filter(user=request.user).first()
        if wishlist_obj:
            wishlist_product_ids = list(wishlist_obj.products.values_list('id', flat=True))

    return render(request, 'store/products.html', {
        'products': all_products,
        'categories': categories,
        'search_q': search_q,
        'current_category': category_id,
        'current_sort': sort,
        'wishlist_product_ids': wishlist_product_ids,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(category=product.category).exclude(pk=pk)[:4]
    from .models import Review, RecentlyViewed
    reviews = product.reviews.select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    user_review = reviews.filter(user=request.user).first() if request.user.is_authenticated else None
    has_bought = OrderItem.objects.filter(order__user=request.user, product=product).exists() if request.user.is_authenticated else False

    # Track recently viewed
    if request.user.is_authenticated:
        RecentlyViewed.objects.update_or_create(user=request.user, product=product)
        # Keep only last 10
        rv_ids = RecentlyViewed.objects.filter(user=request.user).values_list('id', flat=True)
        if rv_ids.count() > 10:
            old = list(rv_ids)[10:]
            RecentlyViewed.objects.filter(id__in=old).delete()

    in_wishlist = False
    if request.user.is_authenticated:
        wishlist_obj = Wishlist.objects.filter(user=request.user).first()
        if wishlist_obj and wishlist_obj.products.filter(id=product.id).exists():
            in_wishlist = True

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'user_review': user_review,
        'has_bought': has_bought,
        'in_wishlist': in_wishlist,
    })

from django.shortcuts import get_object_or_404


def bmi(request):
    result = None
    category = None
    if request.method == 'POST':
        try:
            weight = float(request.POST.get('weight', 0))
            height = float(request.POST.get('height', 0)) / 100  # cm to m
            if height > 0:
                bmi_val = weight / (height ** 2)
                result = round(bmi_val, 1)
                if bmi_val < 18.5:
                    category = ('Underweight', 'info')
                elif bmi_val < 25:
                    category = ('Normal weight', 'success')
                elif bmi_val < 30:
                    category = ('Overweight', 'warning')
                else:
                    category = ('Obese', 'error')
        except (ValueError, ZeroDivisionError):
            pass
    return render(request, 'store/bmi.html', {'result': result, 'category': category})


# --- Auth Views ---
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import redirect
from .models import User


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')

        role_choice = request.POST.get('role', 'customer')
        if role_choice == 'admin':
            messages.error(request, 'Cannot register as an admin.')
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password,
                                         phone_number=phone)
        
        if role_choice == 'shop_owner':
            user.role = User.IS_SHOP_OWNER
            user.save()
            login(request, user)
            messages.success(request, f'Vendor account created. Please register your shop details.')
            return redirect('shop_register')
        else:
            user.role = User.IS_CUSTOMER
            user.save()
            login(request, user)
            messages.success(request, f'Welcome to VigorCart, {username}!')
            return redirect('home')

    return render(request, 'store/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone', user.phone_number)
        user.address = request.POST.get('address', user.address)
        new_password = request.POST.get('new_password', '')
        if new_password:
            user.set_password(new_password)
            login(request, user)  # Keep user logged in after password change
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    from .models import RecentlyViewed
    recent_views = RecentlyViewed.objects.filter(user=request.user).select_related('product')[:6]
    recently_viewed = [rv.product for rv in recent_views]

    # Recently purchased (unique products)
    order_items = OrderItem.objects.filter(order__user=request.user).select_related('product').order_by('-order__created_at')
    recently_purchased = []
    seen_products = set()
    for item in order_items:
        if item.product.id not in seen_products:
            recently_purchased.append(item.product)
            seen_products.add(item.product.id)
        if len(recently_purchased) >= 6:
            break

    return render(request, 'store/profile.html', {
        'recently_viewed': recently_viewed,
        'recently_purchased': recently_purchased,
    })


def cart(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart_obj})

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    item, item_created = CartItem.objects.get_or_create(cart=cart_obj, product=product)
    
    if not item_created:
        item.quantity += 1
        item.save()
    
    messages.success(request, f"{product.p_name} added to cart.")
    return redirect('cart')

def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

import uuid

def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    cart_obj, created = Cart.objects.get_or_create(user=request.user)
    if not cart_obj.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('products')
    
    if request.method == 'POST':
        address = request.POST.get('address')
        email = request.POST.get('email', request.user.email)
        
        # Create Order
        order = Order.objects.create(
            o_id=str(uuid.uuid4())[:8].upper(),
            user=request.user,
            email=email,
            delivery_address=address,
            total_amount=cart_obj.total_price
        )
        
        # Create Order Items
        for item in cart_obj.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            # Update Stock
            if item.product.stock_availability >= item.quantity:
                item.product.stock_availability -= item.quantity
                item.product.save()
        
        # Clear Cart
        cart_obj.items.all().delete()
        
        messages.success(request, f"Order placed successfully! Order ID: {order.o_id}")
        return redirect('orders')
        
    return render(request, 'store/checkout.html', {'cart': cart_obj})


def wishlist_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products_in_wishlist = wishlist.products.all()
    return render(request, 'store/wishlist.html', {'wishlist_products': products_in_wishlist})


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.info(request, f'"{product.p_name}" removed from wishlist.')
    else:
        wishlist.products.add(product)
        messages.success(request, f'"{product.p_name}" added to wishlist! ❤️')
    # Go back to where the user came from, with fallback to wishlist page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('wishlist')


def remove_from_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.remove(product)
    messages.info(request, f'"{product.p_name}" removed from wishlist.')
    return redirect('wishlist')

def orders(request):
    if not request.user.is_authenticated:
        return redirect('login')
    status_filter = request.GET.get('status', 'all')
    user_orders = request.user.orders.all().order_by('-created_at')
    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        user_orders = user_orders.filter(delivery_status=status_filter)
    status_tabs = [
        ('All', 'all'),
        ('⏳ Pending', 'Pending'),
        ('✅ Completed', 'Completed'),
        ('✕ Cancelled', 'Cancelled'),
    ]
    return render(request, 'store/orders.html', {
        'orders': user_orders,
        'status_filter': status_filter,
        'status_tabs': status_tabs,
    })


def cancel_order(request, order_id):
    if not request.user.is_authenticated:
        return redirect('login')
    order = get_object_or_404(Order, o_id=order_id, user=request.user)
    if order.delivery_status == 'Pending':
        order.delivery_status = 'Cancelled'
        order.save()
        messages.success(request, f'Order {order.o_id} has been cancelled.')
    else:
        messages.error(request, 'Only pending orders can be cancelled.')
    return redirect('orders')


def review_product(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    product = get_object_or_404(Product, pk=pk)
    from .models import Review
    # Check if user has purchased this product
    has_bought = OrderItem.objects.filter(order__user=request.user, product=product).exists()
    existing_review = Review.objects.filter(user=request.user, product=product).first()

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '')
        Review.objects.update_or_create(
            user=request.user, product=product,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, 'Your review has been submitted!')
        return redirect('product_detail', pk=pk)

    return render(request, 'store/review_product.html', {
        'product': product,
        'has_bought': has_bought,
        'existing_review': existing_review,
    })


def feedback_view(request):
    if request.method == 'POST':
        from .models import Feedback
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        feedback_text = request.POST.get('feedback', '')
        if name and feedback_text:
            Feedback.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                feedback=feedback_text,
            )
            messages.success(request, 'Thank you for your feedback! 🙏')
            return redirect('feedback')
        else:
            messages.error(request, 'Name and feedback are required.')
    return render(request, 'store/feedback.html')


# --- Shop Owner Views ---
from functools import wraps


def shop_owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.IS_SHOP_OWNER:
            messages.error(request, 'Access denied. Shop Owner account required.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@shop_owner_required
def shop_dashboard(request):
    shop = request.user.owned_shops.first()
    if not shop:
        messages.info(request, "You haven't registered a shop yet.")
        return redirect('shop_register')

    products_count = shop.products.count()
    orders_count = OrderItem.objects.filter(product__shop=shop).count()
    revenue = sum(
        item.price * item.quantity
        for item in OrderItem.objects.filter(
            product__shop=shop, order__delivery_status=Order.PAYMENT_COMPLETED
        )
    )
    recent_orders = OrderItem.objects.filter(
        product__shop=shop
    ).select_related('order', 'product').order_by('-order__created_at')[:10]

    return render(request, 'store/shop_dashboard.html', {
        'shop': shop,
        'products_count': products_count,
        'orders_count': orders_count,
        'revenue': revenue,
        'recent_orders': recent_orders,
    })


@shop_owner_required
def manage_products(request):
    shop = request.user.owned_shops.first()
    products_list = shop.products.all().order_by('-created_at')
    return render(request, 'store/manage_products.html', {'products': products_list})


@shop_owner_required
def add_product(request):
    shop = request.user.owned_shops.first()
    if not shop:
        messages.error(request, "You need a registered shop to add products.")
        return redirect('shop_register')

    categories = Category.objects.all()
                
    if request.method == 'POST':
        try:
            p_name = request.POST.get('p_name')
            price = request.POST.get('price')
            
            if not p_name or not price:
                messages.error(request, "Name and Price are required.")
                return render(request, 'store/product_form.html', {'categories': categories, 'action': 'Add'})

            image = request.FILES.get('image')
            
            Product.objects.create(
                shop=shop,
                p_name=p_name,
                asset_id=request.POST.get('asset_id', ''),
                description=request.POST.get('description', ''),
                size=request.POST.get('size', ''),
                detail=request.POST.get('detail', ''),
                price=price,
                stock_availability=request.POST.get('stock', 0),
                category_id=request.POST.get('category') or None,
                image=image,
            )
            messages.success(request, 'Product added successfully.')
            return redirect('manage_products')
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
            return render(request, 'store/product_form.html', {'categories': categories, 'action': 'Add'})
            
    return render(request, 'store/product_form.html', {
        'categories': categories,
        'action': 'Add',
    })


@shop_owner_required
def edit_product(request, pk):
    shop = request.user.owned_shops.first()
    product = get_object_or_404(Product, pk=pk, shop=shop)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.p_name = request.POST.get('p_name')
        product.asset_id = request.POST.get('asset_id', '')
        product.description = request.POST.get('description', '')
        product.size = request.POST.get('size', '')
        product.detail = request.POST.get('detail', '')
        product.price = request.POST.get('price')
        product.stock_availability = request.POST.get('stock', 0)
        product.category_id = request.POST.get('category') or None
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('manage_products')
    return render(request, 'store/product_form.html', {
        'product': product,
        'categories': categories,
        'action': 'Edit',
    })


@shop_owner_required
def shop_orders(request):
    shop = request.user.owned_shops.first()
    if not shop:
        messages.error(request, "You haven't registered a shop yet.")
        return redirect('shop_register')

    # Find all orders containing products belonging to this shop
    orders_list = Order.objects.filter(items__product__shop=shop).distinct().order_by('-created_at')

    status_filter = request.GET.get('status', 'all')
    if status_filter in ('Pending', 'Completed', 'Cancelled'):
        orders_list = orders_list.filter(delivery_status=status_filter)

    for order in orders_list:
        order.shop_items = order.items.filter(product__shop=shop).select_related('product')
        order.shop_revenue = sum(item.price * item.quantity for item in order.shop_items)

    status_tabs = [
        ('All', 'all'),
        ('⏳ Pending', 'Pending'),
        ('✅ Completed', 'Completed'),
        ('✕ Cancelled', 'Cancelled'),
    ]

    return render(request, 'store/shop_orders.html', {
        'orders': orders_list,
        'shop': shop,
        'status_filter': status_filter,
        'status_tabs': status_tabs,
    })


@shop_owner_required
def update_order_status(request, order_id):
    shop = request.user.owned_shops.first()
    if not shop:
        messages.error(request, "You haven't registered a shop yet.")
        return redirect('shop_register')

    order = get_object_or_404(Order, o_id=order_id, items__product__shop=shop)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [Order.PAYMENT_PENDING, Order.PAYMENT_COMPLETED, Order.PAYMENT_CANCELLED]:
            order.delivery_status = new_status
            order.save()
            messages.success(request, f"Order #{order.o_id} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status.")

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('shop_dashboard')


def shop_register(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff or request.user.role == User.IS_ADMIN:
        messages.error(request, 'Admins cannot register a shop.')
        return redirect('admin_dashboard')
    
    # Only redirect to dashboard if shop exists
    if request.user.owned_shops.exists():
        return redirect('shop_dashboard')
        
    if request.method == 'POST':
        Shop.objects.create(
            owner=request.user,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone', ''),
            location=request.POST.get('location', ''),
            opening_hours=request.POST.get('hours', ''),
            password='',
        )
        request.user.role = User.IS_SHOP_OWNER
        request.user.save()
        messages.success(request, 'Shop registered! Awaiting admin verification.')
        return redirect('shop_dashboard')
    return render(request, 'store/shop_register.html')


# --- Partner & Admin Views ---

def partner_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.user.role == User.IS_SHOP_OWNER:
            return redirect('shop_dashboard')
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_staff or user.role == User.IS_SHOP_OWNER:
                login(request, user)
                messages.success(request, f"Welcome to the Partner Portal, {user.username}!")
                return redirect('admin_dashboard' if user.is_staff else 'shop_dashboard')
            else:
                messages.error(request, "This portal is for Partners only. Please use the customer login.")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'store/partner_auth.html', {'action': 'Login'})


def partner_register(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role') # 'shop_owner' or 'admin'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('partner_register')
            
        user = User.objects.create_user(username=username, email=email, password=password)
        
        user.role = User.IS_SHOP_OWNER
        user.save()
        login(request, user)
        messages.success(request, f"Welcome to VigorCart Partners, {username}!")
        return redirect('shop_register')

    return render(request, 'store/partner_auth.html', {'action': 'Register'})


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    # Stats
    total_sales = Order.objects.filter(delivery_status=Order.PAYMENT_COMPLETED).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_shops = Shop.objects.count()
    
    # Recent Shops awaiting verification
    pending_shops = Shop.objects.filter(is_verified=False).order_by('-id')
    
    # Recent Orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    return render(request, 'store/admin_dashboard.html', {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_shops': total_shops,
        'pending_shops': pending_shops,
        'recent_orders': recent_orders,
    })

@staff_member_required
def verify_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.is_verified = True
    shop.save()
    messages.success(request, f"Shop '{shop.name}' has been verified.")
    
    # Redirect back to referring page or admin dashboard
    referer = request.META.get('HTTP_REFERER')
    if referer and 'admin-dashboard' in referer:
        return redirect(referer)
    return redirect('admin_dashboard')


@staff_member_required
def admin_users(request):
    users_list = User.objects.all().order_by('-date_joined')
    return render(request, 'store/admin_users.html', {'users': users_list})


@staff_member_required
def admin_shops(request):
    shops_list = Shop.objects.all().annotate(product_count=Count('products')).order_by('-id')
    return render(request, 'store/admin_shops.html', {'shops': shops_list})


@staff_member_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete your own admin account.")
        else:
            username = user_to_delete.username
            user_to_delete.delete()
            messages.success(request, f"User '{username}' has been deleted.")
    return redirect('admin_users')


@staff_member_required
def delete_shop(request, shop_id):
    if request.method == 'POST':
        shop_to_delete = get_object_or_404(Shop, id=shop_id)
        shop_name = shop_to_delete.name
        shop_to_delete.delete()
        messages.success(request, f"Shop '{shop_name}' has been successfully deleted.")
    return redirect('admin_shops')


def shop_detail(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    products = Product.objects.filter(shop=shop)
    return render(request, 'store/shop_detail.html', {
        'shop': shop,
        'products': products,
    })
