FROM python:3.13-alpine

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv pip install . --system

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
