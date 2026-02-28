// Change active state on click

// Login button interaction
//document.querySelector('.login-btn').addEventListener('click', () => {
  //  alert('Redirecting to Triwise Login...');
//});


/* function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    if (sidebar.style.width === "250px") {
        sidebar.style.width = "0";
    } else {
        sidebar.style.width = "250px";
    }
}

// Ensure the active class works on nav links
const navLinks = document.querySelectorAll('.nav-links a');
navLinks.forEach(link => {
    link.addEventListener('click', function() {
        navLinks.forEach(l => l.classList.remove('active'));
        this.classList.add('active');
    });
}); */

// Side nav functions
function openNav() {
    document.getElementById("sideNav").style.width = "250px";
    document.body.style.overflow = "hidden"; // prevent scrolling
}

function closeNav() {
    document.getElementById("sideNav").style.width = "0";
    document.body.style.overflow = "auto";
}

// Close side nav when clicking outside
document.addEventListener('click', function(event) {
    var sideNav = document.getElementById('sideNav');
    var menuBtn = document.querySelector('.menu-btn');
    if (sideNav && sideNav.style.width === '250px' && 
        !sideNav.contains(event.target) && 
        (!menuBtn || !menuBtn.contains(event.target))) {
        closeNav();
    }
});

// Optional: search functionality (placeholder)
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-container input');
    const searchIcon = document.querySelector('.search-icon');
    if (searchIcon) {
        searchIcon.addEventListener('click', function() {
            alert('Search for: ' + searchInput.value);
        });
    }
});

fetch('/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        window.location.href = `/order-confirmed/${data.order_id}`;
    } else {
        if (data.redirect) {
            alert(data.error);
            window.location.href = data.redirect;
        } else {
            alert('Error: ' + data.error);
        }
        this.textContent = 'Place Order';
        this.disabled = false;
    }
});


// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('show');
            
            // Change icon when menu is open
            const icon = this.querySelector('i');
            if (navLinks.classList.contains('show')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navLinks.contains(event.target) && !menuToggle.contains(event.target)) {
                navLinks.classList.remove('show');
                const icon = menuToggle.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
});

