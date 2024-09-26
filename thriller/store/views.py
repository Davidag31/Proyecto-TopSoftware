from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import Record, ShoppingCart, CartItem, Order, UserProfile
from .forms import RecordForm, CustomUserCreationForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages 
from django.db.models import Q  

def record_list(request):
    records = Record.objects.all()
    return render(request, 'store/record_list.html', {'records': records})

def record_detail(request, record_id):
    record = get_object_or_404(Record, pk=record_id)
    return render(request, 'store/record_detail.html', {'record': record})

def search_records(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda de la query
    records = Record.objects.all()  # Obtiene todos los registros por defecto

    if query:  # Si hay un término de búsqueda
        records = records.filter(Q(title__icontains=query) | Q(artist__icontains=query))  # Filtra los registros

    return render(request, 'store/record_list.html', {'records': records, 'query': query})

@login_required
def profile_view(request):
    return render(request, 'store/profile.html')

@login_required
def add_to_cart(request, record_id):
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)
    record = get_object_or_404(Record, pk=record_id)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, record=record)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart_view')

@login_required
def cart_view(request):
    cart = ShoppingCart.objects.get(user=request.user)
    cart_items = cart.cartitem_set.all()
    total_price = cart.total_price()
    
    return render(request, 'store/cart_view.html', {'cart': cart, 'cart_items': cart_items, 'total_price': total_price})

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, pk=cart_item_id)
    cart_item.delete()
    return redirect('cart_view')

@login_required
def checkout(request):
    cart = ShoppingCart.objects.get(user=request.user)
    if not cart.cartitem_set.exists():
        return HttpResponse("No tienes artículos en tu carrito", status=400)

    order = Order.objects.create(user=request.user, cart=cart)
    return redirect('order_success')

@login_required
def order_success(request):
    return render(request, 'store/order_success.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    return render(request, 'store/order_history.html', {'orders': orders})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.is_paid and not order.is_cancelled:
        order.is_cancelled = True
        order.save()
        return redirect('order_history')
    
    return HttpResponse("El pedido ya está pagado o cancelado", status=400)

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-ordered_at')
    return render(request, 'store/admin_order_list.html', {'orders': orders})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/admin_order_detail.html', {'order': order})

@staff_member_required
def mark_order_paid(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if not order.is_paid:
        order.is_paid = True
        order.save()
        return redirect('admin_order_list')
    
    return HttpResponse("El pedido ya fue pagado", status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Verifica si el usuario es un administrador
def create_record(request):
    if request.method == 'POST':
        form = RecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('record_list')
    else:
        form = RecordForm()
    
    return render(request, 'store/create_record.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Crea el usuario
            # Crear el perfil de usuario
            UserProfile.objects.create(user=user, address=form.cleaned_data['address'])
            login(request, user)  # Inicia sesión al usuario
            messages.success(request, "¡Registro exitoso! Bienvenido.")
            return redirect('record_list')
        else:
            messages.error(request, "Error en el registro. Por favor, corrige los errores.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/register.html', {'form': form})
