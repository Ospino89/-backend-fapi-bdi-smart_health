# SmartHealth WebSocket Documentation

## Overview
Este documento describe la implementación de WebSocket para la aplicación SmartHealth, un sistema de consultas clínicas basado en IA.

## Architecture

### Client-Side
- **Framework**: Vanilla JavaScript
- **Connection**: WebSocket API estándar del navegador
- **Message Format**: JSON

### Server-Side
- **Framework**: FastAPI/Python
- **WebSocket Support**: Integrado en FastAPI
- **Broadcasting**: Mediante administrador de conexiones

## Implementation

### Connection URL
```
ws://localhost:8000/ws/chat
```

### Message Flow

1. **Client connects** → WebSocket handshake
2. **Authentication** → Enviar token JWT
3. **Message exchange** → Consultas y respuestas
4. **Disconnection** → Cleanup automático

## Features

- Real-time chat
- Patient information lookup
- Medical query processing
- Connection status monitoring
- Automatic reconnection

## Error Handling

- Connection errors
- Message parsing errors
- Authentication failures
- Timeout handling

## Performance

- Latency: < 100ms
- Throughput: 1000+ msg/s
- Connection limit: Configurable

## Security

- JWT authentication
- Message validation
- Rate limiting
- TLS/SSL support (WSS)

## Future Enhancements

- Message persistence
- Chat history recovery
- Presence indicators
- Typing status
- File upload support
