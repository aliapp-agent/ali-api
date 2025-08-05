# 🔥 Firebase Setup Guide

Este guia detalha como configurar Firebase para a Ali API.

## 1. Criar Projeto Firebase

1. Acesse o [Firebase Console](https://console.firebase.google.com/)
2. Clique em "Criar projeto" ou "Add project"
3. Nome do projeto: `ali-api-project` (ou nome de sua escolha)
4. Habilite Google Analytics (opcional)
5. Aguarde a criação do projeto

## 2. Habilitar Serviços Firebase

### 2.1 Firebase Authentication
1. No console Firebase, vá para **Authentication**
2. Clique em "Get started"
3. Na aba **Sign-in method**, habilite:
   - Email/Password
   - Google (opcional)
   - Anonymous (opcional para testes)

### 2.2 Cloud Firestore
1. Vá para **Firestore Database**
2. Clique em "Create database"
3. Escolha "Start in test mode" (por enquanto)
4. Selecione localização: `us-central1`

### 2.3 Cloud Storage
1. Vá para **Storage**
2. Clique em "Get started"
3. Escolha "Start in test mode"
4. Selecione localização: `us-central1`

### 2.4 Cloud Logging
1. No [Google Cloud Console](https://console.cloud.google.com/)
2. Navegue para **Logging** > **Logs Explorer**
3. O serviço é habilitado automaticamente

## 3. Configurar Credenciais

### 3.1 Service Account Key
1. No Firebase Console, vá para **Project Settings** (ícone de engrenagem)
2. Aba **Service accounts**
3. Clique em "Generate new private key"
4. Salve o arquivo como `firebase-credentials.json` na raiz do projeto

### 3.2 Configurar Variáveis de Ambiente
Copie `.env.firebase` para `.env` e atualize:

```bash
FIREBASE_PROJECT_ID=seu-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=seu-project-id.appspot.com
FIREBASE_REGION=us-central1
```

## 4. Estrutura do Firestore


### Collections principais:
```
/users/{userId}
  - email: string
  - role: string
  - created_at: timestamp
  - profile: object

/chat_sessions/{sessionId}
  - user_id: string
  - name: string
  - created_at: timestamp
  - message_count: number

/chat_sessions/{sessionId}/messages/{messageId}
  - role: "user" | "assistant"
  - content: string
  - timestamp: timestamp
  - metadata: object

/documents/{docId}
  - title: string
  - user_id: string
  - category: string
  - status: string
  - gcs_url: string
  - created_at: timestamp

/user_invitations/{inviteId}
  - email: string
  - role: string
  - status: "pending" | "accepted" | "expired"
  - expires_at: timestamp
  - token: string
```

## 5. Security Rules

### Firestore Security Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Chat sessions belong to users
    match /chat_sessions/{sessionId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.user_id;
      
      match /messages/{messageId} {
        allow read, write: if request.auth != null 
          && request.auth.uid == get(/databases/$(database)/documents/chat_sessions/$(sessionId)).data.user_id;
      }
    }
    
    // Documents access based on permissions
    match /documents/{docId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null 
        && request.auth.uid == resource.data.user_id;
    }
  }
}
```

### Storage Security Rules:
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /documents/{userId}/{fileName} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 6. Instalar Firebase CLI

```bash
npm install -g firebase-tools
firebase login
firebase projects:list
firebase use ali-api-project
```

## 7. Testar Configuração

Execute o seguinte para verificar se tudo está funcionando:

```python
from app.core.firebase import get_firestore, get_firebase_auth

# Teste Firestore
db = get_firestore()
test_doc = db.collection('test').document('test').set({'test': True})

# Teste Auth
auth = get_firebase_auth()
users = auth.list_users()
print(f"Users found: {len(users.users)}")
```

## 8. Próximos Passos

1. ✅ Configurar projeto Firebase
2. ✅ Habilitar serviços
3. ✅ Configurar credenciais
4. 🔄 Implementar repositórios Firestore
5. 🔄 Migrar dados PostgreSQL → Firestore
6. 🔄 Configurar Qdrant
7. 🔄 Deploy e testes

## Troubleshooting

### Erro: "insufficient permissions"
- Verifique se o service account tem as permissões necessárias
- No IAM, adicione roles: Firebase Admin, Firestore User, Storage Admin

### Erro: "project not found"
- Verifique se FIREBASE_PROJECT_ID está correto
- Execute `firebase projects:list` para listar projetos

### Erro: "credentials not found"
- Verifique se o caminho do arquivo firebase-credentials.json está correto
- Certifique-se de que o arquivo foi baixado corretamente