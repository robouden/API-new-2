/* eslint-disable no-unused-vars */
/* global L */

// --- STATE MANAGEMENT ---
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

const initializeApp = async () => {
    window.appState = {
        token: localStorage.getItem('token'),
        currentUser: null,
        importsData: [],
        currentFilter: 'all',
        currentOwner: 'yours',
        sortField: 'id',
        sortOrder: 'desc',
    };
    setupEventListeners();
    await fetchInitialData();
    handleRouteChange(); // Render initial route
};

const setupEventListeners = () => {
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');

    // Modal event listeners with error handling
    const signinLink = document.getElementById('signin-link');
    const registerLink = document.getElementById('register-link');
    
    if (signinLink && loginModal) {
        signinLink.addEventListener('click', (e) => { 
            e.preventDefault(); 
            loginModal.classList.remove('hidden'); 
        });
    }
    
    if (registerLink && signupModal) {
        registerLink.addEventListener('click', (e) => { 
            e.preventDefault(); 
            signupModal.classList.remove('hidden'); 
        });
    }
    
    if (loginModal) {
        const closeBtn = loginModal.querySelector('.close-button');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => loginModal.classList.add('hidden'));
        }
    }
    
    if (signupModal) {
        const closeBtn = signupModal.querySelector('.close-button');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => signupModal.classList.add('hidden'));
        }
    }

    window.addEventListener('click', (event) => {
        if (event.target === loginModal) {
            loginModal.classList.add('hidden');
        }
        if (event.target === signupModal) {
            signupModal.classList.add('hidden');
        }
    });

    // Form event listeners
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const logoutButton = document.getElementById('logout-button');
    const uploadBtn = document.getElementById('upload-btn');
    
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (signupForm) signupForm.addEventListener('submit', handleSignup);
    if (logoutButton) logoutButton.addEventListener('click', handleLogout);
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            if (window.location.hash !== '#bgeigie-imports') {
                window.location.hash = '#bgeigie-imports';
            }
            setTimeout(() => {
                const uploadSection = document.getElementById('upload-section');
                if (uploadSection) uploadSection.style.display = 'block';
            }, 100);
        });
    }

    // Sidebar navigation
    document.querySelectorAll('aside a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const hash = e.currentTarget.getAttribute('href');
            if (window.location.hash !== hash) {
                window.location.hash = hash;
            } else {
                handleRouteChange();
            }
        });
    });
};

// --- AUTHENTICATION & DATA FETCHING ---
const fetchInitialData = async () => {
    if (window.appState.token) {
        try {
            const response = await fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${window.appState.token}` } });
            if (response.ok) {
                window.appState.currentUser = await response.json();
                updateUIForLoggedIn(window.appState.currentUser);
            } else {
                handleLogout();
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
            handleLogout();
        }
    } else {
        updateUIForPublicView();
    }
    
    // Add hash change listener
    window.addEventListener('hashchange', handleRouteChange);
};

const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
        const response = await fetch('/users/token', { method: 'POST', body: formData });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            window.appState.token = data.access_token;
            document.getElementById('login-modal').classList.add('hidden');
            e.target.reset();
            await fetchInitialData();
        } else {
            alert('Login failed: Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed: Network error');
    }
};

const handleSignup = async (e) => {
    e.preventDefault();
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    try {
        const response = await fetch('/users/users/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        if (response.ok) {
            alert('Signup successful! Please log in.');
            document.getElementById('signup-modal').classList.add('hidden');
            e.target.reset();
            document.getElementById('login-modal').classList.remove('hidden');
        } else {
            const error = await response.json();
            alert(`Signup failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Signup error:', error);
        alert('Signup failed: Network error');
    }
};

const handleLogout = () => {
    localStorage.removeItem('token');
    window.appState.token = null;
    window.appState.currentUser = null;
    updateUIForPublicView();
    window.location.hash = '#';
};

// --- UI UPDATES ---
const updateUIForLoggedIn = (user) => {
    document.getElementById('auth-nav').classList.add('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    document.getElementById('user-email').textContent = user.email;
    document.getElementById('user-api-key').textContent = user.api_key;
    document.getElementById('upload-btn-wrapper').classList.remove('hidden');
};

const updateUIForPublicView = () => {
    document.getElementById('auth-nav').classList.remove('hidden');
    document.getElementById('user-info').classList.add('hidden');
    document.getElementById('upload-btn-wrapper').classList.add('hidden');
};

const updateActiveSidebarLink = (hash) => {
    document.querySelectorAll('aside a').forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === hash);
    });
};

// --- ROUTING ---
const handleRouteChange = () => {
    const hash = window.location.hash || '#';
    const main = document.querySelector('main');
    main.innerHTML = '<div class="loader">Loading...</div>';

    updateActiveSidebarLink(hash);

    const isAuthenticated = !!window.appState.token;

    if (hash.startsWith('#bgeigie-imports/') && hash.includes('/detail')) {
        const importId = hash.split('/')[1];
        renderBGeigieImportDetail(importId);
        return;
    }

    const routes = {
        '#': isAuthenticated ? renderBGeigieImportsView : renderPublicHomeView,
        '#bgeigie-imports': isAuthenticated ? renderBGeigieImportsView : renderPublicBGeigieImportsView,
        '#measurements': isAuthenticated ? () => renderGenericView('Measurements') : renderPublicMeasurementsView,
        '#devices': isAuthenticated ? renderDevicesView : renderPublicDevicesView,
        '#device-stories': isAuthenticated ? renderDeviceStoriesView : renderPublicDeviceStoriesView,
        '#users': isAuthenticated ? renderUsersView : renderPublicUsersView,
        '#radiation-index': isAuthenticated ? () => renderGenericView('Radiation Index') : renderPublicRadiationIndexView,
        '#ingest-export': isAuthenticated ? () => renderGenericView('Ingest/Export') : renderPublicIngestExportView,
    };

    const routeHandler = routes[hash] || routes['#'];
    routeHandler();
};

// --- VIEW RENDERING (AUTHENTICATED) ---
const renderBGeigieImportsView = async () => {
    const main = document.querySelector('main');
    main.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h1>bGeigie Imports</h1>
        </div>
        <div id="upload-section" style="display: none; margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa;">
            <h3>Upload bGeigie Log File</h3>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="file-input" name="file" accept=".log,.LOG" required style="margin-bottom: 10px;">
                <div>
                    <button type="submit" class="button-primary">Upload</button>
                    <button type="button" id="cancel-upload" class="button-secondary">Cancel</button>
                </div>
            </form>
        </div>
        <div id="imports-controls"></div>
        <div id="imports-table-container"></div>
    `;

    document.getElementById('cancel-upload').addEventListener('click', () => document.getElementById('upload-section').style.display = 'none');
    document.getElementById('upload-form').addEventListener('submit', handleUpload);

    try {
        const response = await fetch('/bgeigie-imports/', { headers: { 'Authorization': `Bearer ${window.appState.token}` } });
        if (!response.ok) throw new Error('Failed to fetch imports');
        window.appState.importsData = await response.json();
        renderImportsTable();
    } catch (error) {
        console.error('Error fetching imports:', error);
        main.querySelector('#imports-table-container').innerHTML = '<p>Error loading imports.</p>';
    }
};

const renderDevicesView = async () => {
    const main = document.querySelector('main');
    try {
        const response = await fetch('/devices/', { headers: { 'Authorization': `Bearer ${window.appState.token}` } });
        if (!response.ok) throw new Error('Failed to fetch devices');
        const devices = await response.json();
        let tableHtml = `<h2>Devices</h2>
            <table class="table"><thead><tr><th>ID</th><th>bGeigie Import ID</th><th>Unit</th><th>Sensor</th></tr></thead><tbody>`;
        devices.forEach(device => {
            tableHtml += `<tr><td>${device.id}</td><td>${device.bgeigie_import_id}</td><td>${device.unit}</td><td>${device.sensor}</td></tr>`;
        });
        tableHtml += `</tbody></table>`;
        main.innerHTML = tableHtml;
    } catch (error) {
        console.error('Error rendering devices view:', error);
        main.innerHTML = `<p>Error loading devices.</p>`;
    }
};

const renderDeviceStoriesView = async () => {
    const main = document.querySelector('main');
    try {
        const response = await fetch('/device_stories/', { headers: { 'Authorization': `Bearer ${window.appState.token}` } });
        if (!response.ok) throw new Error('Failed to fetch device stories');
        const stories = await response.json();
        let html = `<h2>Device Stories</h2>`;
        stories.forEach(story => {
            html += `<div class="story"><h3>${story.title}</h3><p>${story.story}</p><small>By User ID: ${story.user_id}</small></div>`;
        });
        main.innerHTML = html;
    } catch (error) {
        console.error('Error rendering device stories view:', error);
        main.innerHTML = `<p>Error loading device stories.</p>`;
    }
};

const renderUsersView = async () => {
    const main = document.querySelector('main');
    try {
        const [usersRes, currentUserRes] = await Promise.all([
            fetch('/users/users/all', { headers: { 'Authorization': `Bearer ${window.appState.token}` } }),
            fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${window.appState.token}` } })
        ]);

        if (!usersRes.ok) throw new Error('Failed to fetch users');
        if (!currentUserRes.ok) throw new Error('Failed to fetch current user');

        const users = await usersRes.json();
        const currentUser = await currentUserRes.json();

        let tableHtml = `<h2>Users</h2>
            <table class="table"><thead><tr><th>ID</th><th>Email</th><th>Is Active</th><th>Role</th><th>API Key</th>`;
        if (currentUser.role === 'admin') tableHtml += `<th>Actions</th>`;
        tableHtml += `</tr></thead><tbody>`;

        users.forEach(user => {
            tableHtml += `<tr>
                <td>${user.id}</td><td>${user.email}</td><td>${user.is_active}</td><td>${user.role}</td><td>${user.api_key}</td>`;
            if (currentUser.role === 'admin') {
                tableHtml += `<td>
                    <select class="role-select" data-user-id="${user.id}">
                        <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                        <option value="moderator" ${user.role === 'moderator' ? 'selected' : ''}>Moderator</option>
                        <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                    </select>
                </td>`;
            }
            tableHtml += `</tr>`;
        });
        tableHtml += `</tbody></table>`;
        main.innerHTML = tableHtml;

        if (currentUser.role === 'admin') {
            document.querySelectorAll('.role-select').forEach(select => {
                select.addEventListener('change', handleRoleChange);
            });
        }
    } catch (error) {
        console.error('Error rendering users view:', error);
        main.innerHTML = `<p>Error loading users.</p>`;
    }
};

const renderGenericView = (title) => {
    document.querySelector('main').innerHTML = `<h2>${title}</h2><p>Content for this section is not yet available.</p>`;
};

// --- VIEW RENDERING (PUBLIC) ---
const renderPublicHomeView = () => {
    document.querySelector('main').innerHTML = `
        <h1>The Safecast API</h1>
        <p>Query and add to the Safecast dataset with your own application.</p>
        <p><strong>Browse public radiation data below, or <a href="#" id="signin-link-main">sign in</a> to upload your own measurements.</strong></p>
        <h2>Public Data Access</h2>
        <p>You can browse all approved radiation measurements without signing in.</p>`;
    const mainSigninLink = document.getElementById('signin-link-main');
    if (mainSigninLink) {
        mainSigninLink.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('login-modal').classList.remove('hidden');
        });
    }
};

const renderPublicBGeigieImportsView = async () => {
    const main = document.querySelector('main');
    main.innerHTML = `
        <h1>Public bGeigie Imports</h1>
        <p>Showing all publicly approved bGeigie log file imports.</p>
        <div id="imports-controls"></div>
        <div id="imports-table-container"></div>
    `;
    try {
        const response = await fetch('/bgeigie-imports/');
        if (!response.ok) throw new Error('Failed to fetch public imports');
        window.appState.importsData = await response.json();
        window.appState.currentFilter = 'approved';
        window.appState.currentOwner = 'everyone';
        renderImportsTable();
    } catch (error) {
        console.error('Error fetching public imports:', error);
        main.querySelector('#imports-table-container').innerHTML = '<p>Error loading public imports.</p>';
    }
};

const renderPublicMeasurementsView = () => { document.querySelector('main').innerHTML = `<h1>Public Measurements</h1><p>Browse radiation measurements from approved bGeigie imports. <em>Sign in to upload your own measurements.</em></p>`; };
const renderPublicDevicesView = () => { document.querySelector('main').innerHTML = `<h1>Public Devices</h1><p>View information about radiation detection devices. <em>Sign in to manage devices.</em></p>`; };
const renderPublicDeviceStoriesView = () => { document.querySelector('main').innerHTML = `<h1>Public Device Stories</h1><p>Read stories and experiences from the Safecast community. <em>Sign in to share your own stories.</em></p>`; };
const renderPublicUsersView = () => { document.querySelector('main').innerHTML = `<h1>Public Users</h1><p>View public information about Safecast community members. <em>Sign in to manage your profile.</em></p>`; };
const renderPublicRadiationIndexView = () => { document.querySelector('main').innerHTML = `<h1>Radiation Index</h1><p>Browse radiation data by location and time. <em>Sign in to access advanced filtering options.</em></p>`; };
const renderPublicIngestExportView = () => { document.querySelector('main').innerHTML = `<h1>Ingest Export</h1><p>Access data export and ingestion tools. <em>Sign in to upload and export data.</em></p>`; };

// --- BGEIGIE IMPORTS TABLE & ACTIONS ---
const renderImportsTable = () => {
    const tableContainer = document.getElementById('imports-table-container');
    const controlsContainer = document.getElementById('imports-controls');
    if (!tableContainer || !controlsContainer) return;

    const { importsData, currentUser, currentFilter, currentOwner, sortField, sortOrder } = window.appState;

    if (currentUser) {
        controlsContainer.innerHTML = `
            <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                <button class="filter-btn ${currentFilter === 'all' ? 'active' : ''}" data-filter="all">All</button>
                <button class="filter-btn ${currentFilter === 'unprocessed' ? 'active' : ''}" data-filter="unprocessed">New</button>
                <button class="filter-btn ${currentFilter === 'processed' ? 'active' : ''}" data-filter="processed">Processed</button>
                <button class="filter-btn ${currentFilter === 'submitted' ? 'active' : ''}" data-filter="submitted">Submitted</button>
                <button class="filter-btn ${currentFilter === 'approved' ? 'active' : ''}" data-filter="approved">Approved</button>
            </div>
            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                <button class="owner-filter-btn ${currentOwner === 'yours' ? 'active' : ''}" data-owner="yours">Yours</button>
                <button class="owner-filter-btn ${currentOwner === 'everyone' ? 'active' : ''}" data-owner="everyone">Everyone</button>
            </div>
        `;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.addEventListener('click', handleFilterClick));
        document.querySelectorAll('.owner-filter-btn').forEach(btn => btn.addEventListener('click', handleOwnerFilterClick));
    } else {
        controlsContainer.innerHTML = '';
    }

    const filteredData = importsData.filter(imp => {
        const statusFilter = currentFilter === 'all' || imp.status === currentFilter;
        const ownerFilter = !currentUser || currentOwner === 'everyone' || imp.user_id === currentUser.id;
        return statusFilter && ownerFilter;
    });

    const sortedData = [...filteredData].sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];
        if (sortField === 'user') {
            valA = a.user ? a.user.email : '';
            valB = b.user ? b.user.email : '';
        }
        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
    });

    tableContainer.innerHTML = `
        <p>${sortedData.length} results.</p>
        <table class="bgeigie-imports-table">
        <thead><tr>
            <th data-sort="id">ID ${sortField === 'id' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th data-sort="created_at">Uploaded At ${sortField === 'created_at' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th data-sort="user">User ${sortField === 'user' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}</th>
            <th data-sort="source">File Name</th>
            <th data-sort="measurements_count"># Measures</th>
            <th data-sort="status">Status</th>
            <th>Comment</th>
            <th>Actions</th>
        </tr></thead>
        <tbody>
            ${sortedData.map(imp => `
                <tr>
                    <td><a href="#bgeigie-imports/${imp.id}/detail" style="color: #007bff; text-decoration: none;">${imp.id}</a></td>
                    <td>${new Date(imp.created_at).toLocaleDateString()} ${new Date(imp.created_at).toLocaleTimeString()}</td>
                    <td>${imp.user_email || 'N/A'}</td>
                    <td>${imp.source}</td>
                    <td>${imp.measurements_count || 0}</td>
                    <td><span class="status-${imp.status}">${imp.status}</span></td>
                    <td>${imp.comment || ''}</td>
                    <td class="actions">${getActions(imp)}</td>
                </tr>
            `).join('') || '<tr><td colspan="8">No imports found.</td></tr>'}
        </tbody></table>`;

    tableContainer.querySelectorAll('th[data-sort]').forEach(th => th.addEventListener('click', handleSortClick));
};

const getActions = (imp) => {
    const { currentUser } = window.appState;
    if (!currentUser) return '';

    const isOwner = imp.user_id === currentUser.id;
    const isAdmin = currentUser.role === 'admin';
    let actions = '';

    if (imp.status === 'unprocessed' && (isOwner || isAdmin)) {
        actions += `<button class="button-action" onclick="processImport(${imp.id})">Process</button>`;
    }
    if (imp.status === 'submitted' && isAdmin) {
        actions += `<button class="button-success" onclick="approveImport(${imp.id})">Approve</button> `;
        actions += `<button class="button-warning" onclick="rejectImport(${imp.id})">Reject</button>`;
    }
    if (isOwner || isAdmin) {
        actions += `<button class="button-danger" onclick="deleteImport(${imp.id})">Delete</button>`;
    }
    return actions;
};

const handleFilterClick = (e) => {
    window.appState.currentFilter = e.target.dataset.filter;
    renderImportsTable();
};

const handleOwnerFilterClick = (e) => {
    window.appState.currentOwner = e.target.dataset.owner;
    renderImportsTable();
};

const handleSortClick = (e) => {
    const field = e.currentTarget.dataset.sort;
    if (window.appState.sortField === field) {
        window.appState.sortOrder = window.appState.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        window.appState.sortField = field;
        window.appState.sortOrder = 'desc';
    }
    renderImportsTable();
};

const handleUpload = async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) { return alert('Please select a file.'); }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/bgeigie-imports/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${window.appState.token}` },
            body: formData
        });
        if (response.ok) {
            const newImport = await response.json();
            alert('File uploaded successfully!');
            document.getElementById('upload-section').style.display = 'none';
            document.getElementById('upload-form').reset();
            window.location.hash = `#bgeigie-imports/${newImport.id}/detail`;
        } else {
            const error = await response.json();
            alert(`Upload failed: ${error.detail}`);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Upload failed: Network error');
    }
};

const handleRoleChange = async (e) => {
    const userId = e.target.dataset.userId;
    const newRole = e.target.value;
    try {
        const response = await fetch(`/users/${userId}/role`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.appState.token}`
            },
            body: JSON.stringify({ role: newRole })
        });
        if (response.ok) {
            alert('User role updated successfully!');
        } else {
            const error = await response.json();
            alert(`Failed to update role: ${error.detail}`);
            renderUsersView(); // Re-render to show original role
        }
    } catch (error) {
        console.error('Error updating user role:', error);
        alert('Failed to update user role.');
    }
};

const renderBGeigieImportDetail = async (importId) => {
    const main = document.querySelector('main');
    
    try {
        // Fetch import data directly from API instead of HTML template
        const response = await fetch(`/bgeigie-imports/${importId}`);
        if (!response.ok) throw new Error('Failed to fetch import details');
        const importData = await response.json();
        
        // Render the SPA-compatible layout
        main.innerHTML = `
            <h1>bGeigie Import: Import #${importData.id}</h1>
            
            <div class="import-status ${importData.status}" style="background: #d4edda; padding: 10px; margin: 15px 0; border-radius: 4px;">
                <strong>Status: ${importData.status.charAt(0).toUpperCase() + importData.status.slice(1)}</strong>
            </div>

            <div class="import-stats" style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; min-width: 120px;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;" id="total-measurements">${importData.measurements_count || 0}</div>
                    <div style="font-size: 12px; color: #666;">TOTAL MEASUREMENTS</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; min-width: 120px;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;" id="avg-cpm">-</div>
                    <div style="font-size: 12px; color: #666;">AVERAGE CPM</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; min-width: 120px;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;" id="max-cpm">-</div>
                    <div style="font-size: 12px; color: #666;">MAX CPM</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; min-width: 120px;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;" id="min-cpm">-</div>
                    <div style="font-size: 12px; color: #666;">MIN CPM</div>
                </div>
            </div>

            <div style="margin: 20px 0;">
                <button onclick="toggleHeatmap()" style="background: #6c757d; color: white; border: none; padding: 8px 16px; margin-right: 10px; border-radius: 4px; cursor: pointer;">Toggle Heatmap</button>
                <button onclick="fitToData()" style="background: #007bff; color: white; border: none; padding: 8px 16px; margin-right: 10px; border-radius: 4px; cursor: pointer;">Fit to Data</button>
                <button onclick="exportData(${importData.id})" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Export Data</button>
            </div>

            <div id="import-map" style="height: 500px; width: 100%; border: 1px solid #ddd; border-radius: 4px; margin: 20px 0;"></div>

            ${importData.status === 'processed' || importData.status === 'approved' ? `
            <div style="background: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0;">
                <h3>Add Import Metadata</h3>
                <p>Please provide additional information about this radiation measurement drive:</p>
                
                <form id="metadata-form" style="display: grid; gap: 15px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <label for="name" style="display: block; margin-bottom: 5px; font-weight: bold;">Import Name</label>
                            <input type="text" id="name" name="name" placeholder="Give this import a descriptive name" required
                                   value="${importData.name || ''}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div>
                            <label for="subtype" style="display: block; margin-bottom: 5px; font-weight: bold;">Measurement Type</label>
                            <select id="subtype" name="subtype" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">Select type...</option>
                                <option value="Drive" ${importData.subtype === 'Drive' ? 'selected' : ''}>Mobile Drive</option>
                                <option value="Walk" ${importData.subtype === 'Walk' ? 'selected' : ''}>Walking Survey</option>
                                <option value="Cosmic" ${importData.subtype === 'Cosmic' ? 'selected' : ''}>Cosmic Ray Detection</option>
                                <option value="Fixed" ${importData.subtype === 'Fixed' ? 'selected' : ''}>Fixed Point</option>
                                <option value="Other" ${importData.subtype === 'Other' ? 'selected' : ''}>Other</option>
                            </select>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <label for="cities" style="display: block; margin-bottom: 5px; font-weight: bold;">Cities/Locations Covered</label>
                            <input type="text" id="cities" name="cities" placeholder="e.g., Tokyo, Shibuya, Harajuku" required 
                                   value="${importData.cities || ''}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div>
                            <label for="credits" style="display: block; margin-bottom: 5px; font-weight: bold;">Credits/Attribution</label>
                            <input type="text" id="credits" name="credits" placeholder="Measurement team or organization" required
                                   value="${importData.credits || ''}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                    </div>
                    
                    <div>
                        <label for="description" style="display: block; margin-bottom: 5px; font-weight: bold;">Description</label>
                        <textarea id="description" name="description" placeholder="Describe the measurement drive, purpose, or any notable observations..."
                                  style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; height: 100px; resize: vertical;">${importData.description || ''}</textarea>
                    </div>
                    
                    <button type="submit" style="background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px;">
                        Submit for Approval
                    </button>
                </form>
            </div>
            ` : ''}
        `;
        
        // Load Leaflet CSS and JS if not already loaded
        if (!document.querySelector('link[href*="leaflet"]')) {
            const leafletCSS = document.createElement('link');
            leafletCSS.rel = 'stylesheet';
            leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            document.head.appendChild(leafletCSS);
        }
        
        // Load Leaflet JS and heat plugin
        const loadScript = (src) => {
            return new Promise((resolve, reject) => {
                if (document.querySelector(`script[src="${src}"]`)) {
                    resolve();
                    return;
                }
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        };
        
        await loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
        await loadScript('https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js');
        
        // Set up metadata form handler
        const metadataForm = document.getElementById('metadata-form');
        if (metadataForm) {
            metadataForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const metadata = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch(`/bgeigie-imports/${importId}/metadata`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${window.appState.token}`
                        },
                        body: JSON.stringify(metadata)
                    });
                    
                    if (response.ok) {
                        alert('Metadata saved successfully! Import submitted for approval.');
                        window.location.hash = '#bgeigie-imports';
                    } else {
                        throw new Error('Failed to save metadata');
                    }
                } catch (error) {
                    console.error('Error saving metadata:', error);
                    alert('Failed to save metadata. Please try again.');
                }
            });
        }
        
        // Initialize the map after scripts are loaded
        setTimeout(() => {
            initializeBGeigieMap(importId);
        }, 100);
        
    } catch (error) {
        console.error(`Error fetching import detail for ${importId}:`, error);
        main.innerHTML = `<p>Error loading import details.</p>`;
    }
};

// Initialize bGeigie map for import detail view
const initializeBGeigieMap = async (importId) => {
    if (typeof L === 'undefined') {
        console.error('Leaflet not loaded');
        return;
    }
    
    const mapContainer = document.getElementById('import-map');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }
    
    // Clear any existing map
    if (window.bgeigieMapInstance) {
        window.bgeigieMapInstance.remove();
    }
    
    // Initialize map
    const map = L.map('import-map').setView([35.6762, 139.6503], 10);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    window.bgeigieMapInstance = map;
    
    // Load and display measurement data
    try {
        const response = await fetch(`/bgeigie-imports/${importId}/measurements`);
        if (!response.ok) throw new Error('Failed to load measurements');
        
        const data = await response.json();
        const measurements = data.measurements || [];
        
        if (measurements.length === 0) {
            console.warn('No measurements found for import');
            return;
        }
        
        const markers = [];
        
        // Add markers for each measurement
        measurements.forEach(measurement => {
            if (measurement.latitude && measurement.longitude) {
                const cpm = measurement.cpm || 0;
                const microSvPerHour = cpm / 334; // LND7317 conversion
                
                // Color based on radiation level
                const getColor = (cpm) => {
                    const uSvh = cpm / 334;
                    if (uSvh >= 100) return '#ffff00';
                    if (uSvh >= 10) return '#ff8000';
                    if (uSvh >= 1) return '#ff0000';
                    if (uSvh >= 0.25) return '#8000ff';
                    if (uSvh >= 0.08) return '#00ffff';
                    return '#0000ff';
                };
                
                const marker = L.circleMarker([measurement.latitude, measurement.longitude], {
                    radius: Math.max(3, Math.min(10, Math.log(cpm + 1) * 2)),
                    fillColor: getColor(cpm),
                    color: '#000',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.7
                });
                
                // Add hover tooltip with measurement details
                const tooltipContent = `
                    <div class="measurement-tooltip" style="background: white; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); font-size: 12px; line-height: 1.3;">
                        <strong>${microSvPerHour.toFixed(2)} µSv/h</strong><br>
                        <strong>${cpm} CPM</strong><br>
                        Lat: ${measurement.latitude.toFixed(6)}<br>
                        Lng: ${measurement.longitude.toFixed(6)}<br>
                        Alt: ${(measurement.altitude ?? 0)} m<br>
                        ${measurement.captured_at ? new Date(measurement.captured_at).toLocaleString() : ''}
                    </div>
                `;

                marker.bindTooltip(tooltipContent, {
                    permanent: false,
                    direction: 'top',
                    offset: [0, -10],
                    className: 'custom-tooltip',
                    interactive: true,
                    sticky: true
                });

                // Ensure tooltip opens/closes on hover explicitly
                marker.on('mouseover', function () { this.openTooltip(); });
                marker.on('mouseout', function () { this.closeTooltip(); });

                marker.addTo(map);
                markers.push(marker);
            }
        });
        
        // Store markers globally for control buttons
        window.currentMarkers = markers;
        
        // Fit map to show all markers
        if (markers.length > 0) {
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
        
        // Update statistics
        const totalMeasurements = measurements.length;
        const avgCPM = measurements.reduce((sum, m) => sum + (m.cpm || 0), 0) / totalMeasurements;
        const maxCPM = Math.max(...measurements.map(m => m.cpm || 0));
        const minCPM = Math.min(...measurements.map(m => m.cpm || 0));
        
        // Update stats in the UI
        const totalEl = document.getElementById('total-measurements');
        const avgEl = document.getElementById('avg-cpm');
        const maxEl = document.getElementById('max-cpm');
        const minEl = document.getElementById('min-cpm');
        
        if (totalEl) totalEl.textContent = totalMeasurements;
        if (avgEl) avgEl.textContent = avgCPM.toFixed(1);
        if (maxEl) maxEl.textContent = maxCPM;
        if (minEl) minEl.textContent = minCPM;
        
    } catch (error) {
        console.error('Error loading measurement data:', error);
    }
};

// Global functions for map controls
window.toggleHeatmap = () => {
    if (window.bgeigieMapInstance && window.currentMarkers) {
        // Simple toggle between markers and heatmap view
        console.log('Toggle heatmap functionality - to be implemented');
    }
};

window.fitToData = () => {
    if (window.bgeigieMapInstance && window.currentMarkers && window.currentMarkers.length > 0) {
        const group = new L.featureGroup(window.currentMarkers);
        window.bgeigieMapInstance.fitBounds(group.getBounds().pad(0.1));
    }
};

window.exportData = (importId) => {
    window.open(`/bgeigie-imports/${importId}/export`, '_blank');
};

// --- GLOBAL ACTION HANDLERS (for onclick) ---
window.processImport = async (importId) => {
    try {
        const response = await fetch(`/bgeigie-imports/${importId}/process`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${window.appState.token}` }
        });
        if (response.ok) {
            alert('Import processed successfully!');
            // Refresh the imports list to show updated status
            await renderBGeigieImportsView();
        } else {
            const error = await response.json();
            alert(`Failed to process import: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error processing import:', error);
        alert('Failed to process import');
    }
};

window.approveImport = async (importId) => {
    try {
        const response = await fetch(`/bgeigie-imports/${importId}/approve`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${window.appState.token}` }
        });
        if (response.ok) {
            alert('Import approved successfully!');
            // Refresh the imports list
            await renderBGeigieImportsView();
        } else {
            const error = await response.json();
            alert(`Failed to approve import: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error approving import:', error);
        alert('Error approving import.');
    }
};

window.rejectImport = async (importId) => {
    try {
        const response = await fetch(`/bgeigie-imports/${importId}/reject`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${window.appState.token}` }
        });
        if (response.ok) {
            alert('Import rejected successfully!');
            // Refresh the imports list
            await renderBGeigieImportsView();
        } else {
            const error = await response.json();
            alert(`Error rejecting import: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error rejecting import:', error);
        alert('Error rejecting import.');
    }
};

window.deleteImport = async (importId) => {
    try {
        const response = await fetch(`/bgeigie-imports/${importId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${window.appState.token}` }
        });
        if (response.ok) {
            alert('Import deleted successfully!');
            // Refresh the imports list
            await renderBGeigieImportsView();
        } else {
            const error = await response.json();
            alert(`Failed to delete import: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error deleting import:', error);
        alert('Failed to delete import');
    }
};
