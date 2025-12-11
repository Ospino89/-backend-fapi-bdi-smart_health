/**
 * SmartHealth - Lógica de Autenticación
 */

// ============ Login Form ============
function initLoginForm() {
    const form = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const submitButton = form.querySelector('button[type="submit"]');

    // Verificar si ya está autenticado
    if (Auth.isAuthenticated()) {
        window.location.href = '/chat';
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        UI.hideError('errorMessage');

        // Validar campos
        const email = emailInput.value.trim();
        const password = passwordInput.value;

        if (!Validator.email(email)) {
            UI.showError('errorMessage', 'Por favor ingresa un correo válido');
            return;
        }

        if (!Validator.required(password)) {
            UI.showError('errorMessage', 'Por favor ingresa tu contraseña');
            return;
        }

        // Mostrar loading
        UI.setLoading(submitButton, true);
        UI.disableForm(form);

        try {
            // Llamada real al backend
            const response = await API.post('/auth/login', {
                email: email,
                password: password
            });

            // Guardar token
            if (!response.access_token) {
                throw new Error('No se recibió el token de acceso');
            }
            
            Auth.setToken(response.access_token);
            
            // Obtener datos del usuario desde el token
            try {
                const tokenPayload = JSON.parse(atob(response.access_token.split('.')[1]));
                const userId = tokenPayload.sub || tokenPayload.user_id;
                
                // Intentar obtener datos completos del usuario (no crítico si falla)
                try {
                    const userResponse = await API.get('/user/me');
                    Auth.setUser({
                        user_id: userResponse.user_id,
                        email: userResponse.email,
                        full_name: `${userResponse.first_name || ''} ${userResponse.first_surname || ''}`.trim() || email.split('@')[0]
                    });
                } catch (e) {
                    console.warn('No se pudieron obtener datos completos del usuario, usando datos del token:', e);
                    // Si falla, usar datos del token
                    Auth.setUser({
                        user_id: userId,
                        email: email,
                        full_name: email.split('@')[0]
                    });
                }
            } catch (e) {
                console.warn('Error decodificando token, usando valores por defecto:', e);
                // Si no podemos decodificar el token, usar valores por defecto
                Auth.setUser({
                    user_id: 'user_' + Date.now(),
                    email: email,
                    full_name: email.split('@')[0]
                });
            }

            // Redirigir al chat
            window.location.href = '/chat';

        } catch (error) {
            UI.showError('errorMessage', error.message || 'Error al iniciar sesión. Verifica tus credenciales.');
        } finally {
            UI.setLoading(submitButton, false);
            UI.enableForm(form);
        }
    });

    // Auto-focus en el primer campo
    emailInput.focus();
}

// ============ Register Form ============
function initRegisterForm() {
    const form = document.getElementById('registerForm');
    const firstNameInput = document.getElementById('firstName');
    const middleNameInput = document.getElementById('middleName');
    const firstSurnameInput = document.getElementById('firstSurname');
    const secondSurnameInput = document.getElementById('secondSurname');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const termsCheckbox = document.getElementById('terms');
    const submitButton = form.querySelector('button[type="submit"]');

    // Verificar si ya está autenticado
    if (Auth.isAuthenticated()) {
        window.location.href = '/chat';
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        UI.hideError('errorMessage');
        UI.hideError('successMessage');

        // Validar campos
        const firstName = firstNameInput.value.trim();
        const middleName = middleNameInput.value.trim();
        const firstSurname = firstSurnameInput.value.trim();
        const secondSurname = secondSurnameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Validaciones
        if (!Validator.required(firstName) || firstName.length < 1) {
            UI.showError('errorMessage', 'El primer nombre es requerido');
            return;
        }
        
        if (!Validator.required(firstSurname) || firstSurname.length < 1) {
            UI.showError('errorMessage', 'El primer apellido es requerido');
            return;
        }

        if (!Validator.email(email)) {
            UI.showError('errorMessage', 'Por favor ingresa un correo válido');
            return;
        }

        if (!Validator.password(password, 8)) {
            UI.showError('errorMessage', 'La contraseña debe tener al menos 8 caracteres');
            return;
        }

        if (!Validator.match(password, confirmPassword)) {
            UI.showError('errorMessage', 'Las contraseñas no coinciden');
            return;
        }

        if (!termsCheckbox.checked) {
            UI.showError('errorMessage', 'Debes aceptar los términos y condiciones');
            return;
        }

        // Mostrar loading
        UI.setLoading(submitButton, true);
        UI.disableForm(form);

        try {
            // Llamada real al backend
            const response = await API.post('/auth/register', {
                email: email,
                first_name: firstName,
                middle_name: middleName || null,
                first_surname: firstSurname,
                second_surname: secondSurname || null,
                password: password
            });

            // Mostrar mensaje de éxito
            UI.showSuccess('successMessage', '¡Cuenta creada exitosamente! Redirigiendo al login...');

            // Redirigir al login después de 2 segundos
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);

        } catch (error) {
            UI.showError('errorMessage', error.message || 'Error al crear la cuenta. Intenta nuevamente.');
        } finally {
            UI.setLoading(submitButton, false);
            UI.enableForm(form);
        }
    });

    // Validación en tiempo real de contraseñas
    confirmPasswordInput.addEventListener('input', () => {
        if (confirmPasswordInput.value && !Validator.match(passwordInput.value, confirmPasswordInput.value)) {
            confirmPasswordInput.classList.add('error');
        } else {
            confirmPasswordInput.classList.remove('error');
        }
    });

    // Auto-focus en el primer campo
    firstNameInput.focus();
}

// ============ Funciones de Simulación (TEMPORAL) ============
// Estas funciones simulan las respuestas del backend
// DEBEN SER ELIMINADAS cuando el backend esté implementado

async function simulateLogin(email, password) {
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simular validación
    if (email === 'test@smarthealth.com' && password === 'password123') {
        // Simular respuesta exitosa
        const mockToken = 'mock_jwt_token_' + Date.now();
        const mockUser = {
            user_id: 'user_001',
            full_name: 'Usuario de Prueba',
            email: email
        };

        Auth.setToken(mockToken);
        Auth.setUser(mockUser);
        return;
    }

    // Simular error
    throw new Error('Credenciales inválidas');
}

async function simulateRegister(fullName, email, password) {
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Simular validación (email ya existe)
    if (email === 'existing@smarthealth.com') {
        throw new Error('Este correo ya está registrado');
    }

    // Simular éxito
    console.log('Usuario registrado:', { fullName, email });
}

// ============ Inicialización Automática ============
// Detectar qué página estamos y inicializar el formulario correspondiente
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path === '/login') {
        initLoginForm();
    } else if (path === '/register') {
        initRegisterForm();
    }
});
