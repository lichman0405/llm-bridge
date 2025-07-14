FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY models.yml .
COPY .env .

RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

COPY ./app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]