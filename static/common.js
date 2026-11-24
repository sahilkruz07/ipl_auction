/* Shared helpers: CSRF-aware fetch wrapper, HTML escaping, toasts. */
window.api = async function (method, url, body) {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const res = await fetch(url, {
    method, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data = {};
  try { data = await res.json(); } catch (e) { /* non-JSON response */ }
  if (res.status === 401) { location.href = '/login'; }
  return { ok: res.ok, status: res.status, data };
};

window.esc = function (s) {
  const d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
};

window.fmt = (v) => Number(v).toFixed(2);
window.round2 = (v) => Math.round((Number(v) + Number.EPSILON) * 100) / 100;

window.toast = function (msg, kind) {
  const el = document.createElement('div');
  el.className = 'toast align-items-center text-bg-' + (kind || 'dark') + ' border-0';
  el.innerHTML = '<div class="d-flex"><div class="toast-body"></div>' +
    '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
  el.querySelector('.toast-body').textContent = msg;
  document.getElementById('toasts').appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 3500 });
  el.addEventListener('hidden.bs.toast', () => el.remove());
  t.show();
};

document.querySelectorAll('.app-nav .nav-link').forEach((a) => {
  if (a.pathname === location.pathname) a.classList.add('active');
});
