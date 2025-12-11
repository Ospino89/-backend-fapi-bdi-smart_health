/**
 * SmartHealth - Funciones de Utilidad
 */

// ============ Gestión de LocalStorage ============
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error guardando en localStorage:', error);
            return false;
        }
    },

    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error leyendo de localStorage:', error);
            return null;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error eliminando de localStorage:', error);
            return false;
        }
    },

    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error limpiando localStorage:', error);
            return false;
        }
    }
};

// ============ Gestión de Tokens JWT ============
const Auth = {
    setToken(token) {
        Storage.set('jwt_token', token);
    },

    getToken() {
        return Storage.get('jwt_token');
    },

    setUser(user) {
        Storage.set('user_data', user);
    },

    getUser() {
        return Storage.get('user_data');
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    logout() {
        Storage.remove('jwt_token');
        Storage.remove('user_data');
        window.location.href = '/login';
    }
};

// ============ Llamadas a API ============
const API = {
    baseURL: window.location.origin, // Se ajusta automáticamente al servidor actual

    async request(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Agregar token si existe
        const token = Auth.getToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            // Intentar parsear JSON
            let data;
            try {
                data = await response.json();
            } catch (e) {
                // Si no es JSON, leer como texto
                const text = await response.text();
                throw new Error(text || `Error ${response.status}: ${response.statusText}`);
            }

            if (!response.ok) {
                // Manejar errores del backend
                const errorMsg = data.detail || data.message || data.error?.message || `Error ${response.status}`;
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            console.error('Error en API request:', error);
            throw error;
        }
    },

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    async put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    },

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// ============ Validación de Formularios ============
const Validator = {
    email(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },

    password(password, minLength = 8) {
        return password.length >= minLength;
    },

    required(value) {
        return value !== null && value !== undefined && value.trim() !== '';
    },

    match(value1, value2) {
        return value1 === value2;
    }
};

// ============ Utilidades de UI ============
const UI = {
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            element.classList.add('error-message');
        }
    },

    hideError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
            element.textContent = '';
        }
    },

    showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            element.classList.add('success-message');
        }
    },

    setLoading(buttonElement, isLoading) {
        if (!buttonElement) return;

        const textSpan = buttonElement.querySelector('.btn-text');
        const loaderSpan = buttonElement.querySelector('.btn-loader');

        if (isLoading) {
            buttonElement.disabled = true;
            if (textSpan) textSpan.style.display = 'none';
            if (loaderSpan) loaderSpan.style.display = 'block';
        } else {
            buttonElement.disabled = false;
            if (textSpan) textSpan.style.display = 'inline';
            if (loaderSpan) loaderSpan.style.display = 'none';
        }
    },

    disableForm(formElement) {
        const inputs = formElement.querySelectorAll('input, button, select, textarea');
        inputs.forEach(input => input.disabled = true);
        formElement.classList.add('form-loading');
    },

    enableForm(formElement) {
        const inputs = formElement.querySelectorAll('input, button, select, textarea');
        inputs.forEach(input => input.disabled = false);
        formElement.classList.remove('form-loading');
    }
};

// ============ Formateo de Fechas ============
const DateFormatter = {
    toISO(date = new Date()) {
        return date.toISOString();
    },

    toReadable(dateString) {
        const date = new Date(dateString);
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('es-ES', options);
    },

    toTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    timeAgo(date) {
        const now = new Date();
        const past = new Date(date);
        const diffMs = now - past;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Hace un momento';
        if (diffMins < 60) return `Hace ${diffMins} min`;
        if (diffHours < 24) return `Hace ${diffHours} h`;
        if (diffDays < 7) return `Hace ${diffDays} días`;
        
        // Formato de fecha para más de una semana
        const day = past.getDate();
        const month = past.getMonth() + 1;
        const year = past.getFullYear();
        return `${day}/${month}/${year}`;
    },

    getRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Ahora';
        if (diffMins < 60) return `Hace ${diffMins} min`;
        if (diffHours < 24) return `Hace ${diffHours} h`;
        if (diffDays < 7) return `Hace ${diffDays} días`;
        return this.toReadable(dateString);
    }
};

// ============ Generación de UUID ============
const Utils = {
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },

    getInitials(name) {
        if (!name) return 'U';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return parts[0][0].toUpperCase();
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// ============ Exportar para uso global ============
window.Storage = Storage;
window.Auth = Auth;
window.API = API;
window.Validator = Validator;
window.UI = UI;
window.DateFormatter = DateFormatter;
window.Utils = Utils;
