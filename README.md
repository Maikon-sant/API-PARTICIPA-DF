# 📡 API Participa DF
## Plataforma GovTech para Manifestações Legislativas

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009485?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql)](https://www.mysql.com/)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](#-licença)

**API REST para coleta e processamento de manifestações legislativas**

📍 **https://api.simplificagov.com**

[Instalação](#-instalação) | [Endpoints](#-endpoints) | [Exemplos](#-exemplos) | [Documentação](#-documentação) | [Deploy](#-deploy)

</div>

---

## ℹ️ Sobre

**SimplificaGov API** é uma API REST que permite coleta de manifestações legislativas em múltiplos formatos (texto, áudio, imagem, vídeo) com processamento automático, armazenamento seguro e rastreamento via protocolo único.

### ✨ Características

- 🎤 **Multicanal:** Texto, áudio, imagem ou vídeo
- 🔒 **Anônimo:** Sem login obrigatório
- 📍 **Rastreável:** Protocolo único por manifestação
- 🤖 **Processamento:** OCR, transcrição de áudio, análise de vídeo
- ⚡ **Rápido:** Respostas em JSON
- 📚 **Documentado:** Swagger + ReDoc automático
- 🛡️ **Seguro:** Validação e sanitização completa

---

## 📋 Tecnologia

| Item | Especificação |
|------|---------------|
| **Versão** | 1.0.0 |
| **Framework** | FastAPI 0.109.2+ |
| **Linguagem** | Python 3.11+ |
| **Banco** | MySQL 8.0+ / MariaDB 10.5+ |
| **Autenticação** | Nenhuma (v1.0) / JWT (v2.0) |
| **Documentação** | Swagger/ReDoc automático |
| **Base URL** | `https://api.simplificagov.com/v1` |

---

## 🚀 Instalação Rápida

### 1. Pré-requisitos

**Windows:**
```powershell
choco install python mysql tesseract ffmpeg
```

**macOS:**
```bash
brew install python@3.11 mysql tesseract ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv mysql-server tesseract-ocr ffmpeg
```

### 2. Clonar e Configurar

```bash
# Clonar repositório
git clone https://github.com/simplificagov/api.git
cd api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Banco de Dados

```bash
# Criar banco
mysql -u root -p
mysql> CREATE DATABASE simplificagov CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> EXIT;

# Rodar migrações
alembic upgrade head
```

### 4. Configurar `.env`

```env
DATABASE_URL=mysql+aiomysql://root:senha@localhost/simplificagov
APP_NAME=SimplificaGov
APP_VERSION=1.0.0
DEBUG=false
UPLOADS_DIR=./uploads
MAX_FILE_SIZE_MB=50
PROTOCOL_PREFIX=SG
PROTOCOL_YEAR=2026
```

### 5. Iniciar

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Produção
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Acessar:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔗 Endpoints

### Health Check
```http
GET /v1/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-28T10:00:00Z"
}
```

---

### 1️⃣ Criar Manifestação

```http
POST /v1/manifestations
Content-Type: multipart/form-data
```

**Parâmetros:**

| Param | Tipo | Obrigatório | Descrição |
|-------|------|-----------|-----------|
| `original_text` | string | ❌ | Texto da manifestação |
| `file` | file | ❌ | Arquivo (imagem, áudio, vídeo) |
| `input_type` | string | ✅ | `TEXT` \| `AUDIO` \| `IMAGE` \| `VIDEO` \| `MIXED` |
| `contact_name` | string | ❌ | Nome (se não anônimo) |
| `contact_email` | string | ❌ | Email |
| `contact_phone` | string | ❌ | Telefone |
| `anonymous` | boolean | ❌ | Padrão: `true` |

**Requisição:**
```bash
curl -X POST "http://localhost:8000/v1/manifestations" \
  -F "original_text=Sugiro melhorias no portal legislativo" \
  -F "input_type=TEXT" \
  -F "contact_email=usuario@email.com" \
  -F "anonymous=false"
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "protocol": null,
  "status": "DRAFT",
  "created_at": "2026-01-28T10:05:00Z"
}
```

---

### 2️⃣ Adicionar Anexos

```http
POST /v1/manifestations/{manifestation_id}/attachments
Content-Type: multipart/form-data
```

**Parâmetros:**

| Param | Tipo | Obrigatório |
|-------|------|-----------|
| `file` | file | ✅ |

**Requisição:**
```bash
curl -X POST "http://localhost:8000/v1/manifestations/550e8400-e29b-41d4-a716-446655440000/attachments" \
  -F "file=@documento.jpg"
```

**Response (201):**
```json
{
  "id": "attach-uuid",
  "manifestation_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "IMAGE",
  "filename": "documento.jpg",
  "size_bytes": 2048576,
  "extracted_text": "Texto extraído via OCR...",
  "processing_status": "COMPLETED",
  "created_at": "2026-01-28T10:10:00Z"
}
```

---

### 3️⃣ Atualizar Manifestação (rascunho)

```http
PATCH /v1/manifestations/{manifestation_id}
Content-Type: application/json
```

**Body:**
```json
{
  "original_text": "Texto atualizado",
  "contact_name": "João Silva",
  "contact_email": "joao@email.com"
}
```

**Requisição:**
```bash
curl -X PATCH "http://localhost:8000/v1/manifestations/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"original_text":"Novo texto","contact_name":"João"}'
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DRAFT",
  "updated_at": "2026-01-28T10:15:00Z"
}
```

---

### 4️⃣ Enviar/Finalizar Manifestação

```http
POST /v1/manifestations/{manifestation_id}/submit
Content-Type: application/json
```

**Requisição:**
```bash
curl -X POST "http://localhost:8000/v1/manifestations/550e8400-e29b-41d4-a716-446655440000/submit"
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "protocol": "SG-2026-000001",
  "status": "RECEIVED",
  "submitted_at": "2026-01-28T10:20:00Z",
  "message": "Manifestação recebida com sucesso"
}
```

---

### 5️⃣ Consultar por Protocolo

```http
GET /v1/manifestations/{protocol}
```

**Requisição:**
```bash
curl "http://localhost:8000/v1/manifestations/SG-2026-000001"
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "protocol": "SG-2026-000001",
  "status": "COMPLETED",
  "original_text": "Sugiro melhorias no portal legislativo",
  "input_type": "MIXED",
  "anonymous": false,
  "contact_name": "João Silva",
  "contact_email": "joao@email.com",
  "created_at": "2026-01-28T10:05:00Z",
  "submitted_at": "2026-01-28T10:20:00Z",
  "attachments": [
    {
      "id": "attach-uuid",
      "type": "IMAGE",
      "filename": "documento.jpg",
      "size_bytes": 2048576,
      "extracted_text": "Texto da imagem...",
      "processing_status": "COMPLETED"
    }
  ]
}
```

---

### 6️⃣ Listar Manifestações

```http
GET /v1/manifestations?page=1&page_size=10&status=RECEIVED
```

**Parâmetros Query:**

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `page` | int | 1 | Número da página |
| `page_size` | int | 10 | Itens por página |
| `status` | string | - | Filtro: `DRAFT`, `RECEIVED`, `PROCESSING`, `COMPLETED` |

**Requisição:**
```bash
curl "http://localhost:8000/v1/manifestations?page=1&page_size=5"
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "protocol": "SG-2026-000001",
      "status": "COMPLETED",
      "created_at": "2026-01-28T10:05:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15
}
```

---

### 7️⃣ Deletar Manifestação (Admin)

```http
DELETE /v1/admin/manifestations/{protocol}
```

**Requisição:**
```bash
curl -X DELETE "http://localhost:8000/v1/admin/manifestations/SG-2026-000001"
```

**Response (200):**
```json
{
  "message": "Manifestação deletada com sucesso"
}
```

---

## 💻 Exemplos de Uso

### Python

```python
import requests

BASE_URL = "http://localhost:8000/v1"

# 1. Criar manifestação
response = requests.post(
    f"{BASE_URL}/manifestations",
    data={
        "original_text": "Sugiro melhorias",
        "input_type": "TEXT",
        "contact_email": "usuario@email.com"
    }
)
manifestation = response.json()
print(f"ID: {manifestation['id']}")

# 2. Adicionar anexo
with open("foto.jpg", "rb") as f:
    files = {"file": f}
    requests.post(
        f"{BASE_URL}/manifestations/{manifestation['id']}/attachments",
        files=files
    )

# 3. Enviar
requests.post(f"{BASE_URL}/manifestations/{manifestation['id']}/submit")

# 4. Consultar
response = requests.get(f"{BASE_URL}/manifestations/{manifestation['protocol']}")
print(response.json())
```

### JavaScript (Fetch API)

```javascript
const BASE_URL = "http://localhost:8000/v1";

// 1. Criar manifestação
const formData = new FormData();
formData.append("original_text", "Sugiro melhorias");
formData.append("input_type", "TEXT");

const response = await fetch(`${BASE_URL}/manifestations`, {
  method: "POST",
  body: formData
});

const manifestation = await response.json();
console.log(manifestation.id);

// 2. Adicionar arquivo
const attachForm = new FormData();
attachForm.append("file", document.getElementById("fileInput").files[0]);

await fetch(
  `${BASE_URL}/manifestations/${manifestation.id}/attachments`,
  { method: "POST", body: attachForm }
);

// 3. Enviar
await fetch(`${BASE_URL}/manifestations/${manifestation.id}/submit`, {
  method: "POST"
});

// 4. Consultar
const result = await fetch(`${BASE_URL}/manifestations/${manifestation.protocol}`);
console.log(await result.json());
```

### cURL

```bash
# 1. Criar
RESPONSE=$(curl -X POST "http://localhost:8000/v1/manifestations" \
  -F "original_text=Sugiro melhorias" \
  -F "input_type=TEXT" \
  -F "contact_email=usuario@email.com")

ID=$(echo $RESPONSE | jq -r '.id')

# 2. Adicionar arquivo
curl -X POST "http://localhost:8000/v1/manifestations/$ID/attachments" \
  -F "file=@foto.jpg"

# 3. Enviar
curl -X POST "http://localhost:8000/v1/manifestations/$ID/submit"

# 4. Consultar
PROTOCOL=$(echo $RESPONSE | jq -r '.protocol')
curl "http://localhost:8000/v1/manifestations/$PROTOCOL"
```

---

## 🔐 Códigos HTTP

| Código | Significado |
|--------|-------------|
| **200** | OK - Sucesso |
| **201** | Created - Recurso criado |
| **400** | Bad Request - Dados inválidos |
| **404** | Not Found - Recurso não existe |
| **422** | Validation Error - Validação falhou |
| **500** | Server Error - Erro interno |

---

## 📊 Limites

| Limite | Valor |
|--------|-------|
| Tamanho máx. arquivo | 50 MB |
| Anexos por manifestação | 10 |
| Caracteres de texto | 10.000 |
| Tempo de processamento | 5 min |

---

## 🗄️ Banco de Dados

### Tabela: manifestations
```sql
CREATE TABLE manifestations (
  id CHAR(36) PRIMARY KEY,
  protocol VARCHAR(20) UNIQUE,
  original_text TEXT,
  status ENUM('DRAFT','RECEIVED','PROCESSING','COMPLETED'),
  input_type ENUM('TEXT','AUDIO','IMAGE','VIDEO','MIXED'),
  anonymous BOOLEAN DEFAULT TRUE,
  contact_name VARCHAR(255),
  contact_email VARCHAR(255),
  contact_phone VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  submitted_at TIMESTAMP NULL
) CHARSET=utf8mb4;
```

### Tabela: attachments
```sql
CREATE TABLE attachments (
  id CHAR(36) PRIMARY KEY,
  manifestation_id CHAR(36) NOT NULL,
  type ENUM('IMAGE','AUDIO','VIDEO'),
  filename VARCHAR(255),
  size_bytes INT,
  extracted_text LONGTEXT,
  processing_status ENUM('PENDING','PROCESSING','COMPLETED','ERROR'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (manifestation_id) REFERENCES manifestations(id)
) CHARSET=utf8mb4;
```

---

## 🐳 Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql+aiomysql://root:senha@db/simplificagov
    depends_on:
      - db
    volumes:
      - ./uploads:/app/uploads

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: senha
      MYSQL_DATABASE: simplificagov
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

**Usar:**
```bash
docker-compose up -d
```

---

## 🧪 Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app

# Modo verbose
pytest -v
```

---

## 📚 Documentação

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🚀 Deploy

### Produção (AWS)

**1. EC2 (t3.medium)**
```bash
# Ubuntu 22.04 AMI
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv mysql-client nginx -y

# Clonar e instalar
git clone https://github.com/simplificagov/api.git
cd api
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Rodar com Gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
```

**2. Nginx (reverse proxy)**
```nginx
server {
    listen 443 ssl http2;
    server_name api.simplificagov.com;

    ssl_certificate /etc/ssl/certs/api.simplificagov.com.crt;
    ssl_certificate_key /etc/ssl/private/api.simplificagov.com.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**3. RDS MySQL**
- Engine: MySQL 8.0
- Instance: db.t3.small
- Multi-AZ habilitado
- Backups automáticos

**4. Load Balancer (ALB)**
- Health check: GET /v1/health
- Port: 443 (HTTPS)
- Certificate: AWS Certificate Manager

---

## ❓ FAQ

**P: Preciso de API key?**  
R: Não em v1.0. JWT será requerido em v2.0.

**P: Qual é o tempo de processamento?**  
R: Criação é imediato. OCR/transcrição leva 1-5 minutos.

**P: Posso editar depois de enviar?**  
R: Não. Editável apenas em draft. Use PATCH antes de /submit.

**P: Como recupero minha manifestação?**  
R: Guarde o protocolo (ex: SG-2026-000001). Use GET /manifestations/{protocol}.

**P: Há limite de requisições?**  
R: Não em v1.0. Rate limiting em v1.1.

**P: Quais formatos de arquivo são suportados?**  
R: Imagens (JPG, PNG, GIF), áudio (MP3, WAV, OGG), vídeo (MP4, WEBM).

---

## 🤝 Contribuindo

1. Fork
2. Crie branch (`git checkout -b feature/XYZ`)
3. Commit (`git commit -m 'Add XYZ'`)
4. Push (`git push origin feature/XYZ`)
5. Pull Request

---

## 📜 Licença

MIT License - Veja [LICENSE](LICENSE)

---

## 📞 Suporte

- 📧 Email: dev@simplificagov.com.br
- 🐛 Issues: GitHub Issues
- 💬 Discussões: GitHub Discussions

---

<div align="center">

**SimplificaGov API v1.0.0**

Desenvolvido com ❤️ para democratizar a legislação brasileira

[⬆ Voltar ao topo](#-api-simplificagov)

</div>