document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("payment-form");
    const cardNumberInput = document.getElementById("card-number");
    const expiryInput = document.getElementById("expiry");
    const cvvInput = document.getElementById("cvv");
    const amountInput = document.getElementById("amount");
    const submitButton = document.getElementById("submit-button");
    const resultContainer = document.getElementById("result");
    const resultIcon = document.getElementById("result-icon");
    const resultMessage = document.getElementById("result-message");

    // Receipt popup elements
    const receiptPopup = document.getElementById("receipt-popup");
    const closeReceiptBtn = document.getElementById("close-receipt");
    const downloadReceiptBtn = document.getElementById("print-receipt");

    // Add new input references
    const firstNameInput = document.getElementById("firstName");
    const lastNameInput = document.getElementById("lastName");
    const companyNameInput = document.getElementById("companyName");
    const addressInput = document.getElementById("address");
    const zipCodeInput = document.getElementById("zipCode");
    const clientIDInput = document.getElementById("clientID");

    // Format card number with spaces
    cardNumberInput.addEventListener("input", function (e) {
        let value = e.target.value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
        let formattedValue = "";

        for (let i = 0; i < value.length; i++) {
            if (i > 0 && i % 4 === 0) {
                formattedValue += " ";
            }
            formattedValue += value[i];
        }

        e.target.value = formattedValue;
    });

    // Format expiry date (YYYY-MM)
    expiryInput.addEventListener("input", function (e) {
        let value = e.target.value.replace(/[^0-9-]/g, "");

        if (value.length > 4 && value[4] !== "-") {
            value = value.substring(0, 4) + "-" + value.substring(4, 6);
        }

        e.target.value = value;
    });

    // Only allow numbers for CVV
    cvvInput.addEventListener("input", function (e) {
        e.target.value = e.target.value.replace(/\D/g, "");
    });

    // Form validation
    function validateForm() {
        let isValid = true;

        // Validate card number (simple check for length)
        const cardNumber = cardNumberInput.value.replace(/\s+/g, "");
        if (
            cardNumber.length < 13 ||
            cardNumber.length > 19 ||
            !/^\d+$/.test(cardNumber)
        ) {
            document.getElementById("card-number-error").classList.add("visible");
            cardNumberInput.classList.add("error");
            isValid = false;
        } else {
            document.getElementById("card-number-error").classList.remove("visible");
            cardNumberInput.classList.remove("error");
        }

        // Validate expiry date (YYYY-MM format)
        const expiry = expiryInput.value;
        const expiryPattern = /^([0-9]{4})-([0-9]{2})$/;
        if (!expiryPattern.test(expiry)) {
            document.getElementById("expiry-error").classList.add("visible");
            expiryInput.classList.add("error");
            isValid = false;
        } else {
            // Check if date is in the future
            const [year, month] = expiry.split("-");
            const expiryDate = new Date(parseInt(year), parseInt(month) - 1);
            const currentDate = new Date();

            if (expiryDate < currentDate) {
                document.getElementById("expiry-error").classList.add("visible");
                expiryInput.classList.add("error");
                isValid = false;
            } else {
                document.getElementById("expiry-error").classList.remove("visible");
                expiryInput.classList.remove("error");
            }
        }

        // Validate CVV
        const cvv = cvvInput.value;
        if (cvv.length < 3 || cvv.length > 4 || !/^\d+$/.test(cvv)) {
            document.getElementById("cvv-error").classList.add("visible");
            cvvInput.classList.add("error");
            isValid = false;
        } else {
            document.getElementById("cvv-error").classList.remove("visible");
            cvvInput.classList.remove("error");
        }

        // Validate amount
        const amount = amountInput.value;
        if (!amount || parseFloat(amount) <= 0) {
            document.getElementById("amount-error").classList.add("visible");
            amountInput.classList.add("error");
            isValid = false;
        } else {
            document.getElementById("amount-error").classList.remove("visible");
            amountInput.classList.remove("error");
        }

        return isValid;
    }

    // Add these toast functions at the top of the file
    function showToast(message, duration = 3000) {
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

        // Show toast
        toast.classList.add('show');

        // Hide after duration
        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    function showErrorToast(message) {
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

        // Show toast
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
        }, 4000);
    }

    // Then update the showSuccess and showError functions to use the toast system
    function showSuccess(message) {
        showToast(message);
    }

    function showError(message) {
        showErrorToast(message);
    }

    // Handle form submission
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        // Validate form
        if (!validateForm()) {
            return;
        }

        // Show loading state
        submitButton.classList.add("loading");
        submitButton.disabled = true;

        // Prepare payload with additional fields
        const payload = {
            clientID: clientIDInput.value,
            amount: amountInput.value,
            salesperson: document.getElementById("salesperson").value,
            cardDetails: {
                cardNumber: cardNumberInput.value.replace(/\s+/g, ""),
                expirationDate: expiryInput.value,
                cardCode: cvvInput.value,
            },
            customerDetails: {
                firstName: firstNameInput.value,
                lastName: lastNameInput.value,
                companyName: companyNameInput.value,
                address: addressInput.value,
                zipCode: zipCodeInput.value,
            },
        };

        try {
            const response = await fetch("/quickpay/client/transactions/charge", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            // Remove loading state
            submitButton.classList.remove("loading");
            submitButton.disabled = false;

            // Check for success in the response structure
            if (data.success && data.transactionResult.result === "Success") {
                showToast("Payment processed successfully!");
                showReceiptPopup(data.transactionResult);
                form.reset();
            } else {
                showErrorToast(
                    data.transactionResult?.errorText || 
                    data.transactionResult?.error || 
                    "Payment processing failed. Please try again."
                );
            }
        } catch (error) {
            // Handle network errors
            submitButton.classList.remove("loading");
            submitButton.disabled = false;
            showErrorToast("Network error. Please check your connection and try again.");
            console.error("Error:", error);
        }
    });

    // Function to get CSRF token from cookies (for Django)
    function getCsrfToken() {
        const name = "csrftoken";
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Show receipt popup with transaction details
    function showReceiptPopup(data) {
        // Format date
        const dateObj = new Date(data.created_at);
        const formattedDate = dateObj.toLocaleString();

        // Populate receipt fields
        document.getElementById("receipt-invoiceID").textContent = data.invoiceID || "N/A";
        document.getElementById("receipt-refID").textContent = data.refID || "N/A";
        document.getElementById("receipt-amount").textContent = `$${data.amount}` || "N/A";
        document.getElementById("receipt-salesperson").textContent = data.salesperson || "N/A";
        document.getElementById("receipt-date").textContent = formattedDate;
        document.getElementById("receipt-transId").textContent = data.transId || "N/A";
        document.getElementById("receipt-resultText").textContent = data.resultText || "N/A";
        document.getElementById("receipt-authCode").textContent = data.authCode || "N/A";
        document.getElementById("receipt-accountNumber").textContent = data.accountNumber || "N/A";
        document.getElementById("receipt-accountType").textContent = data.accountType || "N/A";

        // Show popup
        receiptPopup.classList.add("show");

        // Auto-hide after 10 seconds
        const autoHideTimer = setTimeout(() => {
            receiptPopup.classList.remove("show");
        }, 10000);

        // Close button event
        closeReceiptBtn.onclick = function () {
            receiptPopup.classList.remove("show");
            clearTimeout(autoHideTimer);
        };

        // Close on background click
        receiptPopup.onclick = function (e) {
            if (e.target === receiptPopup) {
                receiptPopup.classList.remove("show");
                clearTimeout(autoHideTimer);
            }
        };

        downloadReceiptBtn.onclick = function () {
            // Create PDF content using jsPDF
            const { jsPDF } = window.jspdf;
            // Create PDF content using jsPDF - fixed reference
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

            // Add company logo (if exists) - otherwise use styled text
            try {
                // You can replace '/static/images/logo.png' with your actual logo path
                doc.addImage("/static/images/logo.png", "PNG", margin, 10, 50, 20);
            } catch (e) {
                // Fallback to styled company name if logo fails to load
                doc.setFontSize(24);
                doc.setFont("helvetica", "bold");
                doc.setTextColor(...accentColor);
                doc.text("", margin, 20);
            }

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

            const receiptData = [
                [
                    "Invoice ID:",
                    document.getElementById("receipt-invoiceID").textContent,
                ],
                ["Date:", document.getElementById("receipt-date").textContent],
                ["Amount:", document.getElementById("receipt-amount").textContent],
                ["Status:", document.getElementById("receipt-resultText").textContent],
                [
                    "Account:",
                    document.getElementById("receipt-accountNumber").textContent,
                ],
                [
                    "Card Type:",
                    document.getElementById("receipt-accountType").textContent,
                ],
                [
                    "Account Rep:",
                    document.getElementById("receipt-salesperson").textContent,
                ],
            ];

            // Add data rows with improved styling
            let yPos = 45;

            // Add rounded rectangle background for the entire table
            doc.setFillColor(255, 255, 255);
            doc.setDrawColor(220, 220, 220);
            doc.roundedRect(
                margin - 5,
                yPos - 10,
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
                doc.text(row[0], margin + 5, yPos);

                // Add value (normal)
                doc.setFont("helvetica", "normal");
                doc.text(row[1], margin + 50, yPos);

                yPos += 12;
            });

            // Add footer with rounded background
            const footerY = yPos + 15;

            // Add timestamp at bottom
            const currentDate = new Date().toLocaleDateString();
            doc.setFontSize(8);
            doc.setTextColor(150, 150, 150);
            doc.setFont("helvetica", "italic");
            doc.text(`Generated on ${currentDate}`, pageWidth / 2, footerY + 15, {
                align: "center",
            });

            // Generate timestamp for filename
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-");

            // Download PDF
            doc.save(`receipt_${timestamp}.pdf`);
        };
    }

    // Add this at the end of the DOMContentLoaded event handler
    // Hide any static toast messages on page load
    function hideStaticToastMessage() {
        console.log("Hiding static toast message");
        const toast = document.getElementById('toast-notification');
        if (toast) {
            toast.classList.remove('show');
            const toastMessage = document.getElementById('toast-message');
            if (toastMessage) {
                toastMessage.textContent = '';
            }
        }
    }

    // Call hideStaticToastMessage when page loads
    hideStaticToastMessage();
});
