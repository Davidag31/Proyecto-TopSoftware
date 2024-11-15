from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.record_list, name="record_list"),
    path("record/<int:record_id>/", views.record_detail, name="record_detail"),
    path(
        "filter/<str:filter_type>/<path:filter_value>/",
        views.record_list,
        name="records_by_filter",
    ),
    path("record/<int:record_id>/edit/", views.edit_record, name="edit_record"),
    path("search/", views.search_records, name="search_records"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="store/login.html"),
        name="login",
    ),
    path("register/", views.register, name="register"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("create/", views.create_record, name="create_record"),
    path("compare/", views.compare_records, name="compare_records"),
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("i18n/", include("django.conf.urls.i18n")),  # Add this line
    path("set_language/", views.set_language, name="set_language"),
    path(
        "process_payment/<str:method>/", views.process_payment, name="process_payment"
    ),
    path("checkout/", views.checkout, name="checkout"),
    path("album/<int:album_id>/", views.album_detail, name="album_detail"),
    path("api/records/", views.get_api_records, name="records"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
