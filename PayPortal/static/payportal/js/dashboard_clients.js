// Setup event listeners for the create client modal
function setupCreateClientModal() {
    const createClientBtn = document.querySelector('.btn-primary');
    const modal = document.getElementById('create-client-modal');
    const closeBtn = document.getElementById('close-client-modal');
    const cancelBtn = document.getElementById('cancel-client');
    const submitBtn = document.getElementById('submit-client');
    const form = document.getElementById('create-client-form');
    const errorContainer = document.getElementById('client-form-error');

    // Open modal when Create Client button is clicked
    createClientBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent the default link behavior
        modal.classList.add('show');
        // Clear any previous error messages
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';
    });

    // Close modal functions
    function closeModal() {
        modal.classList.remove('show');
        form.reset();
        // Clear any error messages
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';
    }

    // Close modal when X button is clicked
    closeBtn.addEventListener('click', closeModal);

    // Close modal when Cancel button is clicked
    cancelBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Submit form
    submitBtn.addEventListener('click', submitCreateClient);
}

// Show toast notification
function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast-notification');
    const toastMessage = document.getElementById('toast-message');
    
    // Set message
    toastMessage.textContent = message;
    
    // Show toast
    toast.classList.add('show');
    
    // Hide after duration
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// Show error in the form
function showFormError(message) {
    const errorContainer = document.getElementById('client-form-error');
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
}

// Handle client creation submission
async function submitCreateClient() {
    const clientID = parseInt(document.getElementById('client-id').value, 10);
    const companyName = document.getElementById('company-name').value;
    const phone = document.getElementById('phone').value;
    const salesperson = document.getElementById('salesperson').value;
    const email = document.getElementById('email').value;
    const errorContainer = document.getElementById('client-form-error');
    
    // Clear any previous errors
    errorContainer.style.display = 'none';
    errorContainer.textContent = '';

    // Basic validation
    if (!clientID || !companyName || !phone || !salesperson || !email) {
        showFormError('Please fill in all fields');
        return;
    }

    // Validate phone number format
    if (!/^\d{10}$/.test(phone)) {
        showFormError('Please enter a valid 10-digit phone number');
        return;
    }

    try {
        // Show loading state
        const submitBtn = document.getElementById('submit-client');
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating...';
        submitBtn.disabled = true;

        // Create the payload
        const payload = {
            clientDetails: {
                clientID: clientID,
                companyName: companyName,
                phone: phone,
                salesperson: salesperson,
                email: email
            }
        };

        // Send the request to the server
        const response = await fetch('/quickpay/client/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        // Reset button state
        submitBtn.innerHTML = 'Create Client';
        submitBtn.disabled = false;

        // Handle the response
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to create client');
        }

        // Close the modal
        document.getElementById('create-client-modal').classList.remove('show');
        document.getElementById('create-client-form').reset();
        
        // Show success toast notification
        showToast('Client created successfully!');
        
        // Refresh client data
        setTimeout(() => {
            location.reload();
        }, 2000); // Wait for toast to be visible before refreshing
        
    } catch (error) {
        console.error('Error creating client:', error);
        
        // Show error in the form
        showFormError(`Error: ${error.message}`);
        
        // Reset button state
        const submitBtn = document.getElementById('submit-client');
        submitBtn.innerHTML = 'Create Client';
        submitBtn.disabled = false;
    }
}

// CSRF token function if not already implemented
function getCsrfToken() {
    const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (tokenElement) {
        return tokenElement.value;
    }
    
    // Try to get from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Initialize the modal when the page loads
document.addEventListener('DOMContentLoaded', () => {
    setupCreateClientModal();
});