from django.urls import path

from . import views

urlpatterns = [
	path('', views.home_view, name="home"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),
	path('products/', views.products, name="products"),
	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
	path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('blog_list/', views.blog_list, name='blog_list'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('delete-profile/', views.delete_profile, name='delete_profile'),
    path('featured/', views.featured_product_view, name='featured_product'),
    path('orders/', views.order_list, name='order_list'),
]