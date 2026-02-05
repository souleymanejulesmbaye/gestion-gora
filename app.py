import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import os
import io

# --- CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="ETS GORA MBAYE", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .main-title {
        color: #1E3A8A; font-size: 32px; font-weight: bold; text-align: center;
        padding: 10px; border: 2px solid #1E3A8A; border-radius: 10px;
        background-color: white; margin-bottom: 20px;
    }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES FICHIERS ---
def initialiser_fichiers():
    fichiers = {
        'ouvriers.csv': ['nom', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in fichiers.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

def charger_df(f): 
    return pd.read_csv(f, sep=';', encoding='utf-8-sig')

def sauvegarder_df(df, f):
    df.to_csv(f, index=False, sep=';', encoding='utf-8-sig')

initialiser_fichiers()

# --- SYSTÈME DE CONNEXION ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background-color:white;padding:2rem;border-radius:10px;border:1px solid #ddd">', unsafe_allow_html=True)
        st.subheader("🔐 Connexion - ETS GORA MBAYE")
        user = st.text_input("Identifiant")
        pwd = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if user == "admin" and pwd == "GORA2026":
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- LOGIQUE COMPTABLE (26 au 25 + Exception Décembre) ---
def obtenir_periode(mois, annee):
    if mois == 1: # Janvier: 01/01 au 25/01
        debut, fin = datetime(annee, 1, 1), datetime(annee, 1, 25)
    elif mois == 12: # Décembre: 26/11 au 31/12
        debut, fin = datetime(annee, 11, 26), datetime(annee, 12, 31)
    else: # Autres mois: 26 du mois précédent au 25 en cours
        debut = datetime(annee, mois-1, 26)
        fin = datetime(annee, mois, 25)
    return debut, fin

# --- INTERFACE PRINCIPALE ---
st.markdown('<div class="main-title">🏗️ SYSTÈME DE GESTION - ETS GORA MBAYE</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Paramètres")
    mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    mois_c = st.selectbox("Mois de Paie", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
    annee_c = st.number_input("Année", value=datetime.now().year)
    
    date_debut, date_fin = obtenir_periode(mois_c, annee_c)
    st.info(f"📅 Période : {date_debut.strftime('%d/%m')} au {date_fin.strftime('%d/%m/%Y')}")

    st.divider()
    t1, t2 = st.tabs(["👤 Ouvriers", "💵 Acomptes"])
    with t1:
        with st.form("o", clear_on_submit=True):
            n, g = st.text_input("Nom"), st.text_input("Équipe")
            hn, hs = st.number_input("Tarif HN", 0), st.number_input("Tarif HS", 0)
            if st.form_submit_button("Ajouter"):
                df = charger_df('ouvriers.csv')
                sauvegarder_df(pd.concat([df, pd.DataFrame([[n, g, hn, hs]], columns=df.columns)]), 'ouvriers.csv')
                st.rerun()
    with t2:
        df_o = charger_df('ouvriers.csv')
        if not df_o.empty:
            with st.form("a", clear_on_submit=True):
                nom_a = st.selectbox("Ouvrier", sorted(df_o['nom'].tolist()))
                mont_a = st.number_input("Montant", 0)
                if st.form_submit_button("Valider"):
                    df = charger_df('acomptes.csv')
                    new_a = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), nom_a, mont_a]], columns=df.columns)
                    sauvegarder_df(pd.concat([df, new_a]), 'acomptes.csv')
                    st.success("Acompte enregistré")

# --- GRILLE DE POINTAGE ---
df_ouvriers = charger_df('ouvriers.csv')
df_pointage = charger_df('pointage.csv')

if not df_ouvriers.empty:
    grps = sorted(df_ouvriers['groupe'].unique())
    choix_g = st.selectbox("Sélectionner l'équipe de travail :", grps)
    
    noms_f = df_ouvriers[df_ouvriers['groupe'] == choix_g]['nom'].tolist()
    liste_dates = pd.date_range(date_debut, date_fin)
    colonnes_jours = [d.strftime("%Y-%m-%d") for d in liste_dates]
    affichage_jours = [d.strftime("%d/%m") for d in liste_dates]

    # Création de la grille
    grille = pd.DataFrame(0.0, index=noms_f, columns=colonnes_jours)
    
    if not df_pointage.empty:
        df_p = df_pointage.copy()
        df_p['Date'] = pd.to_datetime(df_p['Date']).dt.strftime("%Y-%m-%d")
        for _, r in df_p[df_p['Nom'].isin(noms_f)].iterrows():
            if r['Date'] in grille.columns:
                grille.at[r['Nom'], r['Date']] = r['Heures']

    # On renomme les colonnes pour l'affichage mais on garde les dates réelles pour le calcul
    grille.columns = affichage_jours
    st.subheader("📝 Saisie des heures")
    edits = st.data_editor(grille, use_container_width=True)

    if st.button("💾 ENREGISTRER LE POINTAGE", type="primary"):
        df_base = charger_df('pointage.csv')
        df_base['Date'] = pd.to_datetime(df_base['Date'])
        # Nettoyage de la période pour ces ouvriers
        df_base = df_base[~((df_base['Date'] >= date_debut) & (df_base['Date'] <= date_fin) & (df_base['Nom'].isin(noms_f)))]
        
        nouveaux = []
        for nom in edits.index:
            for i, h in enumerate(edits.loc[nom]):
                if h > 0:
                    d_reelle = liste_dates[i]
                    nouveaux.append({'Date': d_reelle.strftime("%Y-%m-%d"), 'Semaine': d_reelle.isocalendar()[1], 'Nom': nom, 'Heures': h})
        
        sauvegarder_df(pd.concat([df_base, pd.DataFrame(nouveaux)]), 'pointage.csv')
        st.toast("Données sauvegardées !", icon="✅")

# --- BILAN DES SALAIRES ---
st.divider()
st.header("📊 Bilan du Mois Comptable")

if not df_pointage.empty and not df_ouvriers.empty:
    df_c = charger_df('pointage.csv')
    df_c['Date'] = pd.to_datetime(df_c['Date'])
    df_c = df_c[(df_c['Date'] >= date_debut) & (df_c['Date'] <= date_fin)]
    
    if not df_c.empty:
        df_c = df_c.merge(df_ouvriers, left_on='Nom', right_on='nom')
        # Calcul simplifié
        df_c['Total'] = df_c['Heures'] * df_c['tarif_hn']
        bilan = df_c.groupby(['groupe', 'Nom']).agg({'Heures':'sum', 'Total':'sum'}).reset_index()
        
        # Acomptes
        df_ac = charger_df('acomptes.csv')
        df_ac['Date'] = pd.to_datetime(df_ac['Date'])
        ac_mois = df_ac[(df_ac['Date'] >= date_debut) & (df_ac['Date'] <= date_fin)].groupby('Nom')['Montant'].sum()
        
        bilan['Acomptes'] = bilan['Nom'].map(ac_sum).fillna(0) if not ac_mois.empty else 0
        bilan['Net'] = bilan['Total'] - bilan['Acomptes']
        
        st.dataframe(bilan, use_container_width=True)
        
        # Bouton Export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            bilan.to_excel(writer, index=False)
        st.download_button("📥 Télécharger le Bilan Excel", buffer, f"Bilan_{mois_noms[mois_c-1]}.xlsx")
