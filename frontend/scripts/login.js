document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("login-form");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const rememberCheckbox = document.getElementById("remember");

    // Load saved username if "remember me" was checked
    const savedUsername = localStorage.getItem('rememberedUsername');
    if (savedUsername) {
        usernameInput.value = savedUsername;
        rememberCheckbox.checked = true;
    }

    // Input validation and styling
    function validateInput(input, validationFn) {
        input.addEventListener('blur', function() {
            if (this.value && !validationFn(this.value)) {
                this.classList.add('input-error');
                this.classList.remove('input-success');
            } else if (this.value && validationFn(this.value)) {
                this.classList.remove('input-error');
                this.classList.add('input-success');
            } else {
                this.classList.remove('input-error', 'input-success');
            }
        });
    }

    // Username validation (3+ characters, alphanumeric + underscore)
    validateInput(usernameInput, (username) => {
        return username.length >= 3 && /^[a-zA-Z0-9_]+$/.test(username);
    });

    // Password validation (basic length check)
    validateInput(passwordInput, (password) => {
        return password.length >= 6;
    });

    // Message display function
    function showMessage(message, type = 'error') {
        const messageContainer = document.getElementById('message-container');
        messageContainer.innerHTML = `<div class="${type}-message">${message}</div>`;
        
        // Auto-hide message after 5 seconds
        setTimeout(() => {
            if (messageContainer.innerHTML.includes(message)) {
                messageContainer.innerHTML = '';
            }
        }, 5000);
    }

    // Form submission handler
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const submitBtn = document.getElementById('login-btn');

        // Basic validation
        if (!username || !password) {
            showMessage('Please fill in all fields.');
            return;
        }

        if (username.length < 3) {
            showMessage('Username must be at least 3 characters long.');
            return;
        }

        // Add loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            const response = await fetch("http://localhost:5000/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",  // important for Flask session
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.message) {
                // Handle "remember me" functionality
                if (rememberCheckbox.checked) {
                    localStorage.setItem('rememberedUsername', username);
                } else {
                    localStorage.removeItem('rememberedUsername');
                }

                showMessage('Login successful! Redirecting to your dashboard...', 'success');
                
                // Add a small delay for better UX
                setTimeout(() => {
                    window.location.href = "index.html";
                }, 1500);
            } else {
                showMessage(data.error || "Invalid username or password. Please try again.");
            }
        } catch (error) {
            console.error("Login error:", error);
            
            if (error.message.includes('Failed to fetch')) {
                showMessage('Unable to connect to server. Please check your internet connection.');
            } else {
                showMessage('An error occurred during login. Please try again.');
            }
        } finally {
            // Remove loading state
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });

    // Input focus animations
    document.querySelectorAll('.form-input').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    // Initialize particle animations
    window.addEventListener('load', function() {
        const particles = document.querySelectorAll('.particle');
        particles.forEach((particle, index) => {
            particle.style.animationDelay = `${-index * 1.5}s`;
        });
    });

    // Enter key handling for better UX
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && (usernameInput === document.activeElement || passwordInput === document.activeElement)) {
            form.dispatchEvent(new Event('submit'));
        }
    });

    // Forgot password functionality (placeholder)
    document.querySelector('.forgot-password').addEventListener('click', function(e) {
        e.preventDefault();
        showMessage('Password reset functionality coming soon!', 'success');
    });
});