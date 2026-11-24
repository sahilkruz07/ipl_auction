(function () {
  document.getElementById('toggleBtn').addEventListener('click', async () => {
    if (!confirm('Change the betting phase? Locking blocks all bet edits immediately.')) return;
    const r = await api('POST', '/api/admin/cutoff', {});
    if (r.ok) location.reload(); else toast(r.data.error || 'Failed', 'danger');
  });

  document.getElementById('aRows').addEventListener('click', async (e) => {
    const btn = e.target.closest('.save-result');
    if (!btn) return;
    const tr = btn.closest('tr');
    const sold_to = tr.querySelector('.sold-to').value;
    const sold_price = tr.querySelector('.sold-price').value;
    btn.disabled = true;
    const r = await api('POST', `/api/admin/players/${encodeURIComponent(tr.dataset.id)}/result`, { sold_to, sold_price });
    btn.disabled = false;
    if (!r.ok) { toast(r.data.error || 'Failed', 'danger'); return; }
    tr.querySelector('.sold-price').value = r.data.sold_price == null ? '' : fmt(r.data.sold_price);
    toast('Result saved', 'success');
  });

  document.getElementById('aRows').addEventListener('change', (e) => {
    if (!e.target.classList.contains('sold-to')) return;
    const price = e.target.closest('tr').querySelector('.sold-price');
    if (e.target.value === 'UNSOLD') price.value = '0.00';
    else if (e.target.value === '') price.value = '';
  });

  document.getElementById('aSearch').addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    document.querySelectorAll('#aRows tr').forEach((tr) => { tr.hidden = q && !tr.dataset.name.includes(q); });
  });

  async function submitForm(id, url, build) {
    document.getElementById(id).addEventListener('submit', async (e) => {
      e.preventDefault();
      const r = await api('POST', url, build(new FormData(e.target)));
      if (r.ok) { toast('Added', 'success'); setTimeout(() => location.reload(), 600); }
      else toast(r.data.error || 'Failed', 'danger');
    });
  }
  submitForm('playerForm', '/api/admin/players', (f) => ({
    player_name: f.get('player_name'), role: f.get('role'), is_overseas: f.get('is_overseas') === 'on' }));
  submitForm('userForm', '/api/admin/users', (f) => Object.fromEntries(f.entries()));
})();
