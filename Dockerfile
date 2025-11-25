FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la app
COPY chatbotgradio.py .

# Exponer puerto de Gradio
EXPOSE 7860

# Comando para ejecutar la app
CMD ["sh", "-c", "sleep 10 && python chatbotgradio.py"]