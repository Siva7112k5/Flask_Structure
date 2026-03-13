// ========== TRIOWISE MAIN JAVASCRIPT - CLEAN VERSION ==========

// ========== SIDE NAVIGATION FUNCTIONS ==========
function openNav() {
    document.getElementById("sideNav").style.width = "250px";
    document.body.style.overflow = "hidden";
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

// ========== MOBILE MENU TOGGLE ==========
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('show');
            
            const icon = this.querySelector('i');
            if (navLinks.classList.contains('show')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
        
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

// ========== QUICK VIEW FUNCTIONALITY ==========
let quickViewModal = null;

function quickView(productId, event) {
    if (event) event.stopPropagation();
    
    if (!quickViewModal) {
        createQuickViewModal();
        quickViewModal = document.getElementById('quickViewModal');
    }
    
    const content = document.getElementById('quickViewContent');
    if (!content) return;
    
    quickViewModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    content.innerHTML = `
        <div class="quick-view-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <p>Loading product details...</p>
        </div>
    `;
    
    fetch(`/api/product/${productId}`)
        .then(response => {
            if (!response.ok) throw new Error('Product not found');
            return response.json();
        })
        .then(product => {
            content.innerHTML = `
                <div class="quick-view-grid">
                    <div class="quick-view-image">
                        <img src="${product.image}" alt="${product.name}">
                    </div>
                    <div class="quick-view-details">
                        <h2>${product.name}</h2>
                        <div class="quick-view-rating">
                            <span class="stars">${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}</span>
                            <span>(${product.reviews} reviews)</span>
                        </div>
                        <div class="quick-view-price">
                            <span class="current-price">₹${product.price}</span>
                            ${product.compare_price ? `<span class="original-price">₹${product.compare_price}</span>` : ''}
                        </div>
                        <p class="quick-view-description">${product.description || product.short_description || 'No description available.'}</p>
                        <div class="quick-view-actions">
                            <button class="quick-view-add-to-cart" onclick="addToCart(${product.id})">
                                <i class="fa-solid fa-cart-plus"></i> Add to Cart
                            </button>
                            <button class="quick-view-details-btn" onclick="window.location.href='/product/${product.id}'">
                                View Full Details
                            </button>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(() => {
            content.innerHTML = `
                <div class="quick-view-error">
                    <i class="fa-solid fa-exclamation-circle"></i>
                    <p>Failed to load product details.</p>
                    <button onclick="closeQuickView()">Close</button>
                </div>
            `;
        });
}

function createQuickViewModal() {
    const modalHTML = `
        <div id="quickViewModal" class="quick-view-modal" style="display: none;">
            <div class="quick-view-modal-content">
                <div class="quick-view-modal-header">
                    <h3>Quick View</h3>
                    <button class="quick-view-close" onclick="closeQuickView()">&times;</button>
                </div>
                <div class="quick-view-modal-body" id="quickViewContent"></div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeQuickView() {
    const modal = document.getElementById('quickViewModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('quickViewModal');
    if (modal && modal.style.display === 'flex' && event.target === modal) {
        closeQuickView();
    }
});

// Handle escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeQuickView();
    }
});

// ========== TOAST NOTIFICATION SYSTEM ==========
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        padding: 12px 24px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    toast.innerHTML = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ========== WISHLIST FUNCTIONALITY (SINGLE VERSION) ==========
function toggleWishlist(productId, event) {
    if (event) event.stopPropagation();
    
    // Check if user is logged in
    const isAuthenticated = document.body.dataset.userAuthenticated === 'true';
    
    if (!isAuthenticated) {
        showToast('Please login to add items to wishlist', 'error');
        if (typeof showLoginPopup === 'function') {
            showLoginPopup();
        }
        return;
    }
    
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    const isActive = btn.classList.contains('active');
    
    // Determine endpoint
    const endpoint = isActive ? 
        `/api/wishlist/remove/${productId}` : 
        `/api/wishlist/add/${productId}`;
    
    // Show loading state
    btn.style.pointerEvents = 'none';
    icon.className = 'fa-solid fa-spinner fa-spin';
    
    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            btn.classList.toggle('active');
            
            if (btn.classList.contains('active')) {
                icon.className = 'fa-solid fa-heart';
                showToast('Added to wishlist! ❤️');
            } else {
                icon.className = 'fa-regular fa-heart';
                showToast('Removed from wishlist');
            }
            
            const badge = document.querySelector('.wishlist-count-badge');
            if (badge) {
                badge.textContent = data.wishlist_count;
                badge.style.display = data.wishlist_count > 0 ? 'flex' : 'none';
            }
        } else {
            showToast(data.message || 'Error updating wishlist', 'error');
            icon.className = isActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Failed to update wishlist', 'error');
        icon.className = isActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
    })
    .finally(() => {
        btn.style.pointerEvents = 'auto';
    });
}

// ========== VOICE SEARCH (SINGLE WORKING VERSION) ==========
function startVoiceSearch() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Voice search is only supported in Chrome, Edge, and Safari');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    
    const voiceBtn = document.getElementById('voiceSearchBtn');
    
    recognition.onstart = function() {
        console.log('Voice recognition started');
        voiceBtn.classList.add('listening');
        voiceBtn.style.color = '#dc3545';
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Heard:', transcript);
        window.location.href = `/search?q=${encodeURIComponent(transcript)}`;
    };
    
    recognition.onerror = function(event) {
        console.error('Error:', event.error);
        alert('Error: ' + event.error + '. Please check microphone permissions.');
        voiceBtn.classList.remove('listening');
        voiceBtn.style.color = '';
    };
    
    recognition.onend = function() {
        voiceBtn.classList.remove('listening');
        voiceBtn.style.color = '';
    };
    
    recognition.start();
}

// ========== MOBILE SPECS GENERATOR ==========
document.addEventListener('DOMContentLoaded', function() {
    // Only run on mobile
    if (window.innerWidth <= 768) {
        const productCards = document.querySelectorAll('.product-card');
        
        productCards.forEach(card => {
            if (!card.querySelector('.key-specs')) {
                const productInfo = card.querySelector('.product-info');
                const price = card.querySelector('.price');
                
                const specsDiv = document.createElement('div');
                specsDiv.className = 'key-specs';
                
                const productName = card.querySelector('.product-info h3')?.textContent || '';
                const category = getCategoryFromProduct(productName);
                
                if (category === 'mobile') {
                    specsDiv.innerHTML = `
                        <span class="spec-chip"><i class="fa-regular fa-microchip"></i> 8 GB RAM</span>
                        <span class="spec-chip"><i class="fa-regular fa-database"></i> 128 GB ROM</span>
                        <span class="spec-chip"><i class="fa-regular fa-battery-full"></i> 5000 mAh</span>
                    `;
                } else if (category === 'laptop') {
                    specsDiv.innerHTML = `
                        <span class="spec-chip"><i class="fa-regular fa-microchip"></i> 16 GB RAM</span>
                        <span class="spec-chip"><i class="fa-regular fa-database"></i> 512 GB SSD</span>
                        <span class="spec-chip"><i class="fa-regular fa-cpu"></i> i7</span>
                    `;
                }
                
                if (price && price.nextSibling) {
                    price.parentNode.insertBefore(specsDiv, price.nextSibling);
                } else if (price) {
                    price.parentNode.appendChild(specsDiv);
                }
            }
        });
    }
});

function getCategoryFromProduct(productName) {
    productName = productName.toLowerCase();
    if (productName.includes('iphone') || productName.includes('samsung') || productName.includes('redmi') || productName.includes('oneplus') || productName.includes('motorola')) {
        return 'mobile';
    } else if (productName.includes('laptop') || productName.includes('macbook') || productName.includes('dell') || productName.includes('hp')) {
        return 'laptop';
    }
    return 'other';
}

// ========== CHAT FUNCTIONALITY ==========
let socket = null;
let currentChatId = null;
let isAgent = false;

function initChat() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to chat server');
        if (isAgent) {
            socket.emit('agent_join', {
                name: '{{ current_user.name if current_user.is_authenticated else "Support Agent" }}'
            });
        }
    });
    
    socket.on('chat_started', function(data) {
        currentChatId = data.chat_id;
        addSystemMessage(data.message);
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
        document.getElementById('chatStatus').textContent = 'Connected with ' + data.agent_name;
    });
    
    socket.on('new_message', function(data) {
        addMessage(data);
    });
    
    socket.on('chat_ended', function(data) {
        addSystemMessage(data.message);
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
        if (currentChatId && socket) {
            socket.emit('end_chat', { chat_id: currentChatId });
        }
    } else {
        chatWindow.style.display = 'flex';
        chatWindow.style.flexDirection = 'column';
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
    
    socket.emit('start_chat', { name, email });
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message || !currentChatId) return;
    
    socket.emit('send_message', {
        chat_id: currentChatId,
        message: message,
        sender: isAgent ? 'agent' : 'user'
    });
    
    input.value = '';
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
    document.getElementById('chatStatus').textContent = 'Online';
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
/* 
// Show loader on page navigation
document.addEventListener('DOMContentLoaded', function() {
    const loader = document.getElementById('pageLoader');
    
    // Hide loader when page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(function() {
            if (loader) loader.classList.add('hidden');
        }, 500); // Small delay for smooth transition
    });
    
    // Show loader when navigating to another page
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't show loader for links that open in new tab or are external
            if (this.target === '_blank' || this.hostname !== window.location.hostname) return;
            
            // Don't show loader for hash links
            if (this.hash && this.pathname === window.location.pathname) return;
            
            loader.classList.remove('hidden');
        });
    });
    
    // Show loader on form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            loader.classList.remove('hidden');
        });
    });
});

// Manual control functions
function showLoader() {
    document.getElementById('pageLoader')?.classList.remove('hidden');
}

function hideLoader() {
    document.getElementById('pageLoader')?.classList.add('hidden');
} */