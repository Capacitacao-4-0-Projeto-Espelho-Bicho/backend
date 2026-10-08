# Imagem base Python
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para aproveitar cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor porta
EXPOSE 5000

# Variáveis de ambiente padrão
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Comando para iniciar o Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]