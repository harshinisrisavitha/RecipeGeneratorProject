def get_connection():
    import mysql.connector
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="recipe_generator"
    )
