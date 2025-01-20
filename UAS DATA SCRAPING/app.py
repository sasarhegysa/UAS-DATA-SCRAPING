from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

@app.route("/")
def Home():
    return render_template("index.html")

@app.route("/cnn-wisata")
def cnn_wisata():
    html_doc = requests.get("https://www.cnnindonesia.com/tag/wisata")
    soup = BeautifulSoup(html_doc.text, "html.parser")
    populer_area = soup.find(attrs={'class': 'flex flex-col gap-5'})

    articles = []
    if populer_area:
        items = populer_area.findAll("article")
        for item in items:
            image = item.find("img")
            link = item.find("a")
            title = item.find("h2")
            category = item.find("span", {"class": "text-cnn_red"})
            time = item.find("span", {"class": "text-cnn_black_light3"})

            if image and link and title and category and time:
                articles.append({
                    "img_src": image["src"],
                    "img_alt": image["alt"],
                    "link": f"/detail/cnn/{link['href']}",
                    "title": title.text.strip(),
                    "category": category.text.strip(),
                    "time": time.text.strip()
                })

    return render_template("cnn.html", articles=articles)


@app.route("/kompas-wisata")
def kompas_wisata():
    html_doc = requests.get("https://travel.kompas.com/travel-ideas")
    soup = BeautifulSoup(html_doc.text, "html.parser")
    populer_area = soup.find(attrs={'class': 'latest--news mt2 clearfix'})

    articles = []
    if populer_area:
        items = populer_area.findAll("div", {"class": "article__list clearfix"})
        for item in items:
            image = item.find("img")
            link = item.find("a")
            title = item.find("h3")
            category = item.find("div", {"class": "article__subtitle article__subtitle--inline"})
            time = item.find("div", {"class": "article__date"})

            if image and link and title and category and time:
                articles.append({
                    "img_src": image["data-src"],
                    "img_alt": image["alt"],
                    "link": f"/detail/kompas/{link['href']}",
                    "title": title.text.strip(),
                    "category": category.text.strip(),
                    "time": time.text.strip()
                })

    return render_template("kompas.html", articles=articles)


@app.route("/detik-wisata")
def detik_wisata():
    html_doc = requests.get("https://travel.detik.com/travel-news/indeks")
    soup = BeautifulSoup(html_doc.text, "html.parser")
    populer_area = soup.find(attrs={'class': 'grid-row list-content'})

    articles = []
    if populer_area:
        items = populer_area.findAll("article", {"class": "list-content__item"})
        for item in items:
            image = item.find("img")
            link = item.find("a")
            title = item.find("h3")
            time = item.find("div", {"class": "media__date"})

            if image and link and title and time:
                articles.append({
                    "img_src": image["src"],
                    "img_alt": image["alt"],
                    "link": f"/detail/detik/{link['href']}", 
                    "title": title.text.strip(),
                    "time": time.text.strip()
                })

    return render_template("detik.html", articles=articles)

@app.route("/detail/<source>/<path:url>")
def article_detail(source, url):
    def fetch_content(url):
        """Fetch content and next page link from the article page."""
        try:
            html_doc = requests.get(url)
            html_doc.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None, None, None, None 

        soup = BeautifulSoup(html_doc.text, "html.parser")

        if source == "cnn":
            title = soup.find("h1", class_="text-[32px]").get_text(strip=True) if soup.find("h1", class_="text-[32px]") else "Judul tidak ditemukan"
            content_div = soup.find("div", class_="detail-text")
            content = content_div.get_text(strip=True, separator="\n") if content_div else "Konten tidak tersedia"
            next_page = soup.find("a", {"class": "inline-block py-2 px-4 text-sm border border-cnn_red"})
            next_page_url = urljoin(url, next_page["href"]) if next_page and next_page.get("href", "").startswith("http") else None
            image = soup.find("img", class_="w-full")
            image_src = image["src"] if image else None
        elif source == "kompas":
            title = soup.find("h1").text.strip() if soup.find("h1") else "Judul tidak ditemukan"
            content_div = soup.find("div", {"class": "read__content"})
            content = content_div.get_text(strip=True, separator="\n") if content_div else "Konten tidak ditemukan"
            next_page = soup.find("a", {"class": "paging__link"})
            next_page_url = None
            if next_page:
                href = next_page.get("href", "")
                if href.startswith("http") or href.startswith("/"):
                    next_page_url = urljoin(url, href)
            image = soup.find("div", {"class": "cover-photo -gallery"})
            if image:
                img_tag = image.find("img")
                image_src = img_tag["src"] if img_tag and "src" in img_tag.attrs else None
            else:
                image_src = None
        elif source == "detik":
            title = soup.find("h1").text.strip() if soup.find("h1") else "Judul tidak ditemukan"
            content_div = soup.find("div", {"class": "detail__body-text"})
            content = content_div.get_text(strip=True, separator="\n") if content_div else "Konten tidak ditemukan"
            next_page = soup.find("a", {"class": "detail__btn-next"})
            next_page_url = urljoin(url, next_page["href"]) if next_page and "href" in next_page.attrs else None
            image_section = soup.find("div", {"class": "detail__media"})
            if image_section:
                img_tag = image_section.find("img")
                image_src = img_tag["src"] if img_tag and "src" in img_tag.attrs else None
            else:
                image_src = None

        else:
            return None, None, None, None

        return title, content, next_page_url, image_src

    full_content = ""
    next_url = url
    title = None
    image_src = None

    while next_url:
        current_title, content, next_url, current_image_src = fetch_content(next_url)
        if current_title:
            title = title or current_title
            image_src = image_src or current_image_src 
            full_content += content + "\n"
        else:
            break

    detail = {
        "title": title,
        "content": full_content.strip(),
        "image_src": image_src
    }

    return render_template("detail.html", detail=detail)

if __name__ == "__main__":
    app.run(debug=True)
