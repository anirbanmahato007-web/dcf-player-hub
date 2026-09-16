// DCF | PLAYER HUB - Interactive Frontend Application Logic (Enhanced Deletion & Edge Case Handler)

let currentStep = 1;
let selectedPhotoFile = null;
let allPlayersCache = [];
let adminToken = localStorage.getItem("dcf_admin_token") || null;

const POSITION_MAP = {
  "Goalkeeper": ["GK"],
  "Defender": ["CB", "LB", "RB", "LWB", "RWB", "Sweeper"],
  "Midfielder": ["CDM", "CM", "CAM", "LM", "RM"],
  "Forward": ["LW", "RW", "ST", "CF"]
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
  setupMobileNav();
  loadHomeData();
  updatePlayingPositionChips();
  
  // Check if deep linked or default
  const hash = window.location.hash.replace('#', '');
  if (['squad', 'register', 'admin'].includes(hash)) {
    switchView(hash);
  } else {
    switchView('home');
  }
});

// --- NAVIGATION & VIEWS ---
function switchView(viewName) {
  window.location.hash = viewName;
  document.querySelectorAll('.view-section').forEach(sec => sec.style.display = 'none');
  document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));

  const activeNav = document.getElementById(`nav-${viewName}`);
  if (activeNav) activeNav.classList.add('active');

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) targetView.style.display = 'block';

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (viewName === 'home') {
    loadHomeData();
  } else if (viewName === 'squad') {
    loadSquadData();
  } else if (viewName === 'admin') {
    checkAdminViewStatus();
  }
}

function setupMobileNav() {
  const toggleBtn = document.getElementById('mobile-toggle-btn');
  const navMenu = document.getElementById('nav-menu');
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('mobile-open');
    });
  }
}

// --- HOME PAGE DATA ---
async function loadHomeData() {
  try {
    const res = await fetch('/api/players');
    const players = await res.json();
    allPlayersCache = players;

    // Calculate Stats
    const total = players.length;
    const active = players.filter(p => p.status === 'Active').length;
    const injured = players.filter(p => p.status === 'Injured').length;
    const trial = players.filter(p => p.status === 'Trial').length;

    document.getElementById('home-stat-total').textContent = total;
    document.getElementById('home-stat-active').textContent = active;
    document.getElementById('home-stat-injured').textContent = injured;
    document.getElementById('home-stat-trial').textContent = trial;

    // Position breakdown
    document.getElementById('breakdown-gk').textContent = players.filter(p => p.primary_position === 'Goalkeeper').length;
    document.getElementById('breakdown-def').textContent = players.filter(p => p.primary_position === 'Defender').length;
    document.getElementById('breakdown-mid').textContent = players.filter(p => p.primary_position === 'Midfielder').length;
    document.getElementById('breakdown-fwd').textContent = players.filter(p => p.primary_position === 'Forward').length;

    // Render 4-6 featured players
    const featuredGrid = document.getElementById('home-featured-grid');
    featuredGrid.innerHTML = '';
    const featured = players.slice(0, 6);

    if (featured.length === 0) {
      featuredGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">No registered players found yet. Be the first to join!</div>`;
    } else {
      featured.forEach(p => {
        featuredGrid.appendChild(createPlayerCardElement(p));
      });
    }
  } catch (err) {
    console.error("Error loading home data:", err);
  }
}

// --- STEP-BY-STEP REGISTRATION FLOW ---
function jumpToStep(stepNum) {
  if (stepNum < currentStep || validateStep(currentStep)) {
    showStep(stepNum);
  }
}

function nextStep(stepNum) {
  if (validateStep(currentStep)) {
    showStep(stepNum);
  }
}

function showStep(stepNum) {
  currentStep = stepNum;

  // Update panels
  document.querySelectorAll('.step-panel').forEach(p => p.style.display = 'none');
  const activePanel = document.getElementById(`step-panel-${stepNum}`);
  if (activePanel) activePanel.style.display = 'block';

  // Update stepper nodes & progress bar
  const progressPercent = ((stepNum - 1) / 5) * 100;
  const progressBar = document.getElementById('stepper-progress-bar');
  if (progressBar) progressBar.style.width = `${progressPercent}%`;

  for (let i = 1; i <= 6; i++) {
    const node = document.getElementById(`step-node-${i}`);
    if (node) {
      node.classList.remove('active', 'completed');
      if (i === stepNum) node.classList.add('active');
      else if (i < stepNum) node.classList.add('completed');
    }
  }
}

function validateStep(stepNum) {
  if (stepNum === 1) {
    const name = document.getElementById('reg-name').value.trim();
    if (!name || name.length < 2) {
      showToast("Please enter a valid player full name.", "error");
      return false;
    }
  } else if (stepNum === 2) {
    const primaryPos = document.getElementById('reg-primary-pos').value;
    if (!primaryPos) {
      showToast("Please select your primary position.", "error");
      return false;
    }
    const checkedChips = document.querySelectorAll('#playing-positions-grid input:checked');
    if (checkedChips.length === 0) {
      showToast("Please select at least one specific position of play.", "error");
      return false;
    }
    const foot = document.getElementById('reg-strong-foot').value;
    if (!foot) {
      showToast("Please select your strong foot.", "error");
      return false;
    }
  } else if (stepNum === 3) {
    const jerseyNum = parseInt(document.getElementById('reg-jersey-num').value);
    if (isNaN(jerseyNum) || jerseyNum < 1 || jerseyNum > 99) {
      showToast("Please enter a valid jersey number between 1 and 99.", "error");
      return false;
    }
  } else if (stepNum === 4) {
    const status = document.getElementById('reg-status').value;
    if (!status) {
      showToast("Please select your current player status.", "error");
      return false;
    }
  } else if (stepNum === 5) {
    if (!selectedPhotoFile) {
      showToast("Please upload a player photograph.", "error");
      return false;
    }
  }
  return true;
}

function updatePlayingPositionChips() {
  const primaryPos = document.getElementById('reg-primary-pos').value || "Midfielder";
  const positions = POSITION_MAP[primaryPos] || ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"];
  const grid = document.getElementById('playing-positions-grid');
  grid.innerHTML = '';

  positions.forEach((pos, idx) => {
    const chip = document.createElement('div');
    chip.className = 'chip-item';
    chip.innerHTML = `
      <input type="checkbox" id="chip-${pos}" value="${pos}" ${idx === 0 ? 'checked' : ''}>
      <label for="chip-${pos}" class="chip-label">${pos}</label>
    `;
    grid.appendChild(chip);
  });
}

function handlePhotoSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    showToast("Invalid file type. Please upload a JPG, JPEG, PNG, or WEBP image.", "error");
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    showToast("File size too large. Maximum file size is 5MB.", "error");
    return;
  }

  selectedPhotoFile = file;

  const reader = new FileReader();
  reader.onload = function(e) {
    const imgEl = document.getElementById('photo-preview-img');
    const placeholder = document.getElementById('photo-placeholder');
    const replaceContainer = document.getElementById('replace-photo-btn-container');

    imgEl.src = e.target.result;
    imgEl.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
    if (replaceContainer) replaceContainer.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function handleRegistrationSubmit(event) {
  event.preventDefault();

  if (!validateStep(1) || !validateStep(2) || !validateStep(3) || !validateStep(4) || !validateStep(5)) {
    return;
  }

  const name = document.getElementById('reg-name').value.trim();
  const primaryPosition = document.getElementById('reg-primary-pos').value;
  const checkedPositions = Array.from(document.querySelectorAll('#playing-positions-grid input:checked')).map(c => c.value);
  const playingPositions = checkedPositions.join(", ");
  const strongFoot = document.getElementById('reg-strong-foot').value;
  const preferredJerseyNumber = document.getElementById('reg-jersey-num').value;
  const status = document.getElementById('reg-status').value;

  const submitBtn = document.getElementById('btn-submit-form');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `SUBMITTING PROFILE...`;

  const formData = new FormData();
  formData.append('name', name);
  formData.append('primary_position', primaryPosition);
  formData.append('playing_positions', playingPositions);
  formData.append('strong_foot', strongFoot);
  formData.append('preferred_jersey_number', preferredJerseyNumber);
  formData.append('status', status);
  formData.append('photo', selectedPhotoFile);

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (res.ok && data.success) {
      document.getElementById('registered-player-id').textContent = data.player.player_id;
      showStep(6);
      showToast("Player Profile Registered Successfully!", "success");
      // Reset form
      document.getElementById('registration-form').reset();
      selectedPhotoFile = null;
      document.getElementById('photo-preview-img').style.display = 'none';
      document.getElementById('photo-placeholder').style.display = 'flex';
      document.getElementById('replace-photo-btn-container').style.display = 'none';
    } else {
      showToast(data.detail || "Failed to register profile. Please try again.", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("An error occurred during submission.", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `SUBMIT PLAYER PROFILE`;
  }
}

// --- SQUAD PAGE SEARCH & FILTER ---
async function loadSquadData() {
  handleSquadSearchFilter();
}

async function handleSquadSearchFilter() {
  const search = document.getElementById('squad-search-input').value.trim();
  const primaryPos = document.getElementById('filter-primary-pos').value;
  const specificPos = document.getElementById('filter-specific-pos').value;
  const foot = document.getElementById('filter-strong-foot').value;
  const status = document.getElementById('filter-status').value;

  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (primaryPos && primaryPos !== 'All') params.append('primary_pos', primaryPos);
  if (specificPos && specificPos !== 'All') params.append('specific_pos', specificPos);
  if (foot && foot !== 'All') params.append('foot', foot);
  if (status && status !== 'All') params.append('status', status);

  try {
    const res = await fetch(`/api/players?${params.toString()}`);
    const players = await res.json();

    const grid = document.getElementById('squad-cards-grid');
    const emptyNoSquad = document.getElementById('empty-state-no-squad');
    const emptyNoResults = document.getElementById('empty-state-no-results');

    grid.innerHTML = '';
    emptyNoSquad.style.display = 'none';
    emptyNoResults.style.display = 'none';

    if (players.length === 0) {
      if (!search && primaryPos === 'All' && specificPos === 'All' && foot === 'All' && status === 'All') {
        emptyNoSquad.style.display = 'block';
      } else {
        emptyNoResults.style.display = 'block';
      }
    } else {
      players.forEach(player => {
        grid.appendChild(createPlayerCardElement(player));
      });
    }
  } catch (err) {
    console.error("Error loading squad:", err);
  }
}

function resetSquadFilters() {
  document.getElementById('squad-search-input').value = '';
  document.getElementById('filter-primary-pos').value = 'All';
  document.getElementById('filter-specific-pos').value = 'All';
  document.getElementById('filter-strong-foot').value = 'All';
  document.getElementById('filter-status').value = 'All';
  handleSquadSearchFilter();
}

// --- PLAYER CARD GENERATOR ---
function createPlayerCardElement(p) {
  const card = document.createElement('div');
  card.className = 'player-card';
  card.onclick = () => openPlayerModal(p.player_id);

  const displayJersey = p.official_jersey_number !== null && p.official_jersey_number !== undefined
    ? `#${p.official_jersey_number}`
    : `#${p.preferred_jersey_number}`;

  const statusClass = `status-${p.status.replace(/\s+/g, '-')}`;

  card.innerHTML = `
    <div class="card-photo-wrapper">
      <img src="${p.photo_url}" alt="${p.name}" class="card-photo" onerror="this.src='/static/img/sample_player_2.svg'">
      <div class="card-photo-overlay"></div>
      <div class="card-id-badge">${p.player_id}</div>
      <div class="card-jersey-number">${displayJersey}</div>
    </div>
    <div class="card-body">
      <div class="card-player-name">${p.name}</div>
      <div class="card-meta-row">
        <span class="card-positions">${p.playing_positions}</span>
        <span>${p.strong_foot.toUpperCase()} FOOT</span>
      </div>
      <div style="margin-top: 0.25rem;">
        <span class="status-badge ${statusClass}">
          <span>●</span> ${p.status.toUpperCase()}
        </span>
      </div>
    </div>
  `;
  return card;
}

// --- PLAYER DETAIL MODAL ---
async function openPlayerModal(playerId) {
  try {
    const res = await fetch(`/api/players/${playerId}`);
    if (!res.ok) return;
    const p = await res.json();

    const modalContent = document.getElementById('player-modal-content');
    const displayJersey = p.official_jersey_number !== null && p.official_jersey_number !== undefined
      ? `#${p.official_jersey_number}`
      : `#${p.preferred_jersey_number}`;

    const regDateFormatted = new Date(p.created_at).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric'
    });

    const statusClass = `status-${p.status.replace(/\s+/g, '-')}`;
    const safeName = p.name.replace(/'/g, "\\'");

    modalContent.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));">
        <div style="aspect-ratio: 3/4; background: #000; overflow: hidden; position: relative;">
          <img src="${p.photo_url}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='/static/img/sample_player_2.svg'">
          <div class="card-photo-overlay"></div>
        </div>
        <div style="padding: 2rem; display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
              <span style="font-size: 0.85rem; font-weight: 800; letter-spacing: 2px; color: var(--accent-green-bright);">${p.player_id}</span>
              <span class="font-heading" style="font-size: 2.5rem; color: var(--text-main);">${displayJersey}</span>
            </div>
            <h2 class="font-heading" style="font-size: 2.5rem; line-height: 1; margin-bottom: 1rem; text-transform: uppercase;">${p.name}</h2>
            
            <div style="margin-bottom: 1.5rem;">
              <span class="status-badge ${statusClass}" style="font-size: 0.85rem; padding: 0.4rem 1rem;">
                <span>●</span> ${p.status.toUpperCase()}
              </span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 1rem; font-size: 0.9rem; border-top: 1px solid var(--border-color); padding-top: 1.25rem;">
              <div>
                <span style="color: var(--text-dim); text-transform: uppercase; font-size: 0.75rem; font-weight: 800; display: block;">PRIMARY POSITION</span>
                <strong style="color: var(--text-main); font-size: 1.1rem;">${p.primary_position} (${p.playing_positions})</strong>
              </div>
              <div>
                <span style="color: var(--text-dim); text-transform: uppercase; font-size: 0.75rem; font-weight: 800; display: block;">STRONG FOOT</span>
                <strong style="color: var(--text-main); font-size: 1.1rem;">${p.strong_foot} Foot</strong>
              </div>
              <div>
                <span style="color: var(--text-dim); text-transform: uppercase; font-size: 0.75rem; font-weight: 800; display: block;">JERSEY PREFERENCE</span>
                <strong style="color: var(--text-main);">Preferred: #${p.preferred_jersey_number} | Official: ${p.official_jersey_number !== null ? '#' + p.official_jersey_number : 'Unassigned'}</strong>
              </div>
              <div>
                <span style="color: var(--text-dim); text-transform: uppercase; font-size: 0.75rem; font-weight: 800; display: block;">REGISTRATION DATE</span>
                <strong style="color: var(--text-main);">${regDateFormatted}</strong>
              </div>
            </div>
          </div>

          <div style="margin-top: 2rem; border-top: 1px solid var(--border-color); padding-top: 1.25rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <button class="btn btn-secondary" style="flex: 1;" onclick="closePlayerModal()">CLOSE</button>
            <button class="btn btn-danger" style="padding: 0.6rem 1.2rem; font-size: 0.85rem;" onclick="deletePlayerSelf('${p.player_id}', '${safeName}')">🗑️ DELETE PROFILE</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('player-modal').classList.add('active');
  } catch (err) {
    console.error(err);
  }
}

function closePlayerModal() {
  document.getElementById('player-modal').classList.remove('active');
}

// User Self-Service Deletion
async function deletePlayerSelf(playerId, playerName) {
  if (!confirm(`Are you sure you want to delete player profile for ${playerName} (${playerId}) from the official DCF database?`)) return;

  try {
    const res = await fetch(`/api/players/${playerId}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Player Profile Deleted Successfully!", "success");
      closePlayerModal();
      loadHomeData();
      handleSquadSearchFilter();
    } else {
      showToast(data.detail || "Failed to delete player profile", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error deleting player profile", "error");
  }
}

// --- ADMIN MANAGEMENT PORTAL ---
async function checkAdminViewStatus() {
  const loginBox = document.getElementById('admin-login-box');
  const dashboardBox = document.getElementById('admin-dashboard-box');

  if (adminToken) {
    loginBox.style.display = 'none';
    dashboardBox.style.display = 'block';
    loadAdminDashboardData();
  } else {
    loginBox.style.display = 'block';
    dashboardBox.style.display = 'none';
  }
}

async function handleAdminLogin(event) {
  event.preventDefault();
  const password = document.getElementById('admin-password-input').value;

  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });
    const data = await res.json();
    if (res.ok && data.token) {
      adminToken = data.token;
      localStorage.setItem("dcf_admin_token", adminToken);
      showToast("Admin Logged In Successfully!", "success");
      checkAdminViewStatus();
    } else {
      showToast(data.detail || "Invalid Admin Password", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Authentication Error", "error");
  }
}

function adminLogout() {
  adminToken = null;
  localStorage.removeItem("dcf_admin_token");
  showToast("Logged out of Admin Portal", "success");
  checkAdminViewStatus();
}

async function loadAdminDashboardData() {
  if (!adminToken) return;

  try {
    // Load Stats
    const statsRes = await fetch('/api/admin/stats', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    if (statsRes.ok) {
      const stats = await statsRes.json();
      document.getElementById('admin-stat-total').textContent = stats.total_players;
      document.getElementById('admin-stat-active').textContent = stats.active_players;
      document.getElementById('admin-stat-injured').textContent = stats.injured;
      document.getElementById('admin-stat-unavailable').textContent = stats.unavailable;
      document.getElementById('admin-stat-trial').textContent = stats.trial_players;

      document.getElementById('admin-pos-gk').textContent = stats.positions.goalkeepers;
      document.getElementById('admin-pos-def').textContent = stats.positions.defenders;
      document.getElementById('admin-pos-mid').textContent = stats.positions.midfielders;
      document.getElementById('admin-pos-fwd').textContent = stats.positions.forwards;
    }

    // Load Jersey Conflicts
    const conflictRes = await fetch('/api/admin/jersey-conflicts', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    if (conflictRes.ok) {
      const conflicts = await conflictRes.json();
      const alertBox = document.getElementById('jersey-conflict-alert');
      if (conflicts.length > 0) {
        alertBox.style.display = 'flex';
        const msg = conflicts.map(c => `⚠️ Jersey #${c.jersey_number} selected by ${c.count} players (${c.players.map(p => p.name).join(', ')})`).join(' | ');
        document.getElementById('jersey-conflict-text').textContent = "JERSEY PREFERENCE CONFLICTS DETECTED";
        document.getElementById('jersey-conflict-sub').textContent = msg;
      } else {
        alertBox.style.display = 'none';
      }
    }

    // Load Table
    const playersRes = await fetch('/api/players');
    const players = await playersRes.json();

    const tbody = document.getElementById('admin-players-tbody');
    tbody.innerHTML = '';

    players.forEach(p => {
      const tr = document.createElement('tr');
      const prefNum = `#${p.preferred_jersey_number}`;
      const offNum = p.official_jersey_number !== null ? `#${p.official_jersey_number}` : `<span style="color: var(--text-dim);">Unassigned</span>`;

      tr.innerHTML = `
        <td><img src="${p.photo_url}" class="table-player-thumb" onerror="this.src='/static/img/sample_player_2.svg'"></td>
        <td><strong>${p.player_id}</strong></td>
        <td><strong>${p.name}</strong></td>
        <td>${p.primary_position} (${p.playing_positions})</td>
        <td>Pref: <strong>${prefNum}</strong> | Off: <strong>${offNum}</strong></td>
        <td>${p.strong_foot}</td>
        <td>
          <select class="form-select" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onchange="updatePlayerStatusInline('${p.player_id}', this.value)">
            <option value="Active" ${p.status === 'Active' ? 'selected' : ''}>🟢 Active</option>
            <option value="Injured" ${p.status === 'Injured' ? 'selected' : ''}>🔴 Injured</option>
            <option value="Unavailable" ${p.status === 'Unavailable' ? 'selected' : ''}>⚪ Unavailable</option>
            <option value="Trial" ${p.status === 'Trial' ? 'selected' : ''}>🟡 Trial</option>
            <option value="New Player" ${p.status === 'New Player' ? 'selected' : ''}>🔵 New Player</option>
            <option value="Temporarily Inactive" ${p.status === 'Temporarily Inactive' ? 'selected' : ''}>🔘 Temporarily Inactive</option>
          </select>
        </td>
        <td style="text-align: right;">
          <button class="btn btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;" onclick='openAdminEditModal(${JSON.stringify(p)})'>EDIT</button>
          <button class="btn btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; margin-left: 0.4rem;" onclick="deletePlayerRecord('${p.player_id}')">DELETE</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Admin dashboard load error:", err);
  }
}

async function updatePlayerStatusInline(playerId, newStatus) {
  if (!adminToken) return;
  const formData = new FormData();
  formData.append('status', newStatus);

  try {
    const res = await fetch(`/api/admin/players/${playerId}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${adminToken}` },
      body: formData
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Status updated to ${newStatus}`, "success");
      loadAdminDashboardData();
      loadHomeData();
      handleSquadSearchFilter();
    } else {
      showToast(data.detail || "Failed to update status", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error updating player status", "error");
  }
}

function openAdminEditModal(player) {
  document.getElementById('edit-player-id').value = player.player_id || player.id;
  document.getElementById('edit-name').value = player.name;
  document.getElementById('edit-primary-pos').value = player.primary_position;
  document.getElementById('edit-playing-positions').value = player.playing_positions;
  document.getElementById('edit-strong-foot').value = player.strong_foot;
  document.getElementById('edit-pref-jersey').value = player.preferred_jersey_number;
  document.getElementById('edit-off-jersey').value = player.official_jersey_number !== null ? player.official_jersey_number : '';
  document.getElementById('edit-status').value = player.status;

  document.getElementById('admin-edit-modal').classList.add('active');
}

function closeAdminEditModal() {
  document.getElementById('admin-edit-modal').classList.remove('active');
}

async function handleAdminUpdateSubmit(event) {
  event.preventDefault();
  if (!adminToken) return;

  const playerId = document.getElementById('edit-player-id').value;
  const formData = new FormData();
  formData.append('name', document.getElementById('edit-name').value);
  formData.append('primary_position', document.getElementById('edit-primary-pos').value);
  formData.append('playing_positions', document.getElementById('edit-playing-positions').value);
  formData.append('strong_foot', document.getElementById('edit-strong-foot').value);
  formData.append('preferred_jersey_number', document.getElementById('edit-pref-jersey').value);
  formData.append('official_jersey_number', document.getElementById('edit-off-jersey').value);
  formData.append('status', document.getElementById('edit-status').value);

  const photoFile = document.getElementById('edit-photo-input').files[0];
  if (photoFile) {
    formData.append('photo', photoFile);
  }

  try {
    const res = await fetch(`/api/admin/players/${playerId}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${adminToken}` },
      body: formData
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Player updated successfully!", "success");
      closeAdminEditModal();
      loadAdminDashboardData();
      loadHomeData();
      handleSquadSearchFilter();
    } else {
      showToast(data.detail || "Update failed", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error updating player", "error");
  }
}

async function deletePlayerRecord(playerId) {
  if (!adminToken) return;
  if (!confirm(`Are you sure you want to delete player (${playerId}) from the official DCF database?`)) return;

  try {
    const res = await fetch(`/api/admin/players/${playerId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Player record deleted successfully", "success");
      loadAdminDashboardData();
      loadHomeData();
      handleSquadSearchFilter();
    } else {
      showToast(data.detail || "Failed to delete player", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Error deleting player record", "error");
  }
}

async function exportAdminCSV() {
  if (!adminToken) return;

  try {
    const res = await fetch('/api/admin/export', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "DCF_Player_Database.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast("Database exported as CSV!", "success");
    } else {
      showToast("Failed to export database", "error");
    }
  } catch (err) {
    console.error(err);
  }
}

// --- UTILITY: TOAST NOTIFICATION ---
function showToast(message, type = "success") {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '⚠️'}</span>
    <div style="font-weight: 700; font-size: 0.9rem;">${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
