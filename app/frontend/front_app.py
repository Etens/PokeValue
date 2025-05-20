import base64
import os
import sqlite3
import threading
import time

import pandas as pd
import requests
import streamlit as st
from streamlit_js_eval import streamlit_js_eval


ADD_CARD_API_URL = "http://127.0.0.1:5000/add_card"
GET_CARD_VALUE_API_URL = "http://127.0.0.1:5000/get_card_value"


def get_recent_searches():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT search_query, image_url, price FROM searches ORDER BY id DESC LIMIT 8")
    searches = cursor.fetchall()
    conn.close()
    return searches


def get_collections():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, card_name, card_number, image_url, price FROM collections ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_card_value(pokemon_name, card_number, result_container):
    try:
        response = requests.post(
            GET_CARD_VALUE_API_URL,
            json={"pokemon_name": pokemon_name, "card_number": card_number, "show_browser": show_browser},
        )
        if response.status_code == 200:
            data = response.json()
            result_container["price"] = data.get("average_price", "N/A")
        else:
            result_container["price"] = "N/A"
    except Exception as e:
        result_container["price"] = f"Erreur: {str(e)}"


def render_badge(image_url, price):
    try:
        numeric_price = float(price.replace("€", "").replace(",", ".").strip())
    except ValueError:
        numeric_price = 0.0

    current_dir = os.path.dirname(os.path.abspath(__file__))

    if numeric_price < 20:
        badge_path = os.path.join(current_dir, "resources", "bronze-medal.png")
    elif numeric_price < 100:
        badge_path = os.path.join(current_dir, "resources", "silver-medal.png")
    else:
        badge_path = os.path.join(current_dir, "resources", "gold-medal.png")

    with open(badge_path, "rb") as f:
        badge_bytes = f.read()
    badge_b64 = base64.b64encode(badge_bytes).decode()
    badge_image_url = f"data:image/png;base64,{badge_b64}"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fredoka+One&display=swap');
        .card-container {{
            position: relative;
            display: inline-block;
            width: 100%;
            height: 100%;
            background-color: #262730;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: flex-start;S
        }}
        .badge-img {{
            position: absolute;
            bottom: -4px;
            right: 18px;
            transform: translate(50%, 50%);
            width: 100px;
            height: 100px;
            z-index: 9999;
        }}
        .badge-text {{
            font-family: 'Fredoka One', cursive;
            position: absolute;
            bottom: 11px;
            right: 18px;
            transform: translate(50%, 50%);
            width: 100px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fafafa;
            font-size: 16px;
            z-index: 10000;
        }}
        </style>

        <div class="card-container">
            <img src="{image_url}" style="max-width: 100%;" />
            <img class="badge-img" src="{badge_image_url}" />
            <div class="badge-text">{price}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if "search_result" not in st.session_state:
    st.session_state["search_result"] = {"image_url": None, "price": None, "name": "", "number": ""}

st.title("Évaluateur de cartes Pokémon")

with st.sidebar:
    pokemon_name = st.text_input("Nom du Pokémon")

    col_num_left, col_slash, col_num_right = st.columns([2, 0.5, 2])
    with col_num_left:
        left_part = st.text_input("N° (Gauche)")
    with col_slash:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:18px;'>/</p>", unsafe_allow_html=True)
    with col_num_right:
        right_part = st.text_input("N° (Droite)")

    left_error = False
    right_error = False

    if "already_typed_left" not in st.session_state:
        st.session_state["already_typed_left"] = False
    if "already_typed_right" not in st.session_state:
        st.session_state["already_typed_right"] = False

    if left_part:
        st.session_state["already_typed_left"] = True
    if right_part:
        st.session_state["already_typed_right"] = True

    left_error = False
    right_error = False

    if st.session_state["already_typed_left"] and not left_part:
        st.error("Le champ de gauche ne peut pas être vide.")
        left_error = True
    elif left_part and not left_part.isdigit():
        st.error("Le champ de gauche doit contenir uniquement des chiffres.")
        left_error = True

    if st.session_state["already_typed_right"] and not right_part:
        st.error("Le champ de droite ne peut pas être vide.")
        right_error = True
    elif right_part and not right_part.isdigit():
        st.error("Le champ de droite doit contenir uniquement des chiffres.")
        right_error = True

    right_valid = right_part

    card_number = ""
    if not left_error and not right_error:
        if right_part:
            card_number = f"{left_part}/{right_part}"
        else:
            card_number = left_part
        card_left_number = left_part

    def transform_tg_number(card_number, tg_mode):
        if not tg_mode:
            return card_number
        if "/" in card_number:
            left_side, right_side = card_number.split("/", 1)
            return f"TG{left_side}/TG{right_side}"
        else:
            return f"TG{card_number}"

    promo_mode = st.checkbox("Carte Promo", value=False)
    tg_mode = st.checkbox("Carte Trainer Gallery (TG)", value=False)

    action = st.selectbox(
        "Choisissez une action :",
        [
            "Rechercher une carte",
            "Afficher les recherches récentes",
            "Afficher les collections",
        ],
    )
    show_browser = st.checkbox("Afficher le navigateur pendant la recherche", value=False)


def background_fetch(pokemon_name, card_number, result_container, is_promo, tg_mode):
    final_number = transform_tg_number(card_number, tg_mode)
    final_name = f"{pokemon_name} Promo" if is_promo else pokemon_name
    try:
        response = requests.post(
            GET_CARD_VALUE_API_URL,
            json={"pokemon_name": final_name, "card_number": final_number, "show_browser": show_browser},
        )
        if response.status_code == 200:
            data = response.json()
            result_container["price"] = data.get("average_price", "N/A")
        else:
            result_container["price"] = "N/A"
    except Exception as e:
        result_container["price"] = f"Erreur: {str(e)}"


def track_real_progress(pb, txt):
    while st.session_state["scraping_running"]:
        try:
            resp = requests.get("http://127.0.0.1:5000/progress/state")
            data = resp.json()
            pb.progress(data["percent"])
            txt.text(f"{data['step']} ({data['percent']}%)")
            if data["percent"] >= 100:
                st.session_state["scraping_running"] = False
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1)


if action == "Rechercher une carte":
    if st.button("Rechercher"):
        if pokemon_name and card_number:
            res = {"image_url": None, "price": None}
            card_left_number = str(int(card_left_number))

            def call_scraping():
                r_add = requests.post(
                    ADD_CARD_API_URL,
                    json={"pokemon_name": pokemon_name, "card_number": card_left_number, "show_browser": show_browser},
                )
                if r_add.status_code == 200:
                    d_add = r_add.json()
                    res["image_url"] = d_add["image_url"]
                background_fetch(pokemon_name, card_number, res, promo_mode, tg_mode)

            st.session_state["scraping_running"] = True
            pb = st.progress(0)
            txt = st.empty()

            t_scraping = threading.Thread(target=call_scraping)
            t_scraping.start()

            while t_scraping.is_alive():
                try:
                    resp_prog = requests.get("http://127.0.0.1:5000/progress/state")
                    data_prog = resp_prog.json()
                    pb.progress(data_prog["percent"])
                    txt.text(f"{data_prog['step']} ({data_prog['percent']}%)")
                except requests.RequestException:
                    pass
                time.sleep(1)

            t_scraping.join()

            resp_prog = requests.get("http://127.0.0.1:5000/progress/state")
            final_data = resp_prog.json()
            pb.progress(final_data["percent"])
            txt.text(f"{final_data['step']} {final_data['percent']}%")

            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT id FROM searches ORDER BY id DESC LIMIT 1")
            row_id = c.fetchone()[0]
            c.execute("UPDATE searches SET price=? WHERE id=?", (res["price"], row_id))
            conn.commit()
            conn.close()

            st.session_state["search_result"]["image_url"] = res["image_url"]
            st.session_state["search_result"]["price"] = res["price"]
            st.session_state["search_result"]["name"] = pokemon_name
            st.session_state["search_result"]["number"] = card_number

            st.session_state["search_result"] = {
                "image_url": res["image_url"],
                "price": res["price"],
                "name": pokemon_name,
                "number": card_number,
            }
        else:
            st.error("Veuillez remplir tous les champs (et un numéro valide).")

    if st.session_state["search_result"]["image_url"]:
        render_badge(st.session_state["search_result"]["image_url"], st.session_state["search_result"]["price"])
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("Ajouter à la collection", key="add_from_search"):
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO collections (user_id, card_name, card_number, image_url, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    1,
                    st.session_state["search_result"]["name"],
                    st.session_state["search_result"]["number"],
                    st.session_state["search_result"]["image_url"],
                    st.session_state["search_result"]["price"],
                ),
            )
            conn.commit()
            conn.close()
            st.session_state["search_result"] = {
                "image_url": None,
                "price": None,
                "name": "",
                "number": "",
            }
            st.success("Carte ajoutée dans la collection.")
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            time.sleep(2)
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

elif action == "Afficher les recherches récentes":
    st.subheader("Recherches récentes")
    arr = get_recent_searches()
    if arr:
        cc = st.columns(4)
        for idx, (sq, img, pr) in enumerate(arr):
            with cc[idx % 4]:
                render_badge(img, pr or "N/A")
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                if st.button("Ajouter à la collection", key=f"add_search_{idx}"):
                    splitted = sq.rsplit(" ", 1)
                    if len(splitted) == 2:
                        pname, cnum = splitted
                    else:
                        pname, cnum = (sq, "")
                    conn = sqlite3.connect("database.db")
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO collections (user_id, card_name, card_number, image_url, price)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (1, pname, cnum, img, pr or "N/A"),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Carte ajoutée dans la collection.")
    else:
        st.write("Aucune recherche récente trouvée.")

elif action == "Afficher les collections":
    if "normal_rare_count" not in st.session_state:
        st.session_state["normal_rare_count"] = 0

    st.subheader("Cartes Rares Classiques (1€)")
    col_r_minus, col_r_txt, col_r_plus = st.columns([1, 2, 1])
    with col_r_minus:
        if st.button("–"):
            if st.session_state["normal_rare_count"] > 0:
                st.session_state["normal_rare_count"] -= 1
    with col_r_txt:
        st.markdown(f"<div style='text-align:center;'>**{st.session_state['normal_rare_count']}**</div>", unsafe_allow_html=True)
    with col_r_plus:
        if st.button("+"):
            st.session_state["normal_rare_count"] += 1

    data = get_collections()
    if data:
        df = pd.DataFrame(data, columns=["id", "card_name", "card_number", "image_url", "price"])
        df["numeric_price"] = pd.to_numeric(df["price"].fillna("N/A").str.replace("€", "").str.replace(",", ".").str.strip(), errors="coerce").fillna(0.0)

        base_value = df["numeric_price"].sum()
        total_cards = len(df) + st.session_state["normal_rare_count"]
        total_value = base_value + st.session_state["normal_rare_count"] * 1.0

        st.subheader("Bilan de la collection")
        st.write(f"**Nombre total de cartes** : {total_cards}")
        st.write(f"**Valeur totale** : {total_value:.2f}€")

        st.markdown(
            """
        <style>
        .card-top-text2 {
            font-size: 14px;
            color: #777;
            font-style: italic;
            margin-bottom: 5px;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        filtre = st.text_input("Filtrer par nom ou numéro")
        if filtre:
            df = df[df["card_name"].str.contains(filtre, case=False, na=False) | df["card_number"].str.contains(filtre, case=False, na=False)]

        cards_per_row = 3
        for start_idx in range(0, len(df), cards_per_row):
            subset = df.iloc[start_idx : start_idx + cards_per_row]
            cols = st.columns(len(subset))
            for col_idx, row_data in enumerate(subset.itertuples()):
                with cols[col_idx]:
                    st.markdown(f"<div class='card-top-text2'>{row_data.card_name} – {row_data.card_number}</div>", unsafe_allow_html=True)

                    st.markdown("<div class='card-image'>", unsafe_allow_html=True)
                    render_badge(row_data.image_url, row_data.price or "N/A")
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.button("Supprimer", key=f"del_{row_data.id}"):
                        conn = sqlite3.connect("database.db")
                        cur = conn.cursor()
                        cur.execute("DELETE FROM collections WHERE id=?", (row_data.id,))
                        conn.commit()
                        conn.close()
                        st.success("Carte supprimée de la collection.")
                        time.sleep(1)
                        streamlit_js_eval.js_eval("parent.window.location.reload()")

                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("Aucune collection trouvée.")
