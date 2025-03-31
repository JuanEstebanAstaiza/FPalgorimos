import redis
import json

class RedisDatabase:
    def __init__(self, host='localhost', port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db)

    def store_article(self, article_id, article_content):
        """
        Almacena el artículo completo en Redis.
        :param article_id: ID único del artículo (usado como clave)
        :param article_content: Contenido completo del artículo (puede ser texto o JSON)
        """
        # Se almacena como string; si article_content es un diccionario se convierte a JSON
        if isinstance(article_content, dict):
            article_content = json.dumps(article_content)
        self.r.set(article_id, article_content)

    def get_article(self, article_id):
        """
        Recupera el artículo almacenado en Redis mediante su clave.
        """
        content = self.r.get(article_id)
        if content:
            return content.decode('utf-8')
        return None