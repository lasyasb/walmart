// Main application JavaScript with Firebase integration
import {
    auth,
    db,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    collection,
    addDoc,
    getDocs,
    getDoc,
    setDoc,
    deleteDoc,
    query,
    where,
    doc
} from './firebase.js';

// Global state
let currentUser = null;
let currentBudget = 0;
let personalCart = [];
let sharedCart = [];
let currentSharedSession = null;
let allProducts = [];
let filteredProducts = [];

// DOM elements
const welcomeSection = document.getElementById('welcomeSection');
const appContent = document.getElementById('appContent');
const authButton = document.getElementById('authButton');
const userEmail = document.getElementById('userEmail');
const loadingOverlay = document.getElementById('loadingOverlay');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();

    // Listen for auth state changes
    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        updateUIForAuthState(user);
        if (user) {
            loadUserData();
        }
        // Load all products regardless of auth state
        loadAllProducts();
    });
});

function setupEventListeners() {
    // Auth form handlers
    document.getElementById('signinForm').addEventListener('submit', handleSignIn);
    document.getElementById('signupForm').addEventListener('submit', handleSignUp);
    document.getElementById('authButton').addEventListener('click', handleAuthButtonClick);

    // Budget handlers
    document.getElementById('setBudgetBtn').addEventListener('click', setBudget);

    // Product browsing handlers
    document.getElementById('categoryFilter').addEventListener('change', filterProducts);
    document.getElementById('productSearch').addEventListener('input', searchProducts);
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);

    // Recommendation handlers
    document.getElementById('getRecommendationsBtn').addEventListener('click', getRecommendations);

    // Shared cart handlers
    document.getElementById('createSharedCartBtn').addEventListener('click', createSharedCart);
    document.getElementById('joinSharedCartBtn').addEventListener('click', joinSharedCart);
    document.getElementById('leaveSharedCartBtn').addEventListener('click', leaveSharedCart);
    document.getElementById('clearSharedCartBtn').addEventListener('click', clearSharedCart);
}

// Authentication functions
async function handleSignIn(e) {
    e.preventDefault();
    const email = document.getElementById('signinEmail').value;
    const password = document.getElementById('signinPassword').value;

    try {
        showLoading(true);
        await signInWithEmailAndPassword(auth, email, password);
        bootstrap.Modal.getInstance(document.getElementById('authModal')).hide();
        showAlert('Welcome back!', 'success');
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function handleSignUp(e) {
    e.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'danger');
        return;
    }

    try {
        showLoading(true);
        await createUserWithEmailAndPassword(auth, email, password);
        bootstrap.Modal.getInstance(document.getElementById('authModal')).hide();
        showAlert('Account created successfully!', 'success');
    } catch (error) {
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function handleAuthButtonClick() {
    if (currentUser) {
        try {
            await signOut(auth);
            showAlert('Signed out successfully', 'success');
        } catch (error) {
            showAlert(error.message, 'danger');
        }
    } else {
        const authModal = new bootstrap.Modal(document.getElementById('authModal'));
        authModal.show();
    }
}

function updateUIForAuthState(user) {
    if (user) {
        welcomeSection.style.display = 'none';
        appContent.style.display = 'block';
        authButton.innerHTML = '<i class="fas fa-sign-out-alt me-1"></i> Sign Out';
        userEmail.textContent = user.email;
    } else {
        welcomeSection.style.display = 'block';
        appContent.style.display = 'none';
        authButton.innerHTML = '<i class="fas fa-sign-in-alt me-1"></i> Sign In';
        userEmail.textContent = '';
        // Reset state
        currentBudget = 0;
        personalCart = [];
        sharedCart = [];
    }
}

// Budget functions
async function setBudget() {
    const budgetInput = document.getElementById('budgetInput');
    const budget = parseFloat(budgetInput.value) || 0;

    if (budget <= 0) {
        showAlert('Please enter a valid budget amount', 'warning');
        return;
    }

    try {
        showLoading(true);
        await setDoc(doc(db, 'budgets', currentUser.uid), {
            budget: budget,
            email: currentUser.email,
            updatedAt: new Date()
        });

        currentBudget = budget;
        updateBudgetDisplay();
        budgetInput.value = '';
        showAlert('Budget set successfully!', 'success');
    } catch (error) {
        showAlert('Failed to set budget: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function updateBudgetDisplay() {
    document.getElementById('currentBudget').textContent = Math.round(currentBudget);
    const cartTotal = personalCart.reduce((sum, item) => sum + item.price, 0);
    document.getElementById('cartTotal').textContent = Math.round(cartTotal);

    const progressBar = document.getElementById('budgetProgress');
    const budgetAlert = document.getElementById('budgetAlert');

    if (currentBudget > 0) {
        const percentage = (cartTotal / currentBudget) * 100;
        progressBar.style.width = Math.min(percentage, 100) + '%';

        if (percentage > 100) {
            progressBar.className = 'progress-bar bg-danger';
            budgetAlert.classList.remove('d-none');
        } else if (percentage > 80) {
            progressBar.className = 'progress-bar bg-warning';
            budgetAlert.classList.add('d-none');
        } else {
            progressBar.className = 'progress-bar bg-success';
            budgetAlert.classList.add('d-none');
        }
    }
}

// Cart functions
async function addToPersonalCart(product) {
    try {
        showLoading(true);

        // Debug: Check what's being added
        console.log("Adding product:", product);

        // Add to Firestore
        await addDoc(collection(db, 'cart'), {
            id: product.id,
            name: product.name,
            price: product.price,
            category: product.category,
            tags: product.tags,
            image_url: product.image_url,
            userEmail: currentUser.email,
            userId: currentUser.uid,
            addedAt: new Date()
        });

        // Add to local state
        personalCart.push({
            id: product.id,
            name: product.name,
            price: product.price,
            category: product.category,
            tags: product.tags,
            image_url: product.image_url
        });

        // Debug: Check local cart state
        console.log("Current cart:", personalCart);

        updatePersonalCartDisplay();
        updateBudgetDisplay();
        showAlert('Item added to cart!', 'success');
    } catch (error) {
        console.error("Add to cart error:", error);
        showAlert('Failed to add item: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function removeFromPersonalCart(productId, index) {
    try {
        showLoading(true);
        // Find and delete from Firestore
        const cartQuery = query(
            collection(db, 'cart'), 
            where('userId', '==', currentUser.uid),
            where('id', '==', productId)
        );
        const cartSnapshot = await getDocs(cartQuery);

        if (!cartSnapshot.empty) {
            const docToDelete = cartSnapshot.docs[0];
            await deleteDoc(docToDelete.ref);
        }

        personalCart.splice(index, 1);
        updatePersonalCartDisplay();
        updateBudgetDisplay();
        showAlert('Item removed from cart', 'success');
    } catch (error) {
        showAlert('Failed to remove item: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function addToSharedCart(product) {
    try {
        showLoading(true);
        await addDoc(collection(db, 'shared_cart'), {
            ...product,
            addedBy: currentUser.email,
            addedAt: new Date()
        });

        loadSharedCart();
        showAlert('Item added to shared cart!', 'success');
    } catch (error) {
        showAlert('Failed to add to shared cart: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function updatePersonalCartDisplay() {
    const container = document.getElementById('personalCartItems');
    const totalElement = document.getElementById('personalCartTotal');

    if (personalCart.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                <p>Your cart is empty. Add some items to get started!</p>
            </div>
        `;
        totalElement.textContent = '0';
        return;
    }

    const total = personalCart.reduce((sum, item) => sum + item.price, 0);
    totalElement.textContent = Math.round(total);

    container.innerHTML = personalCart.map((item, index) => `
        <div class="card mb-2">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <img src="${item.image_url || createPlaceholderImage(item.name)}" 
                             alt="${item.name}" 
                             class="img-fluid rounded"
                             style="width: 60px; height: 60px; object-fit: cover;"
                             onerror="this.onerror=null; this.src='${createPlaceholderImage(item.name)}'">
                    </div>
                    <div class="col-md-4">
                        <h6 class="mb-1">${item.name}</h6>
                        <small class="text-muted">${item.tags.join(', ')}</small>
                    </div>
                    <div class="col-md-2">
                        <span class="fw-bold text-success">₹${Math.round(item.price)}</span>
                    </div>
                    <div class="col-md-4">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="addToSharedCart(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                            <i class="fas fa-share me-1"></i>Share
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeFromPersonalCart('${item.id}', ${index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Recommendations
async function getRecommendations() {
    const prompt = document.getElementById('recommendationPrompt').value.trim();

    if (!prompt) {
        showAlert('Please enter a search term', 'warning');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                budget: currentBudget
            })
        });

        const data = await response.json();

        if (data.success) {
            displayRecommendations(data.products);
        } else {
            showAlert(data.error || 'Failed to get recommendations', 'danger');
        }
    } catch (error) {
        showAlert('Failed to get recommendations: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function displayRecommendations(products) {
    const container = document.getElementById('recommendationsResults');

    if (products.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <p>No recommendations found for your search and budget.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <h6 class="mb-3">Found ${products.length} recommendation(s):</h6>
        <div class="row">
            ${products.map(product => `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card h-100">
                        <img src="" alt="${product.name}" class="card-img-top product-image" 
                             data-product="${product.name}" style="height: 200px; object-fit: cover; background-color: #f8f9fa;">
                        <div class="card-body">
                            <h6 class="card-title">${product.name}</h6>
                            <p class="card-text">
                                <small class="text-muted">${product.tags.join(', ')}</small>
                            </p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="fw-bold text-success">₹${Math.round(product.price)}</span>
                                <button class="btn btn-sm btn-walmart-blue" onclick="addToPersonalCart(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                                    <i class="fas fa-cart-plus me-1"></i>Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    // Load product images for recommendations
    loadProductImages();
}

// Shared cart functions
async function loadSharedCart() {
    try {
        const sharedCartSnapshot = await getDocs(collection(db, 'shared_cart'));
        sharedCart = [];

        sharedCartSnapshot.forEach((doc) => {
            sharedCart.push({ id: doc.id, ...doc.data() });
        });

        updateLegacySharedCartDisplay();
    } catch (error) {
        console.error('Failed to load shared cart:', error);
    }
}

function updateLegacySharedCartDisplay() {
    // Legacy function for Firebase-based shared cart (kept for compatibility)
    const container = document.getElementById('sharedCartItems');
    const totalElement = document.getElementById('sharedCartTotal');

    if (sharedCart.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-users fa-3x mb-3"></i>
                <p>Create or join a shared cart to start shopping together!</p>
            </div>
        `;
        totalElement.textContent = '0';
        return;
    }

    // Group items by user
    const groupedByUser = sharedCart.reduce((acc, item) => {
        if (!acc[item.addedBy]) {
            acc[item.addedBy] = [];
        }
        acc[item.addedBy].push(item);
        return acc;
    }, {});

    const grandTotal = sharedCart.reduce((sum, item) => sum + item.price, 0);
    totalElement.textContent = Math.round(grandTotal);

    container.innerHTML = Object.entries(groupedByUser).map(([userEmail, items]) => {
        const userTotal = items.reduce((sum, item) => sum + item.price, 0);
        const isOverBudget = userTotal > 1000;

        return `
            <div class="card mb-3 ${isOverBudget ? 'border-danger' : ''}">
                <div class="card-header ${isOverBudget ? 'bg-danger text-white' : 'bg-light'}">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>${userEmail}</strong>
                        <span class="badge ${isOverBudget ? 'badge-warning' : 'badge-success'}">
                            Subtotal: ₹${Math.round(userTotal)}
                            ${isOverBudget ? ' - OVER BUDGET!' : ''}
                        </span>
                    </div>
                </div>
                <div class="card-body ${isOverBudget ? 'bg-light-danger' : ''}">
                    ${items.map(item => `
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2 rounded" style="background-color: ${isOverBudget ? '#ffe6e6' : '#f8f9fa'}">
                            <div class="d-flex align-items-center">
                                <img src="" alt="${item.name}" class="product-image me-3 rounded" 
                                     data-product="${item.name}" style="width: 40px; height: 40px; object-fit: cover; background-color: #f8f9fa;">
                                <div>
                                    <strong>${item.name}</strong><br>
                                    <small class="text-muted">${item.tags.join(', ')}</small>
                                </div>
                            </div>
                            <span class="fw-bold text-success">₹${Math.round(item.price)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');

    // Load product images for shared cart
    loadProductImages();
}

async function clearSharedCart() {
    if (!confirm('Are you sure you want to clear the shared cart?')) {
        return;
    }

    try {
        showLoading(true);
        const sharedCartSnapshot = await getDocs(collection(db, 'shared_cart'));

        const deletePromises = sharedCartSnapshot.docs.map(doc => deleteDoc(doc.ref));
        await Promise.all(deletePromises);

        sharedCart = [];
        updateSharedCartDisplay();
        showAlert('Shared cart cleared successfully', 'success');
    } catch (error) {
        showAlert('Failed to clear shared cart: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Load user data
async function loadUserData() {
    try {
        // Load budget
        const budgetDoc = await getDoc(doc(db, 'budgets', currentUser.uid));
        if (budgetDoc.exists()) {
            currentBudget = budgetDoc.data().budget || 0;
            updateBudgetDisplay();
        }

        // Load personal cart
        const cartQuery = query(collection(db, 'cart'), where('userId', '==', currentUser.uid));
        const cartSnapshot = await getDocs(cartQuery);
        personalCart = [];

        cartSnapshot.forEach((doc) => {
            const data = doc.data();
            personalCart.push({
                id: data.id,
                name: data.name,
                price: data.price,
                category: data.category,
                tags: data.tags
            });
        });

        updatePersonalCartDisplay();
        updateBudgetDisplay();

        // Load shared cart (legacy Firebase version)
        loadSharedCart();
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
}

// Utility functions
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showAlert(message, type) {
    // Create alert dynamically
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Product image loading functionality with better error handling
async function loadProductImages() {
    // You can actually remove this entire function since we're handling images directly
// in the templates with the onerror handler
}

// Create a better placeholder image with product info
function createPlaceholderImage(productName) {
    const initials = productName.split(' ').map(word => word[0]).join('').substring(0, 2).toUpperCase();
    const colors = ['#004c91', '#ffc220', '#28a745', '#dc3545', '#6f42c1'];
    const bgColor = colors[productName.length % colors.length];

    return `data:image/svg+xml;base64,${btoa(`
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="${bgColor}"/>
            <text x="50%" y="45%" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle" dy=".3em">${initials}</text>
            <text x="50%" y="75%" font-family="Arial, sans-serif" font-size="12" fill="white" text-anchor="middle" dy=".3em">${productName}</text>
        </svg>
    `)}`;
}

// Shared cart session management
async function createSharedCart() {
    const cartName = document.getElementById('newCartName').value.trim() || 'Shared Cart';

    try {
        showLoading(true);
        const response = await fetch('/api/shared-cart/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: cartName })
        });

        const data = await response.json();

        if (data.success) {
            currentSharedSession = {
                id: data.session_id,
                name: data.name
            };

            updateSharedSessionUI();
            loadSharedCartItems();
            showAlert(`Created shared cart: ${data.session_id}`, 'success');
            document.getElementById('newCartName').value = '';
        } else {
            showAlert(data.error || 'Failed to create shared cart', 'danger');
        }
    } catch (error) {
        showAlert('Failed to create shared cart: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function joinSharedCart() {
    const cartId = document.getElementById('joinCartId').value.trim().toUpperCase();

    if (!cartId) {
        showAlert('Please enter a cart ID', 'warning');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`/api/shared-cart/join/${cartId}`);
        const data = await response.json();

        if (data.success) {
            currentSharedSession = {
                id: data.session.id,
                name: data.session.name
            };

            updateSharedSessionUI();
            loadSharedCartItems();
            showAlert(`Joined shared cart: ${data.session.name}`, 'success');
            document.getElementById('joinCartId').value = '';
        } else {
            showAlert(data.error || 'Failed to join shared cart', 'danger');
        }
    } catch (error) {
        showAlert('Failed to join shared cart: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function leaveSharedCart() {
    currentSharedSession = null;
    updateSharedSessionUI();

    // Clear shared cart display
    document.getElementById('sharedCartItems').innerHTML = `
        <div class="text-center text-muted py-4">
            <i class="fas fa-users fa-3x mb-3"></i>
            <p>Create or join a shared cart to start shopping together!</p>
        </div>
    `;

    document.getElementById('billSplitSummary').classList.add('d-none');
    showAlert('Left shared cart session', 'info');
}

function updateSharedSessionUI() {
    const sessionInfo = document.getElementById('currentSessionInfo');
    const sessionName = document.getElementById('currentSessionName');
    const sessionId = document.getElementById('currentSessionId');

    if (currentSharedSession) {
        sessionInfo.classList.remove('d-none');
        sessionName.textContent = currentSharedSession.name;
        sessionId.textContent = currentSharedSession.id;
    } else {
        sessionInfo.classList.add('d-none');
    }
}

async function loadSharedCartItems() {
    if (!currentSharedSession) return;

    try {
        const response = await fetch(`/api/shared-cart/${currentSharedSession.id}/items`);
        const data = await response.json();

        if (data.success) {
            updateSharedCartDisplay(data);
        }
    } catch (error) {
        console.error('Failed to load shared cart items:', error);
    }
}

async function addToSharedCartSession(product) {
    if (!currentSharedSession) {
        showAlert('Please join a shared cart session first', 'warning');
        return;
    }

    try {
        showLoading(true);
        const response = await fetch(`/api/shared-cart/${currentSharedSession.id}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product_id: product.id,
                user_email: currentUser?.email || 'anonymous@example.com'
            })
        });

        const data = await response.json();

        if (data.success) {
            loadSharedCartItems();
            showAlert('Item added to shared cart!', 'success');
        } else {
            showAlert(data.error || 'Failed to add to shared cart', 'danger');
        }
    } catch (error) {
        showAlert('Failed to add to shared cart: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function updateSharedCartDisplay(data) {
    const container = document.getElementById('sharedCartItems');
    const billSummary = document.getElementById('billSplitSummary');
    const totalElement = document.getElementById('sharedCartTotal');
    const userTotalsContainer = document.getElementById('userTotals');

    if (!data.items || data.items.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-shopping-cart fa-3x mb-3"></i>
                <p>No items in this shared cart yet. Add some items to get started!</p>
            </div>
        `;
        billSummary.classList.add('d-none');
        return;
    }

    // Group items by user
    const itemsByUser = {};
    data.items.forEach(item => {
        if (!itemsByUser[item.added_by]) {
            itemsByUser[item.added_by] = [];
        }
        itemsByUser[item.added_by].push(item);
    });

    // Display items grouped by user
    container.innerHTML = Object.entries(itemsByUser).map(([userEmail, items]) => {
        const userTotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
        const isOverBudget = userTotal > 2000; // Budget threshold in rupees

        return `
            <div class="card mb-3 ${isOverBudget ? 'border-danger' : ''}">
                <div class="card-header ${isOverBudget ? 'bg-danger text-white' : 'bg-primary text-white'}">
                    <div class="d-flex justify-content-between align-items-center">
                        <span><i class="fas fa-user me-2"></i>${userEmail}</span>
                        <span class="badge ${isOverBudget ? 'bg-warning text-dark' : 'bg-light text-dark'}">
                            ₹${Math.round(userTotal)} ${isOverBudget ? '(OVER ₹2000!)' : ''}
                        </span>
                    </div>
                </div>
                <div class="card-body">
                    ${items.map(item => `
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2 rounded bg-light">
                            <div class="d-flex align-items-center">
                                <img src="" alt="${item.product.name}" class="product-image me-3 rounded" 
                                     data-product="${item.product.name}" style="width: 50px; height: 50px; object-fit: cover;">
                                <div>
                                    <strong>${item.product.name}</strong><br>
                                    <small class="text-muted">${item.product.tags.join(', ')}</small>
                                </div>
                            </div>
                            <span class="fw-bold text-success">₹${Math.round(item.product.price)} x${item.quantity}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');

    // Show bill split summary
    totalElement.textContent = Math.round(data.grand_total);

    userTotalsContainer.innerHTML = Object.entries(data.user_totals).map(([userEmail, total]) => {
        const isOverBudget = total > 2000;
        return `
            <div class="col-md-4 mb-3">
                <div class="card ${isOverBudget ? 'border-warning' : 'border-primary'}">
                    <div class="card-body text-center">
                        <h6 class="card-title">${userEmail}</h6>
                        <h4 class="text-${isOverBudget ? 'warning' : 'primary'}">₹${Math.round(total)}</h4>
                        ${isOverBudget ? '<small class="text-danger">Over ₹2000 budget!</small>' : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    billSummary.classList.remove('d-none');

    // Load product images
    loadProductImages();
}

// Product loading and display functions
async function loadAllProducts() {
    try {
        showLoading(true);
        const response = await fetch('/api/products');
        const data = await response.json();

        if (data.success) {
            allProducts = data.products;
            filteredProducts = [...allProducts];
            populateCategoryFilter();
            displayAllProducts(filteredProducts);
        } else {
            showAlert('Failed to load products', 'danger');
        }
    } catch (error) {
        console.error('Error loading products:', error);
        showAlert('Failed to load products: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function populateCategoryFilter() {
    const categoryFilter = document.getElementById('categoryFilter');
    const categories = [...new Set(allProducts.map(p => p.category))].sort();

    // Clear existing options except "All Categories"
    categoryFilter.innerHTML = '<option value="all">All Categories</option>';

    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });
}

function displayAllProducts(products) {
    const container = document.getElementById('allProductsGrid');

    if (products.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <p>No products found matching your criteria.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="row">
            ${products.map(product => `
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-img-container" style="height: 200px; overflow: hidden; display: flex; align-items: center; justify-content: center; background-color: #f8f9fa;">
                            <img src="${product.image_url || createPlaceholderImage(product.name)}" 
                                 alt="${product.name}"
                                 class="card-img-top"
                                 style="max-height: 100%; width: auto;"
                                 onerror="this.onerror=null; this.src='${createPlaceholderImage(product.name)}'">
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${product.name}</h5>
                            <p class="text-muted">${product.category}</p>
                            <h6 class="text-walmart-blue">₹${Math.round(product.price)}</h6>
                            <button class="btn btn-walmart-yellow btn-sm add-to-cart" 
                                    data-id="${product.id}"
                                    onclick="addToPersonalCart(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                                <i class="fas fa-cart-plus"></i> Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}


function filterProducts() {
    const selectedCategory = document.getElementById('categoryFilter').value;
    const searchTerm = document.getElementById('productSearch').value.toLowerCase();

    filteredProducts = allProducts.filter(product => {
        const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
        const matchesSearch = searchTerm === '' || 
            product.name.toLowerCase().includes(searchTerm) ||
            product.tags.some(tag => tag.toLowerCase().includes(searchTerm)) ||
            product.category.toLowerCase().includes(searchTerm);

        return matchesCategory && matchesSearch;
    });

    displayAllProducts(filteredProducts);
}

function searchProducts() {
    filterProducts();
}

function clearSearch() {
    document.getElementById('productSearch').value = '';
    filterProducts();
}

// Make functions globally available for onclick handlers
window.addToPersonalCart = addToPersonalCart;
window.removeFromPersonalCart = removeFromPersonalCart;
window.addToSharedCart = addToSharedCartSession;

// Make functions globally available for inline onclick handlers
window.addToPersonalCart = addToPersonalCart;
window.removeFromPersonalCart = removeFromPersonalCart;
window.addToSharedCart = addToSharedCart;
