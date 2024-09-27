import matplotlib.pyplot as plt
import io
import base64

def price_history_graph(record):
    # Obtener el historial de precios del disco
    price_history = record.price_history.all().order_by('date')
    
    # Si no hay historial, retorna None
    if not price_history.exists():
        return None

    # Fechas y precios para la gráfica
    dates = [entry.date for entry in price_history]
    prices = [entry.price for entry in price_history]

    # Crear la gráfica
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, marker='o')
    plt.title(f'Historial de Precios para {record.title}')
    plt.xlabel('Fecha')
    plt.ylabel('Precio')
    plt.grid(True)

    # Guardar la gráfica en un objeto en memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Convertir la imagen a base64 para pasarla a la plantilla
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return f'data:image/png;base64,{image_base64}'
