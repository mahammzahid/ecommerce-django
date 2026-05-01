from itertools import product

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from httpx import request
from .models import Cart, CartItem, Customer, Order, OrderItem, Product, Stock
from rest_framework.permissions import IsAuthenticated
from .serializers import CartSerializer, CustomerSerializer, ProductSerializer,StockSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_yasg import openapi
from django.db import transaction
from django.db.models import F
from django.contrib.auth.decorators import login_required
from drf_yasg.utils import swagger_auto_schema


def product_list(request):

    query = request.GET.get('q')

    products = Product.objects.all()

    # 🔍 SEARCH by name
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'product_list.html', {
        'products': products
    })
@swagger_auto_schema(method='get', responses={200: ProductSerializer(many=True)})
@swagger_auto_schema(method='post', request_body=ProductSerializer)
@api_view(['GET', 'POST'])
def product_list_create(request):

# GET all products
    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

# CREATE product
    if request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)
# UPDATE product
@swagger_auto_schema(method='get', responses={200: ProductSerializer})
@swagger_auto_schema(method='put', request_body=ProductSerializer)
@swagger_auto_schema(method='delete', responses={200: 'Deleted'})    

@api_view(['GET', 'PUT', 'DELETE'])
def product_detail(request, id):

    product = get_object_or_404(Product, id=id)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)

    if request.method == 'DELETE':
        product.delete()
        return Response({"message": "Deleted successfully"})
    #delete option for product
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product-list')

#edit option for product
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)

    # STEP 1: Show form with existing data
    if request.method == 'GET':
        return render(request, 'edit_product.html', {'product': product})

    # STEP 2: Save updated data
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.save()

        return redirect('product-list')
    #add option
def add_product(request):

     if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')

        Product.objects.create(name=name, price=price)

        return redirect('product-list')   # go back to list

     return render(request, 'add_product.html')





# ✅ GET customer profile
@swagger_auto_schema(method='get', responses={200: CustomerSerializer()})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer(request):
    customer = request.user.customer
    serializer = CustomerSerializer(customer)
    return Response(serializer.data)


# ✅ UPDATE customer profile
update_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'phone': openapi.Schema(type=openapi.TYPE_STRING),
        'address': openapi.Schema(type=openapi.TYPE_STRING),
    }
)
@swagger_auto_schema(
    method='put',
    request_body=update_schema,   # 🔥 THIS FIXES YOUR ISSUE
    responses={200: CustomerSerializer()})

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_customer(request):
    customer = request.user.customer
    serializer = CustomerSerializer(customer, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)



from .serializers import CartAddSerializer
@swagger_auto_schema(
    method='post',
    request_body=CartAddSerializer,   # 👈 THIS makes Swagger show product_id + quantity
    responses={200: "Product added to cart"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):

    serializer = CartAddSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data['quantity']

    customer = request.user.customer
    cart, created = Cart.objects.get_or_create(customer=customer)

   
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    cart_item.quantity += quantity if not created else quantity
    cart_item.save()

    return Response({"message": "Product added to cart"})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    customer = request.user.customer
    cart = customer.cart

    item = CartItem.objects.get(id=item_id, cart=cart)
    item.delete()

    return Response({"message": "Item removed"})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart = request.user.customer.cart
    serializer = CartSerializer(cart)
    return Response(serializer.data)


#order related views

@swagger_auto_schema(
    method='post',
    responses={200: 'Order created successfully'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    customer = request.user.customer
    cart = Cart.objects.get(customer=customer)

    if not cart.items.exists():
        return Response({"error": "Cart is empty"}, status=400)

    with transaction.atomic():  # 🔒 START SAFE BLOCK

        order = Order.objects.create(customer=customer)

        for item in cart.items.select_related('product'):

            product_stock = Stock.objects.select_for_update().get(product=item.product)

            # ❌ check stock first
            if product_stock.quantity < item.quantity:
                return Response(
                    {"error": f"Not enough stock for {item.product.name}"},
                    status=400
                )

            # 🔻 reduce stock safely
            product_stock.quantity -= item.quantity
            product_stock.save()

            # 🧾 create order item
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # 🧹 clear cart
        cart.items.all().delete()

    return Response({
        "message": "Order created safely",
        "order_id": order.id
    })



@swagger_auto_schema(
    method='get',
    responses={200: 'List of user orders'}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer)

    data = []
    for order in orders:
        data.append({
            "order_id": order.id,
        })

    return Response(data)


#get single order details
@swagger_auto_schema(
    method='get',
    responses={200: 'Single order detail'}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, id):
    order = Order.objects.get(id=id, customer=request.user.customer)

    items = []
    for item in order.orderitem_set.all():
        items.append({
            "product": item.product.name,
            "quantity": item.quantity,
            "price": item.price
        })

    return Response({
        "order_id": order.id,
        "items": items
    })

#delete order
@swagger_auto_schema(
    method='delete',
    responses={200: 'Order deleted'}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order(request, id):
    order = Order.objects.get(id=id, customer=request.user.customer)
    order.delete()

    return Response({"message": "Order deleted"})

#stock management when order is created

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'product_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    ),
    responses={200: 'Stock updated successfully'}
)
@api_view(['POST'])
def add_stock(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity')

    #  validation
    if not product_id or not quantity:
        return Response({"error": "product_id and quantity required"}, status=400)

    product = get_object_or_404(Product, id=product_id)

    stock, created = Stock.objects.get_or_create(product=product)

    stock.quantity += int(quantity)   # convert to int
    stock.save()

    return Response({"message": "Stock updated"})

@swagger_auto_schema(
    method='get',
    responses={200: 'List of all products with stock'}
)
@api_view(['GET'])
def get_stock(request):
    stock = Stock.objects.all()
    serializer = StockSerializer(stock, many=True)
    return Response(serializer.data)




@login_required
def add_to_cart_web(request):
    if request.method == 'POST':

        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # 🔥 STEP 1: CHECK STOCK
        if product.stock.quantity <= 0:
            return redirect('product-list')  # or show message

        customer = request.user.customer
        cart, _ = Cart.objects.get_or_create(customer=customer)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )

        # 🔥 STEP 2: CHECK AGAIN BEFORE INCREMENT
        if not created:
            if item.quantity + 1 > product.stock.quantity:
                return redirect('cart-page')  # stop over-ordering

            CartItem.objects.filter(id=item.id).update(
                quantity=F('quantity') + 1
            )

    return redirect('cart-page')
@login_required
def cart_page(request):
    customer = request.user.customer

    cart, created = Cart.objects.get_or_create(customer=customer)
    items = cart.items.select_related('product')
    
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'cart.html', {
        'cart': cart,
        'items': items,
        'total': total
    })


@login_required
def create_order_web(request):
    if request.method == 'POST':

        customer = request.user.customer
        cart = customer.cart

        if not cart.items.exists():
            return redirect('cart-page')

        order = Order.objects.create(customer=customer)

        for item in cart.items.all():

            stock = Stock.objects.get(product=item.product)

            # 🚨 STOCK VALIDATION
            if item.quantity > stock.quantity:
                return redirect('cart-page')

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

            # 🔻 Reduce stock
            stock.quantity -= item.quantity
            stock.save()

        cart.items.all().delete()

        return redirect('order-success')

    return redirect('cart-page')
def order_success(request):
    return render(request, 'order_success.html')



@login_required
def remove_item_web(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')

        customer = request.user.customer
        cart = customer.cart

        item = get_object_or_404(cart.items, id=item_id)
        item.delete()

    return redirect('cart-page')

@login_required
def order_history(request):
    customer, created = Customer.objects.get_or_create(user=request.user)

    orders = Order.objects.filter(customer=customer).order_by('-id')

    return render(request, 'order_history.html', {
        'orders': orders
    })

def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)

    items = order.items.all()

    total = sum(item.price * item.quantity for item in items)

    return render(request, 'invoice.html', {
        'order': order,
        'items': items,
        'total': total
    })
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def checkout(request):

    customer = request.user.customer
    cart = customer.cart

    if not cart.items.exists():
        return redirect('cart-page')

    total = sum(item.product.price * item.quantity for item in cart.items.all())

    return render(request, 'checkout.html', {
        'cart': cart,
        'total': total
    })
