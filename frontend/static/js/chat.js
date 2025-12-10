/**
 * SmartHealth - Lógica del Chat (Actualizada)
 */

// Estado global del chat
const ChatState = {
    currentSessionId: null,
    sequenceChatId: 0,
    messages: [],
    websocket: null,
    isConnected: false
};

// ============ Inicialización del Chat ============
function initChat() {
    // Verificar autenticación
    if (!Auth.isAuthenticated()) {
        // Redirigir a pantalla de no autorizado
        window.location.href = '/unauthorized';
        return;
    }

    // Cargar información del usuario
    loadUserInfo();

    // Inicializar elementos del DOM
    initChatElements();

    // Inicializar modal de perfil
    initProfileModal();

    // Inicializar WebSocket (cuando esté disponible)
    // initWebSocket();

    // Cargar historial
    loadChatHistory();

    // Crear nueva sesión
    createNewSession();
}

// ============ Cargar Información del Usuario ============
function loadUserInfo() {
    const user = Auth.getUser();
    if (!user) return;

    const userAvatarInitials = document.getElementById('userAvatarInitials');
    const profileModalInitials = document.getElementById('profileModalInitials');
    const profileModalName = document.getElementById('profileModalName');
    const profileModalEmail = document.getElementById('profileModalEmail');

    const initials = Utils.getInitials(user.full_name);

    if (userAvatarInitials) userAvatarInitials.textContent = initials;
    if (profileModalInitials) profileModalInitials.textContent = initials;
    if (profileModalName) profileModalName.textContent = user.full_name || 'Usuario';
    if (profileModalEmail) profileModalEmail.textContent = user.email || 'usuario@ejemplo.com';
}

// ============ Inicializar Modal de Perfil ============
function initProfileModal() {
    const userAvatarBtn = document.getElementById('userAvatarBtn');
    const profileModalOverlay = document.getElementById('profileModalOverlay');
    const closeProfileModal = document.getElementById('closeProfileModal');
    const logoutBtnModal = document.getElementById('logoutBtnModal');

    // Validar que todos los elementos existan
    if (!userAvatarBtn || !profileModalOverlay || !closeProfileModal || !logoutBtnModal) {
        console.error('Error: No se encontraron todos los elementos del modal de perfil');
        return;
    }

    // Abrir modal al hacer click en el avatar
    userAvatarBtn.addEventListener('click', () => {
        openProfileModal();
    });

    // Cerrar modal con el botón X
    closeProfileModal.addEventListener('click', () => {
        closeProfileModalHandler();
    });

    // Cerrar modal al hacer click fuera de él
    profileModalOverlay.addEventListener('click', (e) => {
        if (e.target === profileModalOverlay) {
            closeProfileModalHandler();
        }
    });

    // Cerrar modal con tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && profileModalOverlay.classList.contains('active')) {
            closeProfileModalHandler();
        }
    });

    // Logout desde el modal
    logoutBtnModal.addEventListener('click', () => {
        showConfirmModal(
            'Cerrar Sesión',
            '¿Estás seguro de que deseas cerrar sesión?',
            () => {
                Auth.logout();
            }
        );
    });
}

// Abrir modal de perfil
function openProfileModal() {
    const profileModalOverlay = document.getElementById('profileModalOverlay');
    profileModalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevenir scroll del body
}

// Cerrar modal de perfil
function closeProfileModalHandler() {
    const profileModalOverlay = document.getElementById('profileModalOverlay');
    profileModalOverlay.classList.remove('active');
    document.body.style.overflow = ''; // Restaurar scroll
}

// ============ Inicializar Elementos del Chat ============
function initChatElements() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const documentNumber = document.getElementById('documentNumber');
    const newChatBtn = document.getElementById('newChatBtn');

    // Auto-resize del textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        
        // Habilitar/deshabilitar botón de envío
        updateSendButton();
    });

    // Enviar con Enter (Shift+Enter para nueva línea)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                sendMessage();
            }
        }
    });

    // Validar número de documento
    documentNumber.addEventListener('input', updateSendButton);

    // Evento de envío
    sendBtn.addEventListener('click', sendMessage);

    // Nueva consulta
    newChatBtn.addEventListener('click', () => {
        createNewSession();
        loadChatHistory(); // Recargar historial después de crear nueva sesión
    });
}

// ============ Actualizar Estado del Botón de Envío ============
function updateSendButton() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const documentNumber = document.getElementById('documentNumber');

    const hasMessage = chatInput.value.trim().length > 0;
    const hasDocument = documentNumber.value.trim().length > 0;

    sendBtn.disabled = !(hasMessage && hasDocument);
}

// ============ Crear Nueva Sesión ============
function createNewSession() {
    ChatState.currentSessionId = Utils.generateUUID();
    ChatState.sequenceChatId = 0;
    ChatState.messages = [];

    // Limpiar el área de mensajes
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <svg width="60" height="60" viewBox="0 0 50 50" fill="none">
                    <path d="M25 5C14.5 5 6 13.5 6 24C6 34.5 14.5 43 25 43C35.5 43 44 34.5 44 24C44 13.5 35.5 5 25 5Z" stroke="#4F46E5" stroke-width="2"/>
                    <path d="M25 15V33M17 24H33" stroke="#4F46E5" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <h2>¡Nueva Consulta!</h2>
            <p>Proporciona la información del paciente y tu pregunta.</p>
        </div>
    `;

    // Limpiar inputs
    document.getElementById('chatInput').value = '';
    document.getElementById('documentNumber').value = '';
    document.getElementById('documentType').value = '1';

    console.log('Nueva sesión creada:', ChatState.currentSessionId);
}

// ============ Enviar Mensaje ============
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const documentType = document.getElementById('documentType');
    const documentNumber = document.getElementById('documentNumber');
    const sendBtn = document.getElementById('sendBtn');

    const question = chatInput.value.trim();
    const docTypeId = parseInt(documentType.value);
    const docNumber = documentNumber.value.trim();

    if (!question || !docNumber) return;

    // Incrementar secuencia
    ChatState.sequenceChatId++;

    // Preparar el mensaje
    const user = Auth.getUser();
    if (!user || !user.user_id) {
        addMessageToChat('assistant', '❌ Error: No estás autenticado. Por favor, inicia sesión.');
        return;
    }
    
    const messageData = {
        user_id: String(user.user_id), // El backend espera string
        session_id: ChatState.currentSessionId,
        document_type_id: docTypeId,
        document_number: docNumber,
        question: question
    };

    // Agregar mensaje del usuario al chat
    addMessageToChat('user', question, {
        documentType: getDocumentTypeName(docTypeId),
        documentNumber: docNumber
    });

    // Limpiar input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Mostrar indicador de escritura
    showTypingIndicator();

    try {
        // Llamada real al backend
        const response = await API.post('/query/', messageData);

        // Ocultar indicador de escritura
        hideTypingIndicator();

        // Agregar respuesta del asistente
        addAssistantResponse(response);

        // Guardar en historial
        saveToHistory(question, response);
        
        // Habilitar botón de envío
        updateSendButton();

    } catch (error) {
        hideTypingIndicator();
        let errorMsg = 'Error desconocido al procesar tu consulta';
        
        if (error.message) {
            errorMsg = error.message;
        } else if (typeof error === 'string') {
            errorMsg = error;
        }
        
        addMessageToChat('assistant', `❌ Error: ${errorMsg}`);
        console.error('Error enviando mensaje:', error);
        console.error('Detalles del error:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        
        // Habilitar botón de envío para permitir reintentar
        updateSendButton();
    }
}

// ============ Agregar Mensaje al Chat ============
function addMessageToChat(role, content, metadata = null) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Remover mensaje de bienvenida si existe
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? Utils.getInitials(Auth.getUser().full_name) : 'SA';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;

    // Si es mensaje del usuario y tiene metadata, agregar info del paciente
    if (role === 'user' && metadata) {
        const patientInfo = document.createElement('div');
        patientInfo.className = 'patient-info-display';
        patientInfo.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"/>
            </svg>
            <span>${metadata.documentType}: ${metadata.documentNumber}</span>
        `;
        contentDiv.appendChild(patientInfo);
    }

    const timeSpan = document.createElement('div');
    timeSpan.className = 'message-time';
    timeSpan.textContent = DateFormatter.toTime(new Date().toISOString());

    contentDiv.appendChild(bubble);
    contentDiv.appendChild(timeSpan);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);

    // Scroll al final
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Guardar mensaje en el estado
    ChatState.messages.push({
        role,
        content,
        timestamp: new Date().toISOString(),
        metadata
    });
}

// ============ Agregar Respuesta del Asistente ============
function addAssistantResponse(response) {
    console.log('Respuesta del servidor:', response); // Debug
    
    if (!response) {
        console.error('Respuesta vacía del servidor');
        addMessageToChat('assistant', '❌ Error: No se recibió respuesta del servidor');
        return;
    }
    
    if (response.status === 'success') {
        const answerText = response.answer?.text || response.answer || 'Sin respuesta';
        addMessageToChat('assistant', answerText);
    } else if (response.status === 'error') {
        const errorMsg = response.error?.message || response.error?.details || response.detail || 'Error desconocido';
        addMessageToChat('assistant', `❌ Error: ${errorMsg}`);
    } else {
        // Respuesta inesperada - intentar extraer texto de cualquier forma
        console.warn('Formato de respuesta inesperado:', response);
        if (response.answer) {
            addMessageToChat('assistant', response.answer.text || response.answer);
        } else if (response.message) {
            addMessageToChat('assistant', response.message);
        } else {
            addMessageToChat('assistant', 'Error: Formato de respuesta no reconocido');
        }
    }
}

// ============ Modal de Confirmación ============
let confirmModalCallback = null;

function showConfirmModal(title, message, onConfirm) {
    const overlay = document.getElementById('confirmModalOverlay');
    const titleEl = document.getElementById('confirmModalTitle');
    const messageEl = document.getElementById('confirmModalMessage');
    const confirmBtn = document.getElementById('confirmModalConfirm');
    const cancelBtn = document.getElementById('confirmModalCancel');
    
    if (!overlay || !titleEl || !messageEl || !confirmBtn || !cancelBtn) {
        // Fallback a confirm nativo si el modal no existe
        if (confirm(message)) {
            onConfirm();
        }
        return;
    }
    
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    // Guardar callback
    confirmModalCallback = onConfirm;
    
    // Mostrar modal
    overlay.classList.add('active');
    
    // Limpiar listeners anteriores
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    // Event listeners
    newConfirmBtn.addEventListener('click', () => {
        if (confirmModalCallback) {
            confirmModalCallback();
        }
        hideConfirmModal();
    });
    
    newCancelBtn.addEventListener('click', () => {
        hideConfirmModal();
    });
    
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            hideConfirmModal();
        }
    });
    
    // Cerrar con Escape
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            hideConfirmModal();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

function hideConfirmModal() {
    const overlay = document.getElementById('confirmModalOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    confirmModalCallback = null;
}

// ============ Indicador de Escritura ============
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message assistant';
    typingDiv.innerHTML = `
        <div class="message-avatar">SA</div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// ============ Guardar en Historial ============
function saveToHistory(question, response) {
    // El historial ya se guarda automáticamente en el backend
    // Recargar el historial después de guardar
    loadChatHistory();
}

// ============ Cargar Historial del Chat ============
async function loadChatHistory() {
    const historyList = document.querySelector('.chat-history-list');
    if (!historyList) return;

    try {
        // Mostrar loading
        historyList.innerHTML = '<div class="empty-history">Cargando historial...</div>';

        // Obtener historial del backend
        const history = await API.get('/history/');

        if (!history || history.length === 0) {
            historyList.innerHTML = '<div class="empty-history">No hay conversaciones recientes</div>';
            return;
        }

        // Agrupar por sesión
        const sessions = {};
        history.forEach(item => {
            const sessionId = item.session_id;
            if (!sessions[sessionId]) {
                sessions[sessionId] = {
                    session_id: sessionId,
                    items: [],
                    latest_date: new Date(item.created_at)
                };
            }
            sessions[sessionId].items.push(item);
            const itemDate = new Date(item.created_at);
            if (itemDate > sessions[sessionId].latest_date) {
                sessions[sessionId].latest_date = itemDate;
            }
        });

        // Ordenar sesiones por fecha más reciente
        const sortedSessions = Object.values(sessions).sort((a, b) => 
            b.latest_date - a.latest_date
        );

        // Limpiar lista
        historyList.innerHTML = '';

        // Renderizar sesiones
        sortedSessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'chat-history-item';
            sessionItem.dataset.sessionId = session.session_id;
            
            // Obtener primera pregunta como título
            const firstQuestion = session.items[0].question;
            const title = firstQuestion.length > 50 
                ? firstQuestion.substring(0, 50) + '...' 
                : firstQuestion;
            
            const timeAgo = DateFormatter.getRelativeTime(session.latest_date);
            
            sessionItem.innerHTML = `
                <div class="chat-history-item-title">${title}</div>
                <div class="chat-history-item-time">${timeAgo}</div>
            `;
            
            // Click handler para cargar sesión
            sessionItem.addEventListener('click', () => {
                loadSession(session.session_id);
            });
            
            historyList.appendChild(sessionItem);
        });

    } catch (error) {
        console.error('Error cargando historial:', error);
        historyList.innerHTML = '<div class="empty-history">Error al cargar historial</div>';
    }
}

// ============ Cargar Sesión del Historial ============
async function loadSession(sessionId) {
    try {
        // Obtener mensajes de la sesión
        const sessionData = await API.get(`/history/session/${sessionId}`);
        
        if (!sessionData || sessionData.length === 0) {
            console.error('Sesión vacía');
            return;
        }

        // Actualizar sesión actual
        ChatState.currentSessionId = sessionId;
        ChatState.messages = [];
        
        // Limpiar mensajes del chat
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // Cargar mensajes de la sesión
        sessionData.forEach(item => {
            // Agregar pregunta del usuario
            const docTypeName = getDocumentTypeName(item.document_type_id);
            addMessageToChat('user', item.question, {
                documentType: docTypeName,
                documentNumber: item.document_number
            });
            
            // Agregar respuesta del asistente
            if (item.response && item.response.answer) {
                const answerText = item.response.answer.text || item.response.answer;
                addMessageToChat('assistant', answerText);
            }
        });
        
        // Actualizar estado de secuencia
        if (sessionData.length > 0) {
            ChatState.sequenceChatId = sessionData[sessionData.length - 1].sequence_chat_id;
        }
        
        // Marcar sesión activa en el historial
        document.querySelectorAll('.chat-history-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.sessionId === sessionId) {
                item.classList.add('active');
            }
        });
        
    } catch (error) {
        console.error('Error cargando sesión:', error);
        addMessageToChat('assistant', '❌ Error al cargar la sesión seleccionada');
    }
}

// ============ Utilidades ============
function getDocumentTypeName(typeId) {
    const types = {
        1: 'CC',
        2: 'TI',
        3: 'CE',
        4: 'PA'
    };
    return types[typeId] || 'CC';
}

// ============ Simulación de Respuesta (TEMPORAL) ============
// Esta función simula la respuesta del backend con RAG
// DEBE SER ELIMINADA cuando el backend esté implementado

async function simulateQueryResponse(messageData) {
    // Simular delay de procesamiento
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Respuesta simulada basada en el formato del proyecto
    return {
        status: "success",
        session_id: messageData.session_id,
        sequence_chat_id: ChatState.sequenceChatId,
        timestamp: new Date().toISOString(),
        patient_info: {
            patient_id: 123,
            full_name: "Juan Pérez García",
            document_type: getDocumentTypeName(messageData.document_type_id),
            document_number: messageData.document_number
        },
        answer: {
            text: `Basado en la información disponible para el paciente ${messageData.document_number}, puedo informarte que:\n\n` +
                  `El paciente ha tenido 2 citas médicas recientes:\n\n` +
                  `1. **15/11/2024** - Consulta de Cardiología\n` +
                  `   - Diagnóstico: Hipertensión arterial grado 2 (CIE-10: I10)\n` +
                  `   - Tratamiento prescrito: Losartán 50mg c/24h\n\n` +
                  `2. **20/10/2024** - Control General\n` +
                  `   - Diagnóstico secundario: Dislipidemia (CIE-10: E78.5)\n` +
                  `   - Indicaciones: Dieta baja en grasas, ejercicio moderado\n\n` +
                  `*Esta información es provisional hasta que se conecte con la base de datos real.*`,
            confidence: 0.94,
            model_used: "claude-sonnet-4.5"
        },
        sources: [
            {
                source_id: 1,
                type: "appointment",
                appointment_id: 458,
                date: "2024-11-15",
                relevance_score: 0.98
            }
        ],
        metadata: {
            total_records_analyzed: 15,
            query_time_ms: 342,
            sources_used: 3,
            context_tokens: 2456
        }
    };
}

// ============ WebSocket (Para implementación futura) ============
function initWebSocket() {
    // Esta función se implementará cuando el backend tenga WebSocket configurado
    /*
    const wsUrl = `ws://${window.location.host}/ws/chat`;
    ChatState.websocket = new WebSocket(wsUrl);

    ChatState.websocket.onopen = () => {
        console.log('WebSocket conectado');
        ChatState.isConnected = true;
    };

    ChatState.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ChatState.websocket.onerror = (error) => {
        console.error('Error en WebSocket:', error);
        ChatState.isConnected = false;
    };

    ChatState.websocket.onclose = () => {
        console.log('WebSocket desconectado');
        ChatState.isConnected = false;
    };
    */
}

// ============ Inicialización Automática ============
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    // Inicializar chat si estamos en la página del chat o en index.html
    if (path === '/chat' || path === '/public/index.html' || path.endsWith('index.html') || path === '/') {
        initChat();
    }
});
