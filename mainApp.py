import mysql.connector  # Importa el conector de MySQL para interactuar con bases de datos MySQL
import requests  # Importa la biblioteca Requests para realizar solicitudes HTTP en Python
import time  # Importamos el módulo time para medir tiempos de ejecución
import matplotlib.pyplot as plt # Importamos matplotlib.pyplot para crear gráficos

# Configuración de la base de datos
CONFIG_BD = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "articleservice"
}

TABLAS = {
    "articulos": {
        "id": "INT AUTO_INCREMENT PRIMARY KEY",
        "nombre_base_datos": "VARCHAR(20) NOT NULL",
        "autores": "VARCHAR(255)",
        "fecha_publicacion": "DATE",
        "titulo": "VARCHAR(255) NOT NULL UNIQUE",
        "enlace": "VARCHAR(255)"
    },
    "articulos_repetidos": {
        "id": "INT AUTO_INCREMENT PRIMARY KEY",
        "nombre_base_datos": "VARCHAR(20) NOT NULL",
        "autores": "VARCHAR(255)",
        "fecha_publicacion": "DATE",
        "titulo": "VARCHAR(255) NOT NULL",
        "enlace": "VARCHAR(255)"
    }
}

# Configuración de APIs
API_KEY_SCOPUS = "70c102fffa4eee4b0b2d1700b3a279ff"
BASE_URL_SCOPUS = "https://api.elsevier.com/content/search/scopus"


def conectar_base_datos():
    """Conecta con la base de datos y la crea si no existe."""
    print("🔄 Conectando a la base de datos...")
    conexion = mysql.connector.connect(**CONFIG_BD)
    print("✅ Conexión establecida con la base de datos.")
    return conexion


def crear_tablas():
    """Crea las tablas definidas en la configuración si no existen."""
    print("📌 Verificando y creando tablas si es necesario...")
    conexion = conectar_base_datos()
    cursor = conexion.cursor()
    for tabla, campos in TABLAS.items():
        columnas = ", ".join(f"{col} {tipo}" for col, tipo in campos.items())
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {tabla} ({columnas})")
        print(f"✅ Tabla '{tabla}' verificada/creada correctamente.")
    conexion.commit()
    cursor.close()
    conexion.close()


def eliminar_tablas():
    """Elimina las tablas de la base de datos si existen."""
    conexion = conectar_base_datos()
    if conexion is None:
        return
    cursor = conexion.cursor()

    for tabla in TABLAS.keys():
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
            print(f"🗑️ Tabla '{tabla}' eliminada correctamente.")
        except mysql.connector.Error as error:
            print(f"❌ Error al eliminar la tabla '{tabla}': {error}")

    conexion.commit()
    cursor.close()
    conexion.close()
    print("✅ Todas las tablas han sido eliminadas.")


def articulo_existe(cursor, titulo):
    """Verifica si un artículo ya existe en la base de datos usando EXISTS."""
    cursor.execute("SELECT EXISTS(SELECT 1 FROM articulos WHERE titulo = %s)", (titulo,))
    return cursor.fetchone()[0] == 1


def guardar_articulos(articulos):
    """Guarda una lista de artículos en la base de datos, indicando cada inserción."""
    if not articulos:
        print("⚠️ No hay artículos para guardar.")
        return

    conexion = conectar_base_datos()
    cursor = conexion.cursor()
    articulos_nuevos, articulos_repetidos = [], []

    for articulo in articulos:
        if articulo_existe(cursor, articulo[3]):  # 3 = título
            articulos_repetidos.append(articulo)
        else:
            articulos_nuevos.append(articulo)

    for tabla, lista in [("articulos", articulos_nuevos), ("articulos_repetidos", articulos_repetidos)]:
        if lista:
            cursor.executemany(f"""
                INSERT INTO {tabla} (nombre_base_datos, autores, fecha_publicacion, titulo, enlace)
                VALUES (%s, %s, %s, %s, %s)
            """, lista)
            for articulo in lista:
                print(f"📝 Guardado en '{tabla}': {articulo[3]}")
            print(f"✅ Se guardaron {len(lista)} artículos en '{tabla}'.")

    conexion.commit()
    cursor.close()
    conexion.close()


def listar_tabla(nombre_tabla):
    """Lista los artículos de una tabla con mayor detalle."""
    conexion = conectar_base_datos()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {nombre_tabla} ORDER BY fecha_publicacion DESC")
    articulos = cursor.fetchall()

    if not articulos:
        print(f"⚠️ No hay artículos en '{nombre_tabla}'.")
    else:
        print(f"\n📜 Lista de {nombre_tabla}:")
        for articulo in articulos:
            print(f"[{articulo['fecha_publicacion']}] {articulo['titulo']} - {articulo['autores']}")

    cursor.close()
    conexion.close()


def obtener_articulos_scopus(consulta="Human Computer Interaction", max_resultados=100):
    """Obtiene artículos de Scopus y los almacena en la base de datos con retroalimentación detallada."""
    print("🔎 Buscando artículos en Scopus...")
    articulos_guardados = 0
    indice_inicio = 0
    articulos_batch = []

    while articulos_guardados < max_resultados:
        respuesta = requests.get(BASE_URL_SCOPUS, params={
            "query": consulta, "apiKey": API_KEY_SCOPUS, "count": 25, "start": indice_inicio
        }, headers={"X-ELS-APIKey": API_KEY_SCOPUS, "Accept": "application/json"})

        if respuesta.status_code != 200:
            print("❌ Error en la solicitud:", respuesta.json())
            break

        articulos = respuesta.json().get("search-results", {}).get("entry", [])
        if not articulos:
            print("⚠️ No se encontraron más artículos en Scopus.")
            break

        for articulo in articulos:
            titulo = articulo.get("dc:title", "Sin título")
            enlace = articulo.get("link", [{}])[0].get("@href", "Sin enlace")
            fecha_publicacion = articulo.get("prism:coverDate", "0000-00-00")
            autores = articulo.get("dc:creator", "Desconocido")
            autores_lista = ", ".join(autores) if isinstance(autores, list) else autores

            print(f"📄 Encontrado: {titulo} ({fecha_publicacion})")
            articulos_batch.append(("Scopus", autores_lista, fecha_publicacion, titulo, enlace))
            articulos_guardados += 1

            if articulos_guardados >= max_resultados:
                break

        indice_inicio += 25

    guardar_articulos(articulos_batch)
    print(f"✅ Se guardaron {articulos_guardados} artículos de Scopus.")


def listar_articulos_ordenados(criterio="fecha_desc"):
    """
    Lista los artículos almacenados en la base de datos según el criterio seleccionado.

    Criterios disponibles:
    - "fecha_desc": Ordenados por fecha de publicación (más recientes primero).
    - "fecha_asc": Ordenados por fecha de publicación (más antiguos primero).
    - "titulo_asc": Ordenados alfabéticamente por título (A-Z).
    - "titulo_desc": Ordenados alfabéticamente por título (Z-A).
    - "autor_asc": Ordenados alfabéticamente por autores (A-Z).
    - "autor_desc": Ordenados alfabéticamente por autores (Z-A).
    - "nombre_base_datos": Ordenados por la base de datos de origen.

    :param criterio: Criterio de ordenamiento (default: "fecha_desc").
    """
    conexion = conectar_base_datos()
    if conexion is None:
        return

    # Diccionario con los criterios de ordenamiento disponibles
    criterios_orden = {
        "fecha_desc": "fecha_publicacion DESC",
        "fecha_asc": "fecha_publicacion ASC",
        "titulo_asc": "titulo ASC",
        "titulo_desc": "titulo DESC",
        "autor_asc": "autores ASC",
        "autor_desc": "autores DESC",
        "nombre_base_datos": "nombre_base_datos ASC"
    }

    # Verificar si el criterio solicitado existe
    if criterio not in criterios_orden:
        print(f"⚠️ Criterio '{criterio}' no válido. Usando 'fecha_desc' por defecto.")
        criterio = "fecha_desc"

    cursor = conexion.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM articulos ORDER BY {criterios_orden[criterio]}")
    articulos = cursor.fetchall()

    if not articulos:
        print("⚠️ No hay artículos registrados.")
    else:
        print(f"\n📜 Lista de artículos ordenados por {criterio.replace('_', ' ')}:")
        for articulo in articulos:
            print(
                f"[{articulo['fecha_publicacion']}] {articulo['titulo']} - {articulo['autores']} ({articulo['nombre_base_datos']})")

    cursor.close()
    conexion.close()

#metodos de ordenamiento (por ejemplo, timsort, quicksort, etc.)
def ejecutar_todos_los_metodos():
    """
    Función principal que se encarga de conectar a la base de datos,
    obtener los artículos almacenados y ejecutar todos los métodos de ordenamiento
    disponibles sobre los artículos.
    Para cada uno de los métodos de ordenamiento, se mide el tiempo de ejecución
    y se muestra el resultado por consola.

    Pasos realizados:
    1. Conectar a la base de datos y obtener los artículos.
    2. Definir los métodos de ordenamiento disponibles.
    3. Ejecutar cada método de ordenamiento con las diferentes claves.
    4. Medir y mostrar el tiempo que tarda cada método.
    5. Crear gráficos con los tiempos de ejecución de los métodos.
    """

    # Establecer conexión con la base de datos
    conexion = conectar_base_datos()

    # Verificar si la conexión es exitosa
    if conexion is None:
        print("❌ No se pudo conectar a la base de datos.")
        return

    # Crear un cursor para ejecutar la consulta en la base de datos
    cursor_bd = conexion.cursor(dictionary=True)

    # Ejecutar la consulta SQL para obtener todos los artículos
    cursor_bd.execute("SELECT id, nombreBD, authors, publication_date, title, link FROM articles")

    # Obtener todos los artículos
    articulos = cursor_bd.fetchall()

    # Cerrar el cursor y la conexión con la base de datos
    cursor_bd.close()
    conexion.close()

    # Verificar si se han obtenido artículos
    if not articulos:
        print("⚠️ No hay artículos almacenados en la base de datos.")
        return

    # Definir los métodos de ordenamiento disponibles en un diccionario
    metodos_ordenamiento = {
        "TimSort": timsort,
        "Comb Sort": comb_sort,
        "Selection Sort": selection_sort,
        "Tree Sort": tree_sort,
        "Pigeonhole Sort": pigeonhole_sort,
        "Bucket Sort": bucket_sort,
        "QuickSort": quicksort,
        "HeapSort": heapsort,
        "Bitonic Sort": bitonic_sort,
        "Gnome Sort": gnome_sort,
        "Binary Insertion Sort": binary_insertion_sort,
        "Radix Sort": radix_sort
    }

    # Lista de claves por las cuales se quiere ordenar los artículos
    claves = ["title", "publication_date", "nombreBD", "authors", "id", "link"]

    # Diccionario para almacenar los tiempos de ejecución de cada método por clave
    tiempos_metodos_por_clave = {clave: [] for clave in claves}
    fallos_por_clave = {clave: [] for clave in claves}  # Almacena los fallos por clave

    # Lista para almacenar las figuras
    figuras = []

    # Recorrer todas las claves para ordenar los artículos por cada una
    for clave in claves:
        print(f"\n🔹 Ordenando por: {clave}")

        # Recorrer todos los métodos de ordenamiento definidos
        for nombre_metodo, metodo in metodos_ordenamiento.items():
            try:
                # Medir el tiempo de ejecución del método de ordenamiento
                tiempo_inicio = time.time()

                # Ejecutar el método de ordenamiento correspondiente
                articulos_ordenados = metodo(articulos, clave)

                # Calcular el tiempo que ha tardado en ordenar y convertir a milisegundos
                tiempo_transcurrido = (time.time() - tiempo_inicio) * 1000

                # Guardar el tiempo de ejecución con el nombre del método y el tiempo
                tiempos_metodos_por_clave[clave].append((f"{nombre_metodo} ({tiempo_transcurrido:.2f} ms)", tiempo_transcurrido))

                # Mostrar el tiempo de ejecución en consola en milisegundos con 2 decimales
                print(f"✅ {nombre_metodo} completado en {tiempo_transcurrido:.2f} milisegundos.")
            except Exception as e:
                # En caso de error, registrar el fallo con su razón
                fallos_por_clave[clave].append((nombre_metodo, str(e)))
                print(f"❌ Error con el método {nombre_metodo} al ordenar por {clave}: {str(e)}")
                continue  # Continúa con el siguiente método de ordenamiento

        # Almacenar los fallos para la clave actual
        if fallos_por_clave[clave]:
            texto_fallidos = f"Métodos que no funcionaron al ordenar por '{clave}':\n\n"
            for metodo, razon in fallos_por_clave[clave]:
                texto_fallidos += f"• {metodo} - Razón: {razon}\n"  # Usamos '•' en lugar de 🔹

            # Crear la figura para los fallos y almacenarla en la lista
            fig, ax = plt.subplots(figsize=(11, 6)) #1100 x 600
            ax.text(0.1, 0.9, texto_fallidos, fontsize=12, wrap=True, ha='left', va='top', color='black')
            ax.axis('off')  # Ocultar los ejes
            ax.set_title(f"Métodos de Ordenamiento que no Funcionaron por la clave '{clave}'")
            figuras.append(fig)  # Agregar la figura a la lista

    # Crear gráficos de barras con los tiempos de ejecución
    for clave, tiempos in tiempos_metodos_por_clave.items():
        # Extraer los nombres de los métodos con sus tiempos y los tiempos
        metodos = [metodo for metodo, _ in tiempos]
        tiempos_values = [tiempo for _, tiempo in tiempos]

        # Crear la gráfica de barras 2000 x 600
        fig, ax = plt.subplots(figsize=(20, 6))
        ax.barh(metodos, tiempos_values, color='skyblue')
        ax.set_xlabel("Tiempo de ejecución (milisegundos)")
        ax.set_title(f"Tiempo de los métodos de ordenamiento según la clave '{clave}'")
        figuras.append(fig)  # Agregar la figura a la lista

    # Mostrar todas las figuras al final
    plt.show()

def timsort(lista, clave):
    """
    Implementación manual de TimSort.

    TimSort combina los algoritmos MergeSort e InsertionSort para ofrecer un rendimiento óptimo
    tanto en listas grandes como pequeñas. Esta implementación es completamente manual, sin el uso
    de funciones integradas como sorted().

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
                 Puede ser cualquier atributo de los elementos de la lista (por ejemplo, 'title', 'authors', etc.).

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """

    # Paso 1: Implementar el algoritmo de Insertion Sort
    def insertion_sort(sublista, clave):
        for i in range(1, len(sublista)):
            elemento_actual = sublista[i]
            j = i - 1
            # Desplazar elementos que son mayores que el actual
            while j >= 0 and sublista[j][clave] > elemento_actual[clave]:
                sublista[j + 1] = sublista[j]
                j -= 1
            sublista[j + 1] = elemento_actual
        return sublista

    # Paso 2: Implementar el algoritmo de Merge Sort
    def merge_sort(sublista, clave):
        if len(sublista) <= 1:
            return sublista
        medio = len(sublista) // 2
        izquierda = merge_sort(sublista[:medio], clave)
        derecha = merge_sort(sublista[medio:], clave)
        return merge(izquierda, derecha, clave)

    # Paso 3: Fusionar las dos sublistas ordenadas
    def merge(izquierda, derecha, clave):
        result = []
        i = j = 0
        # Comparar los elementos y combinarlos en orden
        while i < len(izquierda) and j < len(derecha):
            if izquierda[i][clave] <= derecha[j][clave]:
                result.append(izquierda[i])
                i += 1
            else:
                result.append(derecha[j])
                j += 1
        # Agregar los elementos restantes
        result.extend(izquierda[i:])
        result.extend(derecha[j:])
        return result

    # Paso 4: Dividir la lista en "run" (sublistas pequeñas)
    min_run = 32  # Tamaño mínimo de la sublista para aplicar Insertion Sort
    for i in range(0, len(lista), min_run):
        lista[i:i + min_run] = insertion_sort(lista[i:i + min_run], clave)

    # Paso 5: Combinar las sublistas ordenadas usando Merge Sort
    lista = merge_sort(lista, clave)

    return lista

def comb_sort(lista, clave):
    """
    Implementación manual de Comb Sort.

    Comb Sort es una mejora del algoritmo Bubble Sort, que reduce el número de comparaciones
    y movimientos al utilizar un "factor de reducción" (gap). El gap comienza siendo grande
    y se va reduciendo a medida que el algoritmo avanza.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
                 Puede ser cualquier atributo de los elementos de la lista (por ejemplo, 'title', 'authors', etc.).

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """

    # Paso 1: Inicializar el "gap" y el factor de reducción
    gap = len(lista)
    factor_reduccion = 1.3  # Factor de reducción recomendado para el gap

    # Paso 2: Iterar hasta que el gap sea menor que 1
    while gap > 1:
        # Reducir el gap
        gap = int(gap / factor_reduccion)

        # Iterar sobre la lista para comparar elementos a una distancia igual al gap
        for i in range(len(lista) - gap):
            # Comparar los elementos a distancia 'gap' y hacer el intercambio si es necesario
            if lista[i][clave] > lista[i + gap][clave]:
                # Intercambiar los elementos
                lista[i], lista[i + gap] = lista[i + gap], lista[i]

    # Paso 3: Aplicar una última pasada para asegurar que la lista esté completamente ordenada
    for i in range(1, len(lista)):
        if lista[i - 1][clave] > lista[i][clave]:
            lista[i - 1], lista[i] = lista[i], lista[i - 1]

    return lista

def selection_sort(lista, clave):
    """
    Implementación manual de Selection Sort.

    Selection Sort es un algoritmo de ordenación basado en la selección del elemento más pequeño
    de la lista y su intercambio con el primer elemento no ordenado.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
                 Puede ser cualquier atributo de los elementos de la lista (por ejemplo, 'title', 'authors', etc.).

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """

    # Paso 1: Iterar sobre la lista de elementos
    for i in range(len(lista)):
        # Paso 2: Suponer que el elemento actual es el más pequeño
        indice_minimo = i

        # Paso 3: Buscar el elemento más pequeño en el resto de la lista
        for j in range(i + 1, len(lista)):
            if lista[j][clave] < lista[indice_minimo][clave]:
                indice_minimo = j

        # Paso 4: Intercambiar el elemento actual con el más pequeño encontrado
        if indice_minimo != i:
            lista[i], lista[indice_minimo] = lista[indice_minimo], lista[i]

    return lista


#tree sort
class Nodo:
    """
    Clase que representa un nodo en un árbol binario de búsqueda.
    Cada nodo tiene un valor y referencias a su hijo izquierdo y derecho.
    """

    def __init__(self, valor):
        self.valor = valor  # El valor del nodo, basado en la clave de ordenación
        self.izquierda = None  # Hijo izquierdo
        self.derecha = None  # Hijo derecho
class ArbolBinarioBusqueda:
    """
    Clase que representa un árbol binario de búsqueda.
    Contiene métodos para insertar elementos y hacer un recorrido en orden.
    """

    def __init__(self):
        self.raiz = None  # La raíz del árbol es inicialmente nula

    def insertar(self, valor):
        """
        Inserta un nuevo valor en el árbol binario de búsqueda.
        """
        if self.raiz is None:
            self.raiz = Nodo(valor)
        else:
            self._insertar_en_nodo(self.raiz, valor)

    def _insertar_en_nodo(self, nodo, valor):
        """
        Método auxiliar recursivo para insertar en el nodo adecuado.
        """
        if valor < nodo.valor:
            if nodo.izquierda is None:
                nodo.izquierda = Nodo(valor)
            else:
                self._insertar_en_nodo(nodo.izquierda, valor)
        else:
            if nodo.derecha is None:
                nodo.derecha = Nodo(valor)
            else:
                self._insertar_en_nodo(nodo.derecha, valor)

    def recorrido_en_orden(self):
        """
        Realiza un recorrido en orden del árbol binario de búsqueda.
        Devuelve una lista con los valores ordenados.
        """
        resultado = []
        self._recorrido_en_orden(self.raiz, resultado)
        return resultado

    def _recorrido_en_orden(self, nodo, resultado):
        """
        Método auxiliar recursivo para hacer el recorrido en orden.
        """
        if nodo:
            self._recorrido_en_orden(nodo.izquierda, resultado)  # Primero recorremos la sub-árbol izquierdo
            resultado.append(nodo.valor)  # Luego procesamos el valor del nodo
            self._recorrido_en_orden(nodo.derecha, resultado)  # Finalmente, recorremos la sub-árbol derecho
def tree_sort(lista, clave):
    """
    Implementación manual de Tree Sort.

    Tree Sort construye un árbol binario de búsqueda y luego realiza un recorrido en orden para ordenar los elementos.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    arbol = ArbolBinarioBusqueda()

    # Insertamos los valores de la lista en el árbol
    for elemento in lista:
        arbol.insertar(elemento[clave])

    # Obtenemos los valores ordenados mediante un recorrido en orden
    lista_ordenada = arbol.recorrido_en_orden()

    # Creamos una nueva lista con los elementos ordenados por la clave
    lista_resultado = []
    for valor in lista_ordenada:
        for item in lista:
            if item[clave] == valor:
                lista_resultado.append(item)
                break

    return lista_resultado


def pigeonhole_sort(lista, clave):
    """
    Implementación de Pigeonhole Sort de manera manual.

    Pigeonhole Sort distribuye los elementos en "agujeros" (pigeonholes) basados en el valor del elemento.
    Luego recoge los elementos de los agujeros para colocarlos en orden.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """

    if not lista:
        return lista  # Si la lista está vacía, retornamos la lista vacía

    # Determinamos el rango de los valores
    minimo = min(lista, key=lambda x: x[clave])[clave]
    maximo = max(lista, key=lambda x: x[clave])[clave]

    # Número de agujeros (rangos de valores posibles)
    rango = maximo - minimo + 1

    # Crear los agujeros (vacíos al principio)
    agujeros = [[] for _ in range(rango)]

    # Distribuir los elementos en los agujeros según su valor
    for elemento in lista:
        indice = elemento[clave] - minimo
        agujeros[indice].append(elemento)

    # Recoger los elementos de los agujeros en orden
    lista_ordenada = []
    for agujero in agujeros:
        lista_ordenada.extend(agujero)

    return lista_ordenada

#bucket sort
def bucket_sort(lista, clave):
    """
    Implementación de Bucket Sort de manera manual.

    Bucket Sort distribuye los elementos en cubos (buckets) y luego los ordena por separado.
    Los cubos se ordenan utilizando un algoritmo de ordenación simple (como Insertion Sort),
    y finalmente los cubos ordenados se concatenan para formar la lista ordenada.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """

    if not lista:
        return lista  # Si la lista está vacía, retornamos la lista vacía

    # Determinamos el valor mínimo y máximo en la lista
    minimo = min(lista, key=lambda x: x[clave])[clave]
    maximo = max(lista, key=lambda x: x[clave])[clave]

    # Creamos los cubos (buckets)
    numero_de_buckets = len(lista)
    rango = maximo - minimo + 1
    tamano_bucket = rango / numero_de_buckets

    # Inicializamos los cubos vacíos
    cubos = [[] for _ in range(numero_de_buckets)]

    # Distribuir los elementos en los cubos
    for elemento in lista:
        indice = int((elemento[clave] - minimo) / tamano_bucket)
        if indice == numero_de_buckets:  # Para el valor máximo, debe ir en el último cubo
            indice -= 1
        cubos[indice].append(elemento)

    # Ordenar los cubos individualmente
    for i in range(numero_de_buckets):
        cubos[i] = insertion_sort(cubos[i], clave)

    # Concatenar los cubos ordenados
    lista_ordenada = []
    for cubo in cubos:
        lista_ordenada.extend(cubo)

    return lista_ordenada
def insertion_sort(lista, clave):
    """
    Implementación de Insertion Sort de manera manual.

    Insertion Sort es un algoritmo de ordenación simple que construye la lista ordenada
    al insertar elementos en su lugar correcto uno por uno.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una lista ordenada según la clave especificada.
    """
    for i in range(1, len(lista)):
        clave_elemento = lista[i]
        j = i - 1
        while j >= 0 and clave_elemento[clave] < lista[j][clave]:
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = clave_elemento
    return lista


def quicksort(lista, clave):
    """
    Implementación de QuickSort de manera manual.

    QuickSort es un algoritmo de ordenación que utiliza el enfoque de divide y vencerás.
    Selecciona un elemento como pivote, divide la lista en dos sublistas con elementos menores
    y mayores que el pivote, y luego ordena recursivamente esas sublistas.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    if len(lista) <= 1:
        return lista

    # Elegimos el pivote (en este caso, el primer elemento)
    pivote = lista[0]

    # Sublistas para elementos menores y mayores que el pivote
    menores = []
    mayores = []

    # Particionar los elementos
    for elemento in lista[1:]:
        if elemento[clave] < pivote[clave]:
            menores.append(elemento)
        else:
            mayores.append(elemento)

    # Ordenar recursivamente las sublistas y concatenar el pivote
    return quicksort(menores, clave) + [pivote] + quicksort(mayores, clave)

#heap sort
def heapify(lista, n, i, clave):
    """
    Función que convierte una sublista en un max-heap (montículo).

    Parámetros:
    lista (list): Lista de elementos a organizar como un heap.
    n (int): El tamaño de la lista.
    i (int): El índice del nodo actual.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    """
    # Inicializar el índice del nodo más grande como el nodo actual
    nodo_mayor = i
    izquierda = 2 * i + 1  # Índice del hijo izquierdo
    derecha = 2 * i + 2  # Índice del hijo derecho

    # Verificar si el hijo izquierdo es mayor que el nodo actual
    if izquierda < n and lista[izquierda][clave] > lista[nodo_mayor][clave]:
        nodo_mayor = izquierda

    # Verificar si el hijo derecho es mayor que el nodo actual
    if derecha < n and lista[derecha][clave] > lista[nodo_mayor][clave]:
        nodo_mayor = derecha

    # Si el nodo más grande no es el nodo actual, intercambiamos y aplicamos heapify recursivo
    if nodo_mayor != i:
        lista[i], lista[nodo_mayor] = lista[nodo_mayor], lista[i]
        heapify(lista, n, nodo_mayor, clave)
def heapsort(lista, clave):
    """
    Implementación de HeapSort de manera manual.

    HeapSort convierte la lista en un heap (montículo), luego intercambia el primer
    elemento del heap con el último y reduce el tamaño del heap. Repite el proceso
    hasta que la lista esté ordenada.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    n = len(lista)

    # Construir el heap (montículo) de manera descendente
    for i in range(n // 2 - 1, -1, -1):
        heapify(lista, n, i, clave)

    # Extraer los elementos del heap uno por uno
    for i in range(n - 1, 0, -1):
        # Intercambiar el primer elemento (el mayor) con el último
        lista[i], lista[0] = lista[0], lista[i]

        # Aplicar heapify en el resto de la lista
        heapify(lista, i, 0, clave)

    return lista

#bitonic sort
def comparar_e_intercambiar(lista, i, j, direccion, clave):
    """
    Compara los elementos en las posiciones i y j de la lista y los intercambia
    si están en el orden incorrecto según la dirección indicada.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    i (int): Índice del primer elemento a comparar.
    j (int): Índice del segundo elemento a comparar.
    direccion (bool): Si es True, se ordena de manera ascendente, si es False, descendente.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    """
    if (direccion and lista[i][clave] > lista[j][clave]) or (not direccion and lista[i][clave] < lista[j][clave]):
        lista[i], lista[j] = lista[j], lista[i]
def bitonic_merge(lista, lo, n, direccion, clave):
    """
    Función recursiva para mezclar una secuencia bitónica.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    lo (int): El índice inicial de la secuencia bitónica.
    n (int): El tamaño de la secuencia bitónica.
    direccion (bool): Si es True, se ordena de manera ascendente, si es False, descendente.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    """
    if n > 1:
        k = n // 2
        for i in range(lo, lo + k):
            comparar_e_intercambiar(lista, i, i + k, direccion, clave)
        bitonic_merge(lista, lo, k, direccion, clave)
        bitonic_merge(lista, lo + k, k, direccion, clave)
def bitonic_sort_recursivo(lista, lo, n, direccion, clave):
    """
    Función recursiva que ordena una secuencia bitónica dividiéndola en dos partes,
    ordenando cada una de ellas y luego combinándolas utilizando bitonic_merge.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    lo (int): El índice inicial de la secuencia bitónica.
    n (int): El tamaño de la secuencia bitónica.
    direccion (bool): Si es True, se ordena de manera ascendente, si es False, descendente.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    """
    if n > 1:
        k = n // 2
        bitonic_sort_recursivo(lista, lo, k, True, clave)  # Ordena de forma ascendente
        bitonic_sort_recursivo(lista, lo + k, k, False, clave)  # Ordena de forma descendente
        bitonic_merge(lista, lo, n, direccion, clave)
def bitonic_sort(lista, clave):
    """
    Implementación de BitonicSort de manera manual.

    BitonicSort ordena una lista dividiéndola recursivamente en secuencias bitónicas,
    luego las mezcla utilizando la función bitonic_merge para obtener la lista ordenada.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    bitonic_sort_recursivo(lista, 0, len(lista), True, clave)
    return lista


def gnome_sort(lista, clave):
    """
    Implementación manual de GnomeSort.

    GnomeSort es un algoritmo de ordenación basado en la idea de un "gnomo" que recorre
    la lista de izquierda a derecha. Si encuentra un par de elementos en el orden incorrecto,
    los intercambia y retrocede una posición. Si no, avanza a la siguiente posición.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    indice = 0
    while indice < len(lista):
        if indice == 0:
            indice += 1
        if lista[indice][clave] >= lista[indice - 1][clave]:
            indice += 1
        else:
            # Intercambio los elementos si están en orden incorrecto
            lista[indice], lista[indice - 1] = lista[indice - 1], lista[indice]
            indice -= 1
    return lista

#binary search
def busqueda_binaria(lista, clave, inicio, fin):
    """
    Realiza una búsqueda binaria para encontrar la posición donde debe insertarse el elemento.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    inicio (int): El índice inicial para la búsqueda.
    fin (int): El índice final para la búsqueda.

    Retorna:
    int: El índice donde debe insertarse el elemento.
    """
    while inicio < fin:
        medio = (inicio + fin) // 2
        if lista[medio][clave] < lista[inicio][clave]:
            fin = medio
        else:
            inicio = medio + 1
    return inicio
def binary_insertion_sort(lista, clave):
    """
    Implementación manual de Binary Insertion Sort.

    Binary Insertion Sort mejora el Insertion Sort usando búsqueda binaria para encontrar
    la posición de inserción de un elemento. A pesar de mejorar las comparaciones, la complejidad sigue siendo O(n^2).

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    for i in range(1, len(lista)):
        elemento_actual = lista[i]
        # Buscar la posición de inserción usando búsqueda binaria
        posicion = busqueda_binaria(lista, clave, 0, i)
        # Mover los elementos mayores a la derecha
        lista[posicion + 1:i + 1] = lista[posicion:i]
        # Insertar el elemento en la posición encontrada
        lista[posicion] = elemento_actual
    return lista

#radix
def obtener_maximo(lista, clave):
    """
    Obtiene el valor máximo de la lista según la clave para determinar el número de dígitos.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    int: El valor máximo encontrado en la lista.
    """
    maximo = lista[0][clave]
    for elemento in lista:
        if elemento[clave] > maximo:
            maximo = elemento[clave]
    return maximo
def contar_por_digito(lista, clave, exp):
    """
    Realiza una ordenación de los elementos según el dígito en la posición exp.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.
    exp (int): El exponente que indica el dígito a ordenar.

    Retorna:
    list: Una lista ordenada por el dígito especificado.
    """
    conteo = [0] * 10  # Para contar la cantidad de veces que aparece cada dígito (0-9)
    salida = [None] * len(lista)

    for elemento in lista:
        indice = (elemento[clave] // exp) % 10
        conteo[indice] += 1

    for i in range(1, 10):
        conteo[i] += conteo[i - 1]

    for i in range(len(lista) - 1, -1, -1):
        elemento = lista[i]
        indice = (elemento[clave] // exp) % 10
        salida[conteo[indice] - 1] = elemento
        conteo[indice] -= 1

    return salida
def radix_sort(lista, clave):
    """
    Implementación manual de Radix Sort.

    Radix Sort ordena los elementos por sus dígitos, comenzando desde el menos significativo.
    La lista se ordena de acuerdo con los valores de la clave especificada.

    Parámetros:
    lista (list): Lista de elementos a ordenar.
    clave (str): La clave sobre la cual se ordenarán los elementos de la lista.

    Retorna:
    list: Una nueva lista ordenada según la clave especificada.
    """
    maximo = obtener_maximo(lista, clave)
    exp = 1
    while maximo // exp > 0:
        lista = contar_por_digito(lista, clave, exp)
        exp *= 10
    return lista
#fin metodos ordenamiento

def iniciarApp():
    # 2️⃣ Crear las tablas necesarias en la base de datos si no existen
    crear_tablas()

    # 3️⃣ Obtener artículos desde la API de Scopus y almacenarlos en la base de datos
    obtener_articulos_scopus()

    # 4️⃣ Listar todos los artículos almacenados en la base de datos
    listar_tabla("articulos")

    # 5️⃣ Listar todos los artículos que han sido detectados como repetidos
    listar_tabla("articulos_repetidos")

    # ejecucion diferentes metodos de ordenamiento
    ejecutar_todos_los_metodos()

    # metodo para ordenar por criterio
    # 1️⃣ Ordenar por fecha de publicación (más recientes primero) [DEFAULT]
    listar_articulos_ordenados("fecha_desc")

    # 2️⃣ Ordenar por fecha de publicación (más antiguos primero)
    listar_articulos_ordenados("fecha_asc")

    # 3️⃣ Ordenar por título en orden alfabético (A-Z)
    listar_articulos_ordenados("titulo_asc")

    # 4️⃣ Ordenar por título en orden alfabético inverso (Z-A)
    listar_articulos_ordenados("titulo_desc")

    # 5️⃣ Ordenar por nombre de autor en orden alfabético (A-Z)
    listar_articulos_ordenados("autor_asc")

    # 6️⃣ Ordenar por nombre de autor en orden alfabético inverso (Z-A)
    listar_articulos_ordenados("autor_desc")

    # 7️⃣ Ordenar por nombre de la base de datos de origen
    listar_articulos_ordenados("nombre_base_datos")

#main
iniciarApp()



