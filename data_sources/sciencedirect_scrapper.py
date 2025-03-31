import requests
from bs4 import BeautifulSoup

def fetch_sciencedirect_articles(query):
    """
    Realiza scraping a la plataforma de ScienceDirect para obtener artículos relacionados con el query.
    Se utiliza un header para simular un navegador y se extraen los títulos de los artículos.
    """
    url = f"https://www.sciencedirect.com/search?qs={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error al acceder a ScienceDirect.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    # Ejemplo de extracción: Se buscan etiquetas <h2> que contienen el título del artículo
    for h2 in soup.find_all("h2", class_="result-list-title"):
        title = h2.get_text(strip=True)
        articles.append({"article_name": title})
    return articles

if __name__ == '__main__':
    query = "computational thinking"
    articles = fetch_sciencedirect_articles(query)
    for article in articles:
        print(article)
