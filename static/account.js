(function () {
  const $ = (id) => document.getElementById(id);
  const say = (text, kind) => { $('pwMsg').textContent = text; $('pwMsg').className = 'row-msg mt-2 ' + kind; };

  $('pwForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const current = $('cur').value, n1 = $('new1').value, n2 = $('new2').value;
    if (n1.length < 8) return say('New password must be at least 8 characters.', 'err');
    if (n1 !== n2) return say('New passwords do not match.', 'err');
    if (n1 === current) return say('New password must be different from the current one.', 'err');
    $('pwBtn').disabled = true;
    const r = await api('POST', '/api/account/password', { current_password: current, new_password: n1 });
    $('pwBtn').disabled = false;
    if (!r.ok) return say(r.data.error || 'Could not change password.', 'err');
    e.target.reset();
    say('Password updated.', 'ok');
    toast('Password updated', 'success');
  });
})();
