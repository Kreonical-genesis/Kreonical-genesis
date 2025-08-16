// github.js
// Логика для вкладки GitHub на сайте Kreonical
// Работает с файлом data/{username}.json, который генерирует fetch_github.py

document.addEventListener("DOMContentLoaded", () => {
  const app = document.getElementById("app");
  const username = app.dataset.username;

  // Путь до JSON
  const dataUrl = `data/${username}.json`;

  // Загружаем данные
  fetch(dataUrl)
    .then(r => r.json())
    .then(data => initGitHubPage(data))
    .catch(err => {
      console.error("Ошибка загрузки GitHub JSON:", err);
    });
});

/**
 * Главный инициализатор страницы
 */
function initGitHubPage(data) {
  renderProfile(data.user);
  renderPinned(data.repos);
  renderQuickStats(data.repos);
  renderLanguages(data.repos);
  setupActivityFilters(data.events);
  renderHeatmap(data.commit_activity || []);
  renderRepos(data.repos);
}

/* ------------------ ПРОФИЛЬ ------------------ */
function renderProfile(user) {
  document.getElementById("gh-avatar").src = user.avatar_url;
  document.getElementById("gh-avatar").classList.remove("hidden");
  document.getElementById("gh-name").textContent = user.name || "";
  document.getElementById("gh-login").textContent = `@${user.login}`;
  document.getElementById("gh-bio").textContent = user.bio || "";
  document.getElementById("gh-repos-count").textContent = user.public_repos;
  document.getElementById("gh-followers").textContent = user.followers;
  document.getElementById("gh-following").textContent = user.following;
  document.getElementById("gh-profile-link").href = user.html_url;
}

/* ------------------ PINNED ------------------ */
function renderPinned(repos) {
  const pinnedList = document.getElementById("pinned-list");
  pinnedList.innerHTML = "";

  // Берём топ-4 по звёздам
  const top = [...repos].sort((a, b) => b.stargazers_count - a.stargazers_count).slice(0, 4);
  for (let r of top) {
    const div = document.createElement("div");
    div.className = "pinned-item";
    div.innerHTML = `
      <a href="${r.html_url}" target="_blank" rel="noopener">${r.name}</a>
      <span>⭐ ${r.stargazers_count}</span>
    `;
    pinnedList.appendChild(div);
  }
}

/* ------------------ QUICK STATS ------------------ */
function renderQuickStats(repos) {
  const list = document.getElementById("quick-stats");
  list.innerHTML = "";

  const totalStars = repos.reduce((s, r) => s + r.stargazers_count, 0);
  const totalForks = repos.reduce((s, r) => s + r.forks_count, 0);
  const langs = {};
  repos.forEach(r => {
    if (r.language) langs[r.language] = (langs[r.language] || 0) + 1;
  });
  const topLang = Object.entries(langs).sort((a, b) => b[1] - a[1])[0];

  const items = [
    `Всего репозиториев: ${repos.length}`,
    `Всего ⭐: ${totalStars}`,
    `Всего 🍴: ${totalForks}`,
    topLang ? `Самый частый язык: ${topLang[0]} (${topLang[1]})` : ""
  ];

  for (let t of items) {
    if (!t) continue;
    const li = document.createElement("li");
    li.textContent = t;
    list.appendChild(li);
  }
}

/* ------------------ LANGUAGES ------------------ */
function renderLanguages(repos) {
  const bars = document.getElementById("lang-bars");
  bars.innerHTML = "";

  const allLangs = {};
  repos.forEach(r => {
    if (r.languages_bytes) {
      for (let [lang, bytes] of Object.entries(r.languages_bytes)) {
        allLangs[lang] = (allLangs[lang] || 0) + bytes;
      }
    }
  });

  const total = Object.values(allLangs).reduce((a, b) => a + b, 0);
  const sorted = Object.entries(allLangs).sort((a, b) => b[1] - a[1]);

  for (let [lang, bytes] of sorted) {
    const percent = ((bytes / total) * 100).toFixed(1);

    const row = document.createElement("div");
    row.className = "lang-row";
    row.innerHTML = `
      <div class="lang-label">${lang} • ${percent}%</div>
      <div class="lang-bar-wrap">
        <div class="lang-bar" style="width:${percent}%; background:${colorForLang(lang)}"></div>
      </div>
    `;
    bars.appendChild(row);
  }
}

/* Генератор цвета для языков */
function colorForLang(lang) {
  const colors = {
    JavaScript: "#f1e05aff",
    TypeScript: "#3178c6ff",
    Python: "#3572A5ff",
    Java: "#b07219ff",
    C: "#555555ff",
    "C++": "#f34b7dff",
    HTML: "#e34c26ff",
    CSS: "#563d7cff",
    Shell: "#89e051ff",
    Go: "#00ADD8ff",
    Rust: "#824c00ff",
    Kotlin: "#ff12ffff",
    GDScript: "#3f3f3fff",
    Swift: "#999",
    Julia: "#70005dff",
    Ruby: "#530000ff",
    CoffeeScript: "#475cfeff",
    Elixir: "#9736afff",
    "C#": "#088014ff",
    Scala: "#ff5353ff",
    Erlang: "#b41fc8ff",
    Nim: "#bcc600ff",
    Assembler: "#ffffffff",
    Haskell: "#846784ff",
    Red: "#ff0000ffff",
    Frege: "#62f7ffff",
    Racket: "#3a28ffff",
    OCaml: "#ffcd59ff",
    "Objective-C": "#2e35ffff",
    LiveScript: "#69ff55ff",
    D: "#ff7575ff",
    "F#": "#9d05aeff",
    Raku: "#3c00ffff",
    Chapel: "#adee20ff",
    Gosu: "#767676ff",
    Zig: "#e17c7cff",
    Haxe: "#c1800fff",
    V: "#938cffff",
    Dart: "#25fad6ff",
    Smalltalk: "#3b593dff",
    Mojo: "#ff3f3fff",
    Odin: "#626ef5ff",
    Factor: "#afb9acff"
  };
  return colors[lang] || "#999";
}

/* ------------------ ACTIVITY ------------------ */
function setupActivityFilters(events) {
  const list = document.getElementById("activity-list");
  const typeSelect = document.getElementById("activity-type");
  const searchInput = document.getElementById("activity-search");

  function render() {
    const type = typeSelect.value;
    const search = searchInput.value.toLowerCase();

    list.innerHTML = "";
    const filtered = events.filter(e => {
      if (type && e.type !== type) return false;
      if (search && !e.repo.name.toLowerCase().includes(search)) return false;
      return true;
    });

    for (let ev of filtered.slice(0, 20)) {
      const li = document.createElement("li");
      li.className = "activity-item";
      li.textContent = `${ev.type} → ${ev.repo.name}`;
      list.appendChild(li);
    }
    if (!filtered.length) {
      const li = document.createElement("li");
      li.textContent = "Нет событий";
      list.appendChild(li);
    }
  }

  typeSelect.addEventListener("change", render);
  searchInput.addEventListener("input", render);
  render();
}

/* ------------------ HEATMAP ------------------ */
function renderHeatmap(weeks) {
  const container = document.getElementById("heatmap");
  container.innerHTML = "";

  // weeks = массив из /stats/commit_activity (52 недели)
  const max = Math.max(...weeks.map(w => w.total), 1);

  for (let w of weeks) {
    for (let d of w.days) {
      const div = document.createElement("div");
      const level = d === 0 ? 0 : Math.ceil((d / max) * 4);
      div.className = `level-${level}`;
      container.appendChild(div);
    }
  }

  // легенда
  const legend = document.getElementById("heatmap-legend");
  legend.innerHTML = "Меньше";
  for (let i = 0; i <= 4; i++) {
    const s = document.createElement("span");
    s.className = `level-${i}`;
    legend.appendChild(s);
  }
  legend.innerHTML += "Больше";
}

/* ------------------ REPOS ------------------ */
function renderRepos(repos) {
  const grid = document.getElementById("repos-grid");
  grid.innerHTML = "";

  for (let r of repos) {
    const card = document.createElement("div");
    card.className = "repo-card";

    // Бейджи
    const badges = `
      <div class="repo-badges">
        <span class="repo-badge">⭐ ${r.stargazers_count}</span>
        <span class="repo-badge">🍴 ${r.forks_count}</span>
        ${r.open_issues_count ? `<span class="repo-badge">❗ ${r.open_issues_count}</span>` : ""}
        ${r.pulls_count ? `<span class="repo-badge">🔀 ${r.pulls_count}</span>` : ""}
        ${r.releases_count ? `<span class="repo-badge">📦 ${r.releases_count}</span>` : ""}
        ${r.latest_release ? `<span class="repo-badge repo-badge--muted">release: ${r.latest_release.tag_name}</span>` : ""}
      </div>
    `;

    // Контрибьюторы (до 3)
    let contribHTML = "";
    if (r.contributors && r.contributors.length) {
      contribHTML = `
        <div class="repo-contrib">
          ${r.contributors.slice(0, 3).map(c =>
            `<a href="${c.html_url}" class="contrib" title="${c.login}" target="_blank" rel="noopener">
              <img src="${c.avatar_url}" alt="${c.login}" />
            </a>`
          ).join("")}
        </div>
      `;
    }

    // Последние stargazers
    let starsHTML = "";
    if (r.stargazers_recent && r.stargazers_recent.length) {
      starsHTML = `
        <div class="repo-stars">
          <div class="stars-avatars">
            ${r.stargazers_recent.map(s =>
              `<a href="${s.html_url}" class="star" title="${s.login}" target="_blank" rel="noopener">
                <img src="${s.avatar_url}" alt="${s.login}" />
              </a>`
            ).join("")}
          </div>
          <div class="stars-count">+${r.stargazers_recent.length} недавно</div>
        </div>
      `;
    }

    card.innerHTML = `
      <a class="repo-name" href="${r.html_url}" target="_blank" rel="noopener">${r.name}</a>
      <div class="repo-desc">${r.description || ""}</div>
      ${badges}
      ${contribHTML}
      ${starsHTML}
      <div class="repo-updated">Обновлён: ${new Date(r.updated_at).toLocaleDateString()}</div>
    `;

    grid.appendChild(card);
  }
}
