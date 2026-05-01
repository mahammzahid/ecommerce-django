from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product-list'),
    path('api/products/', views.product_list_create),
    path('products/<int:id>/', views.product_detail),
    #path('delete/<int:id>/', views.delete_product, name='delete-product'),
    #path('edit/<int:id>/', views.edit_product, name='edit-product'),
    #path('add/', views.add_product, name='add-product'),
    # Customer
    path('customer/', views.get_customer),
    path('customer/update/', views.update_customer),
    # Cart
    path('cart/add/', views.add_to_cart),
    path('cart/', views.view_cart),
    path('cart/remove/<int:item_id>/', views.remove_from_cart),
    # Order
    path('create-order/', views.create_order, name='create-order'),
    path('orders/<int:id>/', views.order_detail),
    path('orders/', views.get_orders),
    path('orders/delete/<int:id>/', views.delete_order),
    # Stock management
    path('stock/', views.get_stock),
    path('stock/add/', views.add_stock),
    #cart 
    path('cart/add/web/', views.add_to_cart_web, name='add-to-cart-web'),
    path('cart-page/', views.cart_page, name='cart-page'),
    path('order/create/web/', views.create_order_web, name='create-order-web'),
    path('order/success/', views.order_success, name='order-success'),
    path('order/create/web/', views.create_order_web, name='create-order-web'),
    path('cart/remove/web/', views.remove_item_web, name='remove-item'),
    path('orders/history/', views.order_history, name='order-history'),
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),
    path('checkout/', views.checkout, name='checkout'),
]