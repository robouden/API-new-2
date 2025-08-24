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
                        <th data-column="id">ID</th>
                        <th data-column="source">Source</th>
                        <th data-column="md5sum">MD5 Sum</th>
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
            const response = await fetch('/bgeigie_imports/', { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                const imports = await response.json();
                importsTableBody.innerHTML = '';
                imports.forEach(imp => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${imp.id}</td><td>${imp.source}</td><td>${imp.md5sum}</td>`;
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
            const response = await fetch('/bgeigie_imports/', {
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
            const response = await fetch('/bgeigie_imports/', { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) throw new Error('Failed to fetch bGeigie imports');
            
            const imports = await response.json();
            let tableHtml = `<h2>bGeigie Imports</h2>
                <table id="bgeigie-imports-table">
                    <thead>
                        <tr><th>ID</th><th>Source</th><th>MD5 Sum</th></tr>
                    </thead>
                    <tbody>`;
            imports.forEach(imp => {
                tableHtml += `<tr><td>${imp.id}</td><td>${imp.source}</td><td>${imp.md5sum}</td></tr>`;
            });
            tableHtml += `</tbody></table>`;
            apiDocumentation.innerHTML = tableHtml;
        } catch (error) {
            console.error('Error rendering bGeigie imports view:', error);
            apiDocumentation.innerHTML = `<p>Error loading bGeigie imports.</p>`;
        }
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

    // Initial Load
    fetchUserData();
});
