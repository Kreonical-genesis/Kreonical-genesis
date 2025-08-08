/* main.js: загружает data/<username>.json и рендерит страницу */
(async () => {
  const app = document.getElementById('app');
  const username = app.dataset.username;
  const dataPath = `data/${username}.json`;

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function safe(text) {
    if (!text) return '';
    return text;
  }

  try {
    const res = await fetch(dataPath);
    if (!res.ok) throw new Error(`Ошибка загрузки ${dataPath}: ${res.status}`);
    const data = await res.json();

    // Профиль
    const user = data.user || {};
    document.getElementById('gh-avatar').src = user.avatar_url || 'assets/avatar.png';
    document.getElementById('gh-name').textContent = user.name || user.login || username;
    document.getElementById('gh-login').textContent = user.login ? '@' + user.login : '';
    document.getElementById('gh-bio').textContent = user.bio || '';
    document.getElementById('gh-repos-count').textContent = user.public_repos || 0;
    document.getElementById('gh-followers').textContent = user.followers || 0;
    document.getElementById('gh-following').textContent = user.following || 0;
    document.getElementById('gh-profile-link').href = user.html_url || '#';

    // Repos
    const repos = data.repos || [];
    renderRepos(repos);

    // Languages: суммируем языки по репозиториям
    const langTotals = {};
    repos.forEach(r => {
      const langs = r.languages_bytes || {};
      Object.entries(langs).forEach(([lang, bytes]) => {
        langTotals[lang] = (langTotals[lang] || 0) + (bytes || 0);
      });
    });
    renderLangBars(langTotals);

    // Events / Activity
    const events = data.events || [];
    renderActivity(events);

    // Pinned: возьмём первые 4 репозитория, помеченные как наиболее свежие/популярные
    renderPinned(repos.slice(0, 6));

  } catch (err) {
    console.error(err);
    document.getElementById('repos-grid').textContent = 'Не удалось загрузить данные. Убедитесь, что data/' + username + '.json существует.';
  }

  function renderRepos(repos) {
    const grid = document.getElementById('repos-grid');
    grid.innerHTML = '';
    if (!repos.length) {
      grid.textContent = 'У пользователя нет публичных репозиториев.';
      return;
    }

    repos.forEach(r => {
      const card = el('article', 'repo-card');
      const name = el('a', 'repo-name', r.name);
      name.href = r.html_url;
      name.target = "_blank";

      const desc = el('p', 'repo-desc', r.description || '');
      const meta = el('div', 'repo-meta');
      const lang = el('span', 'repo-lang', r.language || '');
      const stats = el('span', 'repo-stats', `★ ${r.stargazers_count || 0} · Forks ${r.forks_count || 0}`);

      const pushed = el('time', 'repo-updated', r.pushed_at ? `Обновлён: ${new Date(r.pushed_at).toLocaleDateString()}` : '');
      meta.appendChild(lang);
      meta.appendChild(stats);
      card.appendChild(name);
      card.appendChild(desc);
      card.appendChild(meta);
      card.appendChild(pushed);

      grid.appendChild(card);
    });
  }

  function renderLangBars(totals) {
    const container = document.getElementById('lang-bars');
    container.innerHTML = '';
    const entries = Object.entries(totals).sort((a,b)=>b[1]-a[1]);
    const total = entries.reduce((s,[,v])=>s+v, 0) || 1;
    if (!entries.length) {
      container.textContent = 'Нет данных по языкам';
      return;
    }

    entries.forEach(([lang, bytes]) => {
      const row = el('div', 'lang-row');
      const label = el('div', 'lang-label', `${lang} (${Math.round(bytes/1024)} KB)`);
      const barWrap = el('div', 'lang-bar-wrap');
      const bar = el('div', 'lang-bar');
      const pct = Math.round(bytes / total * 100);
      bar.style.width = pct + '%';
      bar.setAttribute('title', pct + '%');
      bar.textContent = pct + '%';
      barWrap.appendChild(bar);
      row.appendChild(label);
      row.appendChild(barWrap);
      container.appendChild(row);
    });
  }

  function renderActivity(events) {
    const ul = document.getElementById('activity-list');
    ul.innerHTML = '';
    if (!events.length) {
      ul.innerHTML = '<li>Нет публичных событий</li>';
      return;
    }
    events.slice(0, 20).forEach(evt => {
      const li = el('li', 'activity-item');
      const when = new Date(evt.created_at).toLocaleString();
      const type = evt.type.replace(/Event$/, '');
      const repo = evt.repo && evt.repo.name ? evt.repo.name : '';
      let txt = `${when} — ${type} ${repo}`;
      // если PushEvent, покажем коммит сообщения
      if (evt.type === 'PushEvent' && evt.payload && evt.payload.commits && evt.payload.commits.length) {
        txt += ` — ${evt.payload.commits[0].message}`;
      }
      li.textContent = txt;
      ul.appendChild(li);
    });
  }

  function renderPinned(repos) {
    const box = document.getElementById('pinned-list');
    box.innerHTML = '';
    if (!repos.length) {
      box.textContent = '—';
      return;
    }
    repos.forEach(r => {
      const a = el('a', 'pinned-item');
      a.href = r.html_url;
      a.target = "_blank";
      a.innerHTML = `<strong>${r.name}</strong><div class="pinned-desc">${safe(r.description)}</div>`;
      box.appendChild(a);
    });
  }

})();
