import requests


def fetch_scopus_articles(query, api_key, max_results=25):
    """
    Accede a la API de Scopus para obtener artículos relacionados con el query.
    Es necesario disponer de un API key válido para utilizar este servicio.

    :param query: Consulta de búsqueda.
    :param api_key: API key proporcionado por Scopus.
    :param max_results: Número máximo de resultados a retornar.
    :return: Lista de diccionarios con información de los artículos.
    """
    url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        'Accept': 'application/json',
        'X-ELS-APIKey': api_key
    }
    params = {
        'query': query,
        'count': max_results
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error al acceder a la API de Scopus: {response.status_code}")
        return []

    data = response.json()
    articles = []
    # Se extrae la información deseada de cada entrada del resultado
    for entry in data.get('search-results', {}).get('entry', []):
        title = entry.get('dc:title', 'Sin título')
        # Se pueden extraer otros campos si se requiere
        articles.append({"article_name": title})
    return articles


if __name__ == '__main__':
    # Ejemplo de uso: Se debe sustituir 'YOUR_SCOPUS_API_KEY' por un API key válido.
    api_key = "YOUR_SCOPUS_API_KEY"
    query = "computational thinking"
    articles = fetch_scopus_articles(query, api_key)
    for article in articles:
        print(article)