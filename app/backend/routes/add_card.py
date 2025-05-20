import logging
import sqlite3
import time

import requests
from flask import Blueprint, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(),
    ],
)

add_card_routes = Blueprint("add_card", __name__)


def update_progress(step, percent):
    requests.post("http://127.0.0.1:5000/progress", json={"step": step, "percent": percent})


@add_card_routes.route("/add_card", methods=["POST"])
def add_card():
    data = request.json
    show_browser = data.get("show_browser", False)
    pokemon_name = data.get("pokemon_name")
    card_number = data.get("card_number")

    update_progress("initialisation du navigateur", 0)

    if not pokemon_name or not card_number:
        return jsonify({"error": "Invalid input"}), 400

    search_query = f"{pokemon_name} {card_number}"
    search_url = f"https://limitlesstcg.com/cards/fr?q={pokemon_name}+{card_number}"

    options = Options()
    if not show_browser:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")

    service = Service("/usr/local/bin/chromedriver")
    driver = None

    try:
        logging.info("Démarrage de Selenium WebDriver")
        update_progress("Démarrage du WebDriver", 2)
        driver = webdriver.Chrome(service=service, options=options)
        if show_browser:
            driver.maximize_window()

        logging.info(f"Ouverture de l'URL : {search_url}")
        update_progress("Ouverture de Limitless TCG", 5)
        driver.get(search_url)

        page_ok = False
        attempts_load = 0
        while attempts_load < 5:
            try:
                logging.info("Vérification du chargement de la page")
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logging.info("Page Limitless TCG chargée correctement")
                page_ok = True
                break
            except Exception as e:
                logging.warning(f"Tentative {attempts_load}: la page semble incorrecte : {e}")
                driver.refresh()
                time.sleep(2)
            attempts_load += 1

        if not page_ok:
            logging.error("Impossible de charger la page après 5 tentatives.")
            update_progress("Erreur de chargement de la page", 10)
            return jsonify({"error": "Page load error"}), 500

        try:
            logging.info("Recherche de l'iframe de cookie")
            iframe_cookie = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sp_message_iframe_1140257")))
            driver.switch_to.frame(iframe_cookie)

            logging.info("Recherche de la div#notice dans l'iframe")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "notice")))

            logging.info("Bannière détectée, on tente de cliquer sur le bouton Accept")
            accept_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Accept']")))
            accept_button.click()
            time.sleep(2)

            notice_still = driver.find_elements(By.ID, "notice")
            if notice_still:
                logging.warning("La bannière de cookies est encore visible après clic")
            else:
                logging.info("Cookies acceptés et bannière disparue")

            driver.switch_to.default_content()

        except Exception as e:
            logging.warning(f"Impossible de détecter/cliquer sur la bannière : {e}")
            html_source = driver.execute_script("return document.body.innerHTML")
            logging.info(f"HTML actuel : {html_source}")

        logging.info("Recherche de l'image de la carte")
        attempts_img = 0
        image_url = None
        while attempts_img < 3:
            try:
                card_img = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.card.shadow")))
                image_url = card_img.get_attribute("src")
                if image_url:
                    logging.info(f"Image trouvée : {image_url}")
                    break
            except Exception as e:
                logging.warning(f"Tentative {attempts_img}: impossible de récupérer l'image : {e}")
                time.sleep(1)
            attempts_img += 1

        update_progress("Image trouvée ou placeholder", 10)

        if not image_url:
            logging.warning("Aucune image trouvée, on peut mettre une image par défaut si besoin")
            image_url = "https://via.placeholder.com/200x280?text=Image+Not+Found"

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

        return jsonify({"image_url": image_url, "message": "Card added successfully!"})

    except Exception as e:
        logging.error(f"Erreur dans le processus : {str(e)}")
        update_progress("Erreur inattendue", 10)
        return jsonify({"error": str(e)}), 500

    finally:
        logging.info("Fermeture de Selenium WebDriver")
        driver.quit()
