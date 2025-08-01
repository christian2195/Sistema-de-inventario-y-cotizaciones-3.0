FROM python:3.13-slim-bullseye

# Instala dependencias del sistema requeridas por WeasyPrint y libgobject
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    fonts-liberation \
    shared-mime-info \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Resto de tu configuración
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
