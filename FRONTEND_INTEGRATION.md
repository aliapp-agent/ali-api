# Frontend Integration Guide

Este guia ajuda a conectar o frontend da Ali App à API backend.

## 🔗 URLs da API

### Ambientes

```javascript
const API_URLS = {
  development: 'http://localhost:8000',
  staging: 'https://ali-api-staging-[hash]-uc.a.run.app',
  production: 'https://ali-api-production-[hash]-uc.a.run.app'
}
```

## 🛠️ Configuração do Cliente HTTP

### Axios Setup (Recomendado)

```javascript
// lib/api.js
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor para adicionar token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor para handle de erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Fetch Alternative

```javascript
// lib/api-fetch.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1`;
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem('authToken');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  get(endpoint) {
    return this.request(endpoint);
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT', 
      body: JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }
}

export default new ApiClient();
```

## 🔐 Autenticação

### Login Flow

```javascript
// services/auth.js
import apiClient from '../lib/api';

export const authService = {
  async login(email, password) {
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      });
      
      const { access_token, user } = response.data;
      
      // Store token
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, user };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Login failed' 
      };
    }
  },

  async register(userData) {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Registration failed' 
      };
    }
  },

  logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    window.location.href = '/login';
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  isAuthenticated() {
    return !!localStorage.getItem('authToken');
  }
};
```

### Protected Routes Hook

```javascript
// hooks/useAuth.js
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { authService } from '../services/auth';

export function useAuth(requireAuth = true) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = () => {
      const currentUser = authService.getCurrentUser();
      const isAuthenticated = authService.isAuthenticated();

      if (requireAuth && !isAuthenticated) {
        router.push('/login');
        return;
      }

      setUser(currentUser);
      setLoading(false);
    };

    checkAuth();
  }, [requireAuth, router]);

  return { user, loading, isAuthenticated: authService.isAuthenticated() };
}
```

## 💬 Chat Integration

### Chat Service

```javascript
// services/chat.js
import apiClient from '../lib/api';

export const chatService = {
  async sendMessage(message, sessionId = null) {
    try {
      const response = await apiClient.post('/chat', {
        message,
        session_id: sessionId
      });
      
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to send message');
    }
  },

  async streamMessage(message, sessionId, onChunk) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        })
      });

      if (!response.ok) throw new Error('Stream request failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;
            
            try {
              const parsed = JSON.parse(data);
              onChunk(parsed);
            } catch (e) {
              console.warn('Failed to parse chunk:', data);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      throw error;
    }
  },

  async getChatHistory(sessionId) {
    try {
      const response = await apiClient.get(`/chat/history/${sessionId}`);
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch chat history');
    }
  }
};
```

### Chat Component Example

```jsx
// components/Chat.jsx
import { useState, useEffect } from 'react';
import { chatService } from '../services/chat';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatService.sendMessage(input, sessionId);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message
      }]);
      
      if (!sessionId) {
        setSessionId(response.session_id);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Erro ao enviar mensagem. Tente novamente.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'Você' : 'Ali'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      
      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite sua mensagem..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
    </div>
  );
}
```

## 📄 Document Management

### Document Service

```javascript
// services/documents.js
import apiClient from '../lib/api';

export const documentService = {
  async uploadDocument(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    Object.keys(metadata).forEach(key => {
      formData.append(key, metadata[key]);
    });

    try {
      const response = await apiClient.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      throw new Error('Failed to upload document');
    }
  },

  async getDocuments() {
    try {
      const response = await apiClient.get('/documents');
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch documents');
    }
  },

  async deleteDocument(documentId) {
    try {
      await apiClient.delete(`/documents/${documentId}`);
      return true;
    } catch (error) {
      throw new Error('Failed to delete document');
    }
  }
};
```

## 🔧 Environment Configuration

### Next.js (.env.local)

```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development

# Staging  
NEXT_PUBLIC_API_URL=https://ali-api-staging-[hash]-uc.a.run.app
NEXT_PUBLIC_ENV=staging

# Production
NEXT_PUBLIC_API_URL=https://ali-api-production-[hash]-uc.a.run.app
NEXT_PUBLIC_ENV=production
```

### Vercel Deployment

Configure as environment variables no dashboard do Vercel:

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_ENV`

## 🎯 Testing Integration

### API Health Check

```javascript
// utils/healthCheck.js
import apiClient from '../lib/api';

export async function checkApiHealth() {
  try {
    const response = await apiClient.get('/health');
    return {
      healthy: response.data.status === 'healthy',
      details: response.data
    };
  } catch (error) {
    return {
      healthy: false,
      error: error.message
    };
  }
}
```

### Integration Test

```javascript
// __tests__/api-integration.test.js
import { authService } from '../services/auth';
import { chatService } from '../services/chat';

describe('API Integration', () => {
  test('should authenticate user', async () => {
    const result = await authService.login('test@example.com', 'password');
    expect(result.success).toBe(true);
  });

  test('should send chat message', async () => {
    const response = await chatService.sendMessage('Hello');
    expect(response.message).toBeDefined();
  });
});
```

## 🚨 Error Handling

### Global Error Handler

```javascript
// utils/errorHandler.js
export function handleApiError(error) {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 401:
        return 'Sessão expirada. Faça login novamente.';
      case 403:
        return 'Acesso negado.';
      case 422:
        return data.message || 'Dados inválidos.';
      case 500:
        return 'Erro interno do servidor. Tente novamente.';
      default:
        return data.message || 'Algo deu errado.';
    }
  } else if (error.request) {
    // Network error
    return 'Erro de conexão. Verifique sua internet.';
  } else {
    // Other error
    return error.message || 'Erro desconhecido.';
  }
}
```

## 📱 Usage Examples

### Complete Login Page

```jsx
// pages/login.jsx
import { useState } from 'react';
import { useRouter } from 'next/router';
import { authService } from '../services/auth';
import { handleApiError } from '../utils/errorHandler';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await authService.login(email, password);
      
      if (result.success) {
        router.push('/dashboard');
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  );
}
```

Esta configuração garante uma integração robusta e segura entre o frontend e a API Ali.