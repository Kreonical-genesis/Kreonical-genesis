/*
  github.js — улучшенная витрина GitHub
  — Читает data/{username}.json, кэширует на 10 минут в localStorage
  — Скелетоны на время загрузки
  — Поиск, фильтр по языку, сортировка
  — Цвета языков через хэш
  — Активность с иконками и «n дней назад»
  — Быстрые метрики (суммы/средние/рекорды)
  — Пины: топ-4 по звёздам (если нет отдельного списка)
*/

(function(){
  const app = document.getElementById('app');
  const username = app?.dataset?.username || 'kreonical-genesis';
  const DATA_URL = `data/${username}.json`;
  const CACHE_KEY = `gh_cache_${username}`;
  const CACHE_TTL_MS = 10 * 60 * 1000; // 10 минут

  // UI элементы
  const searchInput = document.getElementById('search');
  const sortSelect = document.getElementById('sort');
  const filterLangSelect = document.getElementById('filter-language');

  const avatarEl = document.getElementById('gh-avatar');
  const nameEl = document.getElementById('gh-name');
  const loginEl = document.getElementById('gh-login');
  const bioEl = document.getElementById('gh-bio');
  const reposCountEl = document.getElementById('gh-repos-count');
  const followersEl = document.getElementById('gh-followers');
  const followingEl = document.getElementById('gh-following');
  const profileLinkEl = document.getElementById('gh-profile-link');

  const langBarsEl = document.getElementById('lang-bars');
  const activityListEl = document.getElementById('activity-list');
  const reposGridEl = document.getElementById('repos-grid');
  const pinnedListEl = document.getElementById('pinned-list');
  const quickStatsEl = document.getElementById('quick-stats');
  const repoCountersEl = document.getElementById('repo-counters');

  let data = null;
  let repos = [];
  let allLanguages = new Set();

  // --- Утилиты ---
  const fmt = new Intl.NumberFormat('ru-RU');
  const dateFmt = new Intl.DateTimeFormat('ru-RU', { dateStyle:'medium' });

  function timeAgo(iso){
    const d = new Date(iso);
    const diff = Date.now() - d.getTime();
    const sec = Math.floor(diff/1000);
    const min = Math.floor(sec/60);
    const hr = Math.floor(min/60);
    const day = Math.floor(hr/24);
    if(day>0) return `${day} дн. назад`;
    if(hr>0) return `${hr} ч. назад`;
    if(min>0) return `${min} мин назад`;
    return `${sec} сек назад`;
  }

  function hashColor(str){
    // Хэш -> HSL, фиксированная насыщенность/яркость для стабильных цветов
    let h=0;
    for(let i=0;i<str.length;i++) h = (h*31 + str.charCodeAt(i)) >>> 0;
    const hue = h % 360;
    return `hsl(${hue} 70% 55%)`;
  }

  function fromCache(){
    try{
      const raw = localStorage.getItem(CACHE_KEY);
      if(!raw) return null;
      const obj = JSON.parse(raw);
      if(Date.now() - obj.savedAt > CACHE_TTL_MS) return null;
      return obj.payload;
    }catch(e){return null}
  }
  function toCache(payload){
    try{
      localStorage.setItem(CACHE_KEY, JSON.stringify({savedAt: Date.now(), payload}));
    }catch(e){/* ignore */}
  }

  async function loadData(){
    const cached = fromCache();
    if(cached){ data = cached; return; }
    const res = await fetch(DATA_URL, {cache:'no-store'});
    if(!res.ok) throw new Error(`Не удалось загрузить ${DATA_URL}`);
    data = await res.json();
    toCache(data);
  }

  function renderProfile(){
    const u = data.user || {};
    avatarEl.src = u.avatar_url || 'assets/avatar.png';
    avatarEl.classList.remove('hidden');
    nameEl.textContent = u.name || '—';
    loginEl.textContent = u.login ? `@${u.login}` : '—';
    bioEl.textContent = u.bio || '';

    reposCountEl.textContent = fmt.format((data.repos||[]).length);
    followersEl.textContent = fmt.format(u.followers||0);
    followingEl.textContent = fmt.format(u.following||0);
    if(u.html_url) profileLinkEl.href = u.html_url;
  }

  function computeLanguageTotals(){
    const totals = {};
    (data.repos||[]).forEach(r => {
      const lb = r.languages_bytes || {};
      Object.entries(lb).forEach(([lang, bytes]) => {
        allLanguages.add(lang);
        totals[lang] = (totals[lang]||0) + (bytes||0);
      });
    });
    return totals;
  }

  function renderLanguageBars(){
    const totals = computeLanguageTotals();
    const sum = Object.values(totals).reduce((a,b)=>a+b,0) || 1;
    const arr = Object.entries(totals).sort((a,b)=>b[1]-a[1]).slice(0,12);
    langBarsEl.innerHTML = '';
    arr.forEach(([lang, bytes]) => {
      const pct = Math.round(bytes/sum*1000)/10; // 1 знак после запятой
      const row = document.createElement('div');
      row.className = 'lang-row';
      const label = document.createElement('div');
      label.className = 'lang-label';
      label.textContent = `${lang}`;
      const wrap = document.createElement('div');
      wrap.className = 'lang-bar-wrap';
      const bar = document.createElement('div');
      bar.className = 'lang-bar';
      bar.style.width = `${pct}%`;
      bar.style.background = hashColor(lang);
      bar.style.color = '#021';
      bar.textContent = `${pct}%`;
      wrap.appendChild(bar);
      row.appendChild(label);
      row.appendChild(wrap);
      langBarsEl.appendChild(row);
    });

    // Наполнить фильтр по языку
    filterLangSelect.innerHTML = '<option value="">Все языки</option>' +
      Array.from(allLanguages).sort().map(l => `<option value="${l}">${l}</option>`).join('');
  }

  function activityIcon(evt){
    const t = evt.type || '';
    if(t.includes('PushEvent')) return '📦';
    if(t.includes('CreateEvent')) return '🆕';
    if(t.includes('ForkEvent')) return '🍴';
    if(t.includes('WatchEvent')) return '⭐';
    if(t.includes('IssuesEvent')) return '❗';
    if(t.includes('IssueCommentEvent')) return '💬';
    if(t.includes('PullRequestEvent')) return '🔀';
    if(t.includes('ReleaseEvent')) return '🏷️';
    return '•';
  }

  function renderActivity(){
    const events = (data.events||[]).slice(0,30);
    activityListEl.innerHTML = '';
    events.forEach(e => {
      const li = document.createElement('li');
      li.className = 'activity-item';
      const emoji = document.createElement('span');
      emoji.className = 'activity-emoji';
      emoji.textContent = activityIcon(e);
      const text = document.createElement('div');
      const repo = e.repo?.name || '';
      const at = e.created_at ? timeAgo(e.created_at) : '';
      text.innerHTML = `<div><strong>${e.type}</strong> в <a href="https://github.com/${repo}" target="_blank" rel="noopener">${repo}</a></div><div class="muted">${at}</div>`;
      li.appendChild(emoji);
      li.appendChild(text);
      activityListEl.appendChild(li);
    });
  }

  function enrichRepos(base){
    return base.map(r => ({
      ...r,
      _updated: r.updated_at ? new Date(r.updated_at).getTime() : 0,
      _created: r.created_at ? new Date(r.created_at).getTime() : 0,
      _sizeKB: r.size ? Number(r.size) : 0
    }));
  }

  function sortRepos(list, mode){
    switch(mode){
      case 'stars_desc': return list.sort((a,b)=>(b.stargazers_count||0)-(a.stargazers_count||0));
      case 'created_desc': return list.sort((a,b)=>b._created - a._created);
      case 'size_desc': return list.sort((a,b)=> (b._sizeKB||0) - (a._sizeKB||0));
      case 'name_asc': return list.sort((a,b)=> (a.name||'').localeCompare(b.name||''));
      case 'updated_desc':
      default: return list.sort((a,b)=> b._updated - a._updated);
    }
  }

  function applySearchFilter(list){
    const q = (searchInput.value || '').toLowerCase().trim();
    const fl = (filterLangSelect.value || '').trim();
    return list.filter(r => {
      const matchesQ = !q || (r.name?.toLowerCase().includes(q) || r.description?.toLowerCase().includes(q));
      const matchesLang = !fl || r.language === fl || (r.languages_bytes && r.languages_bytes[fl] > 0);
      return matchesQ && matchesLang;
    });
  }

  function renderRepos(){
    const mode = sortSelect.value || 'updated_desc';
    const filtered = applySearchFilter([...repos]);
    const sorted = sortRepos(filtered, mode);

    const totalStars = sorted.reduce((a,r)=>a+(r.stargazers_count||0),0);
    const totalForks = sorted.reduce((a,r)=>a+(r.forks_count||0),0);
    repoCountersEl.textContent = `Репозиториев: ${fmt.format(sorted.length)} • ⭐ ${fmt.format(totalStars)} • 🍴 ${fmt.format(totalForks)}`;

    reposGridEl.innerHTML = '';
    sorted.forEach(r => {
      const card = document.createElement('div');
      card.className = 'repo-card';
      const name = document.createElement('a');
      name.className = 'repo-name';
      name.href = r.html_url;
      name.target = '_blank';
      name.rel = 'noopener';
      name.textContent = r.name;

      const desc = document.createElement('div');
      desc.className = 'repo-desc';
      desc.textContent = r.description || '';

      const meta = document.createElement('div');
      meta.className = 'repo-meta';

      if(r.language){
        const lang = document.createElement('span');
        lang.className = 'repo-tag';
        lang.textContent = r.language;
        lang.style.background = `${hashColor(r.language)}22`;
        meta.appendChild(lang);
      }

      if(Array.isArray(r.topics)){
        r.topics.slice(0,3).forEach(t => {
          const tag = document.createElement('span');
          tag.className = 'repo-tag';
          tag.textContent = `#${t}`;
          meta.appendChild(tag);
        });
      }

      const stats = document.createElement('span');
      stats.className = 'repo-stats';
      stats.textContent = `⭐ ${fmt.format(r.stargazers_count||0)}  🍴 ${fmt.format(r.forks_count||0)}`;
      meta.appendChild(stats);

      const updated = document.createElement('div');
      updated.className = 'repo-updated';
      const dt = r.updated_at ? dateFmt.format(new Date(r.updated_at)) : '—';
      updated.textContent = `Обновлён: ${dt}`;

      card.appendChild(name);
      card.appendChild(desc);
      card.appendChild(meta);
      card.appendChild(updated);
      reposGridEl.appendChild(card);
    });
  }

  function renderPinned(){
    const top = [...repos]
      .filter(r => !r.fork)
      .sort((a,b)=>(b.stargazers_count||0)-(a.stargazers_count||0))
      .slice(0,4);

    pinnedListEl.innerHTML = '';
    top.forEach(r => {
      const a = document.createElement('a');
      a.className = 'pinned-item';
      a.href = r.html_url; a.target = '_blank'; a.rel = 'noopener';
      a.innerHTML = `<div><strong>${r.name}</strong> • ⭐ ${fmt.format(r.stargazers_count||0)}</div>` +
                    (r.description ? `<div class="pinned-desc">${r.description}</div>` : '');
      pinnedListEl.appendChild(a);
    });
  }

  function renderQuickStats(){
    const list = data.repos || [];
    const totalRepos = list.length;
    const stars = list.reduce((a,r)=>a+(r.stargazers_count||0),0);
    const forks = list.reduce((a,r)=>a+(r.forks_count||0),0);
    const avgStars = totalRepos ? Math.round((stars/totalRepos)*10)/10 : 0;
    const ages = list.map(r => (Date.now()-new Date(r.created_at).getTime())/(1000*60*60*24));
    const avgAgeDays = ages.length ? Math.round(ages.reduce((a,b)=>a+b,0)/ages.length) : 0;

    const totals = computeLanguageTotals();
    const sum = Object.values(totals).reduce((a,b)=>a+b,0) || 1;
    const topLang = Object.entries(totals).sort((a,b)=>b[1]-a[1])[0];

    const rows = [
      [`Всего репозиториев`, fmt.format(totalRepos)],
      [`Всего звёзд`, `⭐ ${fmt.format(stars)} (в ср.: ${avgStars})`],
      [`Всего форков`, `🍴 ${fmt.format(forks)}`],
      [`Средний возраст проекта`, `${fmt.format(avgAgeDays)} дн.`],
      topLang ? [`Топ язык`, `${topLang[0]} — ${Math.round(topLang[1]/sum*100)}%`] : null,
    ].filter(Boolean);

    quickStatsEl.innerHTML = rows.map(([k,v])=>`<li><strong>${k}:</strong> ${v}</li>`).join('');
  }

  function bindControls(){
    [searchInput, sortSelect, filterLangSelect].forEach(el => el && el.addEventListener('input', renderRepos));
    [sortSelect, filterLangSelect].forEach(el => el && el.addEventListener('change', renderRepos));
  }

  async function init(){
    try{
      await loadData();
      repos = enrichRepos(data.repos||[]);
      renderProfile();
      renderLanguageBars();
      renderActivity();
      renderPinned();
      renderQuickStats();
      bindControls();
      renderRepos();
    }catch(e){
      console.error(e);
      reposGridEl.innerHTML = `<div class="repo-card">Ошибка загрузки данных: ${e?.message||e}</div>`;
    }
  }

  init();
})();