import streamlit as st
import requests
import sqlite3
from PIL import Image
from io import BytesIO

API_URL = "http://127.0.0.1:5000/add_card"


def get_recent_searches():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT search_query, image_url FROM searches ORDER BY id DESC LIMIT 5"
    )
    searches = cursor.fetchall()
    conn.close()
    return searches


def get_collections():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT card_name, card_number, image_url FROM collections ORDER BY id DESC"
    )
    collections = cursor.fetchall()
    conn.close()
    return collections


st.title("Évaluateur de cartes Pokémon")

pokemon_name = st.text_input("Nom du Pokémon")
card_number = st.text_input("Numéro de la carte")

if st.button("Rechercher"):
    if pokemon_name and card_number:
        response = requests.post(
            API_URL, json={"pokemon_name": pokemon_name, "card_number": card_number}
        )
        if response.status_code == 200:
            data = response.json()
            image_url = data["image_url"]
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            st.image(image, caption=f"{pokemon_name} {card_number}")
        else:
            st.error("Erreur lors de la recherche.")
    else:
        st.error("Veuillez remplir tous les champs.")

st.subheader("Recherches récentes")
recent_searches = get_recent_searches()
for search_query, image_url in recent_searches:
    st.write(search_query)
    st.image(image_url, width=100)

st.subheader("Collections")
collections = get_collections()
for card_name, card_number, image_url in collections:
    st.write(f"{card_name} - {card_number}")
    st.image(image_url, width=100)
