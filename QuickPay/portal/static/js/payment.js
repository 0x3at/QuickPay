document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('payment-form');
  const cardNumberInput = document.getElementById('card-number');
  const expiryInput = document.getElementById('expiry');
  const cvvInput = document.getElementById('cvv');
  const amountInput = document.getElementById('amount');
  const submitButton = document.getElementById('submit-button');
  const resultContainer = document.getElementById('result');
  const resultIcon = document.getElementById('result-icon');
  const resultMessage = document.getElementById('result-message');
  
  // Receipt popup elements
  const receiptPopup = document.getElementById('receipt-popup');
  const closeReceiptBtn = document.getElementById('close-receipt');
  const downloadReceiptBtn = document.getElementById('print-receipt');
  
  // Format card number with spaces
  cardNumberInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    let formattedValue = '';
    
    for (let i = 0; i < value.length; i++) {
      if (i > 0 && i % 4 === 0) {
        formattedValue += ' ';
      }
      formattedValue += value[i];
    }
    
    e.target.value = formattedValue;
  });
  
  // Format expiry date (YYYY-MM)
  expiryInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/[^0-9-]/g, '');
    
    if (value.length > 4 && value[4] !== '-') {
      value = value.substring(0, 4) + '-' + value.substring(4, 6);
    }
    
    e.target.value = value;
  });
  
  // Only allow numbers for CVV
  cvvInput.addEventListener('input', function(e) {
    e.target.value = e.target.value.replace(/\D/g, '');
  });
  
  // Form validation
  function validateForm() {
    let isValid = true;
    
    // Validate card number (simple check for length)
    const cardNumber = cardNumberInput.value.replace(/\s+/g, '');
    if (cardNumber.length < 13 || cardNumber.length > 19 || !/^\d+$/.test(cardNumber)) {
      document.getElementById('card-number-error').classList.add('visible');
      cardNumberInput.classList.add('error');
      isValid = false;
    } else {
      document.getElementById('card-number-error').classList.remove('visible');
      cardNumberInput.classList.remove('error');
    }
    
    // Validate expiry date (YYYY-MM format)
    const expiry = expiryInput.value;
    const expiryPattern = /^([0-9]{4})-([0-9]{2})$/;
    if (!expiryPattern.test(expiry)) {
      document.getElementById('expiry-error').classList.add('visible');
      expiryInput.classList.add('error');
      isValid = false;
    } else {
      // Check if date is in the future
      const [year, month] = expiry.split('-');
      const expiryDate = new Date(parseInt(year), parseInt(month) - 1);
      const currentDate = new Date();
      
      if (expiryDate < currentDate) {
        document.getElementById('expiry-error').classList.add('visible');
        expiryInput.classList.add('error');
        isValid = false;
      } else {
        document.getElementById('expiry-error').classList.remove('visible');
        expiryInput.classList.remove('error');
      }
    }
    
    // Validate CVV
    const cvv = cvvInput.value;
    if (cvv.length < 3 || cvv.length > 4 || !/^\d+$/.test(cvv)) {
      document.getElementById('cvv-error').classList.add('visible');
      cvvInput.classList.add('error');
      isValid = false;
    } else {
      document.getElementById('cvv-error').classList.remove('visible');
      cvvInput.classList.remove('error');
    }

    // Validate amount
    const amount = amountInput.value;
    if (!amount || parseFloat(amount) <= 0) {
      document.getElementById('amount-error').classList.add('visible');
      amountInput.classList.add('error');
      isValid = false;
    } else {
      document.getElementById('amount-error').classList.remove('visible');
      amountInput.classList.remove('error');
    }
    
    return isValid;
  }
  
  // Handle form submission
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Hide previous results
    resultContainer.className = 'result';
    resultContainer.style.display = 'none';
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Show loading state
    submitButton.classList.add('loading');
    submitButton.disabled = true;
    
    // Prepare payload
    const payload = {
      number: cardNumberInput.value.replace(/\s+/g, ''),
      expiration: expiryInput.value,
      cvv: cvvInput.value,
      amount: amountInput.value,
      salesperson: document.getElementById('salesperson').value
    };
    
    try {
      // Make real API call to backend
      const response = await fetch('/process/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      // Remove loading state
      submitButton.classList.remove('loading');
      submitButton.disabled = false;
      
      // Show result
      if (data.result === 'Success' || data.result === 'Partial Success') {
        showSuccess('Payment processed successfully!');
        // Show receipt popup with transaction details
        showReceiptPopup(data);
        // Reset form on success
        form.reset();
      } else {
        showError(data.errorText || data.error || 'Payment processing failed. Please try again.');
      }
    } catch (error) {
      // Handle network errors
      submitButton.classList.remove('loading');
      submitButton.disabled = false;
      showError('Network error. Please check your connection and try again.');
      console.error('Error:', error);
    }
  });
  
  // Function to get CSRF token from cookies (for Django)
  function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  // Show success message
  function showSuccess(message) {
    resultContainer.className = 'result success';
    resultIcon.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
        <path class="checkmark" d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    resultMessage.textContent = message;
    resultContainer.style.display = 'flex';
  }
  
  // Show error message
  function showError(message) {
    resultContainer.className = 'result error';
    resultIcon.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
        <path d="M15 9L9 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    `;
    resultMessage.textContent = message;
    resultContainer.style.display = 'flex';
  }
  
  // Show receipt popup with transaction details
  function showReceiptPopup(data) {
    // Format date
    const dateObj = new Date(data.created_at);
    const formattedDate = dateObj.toLocaleString();
    
    // Populate receipt fields
    document.getElementById('receipt-invoiceID').textContent = data.invoiceID || 'N/A';
    document.getElementById('receipt-refID').textContent = data.refID || 'N/A';
    document.getElementById('receipt-amount').textContent = `$${data.amount}` || 'N/A';
    document.getElementById('receipt-salesperson').textContent = data.salesperson || 'N/A';
    document.getElementById('receipt-date').textContent = formattedDate;
    document.getElementById('receipt-transId').textContent = data.transId || 'N/A';
    document.getElementById('receipt-resultText').textContent = data.resultText || 'N/A';
    document.getElementById('receipt-authCode').textContent = data.authCode || 'N/A';
    document.getElementById('receipt-accountNumber').textContent = data.accountNumber || 'N/A';
    document.getElementById('receipt-accountType').textContent = data.accountType || 'N/A';
    
    // Show popup
    receiptPopup.classList.add('show');
    
    // Auto-hide after 10 seconds
    const autoHideTimer = setTimeout(() => {
      receiptPopup.classList.remove('show');
    }, 10000);
    
    // Close button event
    closeReceiptBtn.onclick = function() {
      receiptPopup.classList.remove('show');
      clearTimeout(autoHideTimer);
    };
    
    // Close on background click
    receiptPopup.onclick = function(e) {
      if (e.target === receiptPopup) {
        receiptPopup.classList.remove('show');
        clearTimeout(autoHideTimer);
      }
    };
    
    downloadReceiptBtn.onclick = function() {
      // Create PDF content using jsPDF
      const { jsPDF } = window.jspdf;
      // Create PDF content using jsPDF - fixed reference
      const doc = new jspdf.jsPDF();
      
      // Document settings
      const pageWidth = doc.internal.pageSize.width;
      const margin = 20;
      const contentWidth = pageWidth - (margin * 2);
      
      // Colors
      const primaryColor = [44, 62, 80];
      const secondaryColor = [52, 73, 94];
      const accentColor = [41, 128, 185];
      const lightGray = [245, 246, 250];
      
      // Add company logo (if exists) - otherwise use styled text
      try {
        // You can replace '/static/images/logo.png' with your actual logo path
        doc.addImage('/static/images/logo.png', 'PNG', margin, 10, 50, 20);
      } catch (e) {
        // Fallback to styled company name if logo fails to load
        doc.setFontSize(24);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(...accentColor);
        doc.text("QuickPay", margin, 20);
      }
      
      // Add receipt header
      doc.setFont("helvetica", "bold");
      doc.setFontSize(22);
      doc.setTextColor(...primaryColor);
      doc.text("Payment Receipt", pageWidth/2, 30, { align: "center" });
      
      // Add horizontal line
      doc.setDrawColor(...accentColor);
      doc.setLineWidth(0.5);
      doc.line(margin, 35, pageWidth - margin, 35);
      
      // Add receipt details
      doc.setFontSize(11);
      doc.setTextColor(...secondaryColor);
      
      const receiptData = [
        ['Invoice ID:', document.getElementById('receipt-invoiceID').textContent],
        ['Reference ID:', document.getElementById('receipt-refID').textContent],
        ['Amount:', document.getElementById('receipt-amount').textContent],
        ['Salesperson:', document.getElementById('receipt-salesperson').textContent],
        ['Date:', document.getElementById('receipt-date').textContent],
        ['Transaction ID:', document.getElementById('receipt-transId').textContent],
        ['Status:', document.getElementById('receipt-resultText').textContent],
        ['Auth Code:', document.getElementById('receipt-authCode').textContent],
        ['Account:', document.getElementById('receipt-accountNumber').textContent],
        ['Card Type:', document.getElementById('receipt-accountType').textContent]
      ];
    
      // Add data rows with improved styling
      let yPos = 45;
      
      // Add rounded rectangle background for the entire table
      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(220, 220, 220);
      doc.roundedRect(margin - 5, yPos - 10, contentWidth + 10, receiptData.length * 12 + 10, 3, 3, 'FD');
      
      receiptData.forEach((row, index) => {
        // Add subtle background for even rows
        if (index % 2 === 0) {
          doc.setFillColor(...lightGray);
          doc.rect(margin, yPos - 4, contentWidth, 10, 'F');
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
      doc.setFillColor(...accentColor);
      doc.roundedRect(margin, footerY - 8, contentWidth, 15, 3, 3, 'F');
      
      doc.setFontSize(11);
      doc.setTextColor(255, 255, 255);
      doc.setFont("helvetica", "bold");
      doc.text("Thank you for your business!", pageWidth/2, footerY, { align: "center" });
      
      // Add timestamp at bottom
      const currentDate = new Date().toLocaleDateString();
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.setFont("helvetica", "italic");
      doc.text(`Generated on ${currentDate}`, pageWidth/2, footerY + 15, { align: "center" });
      
      // Generate timestamp for filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      
      // Download PDF
      doc.save(`receipt_${timestamp}.pdf`);
    }; 
  }
});