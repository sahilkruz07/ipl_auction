(function () {
  const body = document.querySelector('#board tbody');

  function render(d) {
    const medal = { 1: '🥇', 2: '🥈', 3: '🥉' };
    body.innerHTML = d.leaderboard.map((s) => `<tr>
      <td class="fw-bold">${medal[s.rank] || s.rank}</td><td>${esc(s.displayname)}</td>
      <td class="text-end fw-bold">${s.total_points}</td><td class="text-end">${s.team_hits}</td>
      <td class="text-end">${s.exact_hits}</td><td class="text-end">${s.scored} / ${d.players.length}</td></tr>`).join('');
    document.getElementById('updated').textContent = 'Updated ' + new Date().toLocaleTimeString() + ' · auto-refreshes every 10s';
  }

  async function load() {
    const r = await api('GET', '/api/reveal');
    if (r.status === 403) { document.getElementById('locked').classList.remove('d-none'); body.innerHTML = ''; return; }
    if (r.ok) { document.getElementById('locked').classList.add('d-none'); render(r.data); }
  }
  load();
  setInterval(load, 10000);
})();
