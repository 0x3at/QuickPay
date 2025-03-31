// Add to the top of your file
let isLoading = false;
let clientData = null;

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
                <div class="payment-method-icon" style="color: #006fcf;">
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
    const transactionsTableBody = document.querySelector(
        "#transactions .data-table tbody"
    );
    transactionsTableBody.innerHTML = "";
    transactions.reverse();
    console.log(transactions);
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
                    <span class="status-badge ${transaction.result === "Success" ? "success" : "error"
            }">${transaction.result}</span>
                </td>
                <td>Card ending in ${transaction.accountNumber.slice(-4)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn" title="View Receipt" data-transaction-id="${transaction.transId}">
                            <i class="fa-solid fa-receipt"></i>
                        </button>
                    </div>
                </td>
            </tr>`;

        // TODO: Add refund functionality
        // ${transaction.result === 'Success' ? `
        // <button class="action-btn" title="Refund" data-transaction-id="${transaction.transId}">
        //     <i class="fa-solid fa-rotate-left"></i>
        // </button>` : ''}

        transactionsTableBody.innerHTML += transactionHTML;
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
            </div>
        `;

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

function showErrorMessage(message) {
    // Add error display logic - could be a toast notification or alert
    alert(message);
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

// Setup event listeners for the payment method modal
function setupPaymentMethodModal() {
    const addPaymentBtn = document.querySelector('.payment-methods-container .card-header .btn');
    const modal = document.getElementById('add-payment-modal');
    const closeBtn = document.getElementById('close-payment-modal');
    const cancelBtn = document.getElementById('cancel-payment');
    const submitBtn = document.getElementById('submit-payment');
    const form = document.getElementById('add-payment-form');

    // Open modal when Add Payment Method button is clicked
    if (addPaymentBtn) {
        addPaymentBtn.addEventListener('click', () => {
            modal.classList.add('show');
        });
    }

    // Close modal functions
    function closeModal() {
        modal.classList.remove('show');
        form.reset();
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
        alert('Please fill in all fields');
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
        
        // Show success message
        alert('Payment method added successfully');
        
    } catch (error) {
        console.error('Error adding payment method:', error);
        alert('Error adding payment method: ' + error.message);
        
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

    // Character counter for note textarea
    if (noteContent) {
        noteContent.addEventListener('input', function() {
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
        });
    }

    // Close modal functions
    function closeModal() {
        modal.classList.remove('show');
        form.reset();
        charCount.textContent = '0';
        charCount.style.color = '';
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
    const author = document.getElementById('note-author').value;
    const noteText = document.getElementById('note-content').value;

    // Basic validation
    if (!author || !noteText) {
        alert('Please fill in all fields');
        return;
    }

    // Get the client ID from the current client data
    const clientID = clientData.clientDetails.clientID;

    try {
        // Show loading state
        const submitBtn = document.getElementById('submit-note');
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
        submitBtn.disabled = true;

        // Create the note payload
        const payload = {
            clientID: clientID,
            salesperson: author,
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
        
        // Show success message
        alert('Note added successfully');
        
    } catch (error) {
        console.error('Error adding note:', error);
        alert('Error adding note: ' + error.message);
        
        // Reset button state
        const submitBtn = document.getElementById('submit-note');
        submitBtn.innerHTML = 'Add Note';
        submitBtn.disabled = false;
    }
}

// Initialize page
async function initClientDetailsPage() {
    setupTabSwitching();
    
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
}

// Setup payment form listeners
function setupPaymentFormListeners() {
    const quickPaymentForm = document.querySelector(".quick-payment-form");
    if (quickPaymentForm) {
        quickPaymentForm.addEventListener("submit", handleQuickPayment);
    }

    const quickChargeForm = document.getElementById("quick-charge-form");
    if (quickChargeForm) {
        quickChargeForm.addEventListener("submit", handleQuickCharge);
    }
}

// Handle quick payment submission
async function handleQuickPayment(event) {
    event.preventDefault();

    const amount = document.getElementById("quick-amount").value;
    const paymentMethodId = document.getElementById("quick-payment-method").value;

    if (!amount || parseFloat(amount) <= 0) {
        alert("Please enter a valid amount");
        return;
    }

    // Process payment logic here
    console.log("Processing quick payment:", { amount, paymentMethodId });
    // You would send this to your backend endpoint
}

// Handle quick charge submission
async function handleQuickCharge(event) {
    event.preventDefault();

    const amount = document.getElementById("amount").value;
    const paymentMethodId = document.getElementById("payment-method").value;
    const salesperson = document.getElementById("salesperson").value;

    if (!amount || parseFloat(amount) <= 0) {
        alert("Please enter a valid amount");
        return;
    }

    if (!salesperson) {
        alert("Please enter a salesperson name");
        return;
    }

    // Process charge logic here
    console.log("Processing charge:", { amount, paymentMethodId, salesperson });
    // You would send this to your backend endpoint
}

// Initialize the page when DOM is ready
document.addEventListener("DOMContentLoaded", initClientDetailsPage);
