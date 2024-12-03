from flask import Blueprint, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

get_card_value_routes = Blueprint("get_card_value", __name__)


@get_card_value_routes.route("/get_card_value", methods=["POST"])
def get_card_value():
    data = request.json
    pokemon_name = data.get("pokemon_name")
    card_number = data.get("card_number")

    if not pokemon_name or not card_number:
        return jsonify({"error": "Invalid input"}), 400

    search_query = f"{pokemon_name} {card_number}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920x1080")

    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        ebay_url = (
            f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}"
        )
        driver.get(ebay_url)

        first_result_price = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".s-item__price"))
        )
        price = first_result_price.text

        return jsonify({"price": price, "message": "Card value fetched successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()
