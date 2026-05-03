# ML Category Web

Sistema web para exploração de categorias do Mercado Livre Brasil.

**Stack:** FastAPI · React · PostgreSQL · Celery · Redis · Docker · Nginx · Let's Encrypt

---

## Deploy na VPS (Ubuntu 22.04/24.04)

### Pré-requisitos

- Docker e Docker Compose instalados
- Domínio apontando para o IP da VPS (registro A configurado)
- Portas 80 e 443 abertas no firewall

### 1. Clonar o repositório

```bash
git clone <seu-repositorio> ml-category-web
cd ml-category-web
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com seus valores:

```env
POSTGRES_PASSWORD=senha_forte_aqui
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DOMAIN=seu-dominio.com
CERTBOT_EMAIL=seu@email.com
ENVIRONMENT=production
```

### 3. Substituir o domínio no Nginx

```bash
sed -i 's/YOUR_DOMAIN/seu-dominio.com/g' nginx/nginx.conf
```

### 4. Obter certificado SSL (primeira vez)

```bash
# Sobe Nginx temporariamente na porta 80 para validação ACME
docker compose up -d nginx

# Obtém o certificado
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d seu-dominio.com -d www.seu-dominio.com \
  --email seu@email.com --agree-tos --no-eff-email

# Para o Nginx temporário
docker compose stop nginx
```

### 5. Subir todos os serviços em produção

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 6. Verificar que está funcionando

```bash
# Status dos containers
docker compose ps

# Logs do backend
docker compose logs -f backend

# Logs do Celery worker
docker compose logs -f celery_worker

# Testar health check
curl https://seu-dominio.com/api/health
```

---

## Desenvolvimento local

```bash
cp .env.example .env
# Edite .env com valores de desenvolvimento

docker compose up -d
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Flower (Celery monitor): http://localhost:5555

---

## Comandos úteis

```bash
# Executar migrations manualmente
docker compose exec backend alembic upgrade head

# Criar nova migration
docker compose exec backend alembic revision --autogenerate -m "descricao"

# Acessar banco PostgreSQL
docker compose exec db psql -U mlcategory -d mlcategory

# Ver logs em tempo real
docker compose logs -f

# Reiniciar um serviço
docker compose restart backend

# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker compose down -v
```

---

## Renovação automática do SSL

O container `certbot` renova automaticamente o certificado a cada 12 horas.
A renovação só ocorre quando o certificado está próximo do vencimento (< 30 dias).

Para renovar manualmente:
```bash
docker compose exec certbot certbot renew
docker compose exec nginx nginx -s reload
```
