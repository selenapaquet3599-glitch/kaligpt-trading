import streamlit as st

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Trustx Trading Station",
    page_icon="📈",
    layout="wide"
)

# Titre principal de l'application
st.title("📈 Trustx - Station de Trading & IA")
st.markdown("Bienvenue sur votre plateforme centralisée d'analyse et d'assistant intelligent.")

# Barre latérale (Sidebar) pour les paramètres généraux
with st.sidebar:
    st.header("⚙️ Configuration")
    model_choice = st.selectbox("Modèle IA actif", ["KaliGPT-Standard", "KaliGPT-Trading"])
    temperature = st.slider("Température", 0.0, 1.0, 0.7)
    st.divider()
    st.info("Environnement : Linux / Streamlit local")

# Création d'onglets pour organiser les différentes sections
tab_chat, tab_trading, tab_db = st.tabs(["💬 Assistant IA", "📊 Dashboard Trading", "🗄️ Base de données"])

# --- ONGLET 1 : ASSISTANT IA ---
with tab_chat:
    st.header("Discuter avec KaliGPT")

    # Initialisation de l'historique des messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage de l'historique
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrée utilisateur pour le chat
    if prompt := st.chat_input("Posez votre question à KaliGPT..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Réponse simulée de l'assistant (à connecter à votre logique d'API)
        response = f"Réponse de {model_choice} concernant : '{prompt}'"
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# --- ONGLET 2 : DASHBOARD TRADING ---
with tab_trading:
    st.header("Suivi des Marchés & Stratégies")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Actif surveillé", "BTC/USD", "+2.4%")
    col2.metric("Dernier Signal", "Achat", "Fiabilité 85%")
    col3.metric("Statut Bot", "Actif", "En ligne")
    
    st.subheader("Graphique des performances")
    # Données de test pour le graphique
    chart_data = [100, 105, 102, 110, 115, 118, 122]
    st.line_chart(chart_data)

# --- ONGLET 3 : BASE DE DONNÉES ---
with tab_db:
    st.header("Gestion MariaDB")
    st.markdown("Espace réservé pour la connexion à votre base de données de trading locale.")
    
    if st.button("Tester la connexion MariaDB"):
        # Emplacement futur pour le code de connexion (ex: pymysql ou mysql-connector-python)
        st.success("Connexion à MariaDB simulée avec succès !")
