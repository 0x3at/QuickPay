document.addEventListener("DOMContentLoaded", () => {
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
    const currentPage = window.location.pathname.split("/").pop() || "index.html"
    const sidebarItems = document.querySelectorAll(".sidebar-item")
  
    sidebarItems.forEach((item) => {
      const itemLink = item.querySelector("a").getAttribute("href")
      if (itemLink === currentPage) {
        item.classList.add("active")
      }
    })
  })
  
  