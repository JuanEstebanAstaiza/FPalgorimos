import matplotlib.pyplot as plt
from wordcloud import WordCloud


def generate_bar_chart(data, title="Estadísticas", xlabel="Categoría", ylabel="Frecuencia"):
    """
    Genera un gráfico de barras a partir de un diccionario con datos.
    """
    categories = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(10, 6))
    plt.bar(categories, values, color='skyblue')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def generate_wordcloud(text, title="Nube de Palabras"):
    """
    Genera y muestra una nube de palabras a partir de un string de texto.
    """
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    sample_data = {"Computación": 15, "Datos": 10, "Sistemas": 8, "Algoritmos": 12}
    generate_bar_chart(sample_data, title="Frecuencia de Temáticas")

    sample_text = "computational thinking datos computación algoritmos análisis estadístico modelado visualización"
    generate_wordcloud(sample_text, title="Nube de Palabras de Ejemplo")