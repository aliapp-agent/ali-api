# Frontend Integration Guide

Este guia mostra como integrar o frontend Firebase (https://ali-app-97976.web.app) com a API Ali.

## 🔗 URLs da API

### Desenvolvimento Local
- **API Base**: `http://localhost:8080`
- **Swagger Docs**: `http://localhost:8080/docs`
- **Health Check**: `http://localhost:8080/health`

### Produção (Cloud Run)
- **API Base**: `https://ali-api-production-[hash]-uc.a.run.app`
- **Health Check**: `https://ali-api-production-[hash]-uc.a.run.app/health`

## 🔑 Autenticação Firebase

### 1. Configuração do Firebase no Frontend

```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  projectId: "ali-app-97976",
  // ... outras configurações
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
```

### 2. Obter Token de Autenticação

```javascript
// auth.js
import { auth } from './firebase-config';

async function getAuthToken() {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  throw new Error('Usuário não autenticado');
}
```

### 3. Configurar Cliente API

```javascript
// api-client.js
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://ali-api-production-[hash]-uc.a.run.app'
  : 'http://localhost:8080';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const token = await getAuthToken();
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      },
      ...options
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }

  // Métodos específicos
  async getHealth() {
    return this.request('/health');
  }

  async getUserProfile() {
    return this.request('/api/v1/users/me');
  }

  async sendChatMessage(messages) {
    return this.request('/api/v1/chatbot/chat', {
      method: 'POST',
      body: JSON.stringify({ messages })
    });
  }

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = await getAuthToken();
    
    return fetch(`${this.baseURL}/api/v1/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
  }
}

export const apiClient = new ApiClient();
```

## 📡 Principais Endpoints da API

### Autenticação
- `POST /api/v1/auth/register` - Registrar usuário
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Perfil do usuário
- `POST /api/v1/auth/logout` - Logout

### Chat
- `POST /api/v1/chatbot/chat` - Enviar mensagem
- `GET /api/v1/chatbot/messages` - Histórico de mensagens
- `DELETE /api/v1/chatbot/messages` - Limpar histórico

### Documentos
- `POST /api/v1/documents/upload` - Upload de documento
- `GET /api/v1/documents` - Listar documentos
- `GET /api/v1/documents/{id}` - Obter documento específico
- `DELETE /api/v1/documents/{id}` - Excluir documento

### Usuários
- `GET /api/v1/users/me` - Perfil do usuário
- `PUT /api/v1/users/me` - Atualizar perfil

## 🔄 Exemplo de Integração React

### Hook para Chat

```javascript
// hooks/useChat.js
import { useState, useCallback } from 'react';
import { apiClient } from '../services/api-client';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (content) => {
    setLoading(true);
    
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await apiClient.sendChatMessage([
        ...messages,
        userMessage
      ]);
      
      setMessages(prev => [...prev, ...response.messages]);
    } catch (error) {
      console.error('Erro no chat:', error);
      // Adicionar tratamento de erro
    } finally {
      setLoading(false);
    }
  }, [messages]);

  return {
    messages,
    sendMessage,
    loading
  };
}
```

### Componente de Chat

```javascript
// components/Chat.jsx
import { useState } from 'react';
import { useChat } from '../hooks/useChat';

export function Chat() {
  const [input, setInput] = useState('');
  const { messages, sendMessage, loading } = useChat();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <p>{message.content}</p>
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite sua mensagem..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
    </div>
  );
}
```

## 🛡️ Tratamento de Erros

```javascript
// utils/error-handler.js
export function handleApiError(error) {
  if (error.status === 401) {
    // Usuário não autenticado - redirecionar para login
    window.location.href = '/login';
    return;
  }
  
  if (error.status === 403) {
    // Acesso negado
    alert('Você não tem permissão para esta ação');
    return;
  }
  
  if (error.status === 429) {
    // Rate limit
    alert('Muitas requisições. Tente novamente em alguns minutos.');
    return;
  }
  
  // Erro genérico
  console.error('Erro da API:', error);
  alert('Ocorreu um erro. Tente novamente.');
}
```

## 🔧 Configuração de CORS

A API já está configurada para aceitar requisições do seu frontend:
- `https://ali-app-97976.web.app`
- `https://ali-app-97976.firebaseapp.com`

## 📋 Checklist de Integração

### ✅ Configuração Base
- [ ] Firebase SDK configurado no frontend
- [ ] Cliente API configurado com autenticação
- [ ] URLs da API configuradas (dev/prod)

### ✅ Autenticação
- [ ] Login com Firebase Auth funcionando
- [ ] Token JWT sendo enviado nas requisições
- [ ] Tratamento de token expirado

### ✅ Funcionalidades Principais
- [ ] Chat funcionando
- [ ] Upload de documentos
- [ ] Listagem de documentos
- [ ] Perfil do usuário

### ✅ Tratamento de Erros
- [ ] Erros de rede
- [ ] Erros de autenticação
- [ ] Rate limiting
- [ ] Validação de dados

## 🚀 Deploy e Produção

### Firebase Hosting (Frontend)
Seu frontend já está hospedado em:
- **URL Principal**: `https://ali-app-97976.web.app`
- **URL Alternativa**: `https://ali-app-97976.firebaseapp.com`

### Deploy do Frontend
```bash
# No diretório do seu projeto frontend
npm run build
firebase deploy --only hosting
```

### Cloud Run (API)
1. **API em Produção**: Configurada no Cloud Run
2. **CORS**: Já configurado para aceitar requisições do Firebase Hosting
3. **HTTPS**: Obrigatório em produção (já configurado)

### Configuração de Ambiente no Frontend
```javascript
// .env.production (Firebase Hosting)
REACT_APP_API_URL=https://ali-api-production-[hash]-uc.a.run.app
REACT_APP_FIREBASE_PROJECT_ID=ali-app-97976

// .env.development (Local)
REACT_APP_API_URL=http://localhost:8080
REACT_APP_FIREBASE_PROJECT_ID=ali-app-97976
```

## 📞 Testando a Integração

```bash
# Testar API local com curl
curl -X GET "http://localhost:8080/health" \
  -H "accept: application/json"

# Testar autenticação
curl -X GET "http://localhost:8080/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

## 🎯 Próximos Passos

1. Implementar autenticação no frontend
2. Configurar cliente API com token Firebase
3. Criar componentes para chat e documentos
4. Testar integração completa
5. Deploy em produção