import logging
import re
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

get_card_value_routes = Blueprint("get_card_value", __name__)


def update_progress(step, percent):
    requests.post("http://127.0.0.1:5000/progress", json={"step": step, "percent": percent})


@get_card_value_routes.route("/get_card_value", methods=["POST"])
def get_card_value_routesget_card_value():
    data = request.json
    show_browser = data.get("show_browser", False)
    pokemon_name = data.get("pokemon_name")
    card_number = data.get("card_number")

    logging.info(f"Requête reçue : pokemon_name={pokemon_name}, card_number={card_number}")
    update_progress(f"Analyse des paramètres : {pokemon_name}", 10)

    if not pokemon_name or not card_number:
        logging.warning("Entrée invalide : Nom ou numéro manquant.")
        return jsonify({"error": "Invalid input"}), 400

    search_query = f"{pokemon_name} {card_number}"
    logging.info(f"Construction de la requête : {search_query}")

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
        update_progress("Démarrage du navigateur", 15)
        driver = webdriver.Chrome(service=service, options=options)
        if show_browser:
            driver.maximize_window()

        ebay_url = f"https://www.ebay.fr/sch/i.html?_nkw={search_query.replace(' ', '+')}"
        logging.info(f"Navigation vers URL : {ebay_url}")
        update_progress("Ouverture de la page eBay", 20)
        driver.get(ebay_url)

        update_progress("Chargement de la page eBay", 20)
        page_ok = False
        attempts_load = 0
        while attempts_load < 5:
            try:
                logging.info("Vérification de la page eBay")
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.srp-results")))
                logging.info("Page eBay chargée correctement")
                page_ok = True
                break
            except Exception as e:
                logging.warning(f"Tentative {attempts_load}: la page eBay semble incorrecte : {e}")
                driver.refresh()
                time.sleep(2)
            attempts_load += 1

        if not page_ok:
            logging.error("Impossible de charger correctement la page eBay après 5 tentatives.")
            update_progress("Échec chargement eBay", 25)
            return jsonify({"error": "eBay page load error"}), 500

        attempts = 0
        while attempts < 10:
            try:
                logging.info("Tentative d'accepter les cookies")
                update_progress("Gestion des cookies eBay", 30)
                accept_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "gdpr-banner-accept")))
                driver.execute_script("arguments[0].scrollIntoView(true);", accept_button)
                driver.execute_script("arguments[0].click();", accept_button)

                banner = driver.find_elements(By.ID, "gdpr-banner")
                if not banner:
                    logging.info("Cookies acceptés et bannière disparue")
                    break
            except Exception as e:
                logging.warning(f"Tentative {attempts}: échec du clic pour les cookies : {e}")
            attempts += 1

        attempts_buy_now = 0
        while attempts_buy_now < 10:
            try:
                logging.info("Application du filtre : 'Achat immédiat'")
                update_progress("Filtrage Achat immédiat", 40)
                buy_it_now_radio = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.radio__control[type='radio'][data-value='Achat immédiat']")))
                driver.execute_script("arguments[0].scrollIntoView(true);", buy_it_now_radio)
                driver.execute_script("arguments[0].click();", buy_it_now_radio)

                if "LH_BIN=1" in driver.current_url:
                    logging.info("Le filtre 'Achat immédiat' est bien appliqué")
                    break
            except Exception as e:
                logging.warning(f"Tentative {attempts_buy_now}: Impossible d'appliquer 'Achat immédiat' : {e}")
            attempts_buy_now += 1

        attempts_sold = 0
        while attempts_sold < 10:
            try:
                logging.info("Application du filtre : 'Ventes terminées'")
                update_progress("Filtrage Ventes terminées", 50)
                completed_listings_checkbox = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.checkbox__control[type='checkbox'][aria-label='Ventes terminées']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", completed_listings_checkbox)
                driver.execute_script("arguments[0].click();", completed_listings_checkbox)

                if "LH_Complete=1" in driver.current_url:
                    logging.info("Le filtre 'Ventes terminées' est bien appliqué")
                    break
            except Exception as e:
                logging.warning(f"Tentative {attempts_sold}: Impossible d'appliquer 'Ventes terminées' : {e}")
            attempts_sold += 1

        attempts_graded = 0
        while attempts_graded < 3:
            try:
                logging.info("Tentative d'appliquer le filtre 'Gradée=Non'")
                update_progress("Filtrage Cartes non Gradées", 60)
                graded_parent_li = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//li[@class='x-refine__main__list' and contains(., 'Gradée')]")))
                expanded = graded_parent_li.get_attribute("data-expanded")
                if expanded == "false":
                    heading = graded_parent_li.find_element(By.CSS_SELECTOR, "div.x-refine__item__title-container")
                    driver.execute_script("arguments[0].scrollIntoView(true);", heading)
                    heading.click()
                    time.sleep(1)
                graded_value_li = graded_parent_li.find_element(By.CSS_SELECTOR, "li.x-refine__main__list--value[name='Grad%25C3%25A9e']")
                non_link = graded_value_li.find_element(By.XPATH, ".//span[@class='cbx x-refine__multi-select-cbx' and contains(text(), 'Non')]")
                driver.execute_script("arguments[0].scrollIntoView(true);", non_link)
                non_link.click()
                time.sleep(2)
                if "Grad%C3%A9e=Non" in driver.current_url or "Grad%25C3%25A9e=Non" in driver.current_url:
                    logging.info("Le filtre 'Gradée=Non' est bien appliqué")
                else:
                    logging.warning("Le filtre 'Gradée=Non' ne semble pas appliqué, on réessaie")
                break
            except Exception as e:
                logging.warning(f"Tentative {attempts_graded}: impossible d'appliquer 'Gradée=Non' : {e}")
            attempts_graded += 1

        logging.info("Récupération des prix des annonces")
        update_progress("Lecture des annonces eBay", 70)
        time.sleep(1)
        prices = []

        ul_selector = driver.find_elements(By.CSS_SELECTOR, "ul.srp-results")
        if ul_selector:
            li_elements = ul_selector[0].find_elements(By.TAG_NAME, "li")
        else:
            li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.srp-results li")

        for li in li_elements:
            try:
                rewrite_spans = li.find_elements(By.CSS_SELECTOR, "span")
                found_rewrite_block = any("Résultats correspondant à moins de mots" in s.text for s in rewrite_spans)
                if found_rewrite_block:
                    logging.info("Bloc 'Résultats correspondant à moins de mots' détecté. On s'arrête ici.")
                    break

                title_element = li.find_element(By.CSS_SELECTOR, "div.s-item__title > span")
                title_text = title_element.text.lower()
                tokens = re.split(r"[^a-zA-Z0-9]+", title_text)
                if "et" in tokens:
                    logging.info(f"Annonce ignorée (contient 'et') : {title_text}")
                    continue

                price_element = li.find_element(By.CSS_SELECTOR, "span.s-item__price")
                price_text = price_element.text
                price_value = float(price_text.replace("EUR", "").replace(",", ".").strip())
                prices.append(price_value)
                logging.info(f"Prix trouvé : {price_value}")
            except Exception:
                logging.warning("Impossible de récupérer le prix pour une annonce")

        update_progress("Calcul de la moyenne", 90)
        if prices:
            average_price = sum(prices) / len(prices)
            logging.info(f"Moyenne des prix : {average_price:.2f}")
            update_progress("Affichage des résultats", 100)
            return jsonify(
                {
                    "average_price": f"{average_price:.2f}",
                    "prices": prices,
                    "message": "Card values fetched successfully!",
                }
            )
        else:
            logging.warning("Aucun prix valide trouvé")
            update_progress("Aucun prix trouvé", 95)
            update_progress("Affichage des résultats", 100)
            return jsonify({"error": "No prices found"}), 404

    except Exception as e:
        logging.error(f"Erreur dans le processus : {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            logging.info("Fermeture de Selenium WebDriver")
            driver.quit()
