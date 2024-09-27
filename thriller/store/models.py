from django.contrib.auth.models import User
from django.db import models
import matplotlib.pyplot as plt 
import io
import base64
from django.db.models import Avg

class Record(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to="record_images/", blank=True, null=True)
    genre = models.CharField(max_length=100, default="N/A")
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    def update_average_rating(self):
        """Calcula la calificación promedio basada en las opiniones"""
        average = self.review_set.aggregate(Avg('rating'))['rating__avg']
        self.average_rating = average if average is not None else 0
        self.save()

    def __str__(self):
        return f"{self.title} by {self.artist}"
    

from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating de 1 a 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['record', 'user'], name='unique_review')
        ]

    def __str__(self):
        return f"Review for {self.record.title} by {self.user.username}"

    
class PriceHistory(models.Model):
    record = models.ForeignKey(Record, related_name='price_history', on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Price of {self.record.title} on {self.date}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    records = models.ManyToManyField(Record, through="CartItem")

    def total_price(self):
        return sum(item.total_price() for item in self.cartitem_set.all())

    def __str__(self):
        return f"Shopping Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.quantity * self.record.price

    def __str__(self):
        return f"{self.record.title} (x{self.quantity})"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.OneToOneField(ShoppingCart, on_delete=models.CASCADE)
    ordered_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} for {self.user.username}"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"
