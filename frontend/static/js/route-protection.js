// frontend/static/js/route-protection.js
/**
 * Protección de rutas - Muestra pantalla de "contenido no disponible" si no hay autenticación
 */

// Rutas que requieren autenticación
const PROTECTED_ROUTES = ['/chat', '/history'];

// Rutas que redirigen a /chat si ya estás autenticado
const AUTH_ROUTES = ['/login', '/register'];

/**
 * Verifica si el usuario está autenticado
 */
function isAuthenticated() {
    const token = localStorage.getItem('jwt_token');
    const user = localStorage.getItem('user_data');
    return !!(token && user);
}

/**
 * Verifica la ruta actual y aplica protección
 */
function checkRouteProtection() {
    const currentPath = window.location.pathname;
    
    // Si es una ruta protegida y no está autenticado, mostrar pantalla de no disponible
    if (PROTECTED_ROUTES.some(route => currentPath.startsWith(route))) {
        if (!isAuthenticated()) {
            console.log('Ruta protegida sin autenticación, mostrando pantalla de no disponible');
            // Redirigir a la pantalla de no autorizado
            if (currentPath !== '/unauthorized') {
                window.location.href = '/unauthorized';
            }
            return false;
        }
    }
    
    // Si es una ruta de auth y ya está autenticado, redirigir a chat
    if (AUTH_ROUTES.includes(currentPath)) {
        if (isAuthenticated()) {
            console.log('Ya autenticado, redirigiendo a chat');
            window.location.href = '/chat';
            return false;
        }
    }
    
    // Si está en /unauthorized pero está autenticado, redirigir a chat
    if (currentPath === '/unauthorized' && isAuthenticated()) {
        window.location.href = '/chat';
        return false;
    }
    
    return true;
}

/**
 * Inicializa la protección de rutas
 */
function initRouteProtection() {
    // Verificar al cargar la página
    checkRouteProtection();
    
    // Escuchar cambios de hash (SPA navigation)
    window.addEventListener('hashchange', () => {
        checkRouteProtection();
    });
    
    // Interceptar navegación programática
    const originalPushState = history.pushState;
    history.pushState = function(...args) {
        originalPushState.apply(history, args);
        setTimeout(checkRouteProtection, 0);
    };
    
    const originalReplaceState = history.replaceState;
    history.replaceState = function(...args) {
        originalReplaceState.apply(history, args);
        setTimeout(checkRouteProtection, 0);
    };
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRouteProtection);
} else {
    initRouteProtection();
}

// Exportar para uso en otros scripts
if (typeof window !== 'undefined') {
    window.RouteProtection = {
        isAuthenticated,
        checkRouteProtection,
        initRouteProtection
    };
}

