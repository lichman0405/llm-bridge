FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt
COPY ./app /app/app
EXPOSE 3456
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3456"]