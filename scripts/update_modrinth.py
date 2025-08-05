import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Путь к rp.html (на уровень выше папки scripts)
html_path = Path(__file__).parent.parent / "rp.html"

# Загрузка HTML
with open(html_path, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Поиск всех плиток с data-modrinth-id
tiles = soup.select(".tile[data-modrinth-id]")

for tile in tiles:
    modrinth_id = tile.get("data-modrinth-id")
    print(f"⏳ Получаю данные для {modrinth_id}...")

    # Получение данных проекта
    res = requests.get(f"https://api.modrinth.com/v2/project/{modrinth_id}")
    if res.status_code != 200:
        print(f"⚠️ Не удалось получить проект {modrinth_id}")
        continue
    data = res.json()

    # Получение данных команды (авторы)
    team_res = requests.get(f"https://api.modrinth.com/v2/project/{modrinth_id}/members")
    if team_res.status_code == 200:
        team_data = team_res.json()
        preferred_author = "Kreo_gen"

        authors = [m.get("user", {}).get("username") for m in team_data if m.get("user")]
        authors = [a for a in authors if a]

        if preferred_author in authors:
            authors.remove(preferred_author)
            authors.insert(0, preferred_author)
    else:
        authors = [data.get("author", "Неизвестный автор")]

    # Обновляем содержимое
    title_el = tile.select_one(".tile-title")
    desc_el = tile.select_one(".tile-desc p")
    image_el = tile.select_one(".tile-image")
    link_el = tile.select_one(".tile-link")
    authors_container = tile.select_one(".tile-authors")

    if title_el:
        title_el.string = data.get("title", "Без названия")

    if desc_el:
        desc_el.string = data.get("description", "Без описания")[:200] + "..."

    if image_el:
        icon_url = data.get("icon_url")
        if icon_url:
            image_el["style"] = (
                f"background-image: url('{icon_url}'); "
                f"background-size: cover; background-position: center;"
            )

    if link_el:
        link_el["href"] = f"https://modrinth.com/resourcepack/{modrinth_id}"

    if authors_container:
        authors_container.clear()
        for name in authors:
            author_link = soup.new_tag("a", href=f"https://modrinth.com/user/{name}", target="_blank", **{"class": "author"})
            author_link.string = name
            authors_container.append(author_link)



    print(f"✅ Обновлено: {data.get('title')} (авторы: {', '.join(authors)})")

# Сохраняем обновлённый HTML
with open(html_path, "w", encoding="utf-8") as file:
    file.write(str(soup))

print("🎉 Обновление завершено.")
