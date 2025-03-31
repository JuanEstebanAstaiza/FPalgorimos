import mysql.connector
from mysql.connector import errorcode

class MySQLDatabase:
    def __init__(self, host='localhost', user='root', password='', database='bibliometria'):
        try:
            self.cnx = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
            self.cursor = self.cnx.cursor()
            self.create_database(database)
            self.cnx.database = database
            self.create_table()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.cnx = None

    def create_database(self, database):
        try:
            self.cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database} DEFAULT CHARACTER SET 'utf8'")
        except mysql.connector.Error as err:
            print(f"Failed creating database: {err}")
            exit(1)

    def create_table(self):
        create_table_query = (
            "CREATE TABLE IF NOT EXISTS articles ("
            "  id INT PRIMARY KEY, "
            "  article_name VARCHAR(255), "
            "  author_name VARCHAR(255), "
            "  publication_date DATE, "
            "  theme VARCHAR(255), "
            "  category VARCHAR(255)"
            ") ENGINE=InnoDB"
        )
        try:
            self.cursor.execute(create_table_query)
        except mysql.connector.Error as err:
            print(f"Failed creating table: {err}")

    def insert_article(self, article):
        """
        Inserta o actualiza un registro en la tabla articles.
        article: dict con claves: id, article_name, author_name, publication_date, theme, category
        """
        insert_query = (
            "REPLACE INTO articles "
            "(id, article_name, author_name, publication_date, theme, category) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        data = (
            article['id'],
            article['article_name'],
            article['author_name'],
            article['publication_date'],
            article['theme'],
            article['category']
        )
        try:
            self.cursor.execute(insert_query, data)
            self.cnx.commit()
        except mysql.connector.Error as err:
            print(f"Error inserting article: {err}")

    def close(self):
        self.cursor.close()
        self.cnx.close()