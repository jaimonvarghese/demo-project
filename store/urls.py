from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('bmi/', views.bmi, name='bmi'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('orders/', views.orders, name='orders'),
    path('orders/cancel/<str:order_id>/', views.cancel_order, name='cancel_order'),
    path('profile/', views.profile, name='profile'),
    path('products/<int:pk>/review/', views.review_product, name='review_product'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Shop Owner Routes
    path('shop/register/', views.shop_register, name='shop_register'),
    path('shop/dashboard/', views.shop_dashboard, name='shop_dashboard'),
    path('shop/products/', views.manage_products, name='manage_products'),
    path('shop/products/add/', views.add_product, name='add_product'),
    path('shop/products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('shop/orders/', views.shop_orders, name='shop_orders'),
    path('shop/orders/update/<str:order_id>/', views.update_order_status, name='update_order_status'),
    
    # Partner & Admin Routes
    path('partners/login/', views.partner_login, name='partner_login'),
    path('partners/register/', views.partner_register, name='partner_register'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/verify/<int:shop_id>/', views.verify_shop, name='verify_shop'),
    path('admin-dashboard/users/', views.admin_users, name='admin_users'),
    path('admin-dashboard/shops/', views.admin_shops, name='admin_shops'),
    path('admin-dashboard/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-dashboard/shops/delete/<int:shop_id>/', views.delete_shop, name='delete_shop'),
    
    path('shop/<int:pk>/', views.shop_detail, name='shop_detail'),
]
