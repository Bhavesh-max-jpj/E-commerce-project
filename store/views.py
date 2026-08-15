from django.shortcuts import render, get_object_or_404, redirect
from .models import Products, Customers, Cart, Orders, OrderItems, Sellers, Reviews, Payments, Admin
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.template import RequestContext



def products(request):
    products = Products.objects.all()

    return render(request, 'store/products.html', {'products': products})


def index(request):
    return render(request, 'store/index.html')
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

    reviews = []
    try:
        reviews = Reviews.objects.filter(product_id=product_id).select_related('customer').order_by('-review_date')
    except Exception:
        reviews = []

    return render(
        request,
        'store/product_detail.html',
        {
            'product': product,
            'reviews': reviews
        }
    )


def submit_review(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    if 'customer_id' not in request.session:
        return redirect('/login/')

    customer_id = request.session['customer_id']
    rating = int(request.POST.get('rating', 5))
    review_text = request.POST.get('review_text', '')

    try:
        Reviews.objects.create(
            customer_id=customer_id,
            product_id=product_id,
            rating=rating,
            review_text=review_text,
            review_date=timezone.now()
        )
    except Exception:
        pass

    return redirect('product_detail', product_id=product_id)
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

        # create or update Django User (for auth) and store hashed password in Customers
        user, created = User.objects.get_or_create(username=email, defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })

        if created:
            user.set_password(password)
            user.save()
        else:
            # ensure password is set (overwrite only if plaintext mismatch)
            try:
                if not user.check_password(password):
                    user.set_password(password)
                    user.save()
            except Exception:
                user.set_password(password)
                user.save()

        Customers.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=user.password,
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

        # Prefer Django auth
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            try:
                customer = Customers.objects.get(email=email)
                request.session['customer_id'] = customer.customer_id
                request.session['customer_name'] = customer.first_name
            except Customers.DoesNotExist:
                pass

            return redirect('/products/')

        # Fallback: if legacy plaintext stored in Customers, migrate to Django User
        try:
            customer = Customers.objects.get(email=email)
            if customer.password == password:
                # create Django user and migrate
                u, created = User.objects.get_or_create(username=email, defaults={'email': email, 'first_name': customer.first_name, 'last_name': customer.last_name})
                u.set_password(password)
                u.save()

                # update stored password to hashed
                customer.password = u.password
                customer.save()

                auth_login(request, u)
                request.session['customer_id'] = customer.customer_id
                request.session['customer_name'] = customer.first_name

                return redirect('/products/')
            else:
                return render(request, 'store/login.html', {'error': 'Incorrect password'})
        except Customers.DoesNotExist:
            return render(request, 'store/login.html', {'error': 'Customer does not exist'})

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

        # Redirect to simulated payment page
        return redirect(f'/payment/{order.order_id}/')

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
def seller_login(request):

    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        # Prefer Django auth
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            try:
                seller = Sellers.objects.get(email=email)
                request.session['seller_id'] = seller.seller_id
                request.session['seller_name'] = seller.seller_name
            except Sellers.DoesNotExist:
                pass

            return redirect('/seller/dashboard/')

        # Fallback: legacy plaintext password check and migrate
        try:
            seller = Sellers.objects.get(email=email)
            if seller.password == password:
                u, created = User.objects.get_or_create(username=email, defaults={'email': email, 'first_name': seller.seller_name})
                u.set_password(password)
                u.save()
                seller.password = u.password
                seller.save()

                auth_login(request, u)
                request.session['seller_id'] = seller.seller_id
                request.session['seller_name'] = seller.seller_name

                return redirect('/seller/dashboard/')
            else:
                return render(request, 'store/seller_login.html', {'error': 'Invalid email or password'})
        except Sellers.DoesNotExist:
            return render(request, 'store/seller_login.html', {'error': 'Invalid email or password'})

    return render(
        request,
        'store/seller_login.html'
    )
def seller_dashboard(request):
    if 'seller_id' not in request.session:
        return redirect('/seller/login/')

    seller_id = request.session['seller_id']

    seller = Sellers.objects.get(seller_id=seller_id)

    products = Products.objects.filter(seller_id=seller_id)

    return render(
        request,
        'store/seller_dashboard.html',
        {
            'seller': seller,
            'products': products
        }
    )
def seller_add_product(request):

    if 'seller_id' not in request.session:
        return redirect('/seller/login/')

    if request.method == 'POST':

        Products.objects.create(
            product_id=request.POST['product_id'],
            seller_id=request.session['seller_id'],
            gender=request.POST.get('gender'),
            category=request.POST.get('category'),
            sub_category=request.POST.get('sub_category'),
            product_type=request.POST.get('product_type'),
            colour=request.POST.get('colour'),
            usage_type=request.POST.get('usage_type'),
            product_title=request.POST.get('product_title'),
            image=request.POST.get('image'),
            image_url=request.POST.get('image_url'),
            brand=request.POST.get('brand'),
            price=request.POST.get('price'),
            stock_quantity=request.POST.get('stock_quantity')
        )

        return redirect('/seller/dashboard/')

    return render(
        request,
        'store/seller_add_product.html'
    )
def seller_update_product(request, product_id):

    if 'seller_id' not in request.session:
        return redirect('/seller/login/')

    seller_id = request.session['seller_id']

    try:
        product = Products.objects.get(
            product_id=product_id,
            seller_id=seller_id
        )
    except Products.DoesNotExist:
        return redirect('/seller/dashboard/')

    if request.method == 'POST':

        product.product_title = request.POST.get('product_title')
        product.brand = request.POST.get('brand')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.category = request.POST.get('category')
        product.colour = request.POST.get('colour')

        product.save()

        return redirect('/seller/dashboard/')

    return render(
        request,
        'store/seller_update_product.html',
        {
            'product': product
        }
    )


def seller_delete_product(request, product_id):

    if 'seller_id' not in request.session:
        return redirect('/seller/login/')

    seller_id = request.session['seller_id']

    try:
        product = Products.objects.get(
            product_id=product_id,
            seller_id=seller_id
        )
    except Products.DoesNotExist:
        return redirect('/seller/dashboard/')

    if request.method == 'POST':
        product.delete()
        return redirect('/seller/dashboard/')

    return redirect('/seller/dashboard/')


def seller_logout(request):
    auth_logout(request)
    request.session.pop('seller_id', None)
    request.session.pop('seller_name', None)
    return redirect('/seller/login/')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Prefer Django auth
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            try:
                admin = Admin.objects.get(username=username)
                request.session['admin_id'] = admin.admin_id
                request.session['admin_name'] = admin.username
            except Admin.DoesNotExist:
                pass

            return redirect('/adminpanel/dashboard/')

        # Fallback: legacy Admin plaintext password migration
        try:
            admin = Admin.objects.get(username=username)
            if admin.password == password:
                u, created = User.objects.get_or_create(username=username, defaults={'email': admin.email, 'first_name': admin.username})
                u.set_password(password)
                u.save()
                admin.password = u.password
                admin.save()

                auth_login(request, u)
                request.session['admin_id'] = admin.admin_id
                request.session['admin_name'] = admin.username
                return redirect('/adminpanel/dashboard/')
            else:
                return render(request, 'store/admin_login.html', {'error': 'Incorrect password'})
        except Admin.DoesNotExist:
            return render(request, 'store/admin_login.html', {'error': 'Admin does not exist'})

    return render(request, 'store/admin_login.html')


def admin_logout(request):
    auth_logout(request)
    request.session.pop('admin_id', None)
    request.session.pop('admin_name', None)
    return redirect('/adminpanel/login/')


def admin_dashboard(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    customers_count = Customers.objects.count()
    sellers_count = Sellers.objects.count()
    products_count = Products.objects.count()
    orders_count = Orders.objects.count()

    return render(request, 'store/admin_dashboard.html', {
        'customers_count': customers_count,
        'sellers_count': sellers_count,
        'products_count': products_count,
        'orders_count': orders_count,
    })


def admin_customers(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    customers = Customers.objects.all()
    return render(request, 'store/admin_customers.html', {'customers': customers})


def admin_sellers(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    sellers = Sellers.objects.all()
    return render(request, 'store/admin_sellers.html', {'sellers': sellers})


def admin_products(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    products = Products.objects.all()
    return render(request, 'store/admin_products.html', {'products': products})


def admin_add_product(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    if request.method == 'POST':
        Products.objects.create(
            product_id=request.POST.get('product_id'),
            seller_id=request.POST.get('seller_id') or None,
            gender=request.POST.get('gender'),
            category=request.POST.get('category'),
            sub_category=request.POST.get('sub_category'),
            product_type=request.POST.get('product_type'),
            colour=request.POST.get('colour'),
            usage_type=request.POST.get('usage_type'),
            product_title=request.POST.get('product_title'),
            image=request.POST.get('image'),
            image_url=request.POST.get('image_url'),
            brand=request.POST.get('brand'),
            price=request.POST.get('price') or None,
            stock_quantity=request.POST.get('stock_quantity') or None
        )

        return redirect('/adminpanel/products/')

    return render(request, 'store/admin_add_product.html')


def admin_update_product(request, product_id):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    try:
        product = Products.objects.get(product_id=product_id)
    except Products.DoesNotExist:
        return redirect('/adminpanel/products/')

    if request.method == 'POST':
        product.product_title = request.POST.get('product_title')
        product.brand = request.POST.get('brand')
        product.price = request.POST.get('price') or None
        product.stock_quantity = request.POST.get('stock_quantity') or None
        product.category = request.POST.get('category')
        product.colour = request.POST.get('colour')
        # allow changing seller_id
        seller_val = request.POST.get('seller_id')
        product.seller_id = seller_val if seller_val else None

        product.save()
        return redirect('/adminpanel/products/')

    return render(request, 'store/admin_update_product.html', {'product': product})


def admin_delete_product(request, product_id):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    try:
        product = Products.objects.get(product_id=product_id)
    except Products.DoesNotExist:
        return redirect('/adminpanel/products/')

    if request.method == 'POST':
        product.delete()
        return redirect('/adminpanel/products/')

    return redirect('/adminpanel/products/')


def admin_orders(request):
    if 'admin_id' not in request.session:
        return redirect('/adminpanel/login/')

    orders = Orders.objects.all().order_by('-order_date')
    for order in orders:
        order.items_list = OrderItems.objects.filter(order_id=order.order_id).select_related('product')

    return render(request, 'store/admin_orders.html', {'orders': orders})


def payment_page(request, order_id):
    if 'customer_id' not in request.session:
        return redirect('/login/')

    order = get_object_or_404(Orders, order_id=order_id)

    return render(request, 'store/payment_page.html', {'order': order})


def process_payment(request, order_id):
    if request.method != 'POST':
        return redirect('payment_page', order_id=order_id)

    if 'customer_id' not in request.session:
        return redirect('/login/')

    order = get_object_or_404(Orders, order_id=order_id)

    # simulate payment
    trans_id = f"SIM{order.order_id}{int(timezone.now().timestamp())}"

    Payments.objects.create(
        order=order,
        payment_method='Simulated',
        amount=order.total_amount,
        payment_date=timezone.now(),
        payment_status='Completed',
        transaction_id=trans_id
    )

    order.order_status = 'Paid'
    order.delivery_date = timezone.now()
    order.save()

    return redirect('/orders/')