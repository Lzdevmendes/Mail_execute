# 🚂 Deploy Mailexecute no Railway

## 📋 Pré-requisitos
- ✅ Conta no Railway (railway.app)
- ✅ Projeto no GitHub
- ✅ Repositório público ou privado

## 🚀 Passos para Deploy

### 1️⃣ **Conectar com GitHub**
1. Acesse [railway.app](https://railway.app)
2. Clique em **"Start a New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Escolha o repositório **Mailexecute**

### 2️⃣ **Configurar Variáveis de Ambiente**
No dashboard do Railway, vá em **Variables** e adicione:

```bash
# Essenciais para funcionamento
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PYTHONPATH=/app

# Caminhos otimizados para Railway
MODEL_CACHE_DIR=/tmp/models_cache
UPLOAD_DIR=/tmp/uploads
LOG_FILE=/tmp/logs/app.log

# Configurações de segurança
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true

# Configurações de performance (plano gratuito)
MAX_FILE_SIZE=5242880
MAX_CONTENT_LENGTH=8000
MAX_CONCURRENT_REQUESTS=5
```

### 3️⃣ **Deploy Automático**
- ✅ Railway detecta automaticamente o `Dockerfile`
- ✅ Usa as configurações do `railway.toml`
- ✅ Inicia o build automaticamente

### 4️⃣ **Verificar Deploy**
1. Aguarde o build completar (5-10 minutos)
2. Acesse a URL fornecida pelo Railway
3. Teste a rota `/health` para verificar status
4. Interface estará disponível na URL raiz `/`

## 🔧 Configurações Importantes

### **Limites do Plano Gratuito Railway:**
- 💾 **RAM**: 512MB
- 🕐 **CPU**: Compartilhado
- 📦 **Build**: 10 min/mês
- 🌐 **Tráfego**: Ilimitado
- ⏰ **Uptime**: Sleep após inatividade

### **Otimizações Aplicadas:**
- ✅ Dockerfile simplificado para Railway
- ✅ Variáveis de ambiente configuradas
- ✅ Caminhos temporários (/tmp) para Railway
- ✅ Limites ajustados para plano gratuito
- ✅ Health check configurado

## 🔗 URLs Importantes
- **Aplicação**: `https://mailexecute-production.up.railway.app`
- **API Docs**: `https://sua-url/docs`
- **Health Check**: `https://sua-url/health`
- **Metrics**: `https://sua-url/metrics`

## 🚨 Troubleshooting

### **Se o build falhar:**
1. Verifique logs no Railway dashboard
2. Confirme que todas as variáveis estão configuradas
3. Verifique se o repositório tem todos os arquivos

### **Se a aplicação não iniciar:**
1. Acesse logs do Railway
2. Verifique se `PORT` está sendo usado pelo uvicorn
3. Confirme que health check retorna 200

### **Para atualizar:**
1. Faça push no repositório GitHub
2. Railway fará redeploy automaticamente

## 📞 Suporte
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway