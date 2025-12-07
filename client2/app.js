// Frontend logic for Internship Finder
const API_BASE = 'http://127.0.0.1:5000/api';

// Prevent all form submissions globally
document.addEventListener('submit', (e) => {
  e.preventDefault();
  return false;
}, true);

// Diagnostic: log unload/storage events and localStorage changes to help trace unexpected reloads
window.addEventListener('beforeunload', (e) => {
  try {
    console.log('DIAG: beforeunload fired', { auth_token: localStorage.getItem('auth_token'), user_role: localStorage.getItem('user_role') });
  } catch (err) { console.error('DIAG beforeunload err', err); }
});
window.addEventListener('unload', (e) => {
  try {
    console.log('DIAG: unload fired', { auth_token: localStorage.getItem('auth_token'), user_role: localStorage.getItem('user_role') });
  } catch (err) { console.error('DIAG unload err', err); }
});
window.addEventListener('pagehide', (e) => {
  try {
    console.log('DIAG: pagehide fired', { auth_token: localStorage.getItem('auth_token'), user_role: localStorage.getItem('user_role') });
  } catch (err) { console.error('DIAG pagehide err', err); }
});
window.addEventListener('storage', (e) => {
  try {
    console.log('DIAG: storage event', e);
  } catch (err) { console.error('DIAG storage err', err); }
});

// Polling guard: detect when auth_token is changed/cleared and log stack for diagnosis
(() => {
  try {
    let lastAuth = localStorage.getItem('auth_token');
    setInterval(() => {
      try {
        const cur = localStorage.getItem('auth_token');
        if (cur !== lastAuth) {
          console.log('DIAG: auth_token changed', { from: lastAuth, to: cur, stack: (new Error()).stack });
          lastAuth = cur;
        }
      } catch (err) { console.error('DIAG polling err', err); }
    }, 400);
  } catch (err) { console.error('DIAG setup err', err); }
})();
// Globals
let userRole = null; // 'student' | 'admin'

// Elements
const qInput = document.getElementById('search-q');
const catSelect = document.getElementById('filter-category');
const searchBtn = document.getElementById('search-btn');
const refreshBtn = document.getElementById('refresh-btn');
const resultsDiv = document.getElementById('results');
const trackerList = document.getElementById('tracker-list');
const addForm = document.getElementById('add-internship-form');
const addStatus = document.getElementById('add-i-status');
const adminSection = document.getElementById('admin-section');

const showSignup = document.getElementById('show-signup');
const showLogin = document.getElementById('show-login');
const showAdminSignup = document.getElementById('show-admin-signup');
const showAdminLogin = document.getElementById('show-admin-login');
const showProfileBtn = document.getElementById('show-profile');

const signupForm = document.getElementById('signup-form');
const adminSignupForm = document.getElementById('admin-signup-form');
const loginForm = document.getElementById('login-form');
const adminLoginForm = document.getElementById('admin-login-form');

const signupBtn = document.getElementById('signup-btn');
const adminSignupBtn = document.getElementById('admin-signup-btn');
const loginBtn = document.getElementById('login-btn');
const adminLoginBtn = document.getElementById('admin-login-btn');

const logoutBtn = document.getElementById('logout');
const userInfo = document.getElementById('user-info');
const profileSection = document.getElementById('profile-section');
const saveProfileBtn = document.getElementById('save-profile-btn');
const profileStatus = document.getElementById('profile-status');

// Global click logger (capture) to diagnose click events on tracker save buttons
document.addEventListener('click', (e) => {
  try {
    if (e.target && e.target.matches && e.target.matches('.tracker-save')) {
      console.log('CAPTURE: tracker-save clicked (document listener)', { id: e.target.getAttribute('data-id') });
    }
    if (e.target && e.target.matches && e.target.matches('.track-btn')) {
      console.log('CAPTURE: +Tracker clicked', { id: e.target.getAttribute('data-id') });
    }
  } catch (err) {
    console.error('Error in global click logger', err);
  }
}, true);

function authHeader() {
  const t = localStorage.getItem('auth_token');
  return t ? { 'Authorization': `Bearer ${t}` } : {};
}

async function fetchInternships(q, category) {
  try {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (category) params.set('category', category);
    const res = await fetch(`${API_BASE}/internships?${params.toString()}`);
    return await res.json();
  } catch (e) {
    console.error('Error fetching internships:', e);
    return null;
  }
}

function renderInternships(list) {
  resultsDiv.innerHTML = '';
  if (!list || list.length === 0) {
    resultsDiv.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:#999;">No internships found. Try a different search.</div>';
    return;
  }
  
  // Create collapse toggle button at the top
  const collapseContainer = document.createElement('div');
  collapseContainer.style.cssText = 'grid-column:1/-1;padding:10px;background:#f0f0f0;border-radius:5px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;';
  collapseContainer.innerHTML = `
    <span style="font-weight:bold;">${list.length} internships found</span>
    <button id="toggle-results" class="btn btn-secondary" style="padding:6px 12px;font-size:12px;">Collapse</button>
  `;
  resultsDiv.appendChild(collapseContainer);
  
  // Create results container
  const resultsContainer = document.createElement('div');
  resultsContainer.id = 'internships-container';
  resultsContainer.style.cssText = 'grid-column:1/-1;display:contents;';
  
  list.forEach(i => {
    const div = document.createElement('div');
    div.className = 'intern';
      const deadline = i.deadline ? i.deadline : 'N/A';
    
    // Build HTML with conditional fields
    let html = `<h4>${i.name}</h4>`;
    
    if (i.organization && i.organization !== 'nan' && i.organization !== 'Unknown') {
      html += `<div><strong>${i.organization}</strong></div>`;
    }
    
    if (i.location && i.location !== 'nan' && i.location !== 'Unknown') {
      html += `<div>📍 ${i.location}</div>`;
    }
    
    if (i.category && i.category !== 'nan') {
      html += `<div>🏷️ ${i.category}</div>`;
    }
    
    if (i.deadline && i.deadline !== 'nan') {
        html += `<div><small style="color:#f00;">📅 Deadline: ${i.deadline}</small></div>`;
    }
    
    if (i.description && i.description !== 'nan') {
      html += `<div style="height:60px;overflow:hidden;font-size:13px;color:#666;margin:8px 0;">${i.description}</div>`;
    }
    
    if (i.contact && i.contact !== 'nan' && i.contact !== 'contact@example.com') {
      html += `<div><small>📧 ${i.contact}</small></div>`;
    }
    
    const visitSiteHTML = (i.Url && i.Url !== '') 
      ? `<a href="${i.Url}" target="_blank" class="btn btn-primary">Visit Site</a>` 
      : '';
    
    html += `<div class="button-group">
      <button type="button" class="track-btn btn btn-secondary" data-id="${i.id}">+ Tracker</button>
      ${visitSiteHTML}
    </div>`;
    
    div.innerHTML = html;
    resultsContainer.appendChild(div);
  });
  
  resultsDiv.appendChild(resultsContainer);
  
  // Add collapse toggle functionality
  const toggleBtn = document.getElementById('toggle-results');
  let isCollapsed = false;
  toggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    isCollapsed = !isCollapsed;
    const container = document.getElementById('internships-container');
    if (isCollapsed) {
      container.style.display = 'none';
      toggleBtn.textContent = 'Expand';
    } else {
      container.style.display = 'contents';
      toggleBtn.textContent = 'Collapse';
    }
  });
}

async function loadCategories() {
  try {
    const json = await fetchInternships();
    if (json && json.internships) {
      const cats = new Set(json.internships.map(i => i.category).filter(Boolean));
      catSelect.innerHTML = '<option value="">All Categories</option>' + [...cats].map(c => `<option value="${c}">${c}</option>`).join('');
    }
  } catch (e) {
    console.error('Error loading categories:', e);
  }
}

async function loadAndRender() {
  const q = qInput.value.trim();
  const cat = catSelect.value;
  const json = await fetchInternships(q, cat);
  if (json && json.internships) renderInternships(json.internships);
}

searchBtn.addEventListener('click', e => { e.preventDefault(); loadAndRender(); });
refreshBtn.addEventListener('click', e => { e.preventDefault(); qInput.value = ''; catSelect.value = ''; loadAndRender(); });

// Add to tracker function (used by both regular search and recommendations)
async function addToTracker(internId) {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    alert('Please login to track internships');
    return;
  }
  const resp = await fetch(`${API_BASE}/tracker`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ internshipId: internId, status: 'interested' })
  });
  const j = await resp.json();
  if (j.success) {
    alert('Added to tracker!');
    loadTracker();
  } else {
    alert('Error: ' + (j.details || j.error));
  }
}

// Add to tracker handler
resultsDiv.addEventListener('click', async (e) => {
  if (e.target.classList.contains('track-btn')) {
    const id = e.target.dataset.id;
    addToTracker(id);
  }
});

// Add internship (admin)
addForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  e.stopPropagation();
  addStatus.textContent = '';
  const payload = {
    name: document.getElementById('i-name').value,
    organization: document.getElementById('i-org').value,
    Url: document.getElementById('i-url').value,
    contact: document.getElementById('i-contact').value,
    deadline: document.getElementById('i-deadline').value,
    category: document.getElementById('i-category').value,
    location: document.getElementById('i-location').value,
    description: document.getElementById('i-desc').value
  };
  const resp = await fetch(`${API_BASE}/internships`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(payload)
  });
  const j = await resp.json();
  if (j.success) {
    addStatus.innerHTML = '<span style="color:green;">✓ Internship added successfully!</span>';
    addForm.reset();
    loadAndRender();
    loadCategories();
  } else {
    addStatus.innerHTML = '<span style="color:red;">✗ Error: ' + (j.details || j.error) + '</span>';
  }
  return false;
});

// Signup/login toggles
showSignup.addEventListener('click', () => {
  signupForm.style.display = 'block';
  adminSignupForm.style.display = 'none';
  loginForm.style.display = 'none';
  adminLoginForm.style.display = 'none';
});

showAdminSignup.addEventListener('click', () => {
  signupForm.style.display = 'none';
  adminSignupForm.style.display = 'block';
  loginForm.style.display = 'none';
  adminLoginForm.style.display = 'none';
});

showLogin.addEventListener('click', () => {
  signupForm.style.display = 'none';
  adminSignupForm.style.display = 'none';
  loginForm.style.display = 'block';
  adminLoginForm.style.display = 'none';
});

showAdminLogin.addEventListener('click', () => {
  signupForm.style.display = 'none';
  adminSignupForm.style.display = 'none';
  loginForm.style.display = 'none';
  adminLoginForm.style.display = 'block';
});

// Student Signup
signupBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  const payload = {
    username: document.getElementById('su-username').value,
    password: document.getElementById('su-password').value,
    first_name: document.getElementById('su-first').value,
    last_name: document.getElementById('su-last').value,
    school: document.getElementById('su-school').value,
    email_personal: document.getElementById('su-emailp').value,
    email_school: document.getElementById('su-emails').value,
    age: document.getElementById('su-age').value,
    grade: document.getElementById('su-grade').value
    ,extracurriculars: document.getElementById('su-extracurriculars').value,
    interests: document.getElementById('su-interests').value,
    gpa: document.getElementById('su-gpa').value,
    courses: document.getElementById('su-courses').value
  };
  const res = await fetch(`${API_BASE}/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const j = await res.json();
  const status = document.getElementById('signup-status');
  if (j.success) {
    localStorage.setItem('auth_token', j.auth_token);
    localStorage.setItem('user_role', 'student');
    status.innerHTML = '<span style="color:green;">✓ Signup successful!</span>';
    userRole = 'student';
    setLoggedIn('Student');
  } else {
    status.innerHTML = '<span style="color:red;">✗ ' + (j.details || j.error) + '</span>';
  }
});

// Profile button shows/hides profile section
showProfileBtn && showProfileBtn.addEventListener('click', (e) => {
  e.preventDefault();
  if (!profileSection) return;
  profileSection.style.display = profileSection.style.display === 'none' ? 'block' : 'none';
});

async function fetchProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile`, { headers: { ...authHeader() } });
    if (!res.ok) return null;
    const j = await res.json();
    if (j.success) return j.user;
    return null;
  } catch (e) {
    console.error('Error fetching profile:', e);
    return null;
  }
}

function makeChipsFromCSV(csv) {
  if (!csv) return [];
  return csv.split(',').map(s => s.trim()).filter(Boolean);
}

function renderProfileMeta(profile) {
  try {
    const initials = ((profile.first_name || '').charAt(0) + (profile.last_name || '').charAt(0)).toUpperCase() || 'S';
    const avatar = document.getElementById('profile-avatar');
    const metaName = document.getElementById('meta-name');
    const metaSchool = document.getElementById('meta-school');
    const chipsContainer = document.getElementById('meta-chips');
    if (avatar) avatar.textContent = initials;
    if (metaName) metaName.textContent = `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || 'Student';
    if (metaSchool) metaSchool.textContent = profile.school || '';
    if (chipsContainer) {
      chipsContainer.innerHTML = '';
      const extras = makeChipsFromCSV(profile.extracurriculars);
      const interests = makeChipsFromCSV(profile.interests);
      const courses = makeChipsFromCSV(profile.courses);
      extras.concat(interests).concat(courses).slice(0,8).forEach(x => {
        const span = document.createElement('span');
        span.className = 'chip';
        span.textContent = x;
        chipsContainer.appendChild(span);
      });
    }
  } catch (e) { console.error('renderProfileMeta error', e); }
}

async function saveProfile() {
  profileStatus.textContent = '';
  const payload = {
    first_name: document.getElementById('p-first').value,
    last_name: document.getElementById('p-last').value,
    school: document.getElementById('p-school').value,
    email_personal: document.getElementById('p-emailp').value,
    age: document.getElementById('p-age').value,
    grade: document.getElementById('p-grade').value,
    extracurriculars: document.getElementById('p-extracurriculars').value,
    interests: document.getElementById('p-interests').value,
    gpa: document.getElementById('p-gpa').value,
    courses: document.getElementById('p-courses').value
  };
  try {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(payload)
    });
    const j = await res.json();
    if (j.success) {
      profileStatus.innerHTML = '<span style="color:green;">✓ Saved</span>';
      setTimeout(() => profileStatus.textContent = '', 2000);
      // refresh meta display
      try {
        const p = await fetchProfile();
        if (p && typeof renderProfileMeta === 'function') renderProfileMeta(p);
      } catch (e) { console.error('Error refreshing profile after save', e); }
      return true;
    } else {
      profileStatus.innerHTML = '<span style="color:red;">✗ ' + (j.details || j.error || 'Failed') + '</span>';
      return false;
    }
  } catch (e) {
    profileStatus.innerHTML = '<span style="color:red;">Network error</span>';
    console.error('Error saving profile:', e);
    return false;
  }
}

saveProfileBtn && saveProfileBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  await saveProfile();
});

// Admin Signup
adminSignupBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  const payload = {
    username: document.getElementById('asu-username').value,
    password: document.getElementById('asu-password').value,
    school_name: document.getElementById('asu-school').value,
    email: document.getElementById('asu-email').value
  };
  const res = await fetch(`${API_BASE}/admin/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const j = await res.json();
  const status = document.getElementById('admin-signup-status');
  if (j.success) {
    localStorage.setItem('auth_token', j.auth_token);
    localStorage.setItem('user_role', 'admin');
    status.innerHTML = '<span style="color:green;">✓ Admin account created!</span>';
    userRole = 'admin';
    setLoggedIn('Admin');
  } else {
    status.innerHTML = '<span style="color:red;">✗ ' + (j.details || j.error) + '</span>';
  }
});

// Student Login
loginBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  e.stopPropagation();
  const payload = {
    username: document.getElementById('li-username').value,
    password: document.getElementById('li-password').value
  };
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const j = await res.json();
  const status = document.getElementById('login-status');
  if (j.success) {
    localStorage.setItem('auth_token', j.auth_token);
    localStorage.setItem('user_role', 'student');
    status.innerHTML = '<span style="color:green;">✓ Login successful!</span>';
    userRole = 'student';
    await setLoggedIn('Student');
  } else {
    status.innerHTML = '<span style="color:red;">✗ ' + (j.details || j.error) + '</span>';
  }
});

// Admin Login
adminLoginBtn.addEventListener('click', async (e) => {
  e.preventDefault();
  e.stopPropagation();
  const payload = {
    username: document.getElementById('ali-username').value,
    password: document.getElementById('ali-password').value
  };
  const res = await fetch(`${API_BASE}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const j = await res.json();
  const status = document.getElementById('admin-login-status');
  if (j.success) {
    localStorage.setItem('auth_token', j.auth_token);
    localStorage.setItem('user_role', 'admin');
    status.innerHTML = '<span style="color:green;">✓ Admin login successful!</span>';
    userRole = 'admin';
    await setLoggedIn('Admin');
  } else {
    status.innerHTML = '<span style="color:red;">✗ ' + (j.details || j.error) + '</span>';
  }
});

logoutBtn.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  console.log('Logout button clicked — clearing auth');
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_role');
  setLoggedOut();
});

async function loadTracker() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    trackerList.innerHTML = '(not logged in)';
    return;
  }
  try {
    let res;
    try {
      res = await fetch(`${API_BASE}/tracker`, { headers: { ...authHeader() } });
    } catch (err) {
      trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Network error loading tracker</div>';
      console.error('Tracker GET network error:', err);
      return;
    }
    if (res.status === 401) {
      trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Unauthorized. Your session may have expired. Please refresh or log in again.</div>';
      console.error('Tracker GET 401 Unauthorized');
      return;
    }
    if (!res.ok) {
      trackerList.innerHTML = `<div class="tracker-item" style="color:red;">Error loading tracker (${res.status})</div>`;
      console.error('Tracker GET error:', res.status, await res.text());
      return;
    }
    let j = {};
    try {
      j = await res.json();
    } catch (err) {
      trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Error parsing tracker data</div>';
      console.error('Tracker GET JSON parse error:', err);
      return;
    }
    if (j.success) {
      if (j.trackers.length === 0) {
        trackerList.innerHTML = '<div class="tracker-item">No tracked internships yet</div>';
      } else {
        // Fetch internship details for each tracked item
        const internshipMap = {};
        const ids = j.trackers.map(t => t.internshipId);
        // Fetch all internships (could optimize to fetch only needed)
        const allInternships = await fetchInternships();
        if (allInternships && allInternships.internships) {
          allInternships.internships.forEach(i => { internshipMap[i.id] = i; });
        }
        // Helper to show N/A for nan
        const show = v => (v === 'nan' || v === undefined || v === null || v === '') ? 'N/A' : v;
        trackerList.innerHTML = j.trackers.map(t => {
          const i = internshipMap[t.internshipId] || {};
          return `<div class="tracker-item" style="border:1px solid #eee;padding:10px;margin-bottom:10px;border-radius:6px;">
            <strong>${show(i.name) || t.internshipId.substring(0,8)}</strong><br/>
            ${i.organization ? `<div><strong>${show(i.organization)}</strong></div>` : ''}
            ${i.location ? `<div>📍 ${show(i.location)}</div>` : ''}
            ${i.category ? `<div>🏷️ ${show(i.category)}</div>` : ''}
            ${i.deadline ? `<div><small style='color:#f00;'>📅 Deadline: ${show(i.deadline)}</small></div>` : ''}
            ${i.description ? `<div style='font-size:13px;color:#666;margin:8px 0;'>${show(i.description)}</div>` : ''}
            ${i.Url ? `<a href='${i.Url}' target='_blank' class='btn btn-primary' style='margin-bottom:6px;'>Visit Site</a>` : ''}
            <div style='margin-top:8px;'>
              <label>Status: </label>
              <select class='tracker-status' data-id='${t.id}' style='margin-right:8px;'>
                ${['interested','applying','interviewing','accepted','rejected'].map(s => `<option value='${s}'${t.status===s?' selected':''}>${s.charAt(0).toUpperCase()+s.slice(1)}</option>`).join('')}
              </select>
              <label>Notes:</label>
              <input type='text' class='tracker-notes' data-id='${t.id}' value="${t.notes||''}" style='width:120px;margin-left:4px;' />
              <button type='button' onclick="console.log('INLINE: tracker-save', '${t.id}')" class='tracker-save btn btn-success' data-id='${t.id}' style='margin-left:8px;'>Save</button>
            </div>
          </div>`;
        }).join('');
        // Add event listeners for status/notes changes
        trackerList.querySelectorAll('.tracker-save').forEach(btn => {
          btn.addEventListener('click', async (e) => {
            console.log('tracker-save clicked', {id: btn.getAttribute('data-id'), closestForm: btn.closest('form')});
            e.preventDefault();
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const status = trackerList.querySelector(`.tracker-status[data-id='${id}']`).value;
            const notes = trackerList.querySelector(`.tracker-notes[data-id='${id}']`).value;
            const token = localStorage.getItem('auth_token');
            let resp;
            try {
              const bodyPayload = { id, status, notes };
              console.log('DIAG: About to send PATCH /api/tracker', { body: bodyPayload });
              resp = await fetch(`${API_BASE}/tracker`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', ...authHeader() },
                body: JSON.stringify(bodyPayload)
              });
              console.log('DIAG: PATCH response received', { status: resp.status, ok: resp.ok });
            } catch (err) {
              btn.textContent = 'Network error';
              console.error('Tracker PATCH network error:', err);
              return;
            }
            if (resp.status === 401) {
              btn.textContent = 'Unauthorized';
              trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Unauthorized. Please log in again.</div>';
              console.error('Tracker PATCH 401 Unauthorized');
              return;
            }
            if (!resp.ok) {
              btn.textContent = 'Error';
              const txt = await resp.text();
              console.error('Tracker PATCH error:', resp.status, txt);
              setTimeout(() => { btn.textContent = 'Save'; }, 1200);
              return;
            }
            let j = {};
            try {
              j = await resp.json();
            } catch (err) {
              btn.textContent = 'Error';
              console.error('Tracker PATCH JSON parse error:', err);
              setTimeout(() => { btn.textContent = 'Save'; }, 1200);
              return;
            }
            console.log('DIAG: PATCH parsed JSON', j);
            if (j.success) {
              btn.textContent = 'Saved!';
              setTimeout(() => { btn.textContent = 'Save'; }, 1200);
            } else {
              btn.textContent = 'Error';
              console.error('Tracker PATCH error response:', j);
              setTimeout(() => { btn.textContent = 'Save'; }, 1200);
            }
          });
        });
      }
    } else {
      trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Error loading tracker</div>';
    }
  } catch (e) {
    console.error('Error in loadTracker:', e);
    trackerList.innerHTML = '<div class="tracker-item" style="color:red;">Network error</div>';
  }
}

async function setLoggedIn(role) {
  console.log('setLoggedIn called', role);
  userInfo.textContent = `✓ ${role}`;
  userInfo.style.display = 'inline-block';
  logoutBtn.style.display = 'inline-block';
  showLogin.style.display = 'none';
  showSignup.style.display = 'none';
  showAdminLogin.style.display = 'none';
  showAdminSignup.style.display = 'none';
  signupForm.style.display = 'none';
  adminSignupForm.style.display = 'none';
  loginForm.style.display = 'none';
  adminLoginForm.style.display = 'none';

  if (userRole === 'admin') {
    adminSection.style.display = 'block';
  } else {
    adminSection.style.display = 'none';
  }

  // Fetch user tracker and profile
  await loadTracker();

  // show profile button
  showProfileBtn && (showProfileBtn.style.display = 'inline-block');

  // Try to fetch profile and populate form; if profile fields missing, prompt user to fill them
  try {
    const profile = await fetchProfile();
    if (profile) {
      // populate profile fields if available
      try { document.getElementById('p-first').value = profile.first_name || ''; } catch(e){}
      try { document.getElementById('p-last').value = profile.last_name || ''; } catch(e){}
      try { document.getElementById('p-school').value = profile.school || ''; } catch(e){}
      try { document.getElementById('p-emailp').value = profile.email_personal || ''; } catch(e){}
      try { document.getElementById('p-age').value = profile.age || ''; } catch(e){}
      try { document.getElementById('p-grade').value = profile.grade || ''; } catch(e){}
      try { document.getElementById('p-extracurriculars').value = profile.extracurriculars || ''; } catch(e){}
      try { document.getElementById('p-interests').value = profile.interests || ''; } catch(e){}
      try { document.getElementById('p-gpa').value = profile.gpa || ''; } catch(e){}
      try { document.getElementById('p-courses').value = profile.courses || ''; } catch(e){}

      const needsProfile = !(profile.extracurriculars && profile.extracurriculars.toString().trim()) || !(profile.interests && profile.interests.toString().trim()) || profile.gpa === null || profile.gpa === undefined || profile.gpa === '' || !(profile.courses && profile.courses.toString().trim());
      if (needsProfile) {
        profileSection && (profileSection.style.display = 'block');
      }
    }
  } catch (e) {
    console.error('Error populating profile after login', e);
  }

  // render profile meta (avatar, name, chips)
  try {
    if (typeof renderProfileMeta === 'function') {
      const profile = await fetchProfile();
      if (profile) renderProfileMeta(profile);
    }
  } catch (e) { console.error('Error rendering profile meta', e); }
}

function setLoggedOut() {
  console.log('setLoggedOut called — user logged out UI state applied');
  try { console.trace('DIAG: setLoggedOut stack trace'); } catch (err) { console.error('DIAG trace err', err); }
  userInfo.textContent = '';
  userInfo.style.display = 'none';
  logoutBtn.style.display = 'none';
  showLogin.style.display = 'inline-block';
  showSignup.style.display = 'inline-block';
  showAdminLogin.style.display = 'inline-block';
  showAdminSignup.style.display = 'inline-block';
  trackerList.innerHTML = '(not logged in)';
  adminSection.style.display = 'none';
  userRole = null;
}

// On load
let pageInitialized = false;
(async () => {
  if (pageInitialized) return;
  pageInitialized = true;
  
  try {
    await loadCategories();
    await loadAndRender();
  } catch (e) {
    console.error('Error loading internships:', e);
  }

  const token = localStorage.getItem('auth_token');
  const role = localStorage.getItem('user_role');
  if (token && role) {
    // Verify token with backend before showing logged-in UI
    try {
      await verifyAuthOnLoad(role);
    } catch (err) {
      console.error('Error during auth verification on load:', err);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_role');
      setLoggedOut();
    }
  }
})();

// Verify auth token by calling a lightweight authenticated endpoint.
async function verifyAuthOnLoad(role) {
  console.log('Verifying saved auth_token with backend...');
  try {
    const res = await fetch(`${API_BASE}/tracker`, { headers: { ...authHeader() } });
    if (res.status === 401) {
      console.warn('verifyAuthOnLoad: token invalid (401)');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_role');
      setLoggedOut();
      return false;
    }
    if (!res.ok) {
      console.error('verifyAuthOnLoad: unexpected response', res.status);
      // don't assume valid — clear and logout
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_role');
      setLoggedOut();
      return false;
    }
    // If we get here, token is valid — set UI and load tracker
    userRole = role;
    showAppContainer();
    await setLoggedIn(role === 'admin' ? 'Admin' : 'Student');
    return true;
  } catch (err) {
    console.error('verifyAuthOnLoad network error:', err);
    // On network errors we prefer to keep the stored token but show logged-out UI
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_role');
    setLoggedOut();
    return false;
  }
}

// HOMEPAGE & TAB SYSTEM
function showHomepage() {
  const homepage = document.getElementById('homepage');
  const appContainer = document.getElementById('app-container');
  if (homepage) homepage.style.display = 'flex';
  if (appContainer) appContainer.style.display = 'none';
}

function showAppContainer() {
  const homepage = document.getElementById('homepage');
  const appContainer = document.getElementById('app-container');
  if (homepage) homepage.style.display = 'none';
  if (appContainer) appContainer.style.display = 'block';
}

// Recommendations functions
async function loadRecommendations() {
  const container = document.getElementById('recommendations-container');
  const loading = document.getElementById('recommendations-loading');
  const btn = document.getElementById('load-recommendations-btn');
  
  container.style.display = 'none';
  loading.style.display = 'block';
  btn.disabled = true;
  
  try {
    const response = await fetch(`${API_BASE}/recommendations`, {
      method: 'GET',
      headers: {
        ...authHeader(),
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      renderRecommendations(data.recommendations);
      loading.style.display = 'none';
      container.style.display = 'grid';
    } else {
      loading.innerHTML = `<p style="color: red;">Error: ${data.error || 'Could not load recommendations'}</p>`;
    }
  } catch (error) {
    console.error('Error loading recommendations:', error);
    loading.innerHTML = `<p style="color: red;">Error loading recommendations. Please try again.</p>`;
  } finally {
    btn.disabled = false;
  }
}

function renderRecommendations(recommendations) {
  const container = document.getElementById('recommendations-container');
  container.innerHTML = '';
  
  recommendations.forEach((rec, index) => {
    const card = document.createElement('div');
    card.className = 'intern';
    
    // Conditionally show location only if it's not nan/N/A
    const locationHTML = (rec.location && rec.location !== 'N/A' && rec.location.toLowerCase() !== 'nan') 
      ? `<p class="intern-location">📍 ${rec.location}</p>` 
      : '';
    
    // Conditionally show visit site button if URL exists
    const visitSiteHTML = (rec.url && rec.url !== 'N/A' && rec.url !== 'nan') 
      ? `<a href="${rec.url}" target="_blank" class="btn btn-primary btn-visit-site">Visit Site</a>` 
      : '';
    
    card.innerHTML = `
      <div class="intern-badge">Top ${index + 1}</div>
      <h3>${rec.program_name}</h3>
      <p class="intern-company">${rec.company}</p>
      ${locationHTML}
      <p class="intern-desc">${rec.description.substring(0, 150)}...</p>
      <div class="recommendation-reason">
        <strong>Why for you:</strong> ${rec.ai_reason}
      </div>
      <div class="button-group">
        <button class="track-btn btn btn-secondary" data-id="${rec.id}">+ Add to Tracker</button>
        ${visitSiteHTML}
      </div>
    `;
    container.appendChild(card);
  });
  
  // Attach event listeners to track buttons
  document.querySelectorAll('.track-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const internId = btn.getAttribute('data-id');
      addToTracker(internId);
    });
  });
}

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    const tabName = btn.getAttribute('data-tab');
    
    // Remove active class from all buttons and contents
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    // Add active class to clicked button and corresponding content
    btn.classList.add('active');
    const tabContent = document.getElementById(tabName);
    if (tabContent) {
      tabContent.classList.add('active');
    }
  });
});

// Attach load recommendations button
const loadRecommendationsBtn = document.getElementById('load-recommendations-btn');
if (loadRecommendationsBtn) {
  loadRecommendationsBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loadRecommendations();
  });
}

// Homepage auth form toggles (on homepage)
const linkToSignup = document.getElementById('link-to-signup');
const linkToAdminSignup = document.getElementById('link-to-admin-signup');

if (linkToSignup) {
  linkToSignup.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('signup-form').style.display = 'block';
  });
}

if (linkToAdminSignup) {
  linkToAdminSignup.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('admin-login-form').style.display = 'none';
    document.getElementById('admin-signup-form').style.display = 'block';
  });
}

// Override setLoggedIn to show app container
const originalSetLoggedIn = setLoggedIn;
setLoggedIn = async function(role) {
  showAppContainer();
  return await originalSetLoggedIn.call(this, role);
};

// Override setLoggedOut to show homepage
const originalSetLoggedOut = setLoggedOut;
setLoggedOut = function() {
  showHomepage();
  return originalSetLoggedOut.call(this);
};

// Show homepage initially
showHomepage();

