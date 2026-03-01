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


// Chat functionality
let socket = null;
let currentChatId = null;
let isAgent = false; // Set to true for support agents

function initChat() {
    // Connect to SocketIO server
    socket = io();
    
    // Socket event handlers
    socket.on('connect', function() {
        console.log('Connected to chat server');
        
        // If user is support agent, join as agent
        if (isAgent) {
            socket.emit('agent_join', {
                name: '{{ current_user.name if current_user.is_authenticated else "Support Agent" }}'
            });
        }
    });
    
    socket.on('chat_started', function(data) {
        currentChatId = data.chat_id;
        addSystemMessage(data.message);
        
        // Show chat input
        document.getElementById('preChatForm').style.display = 'none';
        document.getElementById('chatInputGroup').style.display = 'flex';
    });
    
    socket.on('agent_offline', function(data) {
        document.getElementById('chatInputArea').innerHTML = `
            <div class="offline-message">
                <p>${data.message}</p>
                <p>Email us at: <a href="mailto:${data.email}">${data.email}</a></p>
            </div>
        `;
    });
    
    socket.on('agent_assigned', function(data) {
        addSystemMessage(data.message);
        updateChatStatus('Connected with ' + data.agent_name);
    });
    
    socket.on('new_message', function(data) {
        addMessage(data);
    });
    
    socket.on('user_typing', function(data) {
        if (data.is_typing) {
            document.getElementById('typingIndicator').style.display = 'flex';
        } else {
            document.getElementById('typingIndicator').style.display = 'none';
        }
    });
    
    socket.on('chat_ended', function(data) {
        addSystemMessage(data.message);
        
        // Reset chat after 3 seconds
        setTimeout(() => {
            resetChat();
        }, 3000);
    });
}

function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    const isOpen = chatWindow.style.display !== 'none';
    
    if (isOpen) {
        chatWindow.style.display = 'none';
        // End chat if active
        if (currentChatId && socket) {
            socket.emit('end_chat', { chat_id: currentChatId });
        }
    } else {
        chatWindow.style.display = 'flex';
        chatWindow.style.flexDirection = 'column';
        
        // Initialize socket if not already
        if (!socket) {
            initChat();
        }
    }
}

function startChat() {
    const name = document.getElementById('chatName').value;
    const email = document.getElementById('chatEmail').value;
    
    if (!name || !email) {
        alert('Please enter your name and email');
        return;
    }
    
    socket.emit('start_chat', {
        name: name,
        email: email
    });
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message || !currentChatId) return;
    
    const messageData = {
        chat_id: currentChatId,
        message: message,
        sender: isAgent ? 'agent' : 'user'
    };
    
    socket.emit('send_message', messageData);
    
    // Clear input
    input.value = '';
    
    // Stop typing indicator
    socket.emit('typing', {
        chat_id: currentChatId,
        is_typing: false
    });
}

function addMessage(data) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.sender}`;
    
    messageDiv.innerHTML = `
        <div class="message-sender">${data.sender_name || (data.sender === 'user' ? 'You' : 'Support')}</div>
        <div class="message-content">${data.message}</div>
        <div class="message-time">${data.timestamp || new Date().toLocaleTimeString()}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addSystemMessage(message) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `<div class="message-content system">${message}</div>`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateChatStatus(status) {
    document.getElementById('chatStatus').textContent = status;
}

function resetChat() {
    currentChatId = null;
    document.getElementById('chatMessages').innerHTML = `
        <div class="welcome-message">
            <i class="fa-regular fa-headset"></i>
            <h4>Welcome to Triowise Support!</h4>
            <p>How can we help you today?</p>
        </div>
    `;
    document.getElementById('preChatForm').style.display = 'flex';
    document.getElementById('chatInputGroup').style.display = 'none';
    updateChatStatus('Online');
}

// Typing indicator
let typingTimer;
document.getElementById('chatInput')?.addEventListener('input', function() {
    if (!currentChatId) return;
    
    clearTimeout(typingTimer);
    
    socket.emit('typing', {
        chat_id: currentChatId,
        is_typing: true
    });
    
    typingTimer = setTimeout(() => {
        socket.emit('typing', {
            chat_id: currentChatId,
            is_typing: false
        });
    }, 1000);
});

// Initialize chat on page load if user is agent
document.addEventListener('DOMContentLoaded', function() {
    {% if current_user.is_authenticated and current_user.role == 'admin' %}
    isAgent = true;
    initChat();
    {% endif %}
});
