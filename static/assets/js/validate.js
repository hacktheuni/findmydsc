document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('myForm');

    // Validation functions
    function validateName(name) {
        const regex = /^[a-zA-Z\s]+$/;
        return regex.test(name) && name.trim().length > 0;
    }

    function validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    function validateUsername(username) {
        const regex = /^[a-zA-Z0-9]+$/;
        return regex.test(username);
    }

    function validatePassword(password) {
        const regex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;
        return regex.test(password);
    }
    
    

    function validatePhone(phone) {
        const regex = /^\d{10}$/;
        return regex.test(phone);
    }

    // Make validateField globally accessible
    window.validateField = function(field) {
        const value = field.value;
        let isValid = false;
        let errorMessage = '';

        const errorElement = document.getElementById(field.id + 'Error');
        if (!errorElement) {
            console.error('Error element not found for:', field.id + 'Error');
            return;
        }

        switch (field.id) {
            case 'name':
                isValid = validateName(value);
                errorMessage = 'Invalid name. Only letters and spaces are allowed.';
                break;
            case 'email':
                isValid = validateEmail(value);
                errorMessage = 'Invalid email address.';
                break;
            case 'username':
                isValid = validateUsername(value);
                errorMessage = 'Invalid username. Only letters and numbers are allowed.';
                break;
            case 'password':
                isValid = validatePassword(value);
                errorMessage = 'Password must be at least 8 characters long and contain letters, numbers, and special characters (@, $, !, %, *, ?, &, #).';
                break;
            case 'phone':
                isValid = validatePhone(value);
                errorMessage = 'Invalid phone number. Must be exactly 10 digits.';
                break;
            case 'clientPhone':
                isValid = validatePhone(value);
                errorMessage = 'Invalid phone number. Must be exactly 10 digits.';
                break;
        }

        if (isValid) {
            errorElement.textContent = '';
        } else {
            errorElement.textContent = errorMessage;
        }

        checkFormValidity();
    };

    function checkFormValidity() {
        const errors = form.querySelectorAll('.error-message');
        let allValid = true;

        errors.forEach(function(error) {
            if (error.textContent !== '') {
                allValid = false;
            }
        });

       
    }

});
