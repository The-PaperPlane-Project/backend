FROM python:3.14-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "fastapi>=0.136.1,<0.137.0" \
    "uvicorn>=0.47.0,<0.48.0" \
    "sqlalchemy>=2.0.49,<3.0.0" \
    "pydantic>=2.13.4,<3.0.0" \
    "python-dotenv>=1.2.2,<2.0.0" \
    "email-validator>=2.3.0,<3.0.0" \
    "python-jose[cryptography]>=3.5.0,<4.0.0" \
    "passlib[bcrypt]>=1.7.4,<2.0.0" \
    "python-multipart>=0.0.29,<0.0.30"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
