document.addEventListener("DOMContentLoaded", async () => {
    // Sidebar toggle functionality
    const sidebar = document.getElementById("sidebar")
    const sidebarToggle = document.getElementById("sidebar-toggle")
    const mobileSidebarToggle = document.getElementById("mobile-sidebar-toggle")
  
    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed")
  
        // Save sidebar state to localStorage
        localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"))
      })
    }
  
    if (mobileSidebarToggle) {
      mobileSidebarToggle.addEventListener("click", () => {
        sidebar.classList.toggle("show")
      })
    }
  
    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", (event) => {
      if (
        window.innerWidth <= 768 &&
        sidebar.classList.contains("show") &&
        !sidebar.contains(event.target) &&
        event.target !== mobileSidebarToggle
      ) {
        sidebar.classList.remove("show")
      }
    })
  
    // Load sidebar state from localStorage
    const sidebarCollapsed = localStorage.getItem("sidebarCollapsed") === "true"
    if (sidebarCollapsed) {
      sidebar.classList.add("collapsed")
    }
  
    // Handle window resize
    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) {
        sidebar.classList.remove("show")
      }
    })
  
    // Set active sidebar item based on current page
    const currentPath = window.location.pathname;
    const sidebarItems = document.querySelectorAll(".sidebar-item");
  
    sidebarItems.forEach((item) => {
      const itemLink = item.querySelector("a").getAttribute("href");
      // Remove active class first
      item.classList.remove("active");
      
      // Check if current path includes the href path (excluding the root path case)
      if (itemLink === "/quickpay/" && currentPath === "/quickpay/") {
          item.classList.add("active");
      } else if (itemLink !== "/quickpay/" && currentPath.includes(itemLink)) {
          item.classList.add("active");
      }
    });
  
    // Fetch and populate client table
    const clientTableBody = document.querySelector("#clients-table-body");
    if (clientTableBody) {  // Only proceed if the table exists
        try {
            const response = await fetch('/quickpay/client/get');
            const data = await response.json();
            
            if (data.clients && Array.isArray(data.clients)) {
              // if (data.rows.length === 0) {
              //   clientTableBody.innerHTML = `
              //     <tr>
              //       <td colspan="5" style="text-align: center; padding: 2rem; color: var(--muted);">
              //         <i class="fa-solid fa-users-slash" style="font-size: 2rem; margin-bottom: 1rem;"></i>
              //         <p>No clients found...</p>
              //       </td>
              //     </tr>
              //   `;
              // } else {
                clientTableBody.innerHTML = data.clients.map(client => `
                  <tr>
                    <td><span class="badge" style="background-color: #60aaff5c; color:rgb(0, 0, 0);">${client.clientID}</span></td>
                    <td>${client.companyName}</td>
                    <td class="hide-mobile">${client.email}</td>
                    <td class="hide-mobile">${new Date(client.createdAt).toLocaleDateString()}</td>
                    <td class="hide-mobile">${client.salesperson}</td>
                    <td>
                      <div class="action-buttons">
                        <button class="action-btn" title="View Client" onclick="viewClient('${client.clientID}')">
                          <i class="fa-solid fa-eye"></i>
                        </button>
                        <button class="action-btn" title="Edit Client" onclick="editClient('${client.clientID}')">
                          <i class="fa-solid fa-edit"></i>
                        </button>
                        <button class="action-btn" title="New Payment" onclick="newPayment('${client.clientID}')">
                          <i class="fa-solid fa-credit-card"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                `).join('');
              // }
            }
        } catch (error) {
            console.error('Error fetching clients:', error);
            clientTableBody.innerHTML = `
              <tr>
                <td colspan="5" class="error-message">
                  Error loading clients. Please try again later.
                </td>
              </tr>
            `;
        }
    }
  })
  
  // Handler functions for the action buttons
  function viewClient(clientId) {
    console.log('View client:', clientId);
    // Implement view client functionality
  }
  
  function editClient(clientId) {
    console.log('Edit client:', clientId);
    // Implement edit client functionality
  }
  
  function newPayment(clientId) {
    console.log('New payment for client:', clientId);
    // Implement new payment functionality
  }
  
  