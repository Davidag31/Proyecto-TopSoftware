from abc import ABC, abstractmethod
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import ShoppingCart

class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, cart: ShoppingCart, amount: float):
        pass

class CheckPaymentProcessor(PaymentProcessor):
    def process_payment(self, cart: ShoppingCart, amount: float):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, "Pago por cheque")
        p.drawString(100, 735, f"Monto total: ${amount}")
        
        y = 700
        for item in cart.cartitem_set.all():
            if y < 50:  # Si la posición y es menor que 50, crea una nueva página
                p.showPage()
                y = 750  # Reinicia la posición y para la nueva página
                p.drawString(100, y, "Pago por cheque")  # Vuelve a dibujar el título
                y -= 15
            # Aquí, dibujamos cada propiedad en un renglón distinto
            p.drawString(100, y, f"Disco: {item.record.title}")
            y -= 15
            p.drawString(100, y, f"Artista: {item.record.artist}")
            y -= 15
            p.drawString(100, y, f"Cantidad: {item.quantity}")
            y -= 15
            p.drawString(100, y, f"Precio: ${item.record.price}")
            y -= 30  # Espacio adicional entre los ítems

        p.showPage()
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="payment_receipt.pdf"'
        return response

class AccountBalancePaymentProcessor(PaymentProcessor):
    def __init__(self, user):
        self.user = user

    def process_payment(self, cart: ShoppingCart, amount: float):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, "Pago con saldo de cuenta")
        p.drawString(100, 735, f"Monto total: ${amount}")
        
        y = 700
        for item in cart.cartitem_set.all():
            if y < 50:  # Si la posición y es menor que 50, crea una nueva página
                p.showPage()
                y = 750  # Reinicia la posición y para la nueva página
                p.drawString(100, y, "Pago con saldo de cuenta")  # Vuelve a dibujar el título
                y -= 15
            # Aquí, dibujamos cada propiedad en un renglón distinto
            p.drawString(100, y, f"Disco: {item.record.title}")
            y -= 15
            p.drawString(100, y, f"Artista: {item.record.artist}")
            y -= 15
            p.drawString(100, y, f"Cantidad: {item.quantity}")
            y -= 15
            p.drawString(100, y, f"Precio: ${item.record.price}")
            y -= 30  # Espacio adicional entre los ítems

        p.showPage()
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="payment_receipt.pdf"'
        return response
