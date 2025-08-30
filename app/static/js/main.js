document.addEventListener('DOMContentLoaded', () => {
    // State
    let token = localStorage.getItem('token');

    // Elements
    const authNav = document.getElementById('auth-nav');
    const userInfo = document.getElementById('user-info');
    const userEmailSpan = document.getElementById('user-email');
    const logoutButton = document.getElementById('logout-button');
    const apiDocumentation = document.getElementById('api-documentation');
    const staticApiDocs = document.getElementById('static-api-docs');
    
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');

    // Modal triggers
    document.getElementById('signin-link').addEventListener('click', () => loginModal.classList.remove('hidden'));
    document.getElementById('register-link').addEventListener('click', () => signupModal.classList.remove('hidden'));

    // --- Modal Handling ---

    // Function to close all modals
    const closeAllModals = () => {
        loginModal.classList.add('hidden');
        signupModal.classList.add('hidden');
    }

    // Close button listeners
    const loginCloseButton = loginModal.querySelector('.close-button');
    if (loginCloseButton) {
        loginCloseButton.addEventListener('click', () => {
            loginModal.classList.add('hidden');
        });
    }


    const signupCloseButton = signupModal.querySelector('.close-button');
    if (signupCloseButton) {
        signupCloseButton.addEventListener('click', () => {
            signupModal.classList.add('hidden');
        });
    }

    // Click outside to close
    window.addEventListener('click', (event) => {
        if (event.target === loginModal || event.target === signupModal) {
            closeAllModals();
        }
    });

    // UI update functions
    const updateUIForLoggedIn = (user) => {
        authNav.classList.add('hidden');
        userInfo.classList.remove('hidden');
        userEmailSpan.textContent = user.email;
        loginModal.classList.add('hidden');
        staticApiDocs.classList.add('hidden');
        apiDocumentation.classList.remove('hidden');
        fetchDashboardContent(user);
    };

    const updateUIForLoggedOut = () => {
        authNav.classList.remove('hidden');
        userInfo.classList.add('hidden');
        localStorage.removeItem('token');
        token = null;
        staticApiDocs.classList.remove('hidden');
        apiDocumentation.classList.add('hidden');
        clearDashboardContent();
    };

    // API calls
    const fetchUserData = async () => {
        if (!token) {
            updateUIForLoggedOut();
            return;
        }
        try {
            const response = await fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                const user = await response.json();
                updateUIForLoggedIn(user);
            } else {
                updateUIForLoggedOut();
            }
        } catch (error) {
            console.error('Error fetching user data:', error);
            updateUIForLoggedOut();
        }
    };

    // Event Listeners
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(loginForm);

        try {
            const response = await fetch('/users/token', { method: 'POST', body: formData });
            if (response.ok) {
                const data = await response.json();
                token = data.access_token;
                localStorage.setItem('token', token);
                fetchUserData();
            } else {
                alert('Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
        }
    });

    signupForm.addEventListener('submit', async (e) => {
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
                signupModal.classList.add('hidden');
                loginModal.classList.remove('hidden');
            } else {
                const error = await response.json();
                alert(`Signup failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('Signup error:', error);
        }
    });

    logoutButton.addEventListener('click', updateUIForLoggedOut);

    // Sidebar navigation
    const sidebarLinks = document.querySelectorAll('aside ul li a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.textContent.trim();
            renderContent(section);

            // Update active link
            sidebarLinks.forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });


    const fetchDashboardContent = (user) => {
        apiDocumentation.innerHTML = `
            <h3>Your API Key: <code>${user.api_key}</code></h3>

            <h2>Upload bGeigie Log File</h2>
            <form id="upload-form">
                <input type="file" id="file-input" accept=".log" required>
                <button type="submit">Upload</button>
            </form>

            <h2>Your Imports</h2>
            <table id="imports-table">
                <thead>
                    <tr>
                        <th onclick="sortImports('id')">ID</th>
                        <th onclick="sortImports('created_at')">Uploaded At</th>
                        <th onclick="sortImports('user_id')">User</th>
                        <th onclick="sortImports('source')">File Name</th>
                        <th onclick="sortImports('measurements_count')">Measurements Count</th>
                        <th onclick="sortImports('status')">Status</th>
                        <th onclick="sortImports('description')">Comment</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
        `;

        // Add event listeners for the new elements
        document.getElementById('upload-form').addEventListener('submit', handleUpload);
        document.querySelectorAll('#imports-table th').forEach((header, index) => {
            header.addEventListener('click', () => {
                const currentOrder = header.dataset.order || 'desc';
                const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
                header.dataset.order = newOrder;
                sortTable(index, newOrder);
            });
        });

        fetchImports();
    };

    const clearDashboardContent = () => {
        apiDocumentation.innerHTML = '';
    };

    const fetchImports = async () => {
        const importsTableBody = document.querySelector('#imports-table tbody');
        try {
            const response = await fetch('/bgeigie-imports/', { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                const imports = await response.json();
                importsTableBody.innerHTML = '';
                imports.forEach(imp => {
                    const row = document.createElement('tr');
                    row.style.cursor = 'pointer';
                    row.innerHTML = `<td>${imp.id}</td><td>${imp.source}</td><td>${imp.md5sum}</td>`;
                    row.addEventListener('click', () => {
                        window.open(`/bgeigie-imports/${imp.id}/detail`, '_blank');
                    });
                    importsTableBody.appendChild(row);
                });
            } else {
                console.error('Failed to fetch imports');
            }
        } catch (error) {
            console.error('Error fetching imports:', error);
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        if (!file) { alert('Please select a file.'); return; }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/bgeigie-imports/', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            if (response.ok) {
                alert('File uploaded successfully!');
                fetchImports();
                document.getElementById('upload-form').reset();
            } else {
                const error = await response.json();
                alert(`Upload failed: ${error.detail}`);
            }
        } catch (error) {
            console.error('Upload error:', error);
        }
    };

    const sortTable = (columnIndex, order) => {
        const importsTableBody = document.querySelector('#imports-table tbody');
        const rows = Array.from(importsTableBody.querySelectorAll('tr'));
        const sortedRows = rows.sort((a, b) => {
            const aText = a.children[columnIndex].textContent.trim();
            const bText = b.children[columnIndex].textContent.trim();
            const aValue = isNaN(parseFloat(aText)) ? aText : parseFloat(aText);
            const bValue = isNaN(parseFloat(bText)) ? bText : parseFloat(bText);
            if (aValue < bValue) return order === 'asc' ? -1 : 1;
            if (aValue > bValue) return order === 'asc' ? 1 : -1;
            return 0;
        });
        importsTableBody.innerHTML = '';
        sortedRows.forEach(row => importsTableBody.appendChild(row));
    };

    const renderContent = async (section) => {
        if (!token) return; // Do nothing if not logged in

        // Preserve the user object from the initial login
        const response = await fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) {
            updateUIForLoggedOut();
            return;
        }
        const user = await response.json();

        switch (section) {
            case 'Safecast API':
                fetchDashboardContent(user);
                break;
            case 'Users':
                await renderUsersView();
                break;
            case 'Measurements':
                await renderMeasurementsView();
                break;
            case 'Devices':
                await renderDevicesView();
                break;
            case 'bGeigie Imports':
                await renderBGeigieImportsView();
                break;
            case 'Device Stories':
                await renderDeviceStoriesView();
                break;
            default:
                apiDocumentation.innerHTML = `<h2>${section}</h2><p>Content for this section is not yet available.</p>`;
                break;
        }
    };

    const renderDeviceStoriesView = async () => {
        try {
            // Fetch stories and devices
            const [storiesRes, devicesRes] = await Promise.all([
                fetch('/device_stories/', { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch('/devices/', { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (!storiesRes.ok) throw new Error('Failed to fetch device stories');
            if (!devicesRes.ok) throw new Error('Failed to fetch devices');

            const stories = await storiesRes.json();
            const devices = await devicesRes.json();

            // Form for creating a new story
            let formHtml = `<h2>Create a New Device Story</h2>
                <form id="create-story-form">
                    <select id="story-device-id" required>
                        <option value="">Select a Device</option>`;
            devices.forEach(device => {
                formHtml += `<option value="${device.id}">Device ID: ${device.id} (Unit: ${device.unit})</option>`;
            });
            formHtml += `</select>
                    <input type="text" id="story-title" placeholder="Story Title" required>
                    <textarea id="story-content" placeholder="Your Story" required></textarea>
                    <button type="submit">Create Story</button>
                </form>`;

            // Table of existing stories
            let tableHtml = `<h2>Device Stories</h2>
                <table id="device-stories-table">
                    <thead>
                        <tr><th>ID</th><th>Title</th><th>Device ID</th></tr>
                    </thead>
                    <tbody>`;
            stories.forEach(story => {
                tableHtml += `<tr><td>${story.id}</td><td>${story.title}</td><td>${story.device_id}</td></tr>`;
            });
            tableHtml += `</tbody></table>`;

            apiDocumentation.innerHTML = formHtml + tableHtml;

            // Add event listener for the new form
            document.getElementById('create-story-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const device_id = document.getElementById('story-device-id').value;
                const title = document.getElementById('story-title').value;
                const content = document.getElementById('story-content').value;

                const response = await fetch('/device_stories/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ device_id: parseInt(device_id), title, content })
                });

                if (response.ok) {
                    renderDeviceStoriesView(); // Refresh the view
                } else {
                    const error = await response.json();
                    alert(`Failed to create story: ${error.detail}`);
                }
            });

        } catch (error) {
            console.error('Error rendering device stories view:', error);
            apiDocumentation.innerHTML = `<p>Error loading device stories.</p>`;
        }
    };

    const renderBGeigieImportsView = async () => {
        try {
            const [importsRes, userRes] = await Promise.all([
                fetch('/bgeigie-imports/', { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${token}` } })
            ]);
            
            if (!importsRes.ok) throw new Error('Failed to fetch bGeigie imports');
            if (!userRes.ok) throw new Error('Failed to fetch user data');
            
            const imports = await importsRes.json();
            const currentUser = await userRes.json();
            
            let html = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>bGeigie Imports</h2>
                    <button id="upload-btn" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Upload</button>
                </div>
                
                <div id="upload-section" style="display: none; margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa;">
                    <h3>Upload bGeigie Log File</h3>
                    <form id="bgeigie-upload-form">
                        <input type="file" id="bgeigie-file-input" accept=".log" required style="margin-bottom: 10px;">
                        <div>
                            <button type="submit" style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;">Upload</button>
                            <button type="button" id="cancel-upload" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Cancel</button>
                        </div>
                    </form>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <button class="filter-btn active" data-filter="all">All</button>
                        <button class="filter-btn" data-filter="unprocessed">New</button>
                        <button class="filter-btn" data-filter="processed">Processed</button>
                        <button class="filter-btn" data-filter="submitted">Submitted</button>
                        <button class="filter-btn" data-filter="approved">Approved</button>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="owner-filter-btn active" data-owner="yours">Yours</button>
                        <button class="owner-filter-btn" data-owner="everyone">Everyone</button>
                    </div>
                </div>
                
                <div style="margin-bottom: 10px;">
                    <span id="results-count">${imports.length} results.</span>
                </div>
                
                <table id="bgeigie-imports-table" style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                    <thead style="background-color: #f5f5f5;">
                        <tr>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="id">ID ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="created_at">Uploaded At ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="user">User ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="source">File Name ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="measurements_count"># of Measurements ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px; cursor: pointer;" data-sort="status">Status ↕</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Comment</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="imports-tbody">
                    </tbody>
                </table>
            `;
            
            apiDocumentation.innerHTML = html;
            
            // Store imports data for filtering/sorting
            window.importsData = imports;
            window.currentUser = currentUser;
            window.currentFilter = 'all';
            window.currentOwner = 'yours';
            window.sortField = 'id';
            window.sortOrder = 'desc';
            
            // Add upload event listeners
            document.getElementById('upload-btn').addEventListener('click', () => {
                document.getElementById('upload-section').style.display = 'block';
            });
            
            document.getElementById('cancel-upload').addEventListener('click', () => {
                document.getElementById('upload-section').style.display = 'none';
                document.getElementById('bgeigie-upload-form').reset();
            });
            
            document.getElementById('bgeigie-upload-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileInput = document.getElementById('bgeigie-file-input');
                const file = fileInput.files[0];
                if (!file) { 
                    alert('Please select a file.'); 
                    return; 
                }

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/bgeigie-imports/', {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` },
                        body: formData
                    });
                    if (response.ok) {
                        alert('File uploaded successfully!');
                        document.getElementById('upload-section').style.display = 'none';
                        document.getElementById('bgeigie-upload-form').reset();
                        // Refresh the imports view
                        renderBGeigieImportsView();
                    } else {
                        const error = await response.json();
                        alert(`Upload failed: ${error.detail}`);
                    }
                } catch (error) {
                    console.error('Upload error:', error);
                    alert('Upload failed: Network error');
                }
            });
            
            // Add filter event listeners
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    window.currentFilter = e.target.dataset.filter;
                    renderImportsTable();
                });
            });
            
            document.querySelectorAll('.owner-filter-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    document.querySelectorAll('.owner-filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    window.currentOwner = e.target.dataset.owner;
                    renderImportsTable();
                });
            });
            
            document.querySelectorAll('th[data-sort]').forEach(th => {
                th.addEventListener('click', (e) => {
                    const field = e.target.dataset.sort;
                    if (window.sortField === field) {
                        window.sortOrder = window.sortOrder === 'asc' ? 'desc' : 'asc';
                    } else {
                        window.sortField = field;
                        window.sortOrder = 'desc';
                    }
                    renderImportsTable();
                });
            });
            
            renderImportsTable();
            
        } catch (error) {
            console.error('Error rendering bGeigie imports view:', error);
            apiDocumentation.innerHTML = `<p>Error loading bGeigie imports.</p>`;
        }
    };
    
    const renderImportsTable = () => {
        const tbody = document.getElementById('imports-tbody');
        if (!tbody || !window.importsData) return;
        
        let filteredImports = window.importsData;
        
        // Filter by ownership
        if (window.currentOwner === 'yours') {
            filteredImports = filteredImports.filter(imp => imp.user_id === window.currentUser.id);
        }
        
        // Filter by status
        if (window.currentFilter !== 'all') {
            filteredImports = filteredImports.filter(imp => imp.status === window.currentFilter);
        }
        
        // Sort
        filteredImports.sort((a, b) => {
            let aVal = a[window.sortField];
            let bVal = b[window.sortField];
            
            if (window.sortField === 'created_at') {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }
            
            if (aVal < bVal) return window.sortOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return window.sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
        
        // Update results count
        document.getElementById('results-count').textContent = `${filteredImports.length} results.`;
        
        // Render rows
        tbody.innerHTML = '';
        filteredImports.forEach(imp => {
            const row = document.createElement('tr');
            row.style.cursor = 'pointer';
            row.style.borderBottom = '1px solid #ddd';
            
            const createdAt = new Date(imp.created_at || Date.now()).toLocaleDateString() + ' ' + 
                             new Date(imp.created_at || Date.now()).toLocaleTimeString();
            
            const statusColor = {
                'unprocessed': '#ffc107',
                'processed': '#17a2b8', 
                'submitted': '#007bff',
                'approved': '#28a745',
                'rejected': '#dc3545'
            }[imp.status] || '#6c757d';
            
            row.innerHTML = `
                <td style="border: 1px solid #ddd; padding: 8px; color: #007bff;">${imp.id}</td>
                <td style="border: 1px solid #ddd; padding: 8px; color: #007bff;">${createdAt}</td>
                <td style="border: 1px solid #ddd; padding: 8px; color: #007bff;">User ${imp.user_id}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${imp.source}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${imp.measurements_count || 0}<br><small>maximum cpm: ${imp.max_cpm || 'N/A'}</small></td>
                <td style="border: 1px solid #ddd; padding: 8px; color: ${statusColor}; font-weight: bold;">${imp.status || 'unprocessed'}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">${imp.description || ''}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <button class="btn btn-sm btn-primary" onclick="processImport(${imp.id}); event.stopPropagation();">Process</button>
                </td>
            `;
            
            row.addEventListener('click', () => {
                window.location.href = `/bgeigie-imports/${imp.id}/detail`;
            });
            
            tbody.appendChild(row);
        });
    };

    const renderDevicesView = async () => {
        try {
            const response = await fetch('/devices/', { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('Failed to fetch devices');
            
            const devices = await response.json();
            let tableHtml = `<h2>Devices</h2>
                <table id="devices-table">
                    <thead>
                        <tr><th>ID</th><th>bGeigie Import ID</th><th>Unit</th><th>Sensor</th></tr>
                    </thead>
                    <tbody>`;
            devices.forEach(device => {
                tableHtml += `<tr><td>${device.id}</td><td>${device.bgeigie_import_id}</td><td>${device.unit}</td><td>${device.sensor}</td></tr>`;
            });
            tableHtml += `</tbody></table>`;
            apiDocumentation.innerHTML = tableHtml;
        } catch (error) {
            console.error('Error rendering devices view:', error);
            apiDocumentation.innerHTML = `<p>Error loading devices.</p>`;
        }
    };

    const renderMeasurementsView = async () => {
        try {
            const response = await fetch('/measurements/', { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('Failed to fetch measurements');
            
            const measurements = await response.json();
            let tableHtml = `<h2>Measurements</h2>
                <table id="measurements-table">
                    <thead>
                        <tr><th>ID</th><th>CPM</th><th>Latitude</th><th>Longitude</th><th>Captured At</th></tr>
                    </thead>
                    <tbody>`;
            measurements.forEach(m => {
                tableHtml += `<tr><td>${m.id}</td><td>${m.cpm}</td><td>${m.latitude}</td><td>${m.longitude}</td><td>${new Date(m.captured_at).toLocaleString()}</td></tr>`;
            });
            tableHtml += `</tbody></table>`;
            apiDocumentation.innerHTML = tableHtml;
        } catch (error) {
            console.error('Error rendering measurements view:', error);
            apiDocumentation.innerHTML = `<p>Error loading measurements.</p>`;
        }
    };

    const renderUsersView = async () => {
        try {
            const [usersRes, currentUserRes] = await Promise.all([
                fetch('/users/users/all', { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch('/users/users/me', { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (!usersRes.ok) throw new Error('Failed to fetch users');
            if (!currentUserRes.ok) throw new Error('Failed to fetch current user');

            const users = await usersRes.json();
            const currentUser = await currentUserRes.json();

            let tableHtml = `<h2>Users</h2>
                <table id="users-table">
                    <thead>
                        <tr><th>ID</th><th>Email</th><th>Is Active</th><th>Role</th><th>API Key</th>`;
            if (currentUser.role === 'admin') {
                tableHtml += `<th>Actions</th>`;
            }
            tableHtml += `</tr></thead><tbody>`;

            users.forEach(user => {
                tableHtml += `<tr>
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                    <td>${user.is_active}</td>
                    <td>${user.role}</td>
                    <td>${user.api_key}</td>`;
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
            apiDocumentation.innerHTML = tableHtml;

            if (currentUser.role === 'admin') {
                document.querySelectorAll('.role-select').forEach(select => {
                    select.addEventListener('change', async (e) => {
                        const userId = e.target.dataset.userId;
                        const newRole = e.target.value;
                        try {
                            const response = await fetch(`/users/${userId}/role`, {
                                method: 'PUT',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({ role: newRole })
                            });
                            if (response.ok) {
                                alert('User role updated successfully.');
                                renderUsersView(); // Refresh the view
                            } else {
                                const error = await response.json();
                                alert(`Failed to update role: ${error.detail}`);
                            }
                        } catch (error) {
                            console.error('Error updating user role:', error);
                        }
                    });
                });
            }
        } catch (error) {
            console.error('Error rendering users view:', error);
            apiDocumentation.innerHTML = `<p>Error loading users.</p>`;
        }
    };


    // Process import function
    window.processImport = async (importId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/bgeigie-imports/${importId}/process`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Successfully processed ${result.message}`);
                // Refresh the imports list
                if (window.location.hash === '#bgeigie-imports') {
                    renderBGeigieImportsView();
                }
            } else {
                const error = await response.json();
                alert(`Error processing import: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error processing import:', error);
            alert('Error processing import. Please try again.');
        }
    };

    // Approve import function
    window.approveImport = async (importId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/bgeigie-imports/${importId}/approve`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                alert('Import approved successfully!');
                // Refresh the imports list
                if (window.location.hash === '#bgeigie-imports') {
                    renderBGeigieImportsView();
                }
            } else {
                const error = await response.json();
                alert(`Error approving import: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error approving import:', error);
            alert('Error approving import. Please try again.');
        }
    };

    // Reject import function
    window.rejectImport = async (importId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/bgeigie-imports/${importId}/reject`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                alert('Import rejected successfully!');
                // Refresh the imports list
                if (window.location.hash === '#bgeigie-imports') {
                    renderBGeigieImportsView();
                }
            } else {
                const error = await response.json();
                alert(`Error rejecting import: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error rejecting import:', error);
            alert('Error rejecting import. Please try again.');
        }
    };

    // Set up navigation
    setupNavigation();
});
