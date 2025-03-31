import requests
from bs4 import BeautifulSoup

def fetch_sage_articles(query):
    """
    Realiza scraping a la plataforma de SAGE para obtener artículos relacionados con el query.
    Se realiza una solicitud HTTP y se parsea el HTML para extraer títulos de artículos.
    """
    url = f"https://journals.sagepub.com/action/doSearch?AllField={query}"
    response = requests.get(url)
    if response.status_code != 200:
        print("Error al acceder a SAGE Journals.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    # Ejemplo de extracción: Se buscan etiquetas que contienen títulos de artículos
    for tag in soup.find_all("h3", class_="hlFld-Title"):
        title = tag.get_text(strip=True)
        articles.append({"article_name": title})
    return articles

if __name__ == '__main__':
    query = "computational thinking"
    articles = fetch_sage_articles(query)
    for article in articles:
        print(article)
