from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            search_query TEXT NOT NULL,
            image_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            image_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """
    )
    conn.commit()
    conn.close()


@app.route("/search", methods=["POST"])
def search_card():
    data = request.json
    pokemon_name = data.get("pokemon_name")
    card_number = data.get("card_number")

    if not pokemon_name or not card_number:
        return jsonify({"error": "Invalid input"}), 400

    search_query = f"{pokemon_name} {card_number}"

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.pkmcards.fr/")
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="search-bar"]'))
        )
        search_input.click()

        search_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="search-field"]'))
        )
        search_field.send_keys(search_query)

        suggestions_wrapper = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="suggestions-wrapper"]'))
        )

        first_image = WebDriverWait(suggestions_wrapper, 10).until(
            lambda wrapper: wrapper.find_element(By.TAG_NAME, "img")
        )
        image_url = first_image.get_attribute("src")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO searches (user_id, search_query, image_url)
            VALUES (?, ?, ?)
        """,
            (1, search_query, image_url),
        )
        conn.commit()
        conn.close()

        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()


if __name__ == "__main__":
    init_db()
    print("Démarrage du serveur Flask...")
    app.run(debug=True)
