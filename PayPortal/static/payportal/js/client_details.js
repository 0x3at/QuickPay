// Add to the top of your file
let isLoading = false;
let clientData = null;

// Add at the very top of your file
console.log("Client details script loaded - version 1.0.5"); // Change version each time you update

// Get client ID from URL or any other source
function getClientIDFromURL() {
    // Example: Get from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("id");
}

// Function to show loading state
function showLoading(show = true) {
    isLoading = show;
    // You could add a loading spinner here
    const container = document.querySelector(".content-container");

    if (show) {
        const loadingEl = document.createElement("div");
        loadingEl.id = "loading-indicator";
        loadingEl.classList.add("loading-indicator");
        loadingEl.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Loading client data...';
        container.prepend(loadingEl);
    } else {
        const loadingEl = document.getElementById("loading-indicator");
        if (loadingEl) loadingEl.remove();
    }
}

// Fetch client data from API
async function fetchClientData() {
    const clientID = getClientIDFromURL();
    if (!clientID) {
        console.error("No client ID provided");
        showErrorMessage(
            "No client ID provided. Please check the URL and try again."
        );
        return null;
    }

    showLoading(true);

    try {
        const response = await fetch("/quickpay/client/profile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ clientID: parseInt(clientID, 10) }),
        });

        showLoading(false);

        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }

        const data = await response.json();
        if (!data || !data.clientDetails) {
            throw new Error("Invalid client data received");
        }

        return data;
    } catch (error) {
        showLoading(false);
        console.error("Error fetching client data:", error);
        showErrorMessage(`Failed to load client data: ${error.message}`);
        return null;
    }
}

// Function to get CSRF token if needed
function getCsrfToken() {
    const tokenElement = document.querySelector(
        'input[name="csrfmiddlewaretoken"]'
    );
    if (tokenElement) {
        return tokenElement.value;
    }

    // Try to get from cookie
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split("=");
        if (name === "csrftoken") {
            return value;
        }
    }
    return "";
}

// Hydrate client profile info
function hydrateClientProfile(clientDetails) {
    // Client name and identifier
    document.querySelector(".client-info h2").textContent =
        clientDetails.companyName;
    document.querySelector(".client-meta .badge").textContent =
        `Client ID: ${clientDetails.clientID}`;

    // Contact information
    const contactItems = document.querySelectorAll(
        ".client-contact .contact-item"
    );
    contactItems[0].querySelector("span").textContent = clientDetails.email;
    contactItems[1].querySelector("span").textContent = formatPhoneNumber(
        clientDetails.phone
    );
    if (clientDetails.defaultPayment) {
        contactItems[2].querySelector(
            "span"
        ).textContent = `${clientDetails.defaultPayment.streetAddress}, ${clientDetails.defaultPayment.zipCode}`;
    }
}

// Hydrate payment methods section
function hydratePaymentMethods(paymentProfiles) {
    const paymentMethodsList = document.querySelector(".payment-methods-list");
    paymentMethodsList.innerHTML = "";

    paymentProfiles.forEach((profile, index) => {
        const isDefault = index === 0; // Assuming first one is default
        // No need to get specific card type icon

        const paymentMethodHTML = `
            <div class="payment-method-card">
                <div class="payment-method-icon blue-icon">
                    <i class="fa-solid fa-credit-card"></i>
                </div>
                <div class="payment-method-details">
                    <div class="payment-method-name">Credit Card ending in ${profile.lastFour
            }</div>
                    <div class="payment-method-info">${profile.firstName} ${profile.lastName
            }</div>
                    <div class="payment-method-info">${profile.streetAddress} ${profile.zipCode
            }</div>
                    <div class="payment-method-info">${profile.email}</div>
                </div>
                <div class="payment-method-status">
                    ${isDefault
                ? '<span class="badge success">Default</span>'
                : ""
            }
                </div>
                <div class="payment-method-actions">
                    ${!isDefault
                ? '<button class="btn btn-sm btn-outline" style="display: none;">Set Default</button>'
                : ""
            }
                    <button class="btn btn-sm btn-outline" style="display: none;">Edit</button>
                    <button class="btn btn-sm btn-outline btn-danger" style="display: none;">Remove</button>
                </div>
            </div>
        `;

        paymentMethodsList.innerHTML += paymentMethodHTML;
    });

    // Update payment method options in forms
    updatePaymentMethodSelects(paymentProfiles);
}

// Hydrate transactions tab
function hydrateTransactions(transactions) {
    const transactionsTableBody = document.querySelector("#transactions .data-table tbody");
    transactionsTableBody.innerHTML = "";
    transactions.reverse();

    transactions.forEach((transaction) => {
        const date = new Date(transaction.created_at);
        const formattedDate = date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });

        const transactionHTML = `
            <tr>
                <td>
                    <span class="text-primary">${transaction.transId}</span>
                </td>
                <td>${formattedDate}</td>
                <td>$${parseFloat(transaction.amount).toFixed(2)}</td>
                <td>
                    <span class="status-badge ${transaction.result === "Success" ? "success" : "error"}">${transaction.result}</span>
                </td>
                <td>Card ending in ${transaction.accountNumber.slice(-4)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn receipt-view-btn" data-transaction='${JSON.stringify(transaction)}' title="View Receipt">
                            <i class="fa-solid fa-receipt"></i>
                        </button>
                    </div>
                </td>
            </tr>`;

        transactionsTableBody.innerHTML += transactionHTML;
    });

    // Add click handlers after adding the buttons to DOM
    document.querySelectorAll('.receipt-view-btn').forEach(button => {
        button.addEventListener('click', function () {
            const transaction = JSON.parse(this.getAttribute('data-transaction'));
            showReceiptDetails(transaction);
        });
    });
}

// Hydrate client details tab
function hydrateClientDetails(clientDetails) {
    // Company Information
    const detailsSections = document.querySelectorAll(".details-section");

    // Company section
    const companySection = detailsSections[0];
    const companyRows = companySection.querySelectorAll(".details-row");
    companyRows[0].querySelector(".details-value").textContent =
        clientDetails.companyName;
    companyRows[1].querySelector(
        ".details-value"
    ).textContent = `${clientDetails.clientID}`;

    // Primary Contact section
    if (clientDetails.defaultPayment) {
        const contactSection = detailsSections[1];
        const contactRows = contactSection.querySelectorAll(".details-row");
        contactRows[0].querySelector(
            ".details-value"
        ).textContent = `${clientDetails.defaultPayment.firstName} ${clientDetails.defaultPayment.lastName}`;
        contactRows[1].querySelector(".details-value").textContent =
            clientDetails.email;
        contactRows[2].querySelector(".details-value").textContent =
            formatPhoneNumber(clientDetails.phone);
    }

    // Account Information section
    const accountSection = detailsSections[2];
    const accountRows = accountSection.querySelectorAll(".details-row");
    accountRows[0].querySelector(".details-value").textContent =
        clientDetails.salesperson;
    accountRows[1].querySelector(".details-value").textContent = new Date(
        clientDetails.createdAt
    ).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

// Hydrate notes section
function hydrateNotes(notes) {
    const recentNotesContainer = document.querySelector(".recent-notes");
    const notesTimeline = document.querySelector(".notes-timeline");

    // Clear existing notes
    recentNotesContainer.innerHTML = "";
    notesTimeline.innerHTML = "";

    if (notes.length === 0) {
        recentNotesContainer.innerHTML = "<p>No notes available</p>";
        notesTimeline.innerHTML = "<p>No notes available</p>";
        return;
    }

    // Add notes to both recent notes card and notes tab
    notes.slice(0, 2).forEach((note) => {
        const date = new Date(note.createdAt);
        const timeAgo = getTimeAgo(date);

        const notePreviewHTML = `
            <div class="note-preview">
                <div class="note-preview-header">
                    <span class="note-author">${note.createdBy}</span>
                    <span class="note-date">${timeAgo}</span>
                </div>
                <p class="note-text">${note.note}</p>
            </div>
        `;

        recentNotesContainer.innerHTML += notePreviewHTML;
    });

    notes.forEach((note) => {
        const date = new Date(note.createdAt);
        const formattedDate = date.toLocaleString("en-US");
        const initials = getInitials(note.createdBy);

        const noteItemHTML = `
            <div class="note-item">
                <div class="note-avatar">
                    <span>${initials}</span>
                </div>
                <div class="note-content">
                    <div class="note-header">
                        <span class="note-author">${note.createdBy}</span>
                        <span class="note-date">${formattedDate}</span>
                    </div>
                    <div class="note-text">
                        ${note.note}
                    </div>
                    <div class="note-actions">
                        <button class="btn btn-text">Edit</button>
                        <button class="btn btn-text btn-danger">Delete</button>
                    </div>
                </div>
            </div>`;

        notesTimeline.innerHTML += noteItemHTML;
    });
}

// Update payment method dropdowns
function updatePaymentMethodSelects(paymentProfiles) {
    const selects = document.querySelectorAll(
        "#quick-payment-method, #payment-method"
    );

    selects.forEach((select) => {
        select.innerHTML = "";

        paymentProfiles.forEach((profile, index) => {
            const cardType = getCardTypeIcon(profile.cardType || profile.accountType);
            const isDefault = index === 0;

            const option = document.createElement("option");
            option.value = profile.paymentProfileID;
            option.textContent = `${cardType} ending in ${profile.lastFour}${isDefault ? " (Default)" : ""
                }`;
            select.appendChild(option);
        });
    });
}

// Utility functions
function formatPhoneNumber(phone) {
    if (!phone) return "";
    const cleaned = phone.replace(/\D/g, "");
    if (cleaned.length !== 10) return phone;
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
}

function getCardTypeIcon(cardType) {
    const typeMap = {
        Visa: "visa",
        MasterCard: "mastercard",
        AmericanExpress: "amex",
        Discover: "discover",
    };

    return typeMap[cardType] || "Card";
}

function getInitials(name) {
    if (!name) return "";
    return name
        .split(" ")
        .map((part) => part.charAt(0).toUpperCase())
        .slice(0, 2)
        .join("");
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
        }
    }

    return "just now";
}

// Show toast notification - simplified version
function showToast(message, duration = 5000) {
    console.log("Showing toast with message:", message);

    const toast = document.getElementById('toast-notification');
    if (!toast) {
        console.error("Toast element not found!");
        alert(message); // Fallback to alert if toast element not found
        return;
    }

    const toastContent = toast.querySelector('.toast-content');
    const toastMessage = document.getElementById('toast-message');

    // Set success style
    toastContent.classList.remove('error');
    toastContent.classList.add('success');
    toastContent.querySelector('i').className = 'fa-solid fa-check-circle';

    // Set message
    toastMessage.textContent = message;

    // SIMPLER APPROACH: Just use the class-based system
    toast.classList.add('show');

    // Hide after duration
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// Show error message with toast - simplified version
function showErrorMessage(message) {
    console.log("Showing error toast with message:", message);

    const toast = document.getElementById('toast-notification');
    if (!toast) {
        console.error("Toast element not found!");
        alert(message); // Fallback to alert if toast element not found
        return;
    }

    const toastContent = toast.querySelector('.toast-content');
    const toastMessage = document.getElementById('toast-message');

    // Set error style
    toastContent.classList.remove('success');
    toastContent.classList.add('error');
    toastContent.querySelector('i').className = 'fa-solid fa-exclamation-circle';

    // Set message
    toastMessage.textContent = message;

    // SIMPLER APPROACH: Just use the class-based system
    toast.classList.add('show');

    // Hide after duration
    setTimeout(() => {
        toast.classList.remove('show');

        // Reset to success style after hiding
        setTimeout(() => {
            toastContent.classList.remove('error');
            toastContent.classList.add('success');
            toastContent.querySelector('i').className = 'fa-solid fa-check-circle';
        }, 300);
    }, 5000);
}

// Show error in a form
function showFormError(errorContainer, message) {
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
}

// Hide form error
function hideFormError(errorContainer) {
    errorContainer.style.display = 'none';
    errorContainer.textContent = '';
}

// Setup tab switching
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const targetTab = button.getAttribute("data-tab");

            // Update active states
            tabButtons.forEach((btn) => btn.classList.remove("active"));
            tabPanes.forEach((pane) => pane.classList.remove("active"));

            button.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
    });
}

// Setup event listeners for the payment method modal - with enhanced debugging
function setupPaymentMethodModal() {
    console.log("Setting up payment method modal...");

    // Try multiple selectors to find the button
    let addPaymentBtn = document.querySelector('#payment-methods .card-header .btn');
    if (!addPaymentBtn) {
        console.log("Button not found with first selector, trying alternatives...");
        addPaymentBtn = document.querySelector('.card-header .btn-outline.btn-sm');
    }
    if (!addPaymentBtn) {
        console.log("Button not found with second selector, trying another...");
        // Try to find by text content
        const buttons = document.querySelectorAll('.btn');
        for (const btn of buttons) {
            if (btn.textContent.includes("Add Payment Method")) {
                addPaymentBtn = btn;
                console.log("Found button by text content!");
                break;
            }
        }
    }

    console.log("Add Payment Method button found:", !!addPaymentBtn);

    // Add a direct click handler to all buttons in payment methods tab as a fallback
    document.querySelectorAll('#payment-methods button').forEach(btn => {
        console.log("Found a button in payment methods tab:", btn.textContent.trim());
    });

    const modal = document.getElementById('add-payment-modal');
    if (!modal) {
        console.error("Payment modal element not found!");
        return;
    }

    const closeBtn = document.getElementById('close-payment-modal');
    const cancelBtn = document.getElementById('cancel-payment');
    const submitBtn = document.getElementById('submit-payment');
    const form = document.getElementById('add-payment-form');
    const errorContainer = document.getElementById('payment-form-error');

    // Open modal when Add Payment Method button is clicked
    if (addPaymentBtn) {
        console.log("Adding click listener to payment method button");
        addPaymentBtn.addEventListener('click', (e) => {
            console.log("Add Payment Method button clicked!");
            e.preventDefault(); // Prevent default in case it's a form button
            modal.classList.add('show');
            // Clear any previous error messages
            if (errorContainer) hideFormError(errorContainer);
        });
    } else {
        console.error("Add Payment Method button not found after multiple attempts!");
    }

    // Close modal functions
    function closeModal() {
        modal.classList.remove('show');
        form.reset();
        // Clear any error messages
        hideFormError(errorContainer);
    }

    // Close modal when X button is clicked
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close modal when Cancel button is clicked
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Submit form
    if (submitBtn) {
        submitBtn.addEventListener('click', submitPaymentMethod);
    }
}

// Handle payment method submission
async function submitPaymentMethod() {
    const errorContainer = document.getElementById('payment-form-error');
    hideFormError(errorContainer);

    // Get the values from the form
    const cardNumber = document.getElementById('card-number').value.replace(/\s/g, '');
    const expirationDate = document.getElementById('expiration-date').value;
    const cardCode = document.getElementById('card-code').value;
    const firstName = document.getElementById('first-name').value;
    const lastName = document.getElementById('last-name').value;
    const address = document.getElementById('address').value;
    const zipCode = document.getElementById('zip-code').value;

    // Basic validation
    if (!cardNumber || !expirationDate || !cardCode || !firstName || !lastName || !address || !zipCode) {
        showFormError(errorContainer, 'Please fill in all fields');
        return;
    }

    // Get the client ID from the current client data
    const clientID = clientData.clientDetails.clientID;

    try {
        // Show loading state
        const submitBtn = document.getElementById('submit-payment');
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        submitBtn.disabled = true;

        // Create the payload
        const payload = {
            clientID: clientID,
            cardDetails: {
                cardNumber: cardNumber,
                expirationDate: expirationDate,
                cardCode: cardCode
            },
            billingDetails: {
                firstName: firstName,
                lastName: lastName,
                address: address,
                zipCode: zipCode
            }
        };

        // Send the request to the server
        const response = await fetch('/quickpay/client/profiles/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        // Reset button state
        submitBtn.innerHTML = 'Add Payment Method';
        submitBtn.disabled = false;

        // Handle the response
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to add payment method');
        }

        const data = await response.json();

        // Close the modal
        document.getElementById('add-payment-modal').classList.remove('show');
        document.getElementById('add-payment-form').reset();

        // Reload client data to show the new payment method
        clientData = await fetchClientData();
        if (clientData) {
            hydratePaymentMethods(clientData.paymentProfiles);
        }

        // Show success message with toast
        showToast('Payment method added successfully');

    } catch (error) {
        console.error('Error adding payment method:', error);
        showFormError(errorContainer, `Error: ${error.message}`);

        // Reset button state
        const submitBtn = document.getElementById('submit-payment');
        submitBtn.innerHTML = 'Add Payment Method';
        submitBtn.disabled = false;
    }
}

// Setup event listeners for the note modal
function setupNoteModal() {
    const addNoteBtn = document.querySelector('#notes .card-header .btn');
    const modal = document.getElementById('add-note-modal');
    const closeBtn = document.getElementById('close-note-modal');
    const cancelBtn = document.getElementById('cancel-note');
    const submitBtn = document.getElementById('submit-note');
    const form = document.getElementById('add-note-form');
    const noteContent = document.getElementById('note-content');
    const charCount = document.getElementById('char-count');
    const errorContainer = document.getElementById('note-form-error');

    // Character counter for note textarea
    if (noteContent) {
        noteContent.addEventListener('input', function () {
            const currentLength = this.value.length;
            charCount.textContent = currentLength;

            // Change color when approaching limit
            if (currentLength >= 200) {
                charCount.style.color = '#ef4444';
            } else if (currentLength >= 150) {
                charCount.style.color = '#f59e0b';
            } else {
                charCount.style.color = '';
            }
        });
    }

    // Open modal when Add Note button is clicked
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', () => {
            modal.classList.add('show');
            // Clear any previous error messages
            hideFormError(errorContainer);
        });
    }

    // Close modal functions
    function closeModal() {
        modal.classList.remove('show');
        form.reset();
        charCount.textContent = '0';
        charCount.style.color = '';
        // Clear any error messages
        hideFormError(errorContainer);
    }

    // Close modal when X button is clicked
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close modal when Cancel button is clicked
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Submit form
    if (submitBtn) {
        submitBtn.addEventListener('click', submitNote);
    }
}

// Handle note submission
async function submitNote() {
    console.log("submitNote called");

    const errorContainer = document.getElementById('note-form-error');
    hideFormError(errorContainer);

    const author = document.getElementById('note-author').value;
    const noteText = document.getElementById('note-content').value;

    // Basic validation
    if (!author || !noteText) {
        console.log("Validation failed - showing form error");
        showFormError(errorContainer, 'Please fill in all fields');
        return;
    }

    // Get the client ID from the current client data
    const clientID = clientData.clientDetails.clientID;

    try {
        // Show loading state
        const submitBtn = document.getElementById('submit-note');
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
        submitBtn.disabled = true;

        // Log the request
        console.log("Sending note request with payload:", {
            clientID, author, noteText
        });

        // Create the note payload
        const payload = {
            clientID: clientID,
            createdBy: author,
            note: noteText
        };

        // Send the request to the server
        const response = await fetch('/quickpay/client/notes/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        // Reset button state
        submitBtn.innerHTML = 'Add Note';
        submitBtn.disabled = false;

        // Handle the response
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to add note');
        }

        // Close the modal
        document.getElementById('add-note-modal').classList.remove('show');
        document.getElementById('add-note-form').reset();
        document.getElementById('char-count').textContent = '0';
        document.getElementById('char-count').style.color = '';

        // Reload client data to show the new note
        clientData = await fetchClientData();
        if (clientData) {
            hydrateNotes(clientData.notes);
        }

        // Show success message with toast instead of alert
        console.log("Note added successfully, showing toast");
        showToast('Note added successfully');

    } catch (error) {
        console.error('Error adding note:', error);
        showFormError(errorContainer, `Error: ${error.message}`);

        // Reset button state
        const submitBtn = document.getElementById('submit-note');
        submitBtn.innerHTML = 'Add Note';
        submitBtn.disabled = false;
    }
}

// Setup receipt view
function setupReceiptModal() {
    const modal = document.getElementById('charge-receipt-modal');

    // Close receipt modal when clicking close button
    const closeButtons = modal.querySelectorAll('.close-modal');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            modal.classList.remove('show');
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.classList.remove('show');
        }
    });

    // Setup download functionality
    const downloadButton = document.getElementById('download-receipt');
    if (downloadButton) {
        downloadButton.onclick = (e) => {
            e.preventDefault(); // Prevent any default behavior
            generatePDF(transactionResult);
            showToast("Receipt downloaded successfully");
        };
    }
}

// Initialize page
async function initClientDetailsPage() {
    setupTabSwitching();

    // Initialize toast
    hideStaticToastMessage();

    clientData = await fetchClientData();
    if (!clientData) {
        document.querySelector(".content-container").innerHTML = `
            <div class="error-message">
                <i class="fa-solid fa-exclamation-triangle"></i>
                <p>Failed to load client data. Please try again later or contact support.</p>
                <button class="btn btn-primary" onclick="location.reload()">Retry</button>
            </div>
        `;
        return;
    }

    hydrateClientProfile(clientData.clientDetails);
    hydratePaymentMethods(clientData.paymentProfiles);
    hydrateTransactions(clientData.transactions);
    hydrateClientDetails(clientData.clientDetails);
    hydrateNotes(clientData.notes);

    // Setup form event listeners
    setupPaymentFormListeners();
    setupPaymentMethodModal();
    setupNoteModal();
    setupReceiptModal();
}

// Setup payment form listeners
function setupPaymentFormListeners() {
    console.log("Setting up payment form listeners");

    const quickPaymentForm = document.querySelector(".quick-payment-form");
    if (quickPaymentForm) {
        console.log("Quick payment form found, adding submit listener");
        quickPaymentForm.addEventListener("submit", function (e) {
            console.log("Quick payment form submitted");
            handleQuickPayment(e);
        });
    } else {
        console.warn("Quick payment form not found!");
    }

    const quickChargeForm = document.getElementById("quick-charge-form");
    if (quickChargeForm) {
        console.log("Quick charge form found, adding submit listener");
        quickChargeForm.addEventListener("submit", function (e) {
            console.log("Quick charge form submitted");
            handleQuickCharge(e);
        });
    } else {
        console.warn("Quick charge form not found!");
    }
}

// Handle quick payment submission - with improved error handling
async function handleQuickPayment(event) {
    event.preventDefault();

    const amount = document.getElementById("quick-amount").value;
    const paymentProfileID = document.getElementById("quick-payment-method").value;

    if (!amount || parseFloat(amount) <= 0) {
        showErrorMessage("Please enter a valid amount");
        return;
    }

    // Get submit button to show loading state
    const submitButton = event.target.querySelector("button[type='submit']");
    if (submitButton) {
        submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        submitButton.disabled = true;
    }

    try {
        // Create payload for the API
        const payload = {
            clientID: clientData.clientDetails.clientID,
            paymentProfileID: paymentProfileID,
            amount: amount
        };

        console.log("Sending payment request:", payload);

        // Send the request to the backend
        const response = await fetch("/quickpay/client/profiles/charge", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        console.log("Payment response:", data);

        // Reset button state
        if (submitButton) {
            submitButton.innerHTML = '<i class="fa-solid fa-bolt"></i> Process Payment';
            submitButton.disabled = false;
        }

        // Handle the response
        if (data.success && data.transactionResult && data.transactionResult.result === "Success") {
            // Show success message
            showToast("Payment processed successfully!");

            try {
                // Show receipt with transaction details
                showReceiptDetails(data.transactionResult);
            } catch (receiptError) {
                console.error("Error showing receipt:", receiptError);
                // Even if receipt fails, the payment succeeded
                showToast("Payment successful! Receipt unavailable.");
            }

            // Reset form
            event.target.reset();

            // Refresh transaction data
            setTimeout(async () => {
                try {
                    clientData = await fetchClientData();
                    if (clientData) {
                        hydrateTransactions(clientData.transactions);
                    }
                } catch (err) {
                    console.error("Error refreshing transaction data:", err);
                }
            }, 1000);
        } else {
            // Show error message
            const errorMessage = data.transactionResult?.errorText ||
                data.transactionResult?.error ||
                data.error ||
                "Payment processing failed. Please try again.";
            showErrorMessage(errorMessage);
        }
    } catch (error) {
        console.error("Error processing payment:", error);

        // Reset button state
        if (submitButton) {
            submitButton.innerHTML = '<i class="fa-solid fa-bolt"></i> Process Payment';
            submitButton.disabled = false;
        }

        // Show error message
        showErrorMessage("Network error. Please check your connection and try again.");
    }
}

// Handle quick charge submission
async function handleQuickCharge(event) {
    event.preventDefault();

    const amount = document.getElementById("amount").value;
    const paymentProfileID = document.getElementById("payment-method").value;
    const salesperson = document.getElementById("salesperson").value;

    if (!amount || parseFloat(amount) <= 0) {
        showErrorMessage("Please enter a valid amount");
        return;
    }

    if (!salesperson) {
        showErrorMessage("Please enter a salesperson name");
        return;
    }

    // Get submit button to show loading state
    const submitButton = event.target.querySelector("button[type='submit']");
    submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    submitButton.disabled = true;

    try {
        // Create payload for the API - simplified as requested
        const payload = {
            clientID: clientData.clientDetails.clientID,
            paymentProfileID: paymentProfileID,
            amount: amount
            // salesperson removed from payload as requested
        };

        console.log("Sending charge request:", payload);

        // Send the request to the backend
        const response = await fetch("/quickpay/client/profiles/charge", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        // Reset button state
        submitButton.innerHTML = 'Process Charge';
        submitButton.disabled = false;

        // Handle the response
        if (data.success && data.transactionResult && data.transactionResult.result === "Success") {
            // Show success message
            showToast("Charge processed successfully!");

            // For receipt display, we'll use the salesperson from the form 
            // but we'll need to add it to the transaction result
            const enhancedResult = {
                ...data.transactionResult,
                salesperson: salesperson // Add salesperson from form for display purposes
            };

            // Show receipt with transaction details
            showReceiptDetails(enhancedResult);

            // Reset form
            event.target.reset();

            // Reload transactions to show the new one
            clientData = await fetchClientData();
            if (clientData) {
                hydrateTransactions(clientData.transactions);
            }
        } else {
            // Show error message
            const errorMessage = data.transactionResult?.errorText ||
                data.transactionResult?.error ||
                data.error ||
                "Charge processing failed. Please try again.";
            showErrorMessage(errorMessage);
        }
    } catch (error) {
        console.error("Error processing charge:", error);

        // Reset button state
        submitButton.innerHTML = 'Process Charge';
        submitButton.disabled = false;

        // Show error message
        showErrorMessage("Network error. Please check your connection and try again.");
    }
}

// Immediately hide the static toast on page load - simplified version
function hideStaticToastMessage() {
    console.log("Hiding static toast message");
    const toast = document.getElementById('toast-notification');
    if (toast) {
        // Just remove the show class
        toast.classList.remove('show');

        // And clear the message
        const toastMessage = document.getElementById('toast-message');
        if (toastMessage) {
            toastMessage.textContent = '';
        }
    }
}

// Call this immediately
document.addEventListener('DOMContentLoaded', function () {
    hideStaticToastMessage();
    // Continue with normal initialization
    initClientDetailsPage();
});

// At the top of your file
// Add a version query parameter to all dynamically loaded resources
function addVersionToURL(url) {
    const timestamp = new Date().getTime();
    const separator = url.indexOf('?') !== -1 ? '&' : '?';
    return `${url}${separator}v=${timestamp}`;
}

// Debug helper function - can be called from browser console
window.debugShowToast = function (message = "Test toast message") {
    showToast(message);
};

window.debugShowError = function (message = "Test error message") {
    showErrorMessage(message);
};

// Function to display transaction receipt - with error handling
function showReceiptDetails(transactionResult) {
    try {
        const modal = document.getElementById('charge-receipt-modal');
        if (!modal) {
            console.error("Receipt modal not found");
            showToast("Receipt unavailable");
            return;
        }

        // Update status icon and heading based on transaction result
        const statusSection = modal.querySelector('.receipt-status');
        const statusHeading = modal.querySelector('.receipt-status h3');
        const statusIcon = modal.querySelector('.receipt-status .receipt-icon i');

        if (statusHeading && statusIcon) {
            if (transactionResult.result === 'Success') {
                statusHeading.textContent = 'Payment Successful';
                statusIcon.className = 'fa-solid fa-circle-check';
                statusIcon.style.color = 'var(--success)'; // Use success color
                statusSection.style.color = 'var(--success)';
            } else {
                statusHeading.textContent = 'Payment Failed';
                statusIcon.className = 'fa-solid fa-circle-xmark';
                statusIcon.style.color = 'var(--error)'; // Use error color
                statusSection.style.color = 'var(--error)';
            }
        }

        // Rest of the existing code...
        const safeSetText = (id, value) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            } else {
                console.warn(`Element with id '${id}' not found in receipt modal`);
            }
        };

        // Client information
        safeSetText('receipt-client', clientData.clientDetails.companyName);
        safeSetText('receipt-clientId', clientData.clientDetails.clientID);

        // Transaction details
        safeSetText('receipt-transId', transactionResult.transId || "N/A");
        safeSetText('receipt-amount', '$' + parseFloat(transactionResult.amount).toFixed(2));
        safeSetText('receipt-date', new Date(transactionResult.created_at).toLocaleString());
        safeSetText('receipt-card', `${transactionResult.accountType || "Card"} ending in ${(transactionResult.accountNumber || "").slice(-4)}`);
        safeSetText('receipt-status', transactionResult.result || "N/A");

        // Show the modal
        modal.classList.add('show');

        // Setup close functionality
        const closeButtons = modal.querySelectorAll('.close-modal');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                modal.classList.remove('show');
            });
        });

        // Close when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.classList.remove('show');
            }
        });

        // Setup download functionality
        const downloadButton = document.getElementById('download-receipt');
        if (downloadButton) {
            downloadButton.onclick = (e) => {
                e.preventDefault(); // Prevent any default behavior
                generatePDF(transactionResult);
                showToast("Receipt downloaded successfully");
            };
        }

    } catch (error) {
        console.error("Error displaying receipt:", error);
        showToast("Error displaying receipt");
    }
}

// Add this debugging helper to the global scope
window.debugShowModal = function () {
    const modal = document.getElementById('add-payment-modal');
    if (modal) {
        console.log("Manually showing payment modal");
        modal.classList.add('show');
    } else {
        console.error("Modal not found for manual display");
    }
};

// Add new function to show transaction receipt
function showTransactionReceipt(transaction) {
    console.log("Showing receipt for transaction:", transaction);

    try {
        const modal = document.getElementById('charge-receipt-modal');
        if (!modal) {
            console.error("Receipt modal not found");
            showToast("Receipt unavailable");
            return;
        }

        // Set transaction details in the receipt
        const statusHeading = modal.querySelector('.receipt-status h3');
        if (statusHeading) {
            statusHeading.textContent = transaction.result === 'Success' ? 'Payment Successful' : 'Payment Failed';
        }

        // Client information
        document.getElementById('receipt-client').textContent = clientData.clientDetails.companyName;
        document.getElementById('receipt-clientId').textContent = clientData.clientDetails.clientID;

        // Transaction details
        document.getElementById('receipt-transId').textContent = transaction.transId || "N/A";
        document.getElementById('receipt-amount').textContent = `$${parseFloat(transaction.amount).toFixed(2)}`;

        // Format date
        const transDate = transaction.created_at ? new Date(transaction.created_at) : new Date();
        document.getElementById('receipt-date').textContent = transDate.toLocaleString();

        document.getElementById('receipt-card').textContent = `${transaction.accountType || "Card"} ending in ${transaction.accountNumber.slice(-4)}`;
        document.getElementById('receipt-status').textContent = transaction.result || "N/A";

        // Show the modal
        modal.classList.add('show');

        // Setup print functionality
        const printButton = document.getElementById('print-receipt');
        if (printButton) {
            printButton.onclick = () => generatePDF(transaction);
        }
    } catch (error) {
        console.error("Error displaying receipt:", error);
        showToast("Error displaying receipt");
    }
}

// Add PDF generation function
function generatePDF(transaction) {
    try {
        const { jsPDF } = window.jspdf;
        const doc = new jspdf.jsPDF();

        // Document settings
        const pageWidth = doc.internal.pageSize.width;
        const margin = 24;
        const contentWidth = pageWidth - margin * 2;

        // Colors
        const primaryColor = [44, 62, 80];
        const secondaryColor = [52, 73, 94];
        const accentColor = [41, 128, 185];
        const lightGray = [245, 246, 250];

        // Helper function to ensure string values
        const formatValue = (value) => {
            if (value === null || value === undefined) return "N/A";
            return String(value);
        };

        // Add receipt header
        doc.setFont("helvetica", "bold");
        doc.setFontSize(22);
        doc.setTextColor(...primaryColor);
        doc.text("Payment Receipt", pageWidth / 2, 30, { align: "center" });

        // Add horizontal line
        doc.setDrawColor(...accentColor);
        doc.setLineWidth(0.5);
        doc.line(margin, 35, pageWidth - margin, 35);

        // Add receipt details
        doc.setFontSize(11);
        doc.setTextColor(...secondaryColor);

        // Prepare receipt data with proper string formatting
        const receiptData = [
            ["Invoice ID:", formatValue(transaction.invoiceID)],
            ["Reference ID:", formatValue(transaction.refID)],
            ["Transaction ID:", formatValue(transaction.transId)],
            ["Date:", formatValue(new Date(transaction.created_at).toLocaleString())],
            ["Amount:", formatValue(`$${parseFloat(transaction.amount).toFixed(2)}`)],
            ["Status:", formatValue(transaction.result)],
            ["Auth Code:", formatValue(transaction.authCode)],
            ["Card Type:", formatValue(transaction.accountType)],
            ["Card Number:", formatValue(`****${transaction.accountNumber.slice(-4)}`)],
            ["Client:", formatValue(clientData.clientDetails.companyName)],
            ["Client ID:", formatValue(clientData.clientDetails.clientID)],
            ["Salesperson:", formatValue(clientData.clientDetails.salesperson)]
        ];

        // Add data rows with improved styling
        let yPos = 45;

        // Add rounded rectangle background for the entire table
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(220, 220, 220);
        doc.roundedRect(
            margin - 5,
            yPos - 5,
            contentWidth + 10,
            receiptData.length * 12 + 10,
            3,
            3,
            "FD"
        );

        receiptData.forEach((row, index) => {
            // Add subtle background for even rows
            if (index % 2 === 0) {
                doc.setFillColor(...lightGray);
                doc.rect(margin, yPos - 4, contentWidth, 10, "F");
            }

            // Add label (bold)
            doc.setFont("helvetica", "bold");
            doc.text(formatValue(row[0]), margin + 5, yPos);

            // Add value (normal)
            doc.setFont("helvetica", "normal");
            doc.text(formatValue(row[1]), margin + 50, yPos);

            yPos += 12;
        });

        // Add footer with timestamp
        const footerY = yPos + 15;
        doc.setFontSize(8);
        doc.setTextColor(150, 150, 150);
        doc.setFont("helvetica", "italic");
        doc.text(
            `Receipt Generated on ${new Date().toLocaleString()}`,
            pageWidth / 2,
            footerY,
            { align: "center" }
        );

        // Generate timestamp for filename
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const filename = `receipt_${formatValue(transaction.transId)}_${timestamp}.pdf`;

        // Download PDF
        doc.save(filename);
        showToast("Receipt downloaded successfully");

    } catch (error) {
        console.error("Error generating PDF:", error);
        console.error("Transaction data:", transaction);
        showToast("Error generating PDF receipt");
    }
}
