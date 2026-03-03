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
/* 
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
} */


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

// ========== VOICE SEARCH FUNCTIONALITY ==========

// ========== ENHANCED VOICE SEARCH FUNCTIONALITY ==========

let recognition = null;
let isListening = false;
let mediaStream = null;

// Check microphone availability on page load
document.addEventListener('DOMContentLoaded', function() {
    checkMicrophoneSupport();
});

function checkMicrophoneSupport() {
    const voiceBtn = document.getElementById('voiceSearchBtn');
    
    // Check browser support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        voiceBtn.style.opacity = '0.5';
        voiceBtn.title = 'Voice search not supported in your browser';
        voiceBtn.disabled = true;
        console.warn('Speech recognition not supported');
        return false;
    }
    
    // Check if we can access microphone
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        navigator.mediaDevices.enumerateDevices()
            .then(function(devices) {
                const hasMicrophone = devices.some(device => device.kind === 'audioinput');
                if (!hasMicrophone) {
                    voiceBtn.style.opacity = '0.5';
                    voiceBtn.title = 'No microphone found';
                    voiceBtn.disabled = true;
                    console.warn('No microphone found');
                }
            })
            .catch(function(err) {
                console.log('Could not enumerate devices:', err);
            });
    }
    
    return true;
}

function requestMicrophonePermission() {
    return new Promise((resolve, reject) => {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(function(stream) {
                    mediaStream = stream;
                    // Stop all tracks immediately - we just needed permission
                    stream.getTracks().forEach(track => track.stop());
                    resolve(true);
                })
                .catch(function(err) {
                    console.error('Microphone permission error:', err);
                    let errorMessage = '';
                    
                    switch(err.name) {
                        case 'NotAllowedError':
                        case 'PermissionDeniedError':
                            errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings.';
                            break;
                        case 'NotFoundError':
                        case 'DevicesNotFoundError':
                            errorMessage = 'No microphone found. Please connect a microphone.';
                            break;
                        case 'NotReadableError':
                        case 'TrackStartError':
                            errorMessage = 'Microphone is busy. Please close other apps using it.';
                            break;
                        default:
                            errorMessage = 'Could not access microphone. Error: ' + err.message;
                    }
                    
                    reject(errorMessage);
                });
        } else {
            reject('Your browser does not support microphone access');
        }
    });
}

async function startVoiceSearch() {
    const voiceBtn = document.getElementById('voiceSearchBtn');
    const voicePopup = document.getElementById('voicePopup');
    const voiceTranscript = document.getElementById('voiceTranscript');
    
    // Reset transcript
    voiceTranscript.textContent = '';
    
    try {
        // First request microphone permission
        await requestMicrophonePermission();
        
        // Show popup
        voicePopup.classList.add('active');
        voiceBtn.classList.add('listening');
        isListening = true;
        
        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        // Configure recognition
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;
        
        // Handle results
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            voiceTranscript.textContent = transcript;
            
            // If final result, perform search
            if (event.results[0].isFinal) {
                performVoiceSearch(transcript);
            }
        };
        
        // Handle errors
        recognition.onerror = function(event) {
            console.error('Voice recognition error:', event.error);
            let errorMessage = 'An error occurred. ';
            
            switch(event.error) {
                case 'no-speech':
                    errorMessage = 'No speech detected. Please try again.';
                    break;
                case 'audio-capture':
                    errorMessage = 'No microphone found. Please check your microphone.';
                    break;
                case 'not-allowed':
                    errorMessage = 'Microphone access denied. Please allow microphone access.';
                    break;
                case 'network':
                    errorMessage = 'Network error. Please check your internet connection.';
                    break;
                case 'aborted':
                    errorMessage = 'Voice search was aborted.';
                    break;
                default:
                    errorMessage = 'Error: ' + event.error;
            }
            
            showVoiceError(errorMessage);
            closeVoicePopup();
        };
        
        // Handle end of speech
        recognition.onend = function() {
            if (isListening) {
                // If we haven't gotten a result yet, wait a bit then close
                setTimeout(() => {
                    if (isListening) {
                        if (voiceTranscript.textContent) {
                            performVoiceSearch(voiceTranscript.textContent);
                        } else {
                            closeVoicePopup();
                        }
                    }
                }, 2000);
            }
        };
        
        // Start listening
        recognition.start();
        
    } catch (error) {
        showVoiceError(error);
        closeVoicePopup();
    }
}

function showVoiceError(message) {
    const voicePopup = document.getElementById('voicePopup');
    const voiceTranscript = document.getElementById('voiceTranscript');
    
    voiceTranscript.innerHTML = `
        <div style="color: #dc3545; padding: 10px;">
            <i class="fa-solid fa-circle-exclamation"></i>
            <p style="margin-top: 10px;">${message}</p>
        </div>
    `;
    
    // Auto close after 3 seconds
    setTimeout(() => {
        closeVoicePopup();
    }, 3000);
}

function performVoiceSearch(query) {
    if (query && query.trim()) {
        const voiceTranscript = document.getElementById('voiceTranscript');
        voiceTranscript.innerHTML = `
            <div style="color: #28a745;">
                <i class="fa-solid fa-check-circle"></i>
                <p style="margin-top: 10px;">Searching for: "${query}"</p>
            </div>
        `;
        
        // Close popup after short delay
        setTimeout(() => {
            closeVoicePopup();
            // Redirect to search results
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }, 1500);
    }
}

function closeVoicePopup() {
    const voicePopup = document.getElementById('voicePopup');
    const voiceBtn = document.getElementById('voiceSearchBtn');
    
    voicePopup.classList.remove('active');
    voiceBtn.classList.remove('listening');
    
    if (recognition && isListening) {
        try {
            recognition.stop();
        } catch (e) {
            console.log('Error stopping recognition:', e);
        }
    }
    
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    isListening = false;
}

// Close voice popup when clicking outside
document.addEventListener('click', function(event) {
    const popup = document.getElementById('voicePopup');
    const voiceBtn = document.getElementById('voiceSearchBtn');
    
    if (popup.classList.contains('active') && 
        !popup.contains(event.target) && 
        event.target !== voiceBtn && 
        !voiceBtn.contains(event.target)) {
        closeVoicePopup();
    }
});

// Handle escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && document.getElementById('voicePopup').classList.contains('active')) {
        closeVoicePopup();
    }
});

function testMicrophone() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                alert('✅ Microphone working!');
                stream.getTracks().forEach(track => track.stop());
            })
            .catch(function(err) {
                alert('❌ Microphone error: ' + err.message);
            });
    } else {
        alert('❌ MediaDevices not supported');
    }
}

// Uncomment to auto-test on page load (for debugging)
// setTimeout(testMicrophone, 1000);

function getBrowserInstructions() {
    const userAgent = navigator.userAgent;
    let instructions = '';
    
    if (userAgent.indexOf("Chrome") > -1) {
        instructions = `
            <h4>Chrome Instructions:</h4>
            <ol>
                <li>Click the lock/info icon in the address bar</li>
                <li>Find "Microphone" in the permissions list</li>
                <li>Change it to "Allow"</li>
                <li>Refresh the page</li>
            </ol>
        `;
    } else if (userAgent.indexOf("Firefox") > -1) {
        instructions = `
            <h4>Firefox Instructions:</h4>
            <ol>
                <li>Click the lock/info icon in the address bar</li>
                <li>Find "Microphone" in the permissions list</li>
                <li>Change it to "Allow"</li>
                <li>Refresh the page</li>
            </ol>
        `;
    } else if (userAgent.indexOf("Edg") > -1) {
        instructions = `
            <h4>Edge Instructions:</h4>
            <ol>
                <li>Click the lock/info icon in the address bar</li>
                <li>Find "Microphone" in the permissions list</li>
                <li>Change it to "Allow"</li>
                <li>Refresh the page</li>
            </ol>
        `;
    } else if (userAgent.indexOf("Safari") > -1) {
        instructions = `
            <h4>Safari Instructions:</h4>
            <ol>
                <li>Go to Safari > Preferences > Websites</li>
                <li>Find "Microphone" in the left sidebar</li>
                <li>Change permission for this site to "Allow"</li>
                <li>Refresh the page</li>
            </ol>
        `;
    }
    
    return instructions;
}

// Simplified working version
function simpleVoiceSearch() {
    if (!('webkitSpeechRecognition' in window)) {
        alert('Voice search is only supported in Chrome, Edge, and Safari');
        return;
    }
    
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    
    recognition.onstart = function() {
        console.log('Voice recognition started');
        document.getElementById('voiceSearchBtn').classList.add('listening');
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Heard:', transcript);
        window.location.href = `/search?q=${encodeURIComponent(transcript)}`;
    };
    
    recognition.onerror = function(event) {
        console.error('Error:', event.error);
        alert('Error: ' + event.error + '. Please check microphone permissions.');
        document.getElementById('voiceSearchBtn').classList.remove('listening');
    };
    
    recognition.start();
}

// Replace your startVoiceSearch with this simpler version for testing
function startVoiceSearch() {
    simpleVoiceSearch();
}

/* // Fix for login popup - make sure this code exists
document.addEventListener('DOMContentLoaded', function() {
    const popup = document.getElementById('loginPopup');
    if (!popup) return;
    
    const userAuthenticated = document.body.dataset.userAuthenticated === 'true';
    
    if (!userAuthenticated) {
        const popupClosed = sessionStorage.getItem('popupClosed');
        console.log('Popup closed before:', popupClosed);
        
        if (!popupClosed) {
            console.log("Showing popup in 1 second");
            setTimeout(function() {
                showLoginPopup();
            }, 1000);
        } else {
            console.log("Popup was closed before - not showing");
        }
    } else {
        console.log("User is logged in - not showing popup");
    }
});
 */


/* function toggleWishlist(productId, event) {
    event.stopPropagation(); // Prevent card click
    
    // Check if user is logged in first
    const isAuthenticated = document.body.dataset.userAuthenticated === 'true';
    
    if (!isAuthenticated) {
        showToast('Please login to add items to wishlist', 'error');
        // Show login popup
        if (typeof showLoginPopup === 'function') {
            showLoginPopup();
        }
        return;
    }
    
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    const isActive = btn.classList.contains('active');
    
    // Determine endpoint based on current state
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
            
            // Update wishlist count in navbar
            const badge = document.querySelector('.wishlist-count-badge');
            if (badge) {
                badge.textContent = data.wishlist_count;
                badge.style.display = data.wishlist_count > 0 ? 'flex' : 'none';
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
        icon.className = isActive ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
    })
    .finally(() => {
        btn.style.pointerEvents = 'auto';
    });
}

// Add this to your JavaScript file (at the bottom or in a script tag)
function toggleWishlist(button) {
    event.preventDefault(); // Prevent any default button behavior
    
    // Toggle between regular and solid heart icon
    const icon = button.querySelector('i');
    if (icon.classList.contains('fa-regular')) {
        icon.classList.remove('fa-regular');
        icon.classList.add('fa-solid');
        icon.style.color = '#ff4444'; // Red color for wishlisted items
    } else {
        icon.classList.remove('fa-solid');
        icon.classList.add('fa-regular');
        icon.style.color = ''; // Reset to default color
    }
    
    // Optional: Save to localStorage
    const productCard = button.closest('.product-card');
    if (productCard) {
        const productName = productCard.querySelector('h3')?.textContent;
        console.log(`Wishlist toggled for: ${productName}`);
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fa-solid ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}


// Test if the API is working
fetch('/api/wishlist/add/1', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
})
.then(res => res.json())
.then(data => console.log('API Response:', data))
.catch(err => console.error('API Error:', err));

 */