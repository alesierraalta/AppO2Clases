/**
 * O2 Fitness Club - Sistema de Gestión
 * Common JavaScript functions
 */

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar la UI del theme toggle basado en el tema actual
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    updateThemeUI(currentTheme);
    
    // Theme toggle click handler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Log para depuración
            console.log('Cambiando tema de:', currentTheme, 'a:', newTheme);
            
            // Save preference
            localStorage.setItem('theme', newTheme);
            
            // Apply new theme
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            
            // Update UI
            updateThemeUI(newTheme);
            
            // Close dropdown if open
            const dropdown = document.querySelector('.config-submenu .dropdown-menu');
            if (dropdown && dropdown.classList.contains('show')) {
                dropdown.classList.remove('show');
            }
        });
        
        // Marcar como manejado para evitar duplicar event handlers
        themeToggle._hasThemeHandler = true;
    } else {
        console.log('Elemento themeToggle no encontrado en el DOM');
    }
});

// Helper to update theme toggle UI
function updateThemeUI(theme) {
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    
    if (!themeIcon || !themeText) {
        console.log('Elementos de UI de tema no encontrados:', {themeIcon, themeText});
        return;
    }
    
    if (theme === 'dark') {
        themeIcon.className = 'fas fa-sun';
        themeText.textContent = 'Cambiar a modo claro';
    } else {
        themeIcon.className = 'fas fa-moon';
        themeText.textContent = 'Cambiar a modo oscuro';
    }
}

// Global animation and interaction behaviors
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                boundary: document.body
            });
        });
    }
    
    // Initialize popovers
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Back-to-top button behavior
    const backToTopBtn = document.getElementById('btn-back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTopBtn.style.display = 'block';
                setTimeout(() => {
                    backToTopBtn.style.opacity = '1';
                }, 50);
            } else {
                backToTopBtn.style.opacity = '0';
                setTimeout(() => {
                    backToTopBtn.style.display = 'none';
                }, 300);
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}); 