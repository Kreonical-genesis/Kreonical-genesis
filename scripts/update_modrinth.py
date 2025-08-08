import requests
from bs4 import BeautifulSoup
from pathlib import Path

html_path = Path(__file__).parent.parent / "rp.html"

with open(html_path, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Функция для получения авторов проекта
def get_authors(modrinth_id, preferred_author="Kreo_gen"):
    team_res = requests.get(f"https://api.modrinth.com/v2/project/{modrinth_id}/members")
    if team_res.status_code == 200:
        team_data = team_res.json()
        authors = [m.get("user", {}).get("username") for m in team_data if m.get("user")]
        authors = [a for a in authors if a]
        if preferred_author in authors:
            authors.remove(preferred_author)
            authors.insert(0, preferred_author)
        return authors
    return []

# Функция для создания одного блока .tile на основе данных проекта
def create_tile(soup, data, authors):
    tile = soup.new_tag("div", attrs={"class": "tile", "data-modrinth-id": data.get("id", "")})

    tile_content = soup.new_tag("div", attrs={"class": "tile-content"})
    tile.append(tile_content)

    tile_left = soup.new_tag("div", attrs={"class": "tile-left"})
    tile_content.append(tile_left)

    # Картинка
    tile_image = soup.new_tag("div", attrs={"class": "tile-image"})
    icon_url = data.get("icon_url")
    if icon_url:
        tile_image["style"] = f"background-image: url('{icon_url}'); background-size: cover; background-position: center;"
    tile_left.append(tile_image)

    # Ссылка
    tile_link = soup.new_tag("a", href=f"https://modrinth.com/resourcepack/{data.get('id')}", target="_blank", **{"class": "tile-link"})
    tile_link.string = "Открыть на Modrinth"
    tile_left.append(tile_link)

    # Авторы
    authors_container = soup.new_tag("div", attrs={"class": "tile-authors"})
    for author_name in authors:
        author_link = soup.new_tag("a", href=f"https://modrinth.com/user/{author_name}", target="_blank", **{"class": "author"})
        author_link.string = author_name
        authors_container.append(author_link)
    tile_left.append(authors_container)

    tile_right = soup.new_tag("div", attrs={"class": "tile-right"})
    tile_content.append(tile_right)

    # Название
    tile_title = soup.new_tag("div", attrs={"class": "tile-title"})
    tile_title.string = data.get("title", "Без названия")
    tile_right.append(tile_title)

    # Описание
    tile_desc = soup.new_tag("div", attrs={"class": "tile-desc"})
    p = soup.new_tag("p")
    desc_text = data.get("description", "Без описания")
    if len(desc_text) > 200:
        desc_text = desc_text[:200] + "..."
    p.string = desc_text
    tile_desc.append(p)
    tile_right.append(tile_desc)

    return tile


# Обработка одиночных блоков с data-modrinth-id (текущая логика)
single_tiles = soup.select(".tile[data-modrinth-id]")
for tile in single_tiles:
    modrinth_id = tile.get("data-modrinth-id")
    print(f"⏳ Получаю данные для проекта {modrinth_id}...")

    res = requests.get(f"https://api.modrinth.com/v2/project/{modrinth_id}")
    if res.status_code != 200:
        print(f"⚠️ Не удалось получить проект {modrinth_id}")
        continue
    data = res.json()

    authors = get_authors(modrinth_id)
    if not authors:
        authors = [data.get("author", "Неизвестный автор")]

    # Обновляем содержимое существующего блока
    title_el = tile.select_one(".tile-title")
    desc_el = tile.select_one(".tile-desc p")
    image_el = tile.select_one(".tile-image")
    link_el = tile.select_one(".tile-link")
    authors_container = tile.select_one(".tile-authors")

    if title_el:
        title_el.string = data.get("title", "Без названия")

    if desc_el:
        desc_text = data.get("description", "Без описания")
        desc_el.string = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text

    if image_el:
        icon_url = data.get("icon_url")
        if icon_url:
            image_el["style"] = (
                f"background-image: url('{icon_url}'); "
                "background-size: cover; background-position: center;"
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


# Обработка блоков с data-modrinth-name (удаляем дубликаты)
unique_projects = {}

user_tiles = soup.select(".tile[data-modrinth-name]")
for tile in user_tiles:
    username = tile.get("data-modrinth-name")
    print(f"⏳ Получаю проекты пользователя {username}...")

    res = requests.get(f"https://api.modrinth.com/v2/user/{username}/projects")
    if res.status_code != 200:
        print(f"⚠️ Не удалось получить проекты пользователя {username}")
        continue
    projects = res.json()

    for project in projects:
        modrinth_id = project.get("id")
        if not modrinth_id:
            continue
        if modrinth_id not in unique_projects:
            unique_projects[modrinth_id] = project

    tile.decompose()  # Удаляем исходный placeholder


# Вставка всех уникальных проектов в <main class="grid">
main = soup.select_one("main.grid")
if not main:
    print("❌ Не найден <main class='grid'> — некуда вставлять плитки!")
else:
    for project in unique_projects.values():
        modrinth_id = project.get("id")
        authors = get_authors(modrinth_id)
        if not authors:
            authors = [project.get("author", "Неизвестный автор")]

        new_tile = create_tile(soup, project, authors)
        main.append(new_tile)

        print(f"✅ Добавлен проект: {project.get('title')} (авторы: {', '.join(authors)})")


# Сохраняем обновлённый HTML
with open(html_path, "w", encoding="utf-8") as file:
    file.write(str(soup))

print("🎉 Обновление завершено.")
