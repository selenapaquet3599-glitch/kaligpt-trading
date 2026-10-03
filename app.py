
import os
import streamlit as st
import stripe
import mysql.connector
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from google import genai

# 1. Charger les variables d'environnement du fichier .env
load_dotenv()

# 2. Récupérer les configurations et clés secrètes
stripe.api_key = os.getenv("STRIPE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialisation du client Google GenAI
ai_client = None
if GEMINI_API_KEY:
  try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
  except Exception as e:
    print(f"Erreur d'initialisation du client GenAI : {e}")

# Configuration de la connexion MariaDB
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "kaligpt_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mon_mot_de_passe")
DB_NAME = os.getenv("DB_NAME", "kaligpt_trading")

# Configuration de la page Streamlit
st.set_page_config(
    page_title="KaliGPT - Trading, Dark Mode & MariaDB", page_icon="🤖", layout="wide"
)

# --- STYLE CSS PERSONNALISÉ (DARK MODE TRADING) ---
st.markdown(
    """
    <style>
    /* Fond global de l'application */
    .stApp {
        background-color: #0e1117;
        color: #c9d1d9;
    }

    /* Style des conteneurs / cartes */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-color: #30363d !important;
        background-color: #161b22;
        border-radius: 10px;
        padding: 15px;
    }

    /* Boutons principaux */
    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        transition: 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
        box-shadow: 0 0 10px rgba(46, 160, 67, 0.4);
    }

    /* Champs de saisie et formulaires */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
    }

    /* Sidebar élégante */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Métriques */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 KaliGPT - Terminal de Trading Pro")
st.write("Interface unifiée : Marché en direct, RSI, Historique MariaDB, Stripe et IA contextuelle.")


# --- FONCTIONS BASE DE DONNÉES (MARIADB) ---
def get_db_connection():
  try:
    connection = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    return connection
  except Exception:
    return None

def init_db():
  """Crée la table des ordres si elle n'existe pas déjà"""
  conn = get_db_connection()
  if conn:
    try:
      cursor = conn.cursor()
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_type VARCHAR(50),
                    quantity DECIMAL(18,8),
                    price DECIMAL(18,8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
      conn.commit()
      cursor.close()
      conn.close()
    except Exception:
      pass

init_db()

def save_order_to_db(order_type, quantity, price):
  conn = get_db_connection()
  if conn is None:
    st.error("Impossible de se connecter à MariaDB pour enregistrer l'ordre.")
    return False

  try:
    cursor = conn.cursor()
    query = "INSERT INTO orders (order_type, quantity, price) VALUES (%s, %s, %s)"
    cursor.execute(query, (order_type, quantity, price))
    conn.commit()
    cursor.close()
    conn.close()
    return True
  except Exception as e:
    st.error(f"Erreur lors de l'enregistrement de l'ordre dans MariaDB : {e}")
    return False

def get_orders_from_db():
  """Récupère tous les ordres enregistrés dans MariaDB"""
  conn = get_db_connection()
  if conn is None:
    return None

  try:
    query = "SELECT id, order_type AS 'Type', quantity AS 'Quantité', price AS 'Prix (USD)', created_at AS 'Date/Heure' FROM orders ORDER BY created_at DESC"
    df_orders = pd.read_sql(query, conn)
    conn.close()
    return df_orders
  except Exception as e:
    st.error(f"Erreur lors de la récupération des ordres : {e}")
    if conn:
      conn.close()
    return None


# --- FONCTION DE CALCUL DU RSI ---
def calculate_rsi(data, window=14):
  delta = data.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi


# --- 3. SECTION SIDEBAR : ÉTAT DU SYSTÈME ---
with st.sidebar:
  st.header("⚙️ État du Système")
  
  if stripe.api_key:
    st.success("Stripe configuré 🟢")
  else:
    st.error("Stripe manquant (STRIPE_API_KEY) 🔴")

  if GEMINI_API_KEY and ai_client:
    st.success("API Gemini configurée 🟢")
  else:
    st.warning("API Gemini absente ou invalide 🟡")

  db_test = get_db_connection()
  if db_test:
    st.success(f"MariaDB connecté ({DB_NAME}) 🟢")
    db_test.close()
  else:
    st.error("MariaDB non connectable 🔴")


# --- 4. SECTION PASSAGE D'ORDRES & HISTORIQUE MARIADB ---
st.divider()
st.subheader("📝 Passer un Ordre de Trading")

with st.form("order_form"):
  col_o1, col_o2, col_o3 = st.columns(3)
  
  with col_o1:
    order_type = st.selectbox("Type d'ordre", ["Achat (BUY)", "Vente (SELL)"])
  with col_o2:
    quantity = st.number_input("Quantité / Montant", min_value=0.0001, value=1.0, format="%.4f")
  with col_o3:
    price = st.number_input("Prix d'exécution (USD)", min_value=0.01, value=50000.0, format="%.2f")

  submit_order = st.form_submit_button("Exécuter et Enregistrer l'ordre")

  if submit_order:
    success = save_order_to_db(order_type, quantity, price)
    if success:
      st.success("✅ Ordre enregistré avec succès dans MariaDB !")
      st.rerun()

st.markdown("### 📊 Historique des Ordres (MariaDB)")
df_history = get_orders_from_db()
if df_history is not None and not df_history.empty:
  st.dataframe(df_history, use_container_width=True)
else:
  st.info("Aucun ordre enregistré pour le moment.")


# --- 5. SECTION ANALYSE DE MARCHÉ EN DIRECT (RSI) ---
st.divider()
st.subheader("📈 Analyse de Marché en Direct & Indicateur RSI")

col1, col2 = st.columns(2)

with col1:
  crypto_choice = st.selectbox(
      "Actif / Paire", 
      ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"]
  )
with col2:
  rsi_period = st.slider("Période RSI", min_value=5, max_value=30, value=14)
  period_length = st.selectbox("Historique", ["1mo", "3mo", "6mo", "1y"], index=0)

if st.button("Charger les données réelles et calculer le RSI"):
  with st.spinner("Récupération des données du marché en direct..."):
    try:
      df_market = yf.download(crypto_choice, period=period_length, interval="1d", progress=False)
      
      if df_market.empty:
        st.error("Impossible de récupérer les données pour cet actif.")
      else:
        if isinstance(df_market.columns, pd.MultiIndex):
          df_market = df_market.xs('Close', level=0, axis=1)
          if isinstance(df_market, pd.DataFrame):
            close_series = df_market.iloc[:, 0]
          else:
            close_series = df_market
        else:
          close_series = df_market["Close"]

        df_analysis = pd.DataFrame({"Close": close_series})
        df_analysis["RSI"] = calculate_rsi(df_analysis["Close"], window=rsi_period)

        current_rsi = df_analysis["RSI"].iloc[-1]
        current_price = df_analysis["Close"].iloc[-1]

        m_col1, m_col2 = st.columns(2)
        m_col1.metric(label=f"Prix actuel ({crypto_choice})", value=f"{current_price:,.2f} USD")
        m_col2.metric(label=f"RSI Actuel ({rsi_period})", value=f"{current_rsi:.2f}")

        if current_rsi > 70:
          st.warning("⚠ Signal de **Surachat (Overbought)** - Le marché pourrait corriger à la baisse.")
        elif current_rsi < 30:
          st.info("💡 Signal de **Survente (Oversold)** - Potentiel rebond haussier détecté.")
        else:
          st.success("⚖️ Marché en zone neutre.")

        st.line_chart(df_analysis[["Close"]])

    except Exception as e:
      st.error(f"Erreur lors de la récupération des données de marché : {e}")


# --- 6. SECTION PAIEMENT / ABONNEMENT STRIPE ---
st.divider()
st.subheader("💳 Espace Abonnement / Premium")

if st.button("Payer l'accès Premium (29,00 €)"):
  if not stripe.api_key:
    st.error("La clé API Stripe est introuvable dans votre fichier .env.")
  else:
    try:
      checkout_session = stripe.checkout.Session.create(
          payment_method_types=["card"],
          line_items=[
              {
                  "price_data": {
                      "currency": "eur",
                      "product_data": {
                          "name": "Accès Premium KaliGPT Trading",
                      },
                      "unit_amount": 2900,
                  },
                  "quantity": 1,
              }
          ],
          mode="payment",
          success_url="http://localhost:8501/?success=true",
          cancel_url="http://localhost:8501/?canceled=true",
      )

      st.markdown(
          f"""
            <meta http-equiv="refresh" content="0;url={checkout_session.url}">
            """,
          unsafe_allow_html=True,
      )
      st.success("Redirection vers la plateforme de paiement Stripe...")

    except Exception as e:
      st.error(f"Erreur lors de la création de la session Stripe : {e}")

query_params = st.query_params
if "success" in query_params and query_params["success"] == "true":
  st.balloons()
  st.success("Paiement réussi ! Bienvenue dans l'espace premium.")
elif "canceled" in query_params and query_params["canceled"] == "true":
  st.warning("Le processus de paiement a été annulé.")


# --- 7. SECTION CHAT AVEC GEMINI (KALI GPT) ---
st.divider()
st.subheader("💬 Discussion avec KaliGPT (IA Contextuelle & MariaDB)")

if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input("Posez vos questions sur le trading, vos ordres ou vos stratégies..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    with st.spinner("KaliGPT analyse vos ordres et réfléchit..."):
      if not ai_client:
        response_text = "Erreur : La clé API Gemini (`GEMINI_API_KEY`) n'est pas configurée dans votre fichier .env."
        st.markdown(response_text)
      else:
        try:
          # Récupération automatique du contexte des derniers ordres pour l'IA
          df_orders_context = get_orders_from_db()
          orders_summary = (
              df_orders_context.head(5).to_string()
              if df_orders_context is not None and not df_orders_context.empty
              else "Aucun ordre enregistré pour le moment."
          )

          # Construction du prompt système enrichi avec les données de l'utilisateur
          system_prompt = f"""
          Tu es KaliGPT, un assistant de trading expert, technique, concis et professionnel.
          Voici le contexte récent de l'utilisateur extrait de sa base de données MariaDB :
          - Derniers ordres enregistrés :
          {orders_summary}
          
          Réponds à la question suivante de l'utilisateur en tenant compte de ce contexte de trading : {prompt}
          """

          response = ai_client.models.generate_content(
              model="gemini-2.5-flash", contents=system_prompt
          )
          response_text = response.text
          st.markdown(response_text)
        except Exception as e:
          response_text = f"Une erreur est survenue lors de la communication avec l'API Gemini : {e}"
          st.error(response_text)

      st.session_state.messages.append(
          {"role": "assistant", "content": response_text}
      )
