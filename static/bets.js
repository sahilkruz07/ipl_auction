(function () {
  let state = null;
  let flashTimer = null;
  const $ = (s) => document.querySelector(s);
  const teamBar = $('#teamBar');

  const teamByName = (n) => state.teams.find((t) => t.team_name === n);

  // Usage per team from the user's current bets; the player's own bet can be excluded (edits).
  function usage(excludePid) {
    const u = {};
    state.teams.forEach((t) => (u[t.team_name] = { spent: 0, count: 0, os: 0 }));
    state.players.forEach((p) => {
      if (!p.bet || p.player_id === excludePid || p.bet.bet_team === 'UNSOLD') return;
      const x = u[p.bet.bet_team];
      if (!x) return;
      x.spent += p.bet.bet_amount; x.count++;
      if (p.is_overseas) x.os++;
    });
    return u;
  }

  // Mirror of the server-side validation (the server remains the authority).
  function validate(p, team, amount) {
    if (!team) return { error: 'Select a team' };
    if (team === 'UNSOLD') return { amount: 0 };
    const t = teamByName(team);
    if (!t) return { error: 'Invalid team' };
    if (!Number.isFinite(amount) || amount <= 0) return { error: 'Amount must be greater than 0', team };
    const u = usage(p.player_id)[team];
    const purse = round2(t.purse_left - u.spent);
    if (round2(purse - amount) < 0) return { error: `Exceeds ${team} remaining purse of ₹${fmt(purse)} Cr`, team };
    if (t.available_slots - u.count - 1 < 0)
      return { error: `Cannot assign to ${team}: Total slots limit (${u.count}/${t.available_slots}) already reached`, team };
    if (p.is_overseas && t.overseas_slots - u.os - 1 < 0)
      return { error: `Cannot assign to ${team}: Overseas limit (${u.os}/${t.overseas_slots}) already reached`, team };
    return { amount: round2(amount) };
  }

  function renderTeams() {
    const u = usage(null);
    teamBar.innerHTML = state.teams.map((t) => {
      const x = u[t.team_name];
      const slots = t.available_slots - x.count, os = t.overseas_slots - x.os;
      const pct = Math.max(0, Math.min(100, 100 * (t.purse_left - x.spent) / t.purse_left));
      return `<div class="team-card ${slots <= 0 ? 'full' : ''}" data-team="${esc(t.team_name)}" title="${esc(t.full_name)}">
        <div class="code">${esc(t.team_name)}</div>
        <div class="info">
          <div class="stats">
            <span title="Purse left (Cr)"><em>₹</em><b>${fmt(round2(t.purse_left - x.spent))}</b></span>
            <span title="Slots left"><em>Slots</em> <b>${slots}/${t.available_slots}</b></span>
            <span title="Overseas slots left"><em>OS</em> <b>${os}/${t.overseas_slots}</b></span>
          </div>
          <div class="meter"><i style="width:${pct}%"></i></div>
        </div></div>`;
    }).join('');
  }

  function flashTeam(team, persistent) {
    document.querySelectorAll('.team-card.invalid').forEach((c) => c.classList.remove('invalid'));
    clearTimeout(flashTimer);
    if (!team) return;
    const c = teamBar.querySelector(`[data-team="${CSS.escape(team)}"]`);
    if (c) c.classList.add('invalid');
    if (!persistent) flashTimer = setTimeout(() => flashTeam(null), 6000);
  }

  function renderProgress() {
    const done = state.players.filter((p) => p.bet).length, total = state.players.length;
    $('#progressText').textContent = `Completed: ${done} / ${total} players`;
    $('#progressBar').style.width = total ? (100 * done / total) + '%' : '0';
  }

  function betLabel(p) {
    if (!p.bet) return '<span class="badge bg-secondary">Pending</span>';
    if (p.bet.bet_team === 'UNSOLD') return '<span class="badge bg-warning text-dark">UNSOLD</span>';
    return `<span class="badge bg-success">${esc(p.bet.bet_team)} · ₹${fmt(p.bet.bet_amount)} Cr</span>`;
  }

  function tileHtml(p) {
    const opts = ['<option value="">Select team…</option>']
      .concat(state.teams.map((t) => t.team_name).concat(['UNSOLD']).map((n) =>
        `<option value="${esc(n)}" ${p.bet && p.bet.bet_team === n ? 'selected' : ''}>${esc(n)}</option>`)).join('');
    const isUnsold = p.bet && p.bet.bet_team === 'UNSOLD';
    const viewOnly = !!p.bet;  // saved bets start read-only until "Re-edit" is clicked
    const controls = state.locked ? '<div class="text-muted small">Betting locked</div>' : `
      <div class="bet-controls">
        <select class="form-select form-select-sm team-sel" aria-label="Team" ${viewOnly ? 'disabled' : ''}>${opts}</select>
        <input type="number" min="0" step="0.05" class="form-control form-control-sm amt" placeholder="₹ Cr"
               value="${p.bet ? fmt(p.bet.bet_amount) : ''}" ${isUnsold || viewOnly ? 'disabled' : ''} aria-label="Amount in crores">
        <button class="btn btn-sm btn-primary save">Save</button>
        <button class="btn btn-sm btn-outline-danger clear" ${p.bet ? '' : 'disabled'}>Clear</button>
        <button class="btn btn-sm btn-primary reedit">Re-edit</button>
      </div><div class="row-msg"></div>`;
    return `<div class="tile-head"><div class="tile-name">${esc(p.player_name)}</div>
        <div class="tile-tags"><span class="badge bg-secondary text-capitalize">${esc(p.role)}</span>
        ${p.is_overseas ? '<span class="badge bg-info">Overseas</span>' : '<span class="badge bg-secondary">Indian</span>'}</div></div>
      <div class="cur">${betLabel(p)}</div>${controls}`;
  }

  function makeRow(p) {
    const tr = document.createElement('div');
    tr.dataset.id = p.player_id;
    tr.className = 'tile' + (p.bet ? ' has-bet' : '');
    tr.innerHTML = tileHtml(p);
    if (!state.locked) wireRow(tr, p);
    return tr;
  }

  function msg(tr, text, kind) {
    const m = tr.querySelector('.row-msg');
    m.textContent = text || ''; m.className = 'row-msg ' + (kind || '');
  }

  function readRow(tr) {
    const team = tr.querySelector('.team-sel').value;
    const raw = tr.querySelector('.amt').value;
    return { team, amount: raw === '' ? NaN : parseFloat(raw) };
  }

  function wireRow(tr, p) {
    const sel = tr.querySelector('.team-sel'), amt = tr.querySelector('.amt'), save = tr.querySelector('.save');
    const live = () => {
      const { team, amount } = readRow(tr);
      if (!team) { msg(tr, ''); flashTeam(null); save.disabled = true; return; }
      const v = validate(p, team, amount);
      save.disabled = !!v.error && !(v.error === 'Amount must be greater than 0' && amt.value === '');
      msg(tr, v.error || '', v.error ? 'err' : '');
      flashTeam(v.error ? v.team : null, true);
    };
    sel.addEventListener('change', () => {
      if (sel.value === 'UNSOLD') { amt.value = '0.00'; amt.disabled = true; }
      else { amt.disabled = false; if (amt.value === '0.00') amt.value = ''; }
      live();
    });
    amt.addEventListener('input', live);
    amt.addEventListener('keydown', (e) => { if (e.key === 'Enter') save.click(); });
    save.disabled = !sel.value;

    tr.querySelector('.reedit').addEventListener('click', () => {
      tr.classList.add('editing');
      sel.disabled = false;
      amt.disabled = sel.value === 'UNSOLD';
      msg(tr, '');
      (amt.disabled ? sel : amt).focus();
    });

    save.addEventListener('click', async () => {
      const { team, amount } = readRow(tr);
      const v = validate(p, team, amount);
      if (v.error) { msg(tr, v.error, 'err'); flashTeam(v.team); return; }
      save.disabled = true;
      const r = await api('POST', '/api/bets', { player_id: p.player_id, bet_team: team, bet_amount: v.amount });
      if (r.status === 403) { toast(r.data.error || 'Betting is locked', 'danger'); setTimeout(() => location.reload(), 1200); return; }
      if (!r.ok) { msg(tr, r.data.error || 'Save failed', 'err'); flashTeam(r.data.team); save.disabled = false; return; }
      p.bet = r.data.bet;
      flashTeam(null);
      refreshRow(tr, p, 'Saved', 'ok');
    });

    tr.querySelector('.clear').addEventListener('click', async () => {
      const r = await api('DELETE', '/api/bets/' + encodeURIComponent(p.player_id));
      if (r.status === 403) { location.reload(); return; }
      if (!r.ok) { msg(tr, r.data.error || 'Failed', 'err'); return; }
      p.bet = null; flashTeam(null);
      refreshRow(tr, p, 'Cleared', 'ok');
    });
  }

  function refreshRow(tr, p, text, kind) {
    const fresh = makeRow(p);
    tr.replaceWith(fresh);
    msg(fresh, text, kind);
    renderTeams(); renderProgress();
  }

  function renderRows() {
    const q = $('#fSearch').value.trim().toLowerCase(), role = $('#fRole').value,
      origin = $('#fOrigin').value, status = $('#fStatus').value;
    const list = state.players.filter((p) =>
      (!q || p.player_name.toLowerCase().includes(q)) && (!role || p.role === role) &&
      (!origin || (origin === 'overseas') === p.is_overseas) &&
      (!status || (status === 'bet') === !!p.bet));
    const body = $('#playerRows');
    body.innerHTML = '';
    if (!list.length) { body.innerHTML = '<div class="empty">No players match.</div>'; return; }
    list.forEach((p, i) => { const t = makeRow(p); t.style.animationDelay = Math.min(i * 25, 400) + 'ms'; body.appendChild(t); });
  }

  async function init() {
    const r = await api('GET', '/api/state');
    if (!r.ok) { toast(r.data.error || 'Failed to load', 'danger'); return; }
    state = r.data;
    $('#lockBanner').classList.toggle('d-none', !state.locked);
    renderTeams(); renderProgress(); renderRows();
    ['#fSearch', '#fRole', '#fOrigin', '#fStatus'].forEach((s) => $(s).addEventListener('input', renderRows));
  }
  init();
})();
