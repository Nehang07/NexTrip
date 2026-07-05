// Shared across all pages: auth session state, nav avatar/dropdown, login+register modal, toast.

let CURRENT_USER = null;

function initials(name) {
  return name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
}

function showToast(msg) {
  let el = document.getElementById('global-toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'global-toast';
    el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 2400);
}

function renderAuthUI() {
  const slot = document.getElementById('nav-auth-slot');
  if (!slot) return;

  if (CURRENT_USER) {
    slot.innerHTML = `
      <div class="nav-avatar-wrap">
        <button class="nav-avatar" onclick="toggleNavDropdown()">${initials(CURRENT_USER.name)}</button>
        <div class="nav-dropdown" id="nav-dropdown">
          <div class="nav-dropdown-name">${CURRENT_USER.name}</div>
          <a href="bookings.html">My Bookings</a>
          <a href="explorer.html">Saved destinations</a>
          <a href="planner.html">My trip plans</a>
          <a href="budget.html">Budget tracker</a>
          <button onclick="doLogout()">Log out</button>
        </div>
      </div>`;
  } else {
    slot.innerHTML = `<button class="nav-cta" onclick="openAuthModal('login')">Sign in</button>`;
  }
  document.querySelectorAll('.auth-only').forEach(el => {
    el.style.display = CURRENT_USER ? '' : 'none';
  });
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = CURRENT_USER ? 'none' : '';
  });
  document.dispatchEvent(new CustomEvent('nextrip-auth-ready', { detail: { user: CURRENT_USER } }));
}

function toggleNavDropdown() {
  document.getElementById('nav-dropdown').classList.toggle('open');
}
document.addEventListener('click', (e) => {
  const wrap = document.querySelector('.nav-avatar-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const dd = document.getElementById('nav-dropdown');
    if (dd) dd.classList.remove('open');
  }
});

async function fetchMe() {
  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    CURRENT_USER = data.user;
  } catch (e) {
    CURRENT_USER = null;
  }
  renderAuthUI();
  return CURRENT_USER;
}

async function doLogout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  CURRENT_USER = null;
  renderAuthUI();
  showToast('Signed out');
  if (typeof onAuthChanged === 'function') onAuthChanged();
}

/* ---------------- Auth modal ---------------- */

function injectAuthModal() {
  if (document.getElementById('auth-modal')) return;
  const div = document.createElement('div');
  div.innerHTML = `
  <div class="modal-backdrop" id="auth-modal">
    <div class="modal-box">
      <button class="modal-close" onclick="closeAuthModal()">✕</button>
      <div class="modal-title" id="auth-modal-title">Sign in</div>
      <div class="form-error" id="auth-error"></div>

      <form id="login-form" onsubmit="return submitLogin(event)">
        <div class="field"><label>Email</label><input type="email" id="login-email" required></div>
        <div class="field"><label>Password</label><input type="password" id="login-password" required></div>
        <button class="btn-primary" style="width:100%;" type="submit">Sign in</button>
        <div class="modal-switch">New here? <button type="button" onclick="switchAuthMode('register')">Create an account</button></div>
      </form>

      <form id="register-form" style="display:none;" onsubmit="return submitRegister(event)">
        <div class="field"><label>Full name</label><input type="text" id="reg-name" required></div>
        <div class="field"><label>Email</label><input type="email" id="reg-email" required></div>
        <div class="field"><label>Password</label><input type="password" id="reg-password" minlength="6" required></div>
        <button class="btn-primary" style="width:100%;" type="submit">Create account</button>
        <div class="modal-switch">Already have an account? <button type="button" onclick="switchAuthMode('login')">Sign in</button></div>
      </form>
    </div>
  </div>`;
  document.body.appendChild(div.firstElementChild);
}

function openAuthModal(mode) {
  injectAuthModal();
  switchAuthMode(mode || 'login');
  document.getElementById('auth-modal').classList.add('open');
}
function closeAuthModal() {
  const m = document.getElementById('auth-modal');
  if (m) m.classList.remove('open');
}
function switchAuthMode(mode) {
  document.getElementById('auth-error').classList.remove('show');
  document.getElementById('auth-modal-title').textContent = mode === 'login' ? 'Sign in' : 'Create your account';
  document.getElementById('login-form').style.display = mode === 'login' ? 'block' : 'none';
  document.getElementById('register-form').style.display = mode === 'register' ? 'block' : 'none';
}

async function submitLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const res = await fetch('/api/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  const errEl = document.getElementById('auth-error');
  if (!res.ok) {
    errEl.textContent = data.error || 'Could not sign in';
    errEl.classList.add('show');
    return false;
  }
  CURRENT_USER = data;
  closeAuthModal();
  renderAuthUI();
  showToast(`Welcome back, ${data.name.split(' ')[0]}!`);
  if (typeof onAuthChanged === 'function') onAuthChanged();
  return false;
}

async function submitRegister(e) {
  e.preventDefault();
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const res = await fetch('/api/auth/register', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  const data = await res.json();
  const errEl = document.getElementById('auth-error');
  if (!res.ok) {
    errEl.textContent = data.error || 'Could not create account';
    errEl.classList.add('show');
    return false;
  }
  CURRENT_USER = data;
  closeAuthModal();
  renderAuthUI();
  showToast(`Welcome to NexTrip, ${data.name.split(' ')[0]}!`);
  if (typeof onAuthChanged === 'function') onAuthChanged();
  return false;
}

document.addEventListener('DOMContentLoaded', () => {
  injectAuthModal();
  fetchMe();
  initScrollReveal();
});

/* ---------------- Scroll-reveal animation ---------------- */
function initScrollReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  els.forEach(el => observer.observe(el));
}

// Dynamically-injected content (AJAX results) won't exist at DOMContentLoaded —
// call this after rendering new .reveal elements to pick them up too.
function refreshScrollReveal() { initScrollReveal(); }
