from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import (
    Record,
    ShoppingCart,
    CartItem,
    Order,
    UserProfile,
    PriceHistory,
    Review,
)
from .forms import RecordForm, CustomUserCreationForm, ReviewForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import urllib, base64
from django.utils.translation import activate
from django.conf import settings
from django.utils import translation
from .payment_processor import CheckPaymentProcessor, AccountBalancePaymentProcessor
import requests
from django.http import JsonResponse
from requests.auth import HTTPBasicAuth
from .models import Record
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import RecordSerializer


def get_api_records(request):
    # Obtén todos los registros
    records = Record.objects.all()

    # Serializa los datos manualmente
    # Aquí asumimos que 'Record' tiene campos como 'id', 'title', 'artist', etc.
    records_data = list(
        records.values("id", "title", "artist", "price", "stock")
    )  # Cambia los campos según lo que quieras incluir

    # Devuelve la respuesta en formato JSON
    return JsonResponse({"records": records_data})


def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    response = requests.post(
        auth_url,
        data={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
    )
    response_data = response.json()
    return response_data["access_token"]


def get_track_preview_url(track_name):
    token = get_spotify_token()
    search_url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": track_name, "type": "track", "limit": 1}
    response = requests.get(search_url, headers=headers, params=params)
    results = response.json()

    if results["tracks"]["items"]:
        return results["tracks"]["items"][0]["preview_url"]
    return None  # Si no hay preview disponible


def album_detail(request, album_id):
    album = get_object_or_404(Record, id=album_id)
    preview_url = get_track_preview_url(album.title)
    return render(
        request, "store/playback.html", {"album": album, "preview_url": preview_url}
    )


@login_required
def process_payment(request, method):
    cart = ShoppingCart.objects.get(user=request.user)
    total_amount = sum(
        item.record.price * item.quantity for item in cart.cartitem_set.all()
    )

    if method == "check":
        processor = CheckPaymentProcessor()
    elif method == "balance":
        processor = AccountBalancePaymentProcessor(request.user)
    else:
        return HttpResponse("Método de pago no soportado.", content_type="text/plain")

    response = processor.process_payment(cart, total_amount)

    # Vaciar el carrito después de procesar el pago sin redirigir
    clear_cart(request, redirect_to_cart=False)

    return response


@login_required
def checkout(request):
    return render(request, "store/checkout.html")


def set_language(request):
    user_language = request.GET.get(
        "language", "es"
    )  # Get the language from the query, default to 'es'
    translation.activate(user_language)  # Activate the language
    request.session["language"] = user_language  # Save the language in the session

    # Get the previous URL and replace the language code in the path
    previous_url = request.META.get("HTTP_REFERER", "/")
    new_url = previous_url.replace("/en/", f"/{user_language}/").replace(
        "/es/", f"/{user_language}/"
    )

    return redirect(new_url)  # Redirect to the new URL with the updated language code


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

    # Obtener la URL de la demo de Spotify
    preview_url = get_track_preview_url(record.title)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.record = record
            review.save()
            record.update_average_rating()
            return redirect("record_detail", record_id=record.id)
    else:
        form = ReviewForm()

    return render(
        request,
        "store/record_detail.html",
        {
            "record": record,
            "graph": graph,
            "reviews": reviews,
            "form": form,
            "preview_url": preview_url,
        },
    )


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


from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import UserProfile


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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Record, id=product_id)
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, record=product)

    if not created:
        cart_item.quantity += 1
    cart_item.save()

    return redirect("cart_view")


def cart_view(request):
    cart, created = ShoppingCart.objects.get_or_create(user=request.user)
    return render(request, "store/cart.html", {"cart": cart})


def clear_cart(request, redirect_to_cart=True):
    cart = ShoppingCart.objects.get(user=request.user)
    cart.cartitem_set.all().delete()
    if redirect_to_cart:
        return redirect("cart_view")


def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect("cart_view")
