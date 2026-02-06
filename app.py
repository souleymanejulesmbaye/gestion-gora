import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. CONFIGURATION VISUELLE
st.set_page_config(page_title="ETS GORA MBAYE", layout="wide")
st.markdown("""
    <style>
    .main-title { color: white; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; height: 3em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. INITIALISATION ET RÉPARATION DES FICHIERS
def check_files():
    files = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in files.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')
        else:
            # Vérifie si les colonnes sont les bonnes, sinon répare
            df_check = pd.read_csv(f, sep=';', encoding='utf-8-sig')
            if 'Date' not in df_check.columns and f == 'pointage.csv':
                pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

check_files()

# 3. AUTHENTIFICATION
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    with st.form("Login"):
        st.subheader("🔑 Connexion Direction")
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Entrer"):
            if u == "admin" and p == "GORA2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Accès refusé")
    st.stop()

# 4. PARAMÈTRES DE DATE
st.sidebar.header("📅 Période de Paie")
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois = st.sidebar.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee = st.sidebar.number_input("Année", value=2026)

def get_period(m, a):
    if m == 1: return datetime(a, 1, 1), datetime(a, 1, 25)
    return datetime(a, m-1, 26), datetime(a, m, 25)

d_start, d_end = get_period(mois, annee)

# 5. CHARGEMENT DES DONNÉES
df_ouvriers = pd.read_csv('ouvriers.csv', sep=';', encoding='utf-8-sig')
df_pointage = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
df_pointage['Date'] = pd.to_datetime(df_pointage['Date'], errors='coerce')

# 6. INTERFACE DE POINTAGE
st.markdown(f'<div class="main-title"><h1>ETS GORA MBAYE - POINTAGE {mois_noms[mois-1].upper()}</h1></div>', unsafe_allow_html=True)

if not df_ouvriers.empty:
    groupes = sorted(df_ouvriers['groupe'].unique())
    choix_g = st.selectbox("📂 Choisir le groupe à pointer", groupes)
    
    # Filtrer ouvriers du groupe
    noms_g = df_ouvriers[df_ouvriers['groupe'] == choix_g]['nom'].tolist()
    
    # Créer la grille JJ/MM
    jours = pd.date_range(d_start, d_end)
    col_jjmm = [d.strftime("%d/%m") for d in jours]
    mapping_date = {d.strftime("%d/%m"): d.strftime("%Y-%m-%d") for d in jours}
    
    grille = pd.DataFrame(0, index=noms_g, columns=col_jjmm)
    
    # Remplir avec l'existant
    df_existant = df_pointage[df_pointage['Nom'].isin(noms_g)]
    for _, row in df_existant.iterrows():
        if pd.notnull(row['Date']):
            d_str = row['Date'].strftime("%d/%m")
            if d_str in grille.columns:
                grille.at[row['Nom'], d_str] = int(row['Heures'])

    st.subheader(f"📝 Saisie des heures : {choix_g}")
    # Key dynamique pour forcer le rafraîchissement
    edited_grille = st.data_editor(grille, use_container_width=True, key=f"editor_{choix_g}")

    # BOUTON ENREGISTRER
    if st.button(f"💾 ENREGISTRER LE GROUPE {choix_g}"):
        # 1. Charger tout le pointage actuel
        current_p = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
        current_p['Date'] = pd.to_datetime(current_p['Date'], errors='coerce')
        
        # 2. Supprimer les lignes de ce groupe pour ce mois pour éviter les doublons
        mask = (current_p['Nom'].isin(noms_g)) & (current_p['Date'] >= d_start) & (current_p['Date'] <= d_end)
        current_p = current_p[~mask]
        
        # 3. Ajouter les nouvelles saisies
        new_rows = []
        for nom in edited_grille.index:
            for day_col in edited_grille.columns:
                val = edited_grille.at[nom, day_col]
                if val > 0:
                    real_date = mapping_date[day_col]
                    new_rows.append({
                        'Date': real_date,
                        'Semaine': pd.to_datetime(real_date).isocalendar()[1],
                        'Nom': nom,
                        'Heures': int(val)
                    })
        
        if new_rows:
            df_final = pd.concat([current_p, pd.DataFrame(new_rows)], ignore_index=True)
            df_final.to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Pointage {choix_g} enregistré !")
            st.rerun()
        else:
            st.warning("Aucune heure saisie.")

# 7. RÉCAPITULATIF (BILAN)
st.divider()
st.header("📊 Bilan du Mois")
df_view = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
df_view['Date'] = pd.to_datetime(df_view['Date'], errors='coerce')
df_month = df_view[(df_view['Date'] >= d_start) & (df_view['Date'] <= d_end)]

if not df_month.empty:
    recap = df_month.groupby('Nom')['Heures'].sum().reset_index()
    # Fusionner avec les infos ouvriers pour avoir le groupe
    recap = recap.merge(df_ouvriers[['nom', 'groupe', 'fonction']], left_on='Nom', right_on='nom')
    
    for g in sorted(recap['groupe'].unique()):
        st.write(f"**Groupe : {g}**")
        st.table(recap[recap['groupe'] == g][['Nom', 'fonction', 'Heures']])
else:
    st.info("Aucun pointage pour cette période.")
