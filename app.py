import streamlit as st
import pymysql
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI

# Initialisation du client OpenAI (récupère automatiquement la clé depuis les variables d'environnement)
try:
    client = OpenAI()
except Exception:
    client = None

# Configuration de la page (doit toujours être en premier)
st.set_page_config(
    page_title="KaliGPT Trading Station",
    page_icon="📈",
    layout="wide"
)

# Titre principal de l'application
st.title("📈 KaliGPT - Station de Trading & IA")
st.markdown("Plateforme centralisée d'analyse, de trading et d'assistant intelligent.")

# Barre latérale (Sidebar) pour les paramètres généraux et indicateurs
with st.sidebar:
    st.header("⚙ Configuration")
    model_choice = st.selectbox("Modèle IA actif", ["gpt-4o-mini", "gpt-3.5-turbo"])
    temperature = st.slider("Température", 0.0, 1.0, 0.7)
    
    st.divider()
    st.subheader("📊 Indicateurs Techniques")
    show_sma = st.checkbox("Afficher la Moyenne Mobile (SMA)", value=True)
    sma_period = st.slider("Période SMA", min_value=2, max_value=10, value=3)
    
    st.divider()
    st.info("Environnement : Linux / Streamlit local")

# Création des onglets principaux
tab_chat, tab_trading, tab_db = st.tabs(["💬 Assistant IA", "📊 Dashboard Trading", "🗄️ Base de données"])

# --- ONGLET 1 : ASSISTANT IA ---
with tab_chat:
    st.header("Discuter avec KaliGPT")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Posez votre question à KaliGPT..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Réflexion en cours...")
            
            try:
                if client is None:
                    raise ValueError("Client API non initialisé. Vérifiez votre clé OPENAI_API_KEY.")
                
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    temperature=temperature
                )
                
                assistant_response = response.choices[0].message.content
                message_placeholder.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            except Exception as e:
                error_msg = f"Erreur lors de la communication avec l'API : {e}"
                message_placeholder.error(error_msg)

# --- ONGLET 2 : DASHBOARD TRADING (Chandeliers, Moyenne Mobile, Ordres & Historique) ---
with tab_trading:
    st.header("Suivi des Marchés & Stratégies")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Actif surveillé", "BTC/USD", "+2.4%")
    col2.metric("Dernier Signal", "Achat", "Fiabilité 85%")
    col3.metric("Statut Bot", "Actif", "En ligne")
    
    st.subheader("Analyse Graphique & Indicateurs")
    
    # Préparation des données sous forme de DataFrame Pandas
    data = {
        'Date': ['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05', '2026-10-06'],
        'Open': [60000, 61200, 60800, 62100, 61500, 62300],
        'High': [61500, 62000, 62500, 63000, 62800, 63500],
        'Low': [59800, 60500, 60200, 61800, 61000, 62000],
        'Close': [61200, 60800, 62100, 62900, 62200, 63100]
    }

    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])

    # Création du graphique Plotly
    fig = go.Figure()

    # Ajout des chandeliers
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Chandeliers'
    ))

    # Ajout dynamique de la Moyenne Mobile si activée dans la sidebar
    if show_sma:
        df['SMA'] = df['Close'].rolling(window=sma_period).mean()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['SMA'],
            mode='lines',
            name=f'SMA {sma_period}',
            line=dict(color='orange', width=2)
        ))

    fig.update_layout(
        title="Évolution du BTC/USD & Moyenne Mobile",
        xaxis_title="Date",
        yaxis_title="Prix (USD)",
        template="plotly_dark",
        height=450
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📝 Passer un nouvel ordre de trading")
    
    with st.form("order_form"):
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            order_symbol = st.selectbox("Actif", ["BTC/USD", "ETH/USD", "XRP/USD"])
            order_type = st.selectbox("Type d'ordre", ["BUY", "SELL"])
        with col_o2:
            order_amount = st.number_input("Quantité / Montant", min_value=0.0001, value=1.0, format="%.4f")
            order_price = st.number_input("Prix d'exécution (USD)", min_value=0.01, value=60000.0, format="%.2f")
            
        submit_order = st.form_submit_button("Exécuter et enregistrer l'ordre")

    if submit_order:
        try:
            connection = pymysql.connect(
                host="localhost",
                user="root",
                password="",
                database="trading_db",
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO trading_orders (symbol, order_type, amount, price, status) 
                    VALUES (%s, %s, %s, %s, 'EXECUTED')
                """
                cursor.execute(sql, (order_symbol, order_type, order_amount, order_price))
                connection.commit()
                
                st.success(f"Ordre {order_type} de {order_amount} {order_symbol} enregistré avec succès à {order_price} USD !")
                
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement de l'ordre dans MariaDB : {e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

    st.divider()
    st.subheader("📋 Historique des ordres enregistrés")
    
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="trading_db",
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM trading_orders ORDER BY created_at DESC;")
            orders = cursor.fetchall()
            
            if orders:
                st.dataframe(orders, use_container_width=True)
            else:
                st.info("Aucun ordre enregistré pour le moment.")
                
    except Exception as e:
        st.warning(f"Impossible de charger l'historique : {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# --- ONGLET 3 : BASE DE DONNÉES ---
with tab_db:
    st.header("Gestion & Initialisation MariaDB")
    st.markdown("Configurez votre connexion et initialisez vos tables de trading automatiquement.")

    with st.form("db_config_form"):
        db_host = st.text_input("Hôte (Host)", value="localhost")
        db_user = st.text_input("Utilisateur (User)", value="root")
        db_password = st.text_input("Mot de passe", type="password")
        db_name = st.text_input("Nom de la base de données", value="trading_db")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            test_btn = st.form_submit_button("Tester la connexion")
        with col_btn2:
            init_btn = st.form_submit_button("Créer les tables automatiques")

    if test_btn or init_btn:
        try:
            connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
                cursor.execute(f"USE `{db_name}`;")
                
                if test_btn:
                    cursor.execute("SELECT VERSION();")
                    db_version = cursor.fetchone()
                    st.success(f"Connexion réussie ! Version MariaDB : {list(db_version.values())[0]}")

                if init_btn:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS market_prices (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL,
                            price DECIMAL(18, 8) NOT NULL,
                            high DECIMAL(18, 8),
                            low DECIMAL(18, 8),
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trading_orders (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL,
                            order_type VARCHAR(10) NOT NULL,
                            amount DECIMAL(18, 8) NOT NULL,
                            price DECIMAL(18, 8) NOT NULL,
                            status VARCHAR(20) DEFAULT 'PENDING',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    connection.commit()
                    st.success("Tables `market_prices` et `trading_orders` créées avec succès dans MariaDB !")

        except Exception as e:
            st.error(f"Erreur avec MariaDB : {e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()
