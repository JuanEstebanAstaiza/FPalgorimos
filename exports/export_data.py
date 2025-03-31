import json

def export_to_json(data, filename="exports/unified_data.json"):
    """
    Exporta los datos unificados a un archivo JSON.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Datos exportados a {filename}")

def export_to_ris(data, filename="exports/unified_data.ris"):
    """
    Exporta los datos unificados a un archivo en formato RIS.
    Formato RIS (Research Information Systems) es un estándar que utiliza etiquetas
    para identificar campos. Se incluye:
      - TY  - Tipo de referencia (por ejemplo, JOUR para artículos)
      - AU  - Autor principal
      - TI  - Título del artículo
      - PY  - Año de publicación (se extrae de la fecha)
      - ID  - ID del artículo
      - KW  - Temática del artículo
      - CT  - Categoría del artículo
    """
    with open(filename, "w", encoding="utf-8") as f:
        for item in data:
            f.write("TY  - JOUR\n")
            f.write(f"AU  - {item.get('author_name','')}\n")
            f.write(f"TI  - {item.get('article_name','')}\n")
            # Se extrae el año de la fecha de publicación
            publication_date = item.get('publication_date', '')
            year = publication_date.split("-")[0] if publication_date else ""
            f.write(f"PY  - {year}\n")
            f.write(f"ID  - {item.get('id','')}\n")
            f.write(f"KW  - {item.get('theme','')}\n")
            f.write(f"CT  - {item.get('category','')}\n")
            f.write("ER  -\n\n")
    print(f"Datos exportados a {filename}")

def export_to_bibtex(data, filename="exports/unified_data.bib"):
    """
    Exporta los datos unificados a un archivo en formato BibTex.
    Se genera una entrada para cada artículo con:
      - @article: Tipo de entrada para artículos
      - author: Autor principal
      - title: Título del artículo
      - year: Año de publicación (extraído de publication_date)
      - id: ID del artículo (utilizado como clave)
      - note: Se pueden incluir la temática y categoría
    """
    with open(filename, "w", encoding="utf-8") as f:
        for item in data:
            publication_date = item.get('publication_date', '')
            year = publication_date.split("-")[0] if publication_date else ""
            # Se usa el ID para generar la clave de la entrada
            entry_key = f"article{item.get('id','')}"
            f.write(f"@article{{{entry_key},\n")
            f.write(f"  author = {{{item.get('author_name','')}}},\n")
            f.write(f"  title = {{{item.get('article_name','')}}},\n")
            f.write(f"  year = {{{year}}},\n")
            f.write(f"  note = {{{'Temática: ' + item.get('theme','') + '; Categoría: ' + item.get('category','')}}}\n")
            f.write("}\n\n")
    print(f"Datos exportados a {filename}")


