/**
 * SmartHealth - Test Suite
 */

const TestSuite = {
    results: [],

    test(name, fn) {
        try {
            fn();
            this.results.push({
                name,
                status: 'pass',
                message: 'Prueba pasada'
            });
        } catch (error) {
            this.results.push({
                name,
                status: 'fail',
                message: error.message
            });
        }
    },

    assert(condition, message) {
        if (!condition) {
            throw new Error(message || 'Assertion failed');
        }
    },

    assertEqual(actual, expected, message) {
        if (actual !== expected) {
            throw new Error(message || `Expected ${expected}, but got ${actual}`);
        }
    },

    render() {
        const resultsDiv = document.getElementById('test-results');
        if (!resultsDiv) return;

        resultsDiv.innerHTML = this.results.map(result => `
            <div class="test-result ${result.status}">
                <h3>${result.name}</h3>
                <p>${result.message}</p>
            </div>
        `).join('');
    }
};

// ============ Pruebas de Utilidades ============
document.addEventListener('DOMContentLoaded', () => {
    // Test de UUID
    TestSuite.test('Generación de UUID', () => {
        const uuid = Utils.generateUUID();
        TestSuite.assert(uuid && typeof uuid === 'string', 'UUID debe ser un string');
        TestSuite.assert(uuid.length === 36, 'UUID debe tener 36 caracteres');
    });

    // Test de Iniciales
    TestSuite.test('Generación de iniciales', () => {
        const initials = Utils.getInitials('Juan Pérez García');
        TestSuite.assertEqual(initials, 'JP', 'Iniciales incorrectas');
    });

    // Test de Validación de Email
    TestSuite.test('Validación de email válido', () => {
        TestSuite.assert(Validator.email('test@example.com'), 'Email válido no fue reconocido');
    });

    TestSuite.test('Validación de email inválido', () => {
        TestSuite.assert(!Validator.email('invalid-email'), 'Email inválido fue aceptado');
    });

    // Test de Validación de Contraseña
    TestSuite.test('Validación de contraseña fuerte', () => {
        TestSuite.assert(Validator.password('SecurePass123', 8), 'Contraseña fuerte no fue reconocida');
    });

    TestSuite.test('Validación de contraseña débil', () => {
        TestSuite.assert(!Validator.password('weak', 8), 'Contraseña débil fue aceptada');
    });

    // Test de Storage
    TestSuite.test('Almacenamiento en localStorage', () => {
        const testData = { key: 'testValue' };
        Storage.set('test_key', testData);
        const retrieved = Storage.get('test_key');
        TestSuite.assert(retrieved && retrieved.key === 'testValue', 'Storage falló');
        Storage.remove('test_key');
    });

    // Test de DateFormatter
    TestSuite.test('Formateo de fecha ISO', () => {
        const date = new Date('2024-01-15T10:30:00Z');
        const iso = DateFormatter.toISO(date);
        TestSuite.assert(iso.includes('2024-01-15'), 'Formato ISO incorrecto');
    });

    // Renderizar resultados
    TestSuite.render();
});
