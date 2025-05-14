/**
 * O2 Fitness Club - Sistema de Gestión
 * Common JavaScript functions
 */

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add transition-ready class to enable transitions after page load
    setTimeout(() => {
        document.documentElement.classList.add('theme-transition-ready');
    }, 300);
    
    // Check for system preference first, then localStorage
    const savedTheme = localStorage.getItem('theme');
    let preferredTheme;
    
    if (savedTheme) {
        preferredTheme = savedTheme;
    } else {
        // Check system preference
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        preferredTheme = prefersDarkScheme.matches ? 'dark' : 'light';
        // Save the detected preference
        localStorage.setItem('theme', preferredTheme);
    }
    
    // Apply theme
    document.documentElement.setAttribute('data-bs-theme', preferredTheme);
    updateThemeUI(preferredTheme);
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            // Only update automatically if user hasn't explicitly chosen a theme
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            updateThemeUI(newTheme);
        }
    });
    
    // Theme toggle click handler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Add ripple effect to the body for a visual transition
            const ripple = document.createElement('div');
            ripple.className = 'theme-transition-ripple';
            ripple.style.backgroundColor = newTheme === 'dark' ? '#000' : '#fff';
            document.body.appendChild(ripple);
            
            // Animate ripple
            setTimeout(() => {
                ripple.style.transform = 'scale(100)';
                ripple.style.opacity = '0.3';
                
                // Apply new theme after short delay for visual effect
                setTimeout(() => {
                    // Save preference
                    localStorage.setItem('theme', newTheme);
                    
                    // Apply new theme
                    document.documentElement.setAttribute('data-bs-theme', newTheme);
                    
                    // Update UI
                    updateThemeUI(newTheme);
                    
                    // Remove ripple after animation completes
                    setTimeout(() => {
                        document.body.removeChild(ripple);
                    }, 300);
                }, 150);
            }, 10);
            
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
    
    // Trigger any custom theme change events
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
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