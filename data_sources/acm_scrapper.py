import requests
from bs4 import BeautifulSoup


def fetch_acm_articles(query):
    """
    Realiza scraping a la base de datos de ACM para obtener artículos relacionados con el query.
    Este ejemplo es ilustrativo; en un entorno real se debe ajustar según la estructura de la web.
    """
    url = f"https://dl.acm.org/action/doSearch?AllField={query}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error al acceder a ACM.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    for h5 in soup.find_all("h5", class_="issue-item__title"):
        title = h5.get_text(strip=True)
        articles.append({"article_name": title})
    return articles


if __name__ == '__main__':
    query = "computational thinking"
    articles = fetch_acm_articles(query)
    for article in articles:
        print(article)