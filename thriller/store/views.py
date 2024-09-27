from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import Record, ShoppingCart, CartItem, Order, UserProfile, PriceHistory, Review 
from .forms import RecordForm, CustomUserCreationForm, ReviewForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import urllib, base64


def record_list(request, filter_type=None, filter_value=None):
    records = Record.objects.all()

    if filter_type == "artist" and filter_value:
        records = records.filter(artist=filter_value)
    elif filter_type == "genre" and filter_value:
        records = records.filter(genre=filter_value)

    search_query = request.GET.get("q", "")
    if search_query:
        records = records.filter(
            Q(title__icontains=search_query)
            | Q(artist__icontains=search_query)
            | Q(genre__icontains=search_query)
        )

    sort = request.GET.get("sort", "title")
    order = request.GET.get("order", "asc")
    order_direction = "" if order == "asc" else "-"
    records = records.order_by(f"{order_direction}{sort}")

    order_directions = {
        "title": "asc" if sort == "title" and order == "desc" else "desc",
        "artist": "asc" if sort == "artist" and order == "desc" else "desc",
        "genre": "asc" if sort == "genre" and order == "desc" else "desc",
        "price": "asc" if sort == "price" and order == "desc" else "desc",
    }

    context = {
        "records": records,
        "search_query": search_query,
        "order_directions": order_directions,
    }

    return render(request, "store/record_list.html", context)


def price_history_graph(record):
    price_history = record.price_history.all().order_by("date")

    dates = [entry.date for entry in price_history]
    prices = [entry.price for entry in price_history]

    # Crear la gráfica
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, marker="o")
    plt.xlabel("Fecha")
    plt.ylabel("Precio ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar la gráfica en un objeto BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = "data:image/png;base64," + urllib.parse.quote(string)

    return uri


def record_detail(request, record_id):
    record = get_object_or_404(Record, id=record_id)
    graph = price_history_graph(record)
    reviews = Review.objects.filter(record=record)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.record = record
            review.save()
            record.update_average_rating()
            return redirect('record_detail', record_id=record.id)
    else:
        form = ReviewForm()

    return render(request, 'store/record_detail.html', {
        'record': record,
        'graph': graph,
        'reviews': reviews,
        'form': form
    })


def search_records(request):
    query = request.GET.get("q")
    records = Record.objects.all()

    if query:
        records = records.filter(Q(title__icontains=query) | Q(artist__icontains=query))

    return render(
        request, "store/record_list.html", {"records": records, "query": query}
    )


@login_required
def profile_view(request):
    return render(request, "store/profile.html")


@login_required
@user_passes_test(lambda u: u.is_staff)
def create_record(request):
    if request.method == "POST":
        form = RecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("record_list")
    else:
        form = RecordForm()

    return render(request, "store/create_record.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, address=form.cleaned_data["address"])
            login(request, user)
            messages.success(request, "¡Registro exitoso! Bienvenido.")
            return redirect("record_list")
        else:
            messages.error(
                request, "Error en el registro. Por favor, corrige los errores."
            )
    else:
        form = CustomUserCreationForm()

    return render(request, "store/register.html", {"form": form})


def new_price_history(record):
    PriceHistory.objects.create(record=record, price=record.price)


@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_record(request, record_id):
    record = get_object_or_404(Record, id=record_id)

    if request.method == "POST":
        form = RecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            # new_price_history(record)
            messages.success(request, "El disco ha sido actualizado correctamente.")
            return redirect("record_detail", record_id=record.id)
    else:
        form = RecordForm(instance=record)

    return render(request, "store/edit_record.html", {"form": form, "record": record})


def records_by_filter(request, filter_type, filter_value):
    if filter_type == "artist":
        records = Record.objects.filter(artist=filter_value)
    elif filter_type == "genre":
        records = Record.objects.filter(genre=filter_value)
    else:
        records = Record.objects.all()

    return render(
        request,
        "store/record_list.html",
        {
            "records": records,
            "filter_type": filter_type,
            "filter_value": filter_value,
        },
    )


def compare_records(request):
    # IDs de los productos seleccionados de la URL
    ids = request.GET.get("ids", "").split(",")
    records = Record.objects.filter(id__in=ids)

    # Solo se muestran hasta 2 productos
    if records.count() > 2:
        records = records[:2]

    return render(request, "store/compare_records.html", {"records": records})


def add_to_cart(request, product_id):
    product = get_object_or_404(Record, id=product_id) 
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)  
    
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, record=product)
    
    if not created:
        
        cart_item.quantity += 1
    cart_item.save() 

    return redirect('cart_view') 


def cart_view(request):
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)  
    return render(request, 'store/cart.html', {'cart': cart})


def clear_cart(request):
    cart = ShoppingCart.objects.get(user=request.user)
    cart.cartitem_set.all().delete()  
    return redirect('cart_view')  

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()  
    return redirect('cart_view')