(function () {
  const table = document.getElementById('matrix');

  function cell(pred, p) {
    if (!pred) return '<td class="text-muted text-center">—</td>';
    const label = pred.bet_team === 'UNSOLD' ? 'UNSOLD' : `${esc(pred.bet_team)} · ₹${fmt(pred.bet_amount)}`;
    if (pred.points == null) return `<td>${label}</td>`;
    const cls = pred.points > 0 ? 'cell-hit' : '';
    return `<td class="${cls}">${label}
      <span class="badge ${pred.points > 0 ? 'bg-success' : 'bg-secondary'} ms-1" title="Team ${pred.team_points} + Amount ${pred.amount_points}">${pred.points} pts</span></td>`;
  }

  function render(d) {
    const head = '<thead><tr><th>Player</th><th>Official result</th>' +
      d.users.map((u) => `<th>${esc(u.displayname)}</th>`).join('') + '</tr></thead>';
    const rows = d.players.map((p) => {
      const result = p.sold_to == null ? '<span class="badge bg-warning text-dark">Pending</span>'
        : p.sold_to === 'UNSOLD' ? '<span class="badge bg-dark">UNSOLD</span>'
        : `<span class="badge bg-primary">${esc(p.sold_to)}</span> ₹${fmt(p.sold_price)} Cr`;
      return `<tr><td><div class="fw-semibold">${esc(p.player_name)}</div>
        <span class="text-capitalize small text-muted">${esc(p.role)}</span>
        ${p.is_overseas ? '<span class="badge bg-info text-dark">Overseas</span>' : '<span class="badge bg-secondary">Indian</span>'}</td>
        <td>${result}</td>${d.users.map((u) => cell(p.predictions[u.user_id], p)).join('')}</tr>`;
    }).join('');
    table.innerHTML = head + '<tbody>' + rows + '</tbody>';
    document.getElementById('updated').textContent = 'Updated ' + new Date().toLocaleTimeString() + ' · auto-refreshes every 10s';
  }

  async function load() {
    const r = await api('GET', '/api/reveal');
    if (r.status === 403) { document.getElementById('locked').classList.remove('d-none'); table.innerHTML = ''; return; }
    if (r.ok) { document.getElementById('locked').classList.add('d-none'); render(r.data); }
  }
  load();
  setInterval(load, 10000);
})();
