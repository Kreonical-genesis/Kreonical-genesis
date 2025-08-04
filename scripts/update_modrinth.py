import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Путь к rp.html
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
        # Собираем всех авторов по username
        preferred_author = "Kreo_gen"

        authors = [member.get("user", {}).get("username") for member in team_data if member.get("user")]
        authors = [name for name in authors if name]  # Убираем пустые

        # Переносим preferred_author в начало, если он есть
        if preferred_author in authors:
            authors.remove(preferred_author)
            authors.insert(0, preferred_author)

        author_string = ", ".join(authors) if authors else "Неизвестные авторы"

    else:
        author_string = data.get("author", "Неизвестные авторы")

    # Обновляем содержимое плитки
    title_el = tile.select_one(".tile-title")
    desc_el = tile.select_one(".tile-desc")
    author_el = tile.select_one(".tile-author")
    image_el = tile.select_one(".tile-image")

    if title_el:
        title_el.string = data.get("title", "Без названия")

    if desc_el:
        desc_el.string = data.get("description", "Без описания")[:200] + "..."

    if author_el:
        author_el.string = author_string

    if image_el:
        icon_url = data.get("icon_url")
        if icon_url:
            image_el["style"] = f"background-image: url('{icon_url}');"

    print(f"✅ Обновлено: {data.get('title')} (авторы: {author_string})")

# Сохраняем HTML обратно
with open(html_path, "w", encoding="utf-8") as file:
    file.write(str(soup))

print("🎉 Обновление завершено.")
