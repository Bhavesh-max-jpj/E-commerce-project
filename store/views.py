from django.shortcuts import render, get_object_or_404, redirect
from .models import Products, Customers, Cart,Orders,OrderItems
from django.contrib.auth.hashers import make_password
from django.utils import timezone



def products(request):
    products = Products.objects.all()

    return render(
        request,
        'store/products.html',
        {'products': products}
    )
def orders_view(request):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']

    orders = Orders.objects.filter(
        customer_id=customer_id
    ).order_by('-order_date')

    for order in orders:
        order.items_list = OrderItems.objects.filter(
            order_id=order.order_id
        ).select_related('product')

    return render(
        request,
        'store/orders.html',
        {'orders': orders}
    )

def product_detail(request, product_id):
    product = get_object_or_404(
        Products,
        product_id=product_id
    )

    return render(
        request,
        'store/product_detail.html',
        {'product': product}
    )
def register(request):
    if request.method == 'POST':

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        city = request.POST.get('city')
        state = request.POST.get('state')

        Customers.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            gender=gender,
            city=city,
            state=state
        )

        return redirect('/login/')

    return render(request, 'store/register.html')

def profile(request):
    customer_id = request.session.get('customer_id')

    if not customer_id:
        return redirect('/login/')

    customer = Customers.objects.get(
        customer_id=customer_id
    )

    return render(
        request,
        'store/profile.html',
        {'customer': customer}
    )
def cart_view(request):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']

    cart_items = Cart.objects.filter(
        customer_id=customer_id
    ).select_related('product')

    total = 0

    for item in cart_items:
        if item.product.price:
            total += item.product.price * item.quantity

    return render(
        request,
        'store/cart.html',
        {
            'cart_items': cart_items,
            'total': total
        }
    )


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            customer = Customers.objects.get(email=email)

            if customer.password == password:
                request.session['customer_id'] = customer.customer_id
                request.session['customer_name'] = customer.first_name

                return redirect('/products/')

            else:
                return render(
                    request,
                    'store/login.html',
                    {'error': 'Incorrect password'}
                )

        except Customers.DoesNotExist:
            return render(
                request,
                'store/login.html',
                {'error': 'Customer does not exist'}
            )

    return render(request, 'store/login.html')
def add_to_cart(request, product_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']

    customer = Customers.objects.get(
        customer_id=customer_id
    )

    product = Products.objects.get(
        product_id=product_id
    )

    cart_item = Cart.objects.filter(
        customer=customer,
        product=product
    ).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        Cart.objects.create(
            customer=customer,
            product=product,
            quantity=1
        )

    return redirect('/cart/')
def increase_cart(request, cart_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    cart_item = Cart.objects.get(
        cart_id=cart_id,
        customer_id=request.session['customer_id']
    )

    cart_item.quantity += 1
    cart_item.save()

    return redirect('/cart/')


def decrease_cart(request, cart_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    cart_item = Cart.objects.get(
        cart_id=cart_id,
        customer_id=request.session['customer_id']
    )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()

    return redirect('/cart/')


def remove_from_cart(request, cart_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    cart_item = Cart.objects.get(
        cart_id=cart_id,
        customer_id=request.session['customer_id']
    )

    cart_item.delete()

    return redirect('/cart/')
def checkout(request):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']

    cart_items = Cart.objects.filter(
        customer_id=customer_id
    ).select_related('product')

    if not cart_items.exists():
        return redirect('/cart/')

    total = 0

    for item in cart_items:
        if item.product.price:
            total += item.product.price * item.quantity

    if request.method == 'POST':
        shipping_addr = request.POST['shipping_addr']

        order = Orders.objects.create(
            customer_id=customer_id,
            order_date=timezone.now(),
            total_amount=total,
            order_status='Pending',
            shipping_addr=shipping_addr
        )

        for item in cart_items:
            OrderItems.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price,
                subtotal=item.product.price * item.quantity
            )

        cart_items.delete()

        return redirect('/orders/')

    return render(
        request,
        'store/checkout.html',
        {
            'cart_items': cart_items,
            'total': total
        }
    )
def order_detail(request, order_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']

    order = get_object_or_404(
        Orders,
        order_id=order_id,
        customer_id=customer_id
    )

    items = OrderItems.objects.filter(
        order_id=order_id
    ).select_related('product')

    return render(
        request,
        'store/order_detail.html',
        {
            'order': order,
            'items': items
        }
    )