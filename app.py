import streamlit as st
import pymysql
import plotly.graph_objects as go

# Configuration de la page (doit toujours être en premier)
st.set_page_config(
    page_title="KaliGPT Trading Station",
    page_icon="📈",
    layout="wide"
)

# Titre principal de l'application
st.title("📈 KaliGPT - Station de Trading & IA")
st.markdown("Plateforme centralisée d'analyse, de trading et d'assistant intelligent.")

# Barre latérale (Sidebar) pour les paramètres généraux
with st.sidebar:
    st.header("⚙️ Configuration")
    model_choice = st.selectbox("Modèle IA actif", ["KaliGPT-Standard", "KaliGPT-Trading"])
    temperature = st.slider("Température", 0.0, 1.0, 0.7)
    st.divider()
    st.info("Environnement : Linux / Streamlit local")

# Création des onglets principaux
tab_chat, tab_trading, tab_db = st.tabs(["💬 Assistant IA", "📊 Dashboard Trading", "🗄️ Base de données"])

# --- ONGLET 1 : ASSISTANT IA ---
with tab_chat:
    st.header("Discuter avec KaliGPT")

    # Initialisation de l'historique des messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage de l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrée utilisateur pour le chat
    if prompt := st.chat_input("Posez votre question à KaliGPT..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Réponse simulée de l'assistant (prête pour connexion API future)
        response = f"Réponse de {model_choice} concernant : '{prompt}'"
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# --- ONGLET 2 : DASHBOARD TRADING (Avec Plotly) ---
with tab_trading:
    st.header("Suivi des Marchés & Stratégies")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Actif surveillé", "BTC/USD", "+2.4%")
    col2.metric("Dernier Signal", "Achat", "Fiabilité 85%")
    col3.metric("Statut Bot", "Actif", "En ligne")
    
    st.subheader("Analyse Graphique Avancée")
    
    # Données de test pour le graphique en chandeliers (Candlestick)
    fig = go.Figure(data=[go.Candlestick(
        x=['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04'],
        open=[60000, 61200, 60800, 62100],
        high=[61500, 62000, 62500, 63000],
        low=[59800, 60500, 60200, 61800],
        close=[61200, 60800, 62100, 62900]
    )])
    
    fig.update_layout(
        title="Évolution du BTC/USD",
        xaxis_title="Date",
        yaxis_title="Prix (USD)",
        template="plotly_dark",
        height=450
    )
    
    # Affichage du graphique interactif Plotly
    st.plotly_chart(fig, use_container_width=True)

# --- ONGLET 3 : BASE DE DONNÉES ---
with tab_db:
    st.header("Gestion MariaDB")
    st.markdown("Connexion à votre base de données de trading locale.")

    with st.form("db_config_form"):
        db_host = st.text_input("Hôte (Host)", value="localhost")
        db_user = st.text_input("Utilisateur (User)", value="root")
        db_password = st.text_input("Mot de passe", type="password")
        db_name = st.text_input("Nom de la base de données", value="trading_db")
        submit_btn = st.form_submit_button("Tester la connexion")

    if submit_btn:
        try:
            connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                db_version = cursor.fetchone()
                st.success(f"Connexion réussie à MariaDB ! Version du serveur : {list(db_version.values())[0]}")
        except Exception as e:
            st.error(f"Erreur de connexion à MariaDB : {e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()
