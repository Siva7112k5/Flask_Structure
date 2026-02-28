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

// Quick View Functions
function quickView(productId, event) {
    event.stopPropagation(); // Prevent card click
    
    const modal = document.getElementById('quickViewModal');
    const content = document.getElementById('quickViewContent');
    
    // Show modal with loading
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Fetch product details
    fetch(`/api/product/${productId}`)
        .then(response => response.json())
        .then(product => {
            content.innerHTML = `
                <div class="quick-view-grid">
                    <img src="${product.image}" alt="${product.name}">
                    <div class="quick-view-details">
                        <h3>${product.name}</h3>
                        
                        <div class="quick-view-rating">
                            <span class="stars">
                                ${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}
                            </span>
                            <span>(${product.reviews} reviews)</span>
                        </div>
                        
                        <div class="quick-view-price">
                            <span class="current">₹${product.price}</span>
                        </div>
                        
                        <p class="quick-view-description">${product.description}</p>
                        
                        <div class="quick-view-actions">
                            <button class="add-to-cart" onclick="addToCart(${product.id}); closeQuickView();">
                                <i class="fa-solid fa-cart-plus"></i> Add to Cart
                            </button>
                            <button class="view-details" onclick="window.location.href='/product/${product.id}'">
                                View Details
                            </button>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            content.innerHTML = '<div class="error">Failed to load product details</div>';
        });
}

function closeQuickView() {
    document.getElementById('quickViewModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('quickViewModal');
    if (event.target === modal) {
        closeQuickView();
    }
});

// Handle escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeQuickView();
    }
});

// Toggle wishlist function
function toggleWishlist(productId, event) {
    event.stopPropagation(); // Prevent card click
    
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    
    // Check if already in wishlist
    const isActive = btn.classList.contains('active');
    
    // Determine endpoint and method
    const endpoint = isActive ? 
        `/api/wishlist/remove/${productId}` : 
        `/api/wishlist/add/${productId}`;
    
    // Show loading state
    btn.style.pointerEvents = 'none';
    icon.className = 'fa-solid fa-spinner fa-spin';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Toggle active state
            btn.classList.toggle('active');
            
            // Update icon
            if (btn.classList.contains('active')) {
                icon.className = 'fa-solid fa-heart';
                showToast('Added to wishlist! ❤️');
            } else {
                icon.className = 'fa-regular fa-heart';
                showToast('Removed from wishlist');
            }
            
            // Update wishlist count in navbar (if exists)
            const wishlistCount = document.querySelector('.wishlist-count-badge');
            if (wishlistCount) {
                wishlistCount.textContent = data.wishlist_count;
            }
        } else {
            showToast(data.message || 'Error updating wishlist', 'error');
            // Revert icon
            icon.className = isActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to update wishlist', 'error');
        // Revert icon
        icon.className = isActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
    })
    .finally(() => {
        btn.style.pointerEvents = 'auto';
    });
}