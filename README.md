# 📧 Sistema de Classificação de Emails

Sistema inteligente para classificação automática de emails como **produtivos** ou **improdutivos**, com geração de respostas apropriadas usando IA e processamento de linguagem natural.

## 🎯 Funcionalidades Principais

- **Classificação Inteligente**: Análise de emails usando regras baseadas em NLP e modelos de IA
- **Interface Web Responsiva**: Frontend moderno com Bootstrap e JavaScript
- **API REST Completa**: Endpoints para classificação, métricas e upload de arquivos
- **Suporte a Arquivos**: Processamento de PDFs e arquivos de texto
- **Métricas em Tempo Real**: Dashboard com estatísticas de uso
- **Respostas Automáticas**: Geração de respostas contextualizadas

## 🚀 Como Executar

### 1. Backend (FastAPI + Python)
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

### 2. Frontend
Acesse: `http://localhost:8001` após iniciar o backend

### 3. Docker (Recomendado)
```bash
# Build da imagem
docker build -t mail-execute .

# Executar container
docker run -p 8000:8000 mail-execute
```

### 4. Script de Inicialização
```bash
# Usar script personalizado
python start_server.py
```

### 5. Testes
```bash
# Testes completos
python -m pytest tests/

# Ou teste individual
python tests/test_api.py
```

## 📋 Estrutura do Projeto

```
Mail_execute/
├── backend/
│   ├── app/
│   │   ├── services/          # Lógica de negócio
│   │   │   └── email_classifier.py
│   │   ├── utils/             # Utilitários
│   │   │   ├── nlp_processor.py
│   │   │   └── file_processor.py
│   │   ├── models/            # Modelos Pydantic
│   │   │   └── email_models.py
│   │   ├── config.py          # Configurações
│   │   └── main.py            # API FastAPI
│   └── requirements.txt
├── frontend/
│   ├── templates/index.html   # Interface web
│   ├── static/css/style.css   # Estilos
│   └── static/js/app.js       # JavaScript
├── tests/
│   └── test_api.py           # Testes automatizados
├── data/
│   └── sample_emails.txt     # Emails de exemplo
├── models_cache/             # Cache de modelos NLP
├── uploads/                  # Arquivos enviados
├── Dockerfile                # Configuração Docker
├── start_server.py          # Script de inicialização
├── clean_cache.py           # Script de limpeza
├── requirements.txt         # Dependências principais
├── requirements-test.txt    # Dependências de teste
└── README.md
```

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web moderno e rápido
- **Pydantic** - Validação de dados e serialização
- **NLTK** - Processamento de linguagem natural
- **Transformers** - Modelos de IA (opcional)
- **PyPDF2** - Processamento de arquivos PDF

### Frontend
- **HTML5/CSS3** - Estrutura e estilos
- **Bootstrap 5** - Framework CSS responsivo
- **JavaScript ES6** - Interatividade e AJAX
- **Font Awesome** - Ícones

### Qualidade e Testes
- **Pytest** - Framework de testes
- **Loguru** - Sistema de logs
- **Type Hints** - Tipagem estática Python

## 📊 Algoritmo de Classificação

O sistema usa uma abordagem híbrida:

1. **Análise de Características**:
   - Palavras-chave relacionadas a trabalho
   - Urgência (prazos, "urgente", "ASAP")
   - Solicitações de ação
   - Sentimento do texto

2. **Pontuação Ponderada**:
   - Business relevance: peso 0.4
   - Urgency score: peso 0.3
   - Action requests: peso 0.2
   - Sentiment: peso 0.1

3. **Classificação**:
   - **Produtivo**: Score ≥ 0.6
   - **Improdutivo**: Score < 0.6

## 📈 Exemplos de Uso

### Email Produtivo
```
Preciso urgentemente dos relatórios de vendas para 
a reunião de amanhã. O sistema não está funcionando.
```
**Resultado**: `produtivo` (85% confiança)

### Email Improdutivo
```
Oi pessoal! A festa de ontem foi incrível! 
Obrigado por tudo, abraços para todos!
```
**Resultado**: `improdutivo` (90% confiança)

## 🔧 Configuração para Desenvolvimento

### Variáveis de Ambiente (.env)
```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8001
DEBUG=True

# NLP Configuration
NLP_LANGUAGE=portuguese
USE_AI_MODEL=False
```

### Dependências Python
```bash
pip install fastapi uvicorn pydantic nltk transformers
```

## 📋 API Endpoints

### Classificação
- `POST /classify` - Classifica texto
- `POST /classify/file` - Classifica arquivo

### Sistema
- `GET /health` - Status do sistema
- `GET /metrics` - Métricas de uso
- `GET /` - Interface web

## 🐳 Deploy e Containerização

### Docker
O projeto inclui `Dockerfile` otimizado para produção:
- Multi-stage build para reduzir tamanho da imagem
- Imagem final < 1GB (otimizada de 7.6GB original)
- Pronto para deploy em qualquer plataforma

### Deploy em Produção

#### Opção 1: Docker Compose (Recomendado)
```bash
# Criar docker-compose.yml e fazer deploy
docker-compose up -d
```

#### Opção 2: Docker Manual
```bash
# Build da imagem
docker build -t mail-execute .

# Run em produção
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  --name mail-execute \
  mail-execute
```

#### Opção 3: VPS/Servidor Próprio
```bash
# Clone do repositório
git clone https://github.com/Lzdevmendes/Mail_execute.git
cd Mail_execute

# Setup do ambiente
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalação
pip install -r requirements-production.txt

# Execução em produção
python start_server.py
```

**Compatível com**: AWS, Google Cloud, Azure, DigitalOcean, Heroku, VPS próprio, etc.

## 🛠️ Scripts Utilitários

### start_server.py
Script personalizado de inicialização com configurações otimizadas:
```bash
python start_server.py
```

### clean_cache.py
Limpeza automática de cache de modelos e arquivos temporários:
```bash
python clean_cache.py
```

## 🧪 Testes e Validação

O projeto inclui testes automatizados que validam:
- ✅ Importação de módulos
- ✅ Classificação de emails
- ✅ Processamento NLP
- ✅ Modelos Pydantic
- ✅ Endpoints da API

Execute os testes: `python -m pytest tests/` ou `python tests/test_api.py`

## 🎯 Pontos Técnicos para Entrevista

### Arquitetura
- **Clean Architecture**: Separação clara entre camadas
- **Dependency Injection**: Injeção de dependências
- **SOLID Principles**: Código bem estruturado
- **Type Safety**: Uso extensivo de type hints

### Performance
- **Async/Await**: Programação assíncrona
- **Lazy Loading**: Carregamento sob demanda
- **Caching**: Cache de modelos NLP
- **Efficient Processing**: Algoritmos otimizados

### Qualidade
- **Error Handling**: Tratamento robusto de erros
- **Validation**: Validação de dados com Pydantic
- **Logging**: Sistema de logs estruturado
- **Testing**: Cobertura de testes automatizados

### Segurança
- **Input Validation**: Validação de entrada
- **CORS**: Configuração adequada
- **File Security**: Validação de arquivos
- **Error Messages**: Não exposição de informações sensíveis

## 🚀 Pronto para Produção

- ✅ Código limpo e documentado
- ✅ Testes automatizados passando
- ✅ Git configurado corretamente
- ✅ Estrutura profissional
- ✅ Performance otimizada
- ✅ Interface responsiva
- ✅ API RESTful completa
- ✅ **Docker otimizado para deploy**
- ✅ **Deploy-ready para qualquer plataforma**
- ✅ **Scripts de automação**
- ✅ **Cache de modelos inteligente**

---

**Desenvolvido por Lzmendes para demonstrar competências em Python, FastAPI, NLP, Frontend e Arquitetura de Software.**