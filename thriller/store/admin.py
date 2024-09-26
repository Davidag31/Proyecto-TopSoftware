from django.contrib import admin
from .models import Record, ShoppingCart, Order, Payment, CartItem

admin.site.register(Record)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(Payment)
