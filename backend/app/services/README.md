# 🔧 ReadBuddy Backend Services

The Services layer is the core business logic component of the ReadBuddy backend application. It provides specialized services for AI-powered text processing, OCR, text-to-speech, language detection, and authentication. These services act as the bridge between the API endpoints and external AI/cloud services.

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   AI/ML     │ │   Cloud     │ │   Authentication    │ │
│  │  Services   │ │  Services   │ │     Services        │ │
│  │             │ │             │ │                     │ │
│  │ • GPT       │ │ • OCR       │ │ • Auth0             │ │
│  │ • Language  │ │ • TTS       │ │ • JWT               │ │
│  │ • Text      │ │ • Azure     │ │ • Session           │ │
│  │ • Analysis  │ │ • KeyVault  │ │ • Permissions       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                Interface Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Abstract  │ │   Factory   │ │     Utilities       │ │
│  │   Classes   │ │  Patterns   │ │                     │ │
│  │             │ │             │ │ • Config Manager    │ │
│  │ • BaseAI    │ │ • Service   │ │ • Error Handler     │ │
│  │ • BaseCloud │ │ • Factory   │ │ • Retry Logic       │ │
│  │ • BaseAuth  │ │ • Builder   │ │ • Rate Limiter      │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   OpenAI    │ │   Azure     │ │      Auth0          │ │
│  │             │ │             │ │                     │ │
│  │ • GPT-4     │ │ • Cognitive │ │ • OIDC              │ │
│  │ • Whisper   │ │ • Speech    │ │ • JWT               │ │
│  │ • Embeddings│ │ • KeyVault  │ │ • User Management   │ │
│  │ • Moderation│ │ • Document  │ │ • Permissions       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📁 Service Structure

### 🤖 AI & Language Services
- **`gpt_interface.py`**: OpenAI GPT integration for text processing and generation
- **`language_interface.py`**: Language detection and text analysis services

### 🔍 Document Processing Services
- **`ocr_interface.py`**: Optical Character Recognition (OCR) processing
- **`tts_interface.py`**: Text-to-Speech (TTS) synthesis and audio generation

### 🔐 Authentication Services
- **`auth/`**: Authentication and authorization services
  - User authentication and session management
  - JWT token handling and validation
  - Permission and role-based access control

### ☁️ Cloud Services
- **`azure/`**: Azure cloud services integration
  - Azure Cognitive Services
  - Azure Speech Services
  - Azure Document Intelligence
