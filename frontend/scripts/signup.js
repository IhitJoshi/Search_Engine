document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("signup-form");
    const firstNameInput = document.getElementById("first-name");
    const lastNameInput = document.getElementById("last-name");
    const usernameInput = document.getElementById("username");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirm-password");
    const termsCheckbox = document.getElementById("terms");

    // Password strength checker
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');

    function checkPasswordStrength(password) {
        let score = 0;
        let feedback = '';

        if (password.length >= 8) score += 1;
        if (/[a-z]/.test(password)) score += 1;
        if (/[A-Z]/.test(password)) score += 1;
        if (/[0-9]/.test(password)) score += 1;
        if (/[^A-Za-z0-9]/.test(password)) score += 1;

        strengthFill.className = 'strength-fill';
        
        switch (score) {
            case 0:
            case 1:
                strengthFill.classList.add('strength-weak');
                feedback = 'Weak password';
                break;
            case 2:
            case 3:
                strengthFill.classList.add('strength-fair');
                feedback = 'Fair password';
                break;
            case 4:
                strengthFill.classList.add('strength-good');
                feedback = 'Good password';
                break;
            case 5:
                strengthFill.classList.add('strength-strong');
                feedback = 'Strong password';
                break;
        }

        strengthText.textContent = feedback;
        return score;
    }

    passwordInput.addEventListener('input', function() {
        checkPasswordStrength(this.value);
        validatePasswordMatch(); // Also check password match when password changes
    });

    // Password confirmation validation
    function validatePasswordMatch() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword && password !== confirmPassword) {
            confirmPasswordInput.classList.add('input-error');
            confirmPasswordInput.classList.remove('input-success');
            return false;
        } else if (confirmPassword && password === confirmPassword) {
            confirmPasswordInput.classList.remove('input-error');
            confirmPasswordInput.classList.add('input-success');
            return true;
        }
        
        confirmPasswordInput.classList.remove('input-error', 'input-success');
        return confirmPassword === '';
    }

    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    // Email validation
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    emailInput.addEventListener('blur', function() {
        if (this.value && !validateEmail(this.value)) {
            this.classList.add('input-error');
            this.classList.remove('input-success');
        } else if (this.value && validateEmail(this.value)) {
            this.classList.remove('input-error');
            this.classList.add('input-success');
        } else {
            this.classList.remove('input-error', 'input-success');
        }
    });

    // Username validation
    usernameInput.addEventListener('input', function() {
        const username = this.value;
        if (username.length >= 3 && /^[a-zA-Z0-9_]+$/.test(username)) {
            this.classList.remove('input-error');
            this.classList.add('input-success');
        } else if (username.length > 0) {
            this.classList.add('input-error');
            this.classList.remove('input-success');
        } else {
            this.classList.remove('input-error', 'input-success');
        }
    });

    // Name validation (basic)
    function validateName(input) {
        input.addEventListener('blur', function() {
            if (this.value && this.value.length >= 2 && /^[a-zA-Z\s]+$/.test(this.value)) {
                this.classList.remove('input-error');
                this.classList.add('input-success');
            } else if (this.value) {
                this.classList.add('input-error');
                this.classList.remove('input-success');
            } else {
                this.classList.remove('input-error', 'input-success');
            }
        });
    }

    validateName(firstNameInput);
    validateName(lastNameInput);

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
        
        const firstName = firstNameInput.value.trim();
        const lastName = lastNameInput.value.trim();
        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const termsAccepted = termsCheckbox.checked;
        const submitBtn = document.getElementById('signup-btn');

        // Comprehensive validation
        let isValid = true;
        let errorMessage = '';

        if (!firstName || firstName.length < 2 || !/^[a-zA-Z\s]+$/.test(firstName)) {
            errorMessage = 'Please enter a valid first name (letters only, 2+ characters).';
            isValid = false;
        } else if (!lastName || lastName.length < 2 || !/^[a-zA-Z\s]+$/.test(lastName)) {
            errorMessage = 'Please enter a valid last name (letters only, 2+ characters).';
            isValid = false;
        } else if (username.length < 3 || !/^[a-zA-Z0-9_]+$/.test(username)) {
            errorMessage = 'Username must be at least 3 characters and contain only letters, numbers, and underscores.';
            isValid = false;
        } else if (!validateEmail(email)) {
            errorMessage = 'Please enter a valid email address.';
            isValid = false;
        } else if (checkPasswordStrength(password) < 3) {
            errorMessage = 'Password is too weak. Please include uppercase, lowercase, numbers, and special characters.';
            isValid = false;
        } else if (password !== confirmPassword) {
            errorMessage = 'Passwords do not match.';
            isValid = false;
        } else if (!termsAccepted) {
            errorMessage = 'Please accept the Terms of Service and Privacy Policy.';
            isValid = false;
        }

        if (!isValid) {
            showMessage(errorMessage);
            return;
        }

        // Add loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            const response = await fetch('http://localhost:5000/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ 
                    username, 
                    email, 
                    password,
                    firstName,
                    lastName
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.message) {
                showMessage('Account created successfully! Redirecting to your dashboard...', 'success');
                
                // Clear form for security
                form.reset();
                
                // Redirect after success message
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 2000);
            } else {
                showMessage(data.error || 'Registration failed. Please try again.');
            }
        } catch (error) {
            console.error('Signup error:', error);
            
            if (error.message.includes('Failed to fetch')) {
                showMessage('Unable to connect to server. Please check your internet connection.');
            } else {
                showMessage('An error occurred during registration. Please try again.');
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

    // Real-time username availability check (placeholder)
    let usernameCheckTimeout;
    usernameInput.addEventListener('input', function() {
        const username = this.value.trim();
        
        // Clear previous timeout
        clearTimeout(usernameCheckTimeout);
        
        if (username.length >= 3 && /^[a-zA-Z0-9_]+$/.test(username)) {
            // Simulate API call delay
            usernameCheckTimeout = setTimeout(() => {
                // This is where you would check username availability with your backend
                // For now, just validate format
                console.log('Checking username availability:', username);
            }, 500);
        }
    });

    // Terms and Privacy Policy link handlers (placeholder)
    document.querySelectorAll('.terms-checkbox a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const linkText = this.textContent;
            showMessage(`${linkText} page would open here.`, 'success');
        });
    });

    // Form auto-save to sessionStorage (optional feature)
    const formInputs = [firstNameInput, lastNameInput, usernameInput, emailInput];
    
    formInputs.forEach(input => {
        // Load saved values
        const savedValue = sessionStorage.getItem(`signup_${input.id}`);
        if (savedValue) {
            input.value = savedValue;
        }
        
        // Save values as user types
        input.addEventListener('input', function() {
            sessionStorage.setItem(`signup_${input.id}`, this.value);
        });
    });

    // Clear saved data on successful submission
    form.addEventListener('submit', function() {
        // Clear sessionStorage data on form submission
        formInputs.forEach(input => {
            sessionStorage.removeItem(`signup_${input.id}`);
        });
    });
});