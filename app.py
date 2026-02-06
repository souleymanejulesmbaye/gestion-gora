import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="ETS GORA MBAYE", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .main-title { color: #1E3A8A; font-size: 30px; font-weight: bold; text-align: center; border: 2px solid #1E3A8A; border-radius: 10px; background: white; padding: 10px; margin-bottom: 20px; }
    .group-header { background-color: #1E3A8A; color: white; padding: 10px; border-radius: 5px; margin-top: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS FICHIERS ---
def charger_df(f):
    if not os.path.exists(f) or os.stat(f).st_size == 0:
        cols = {'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
                'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
                'acomptes.csv': ['Date', 'Nom', 'Montant']}
        return pd.DataFrame(columns=cols.get(f, []))
    try:
        return pd.read_csv(f, sep=';', encoding='utf-8-sig')
    except:
        return pd.DataFrame()

def sauvegarder_df(df, f):
    df.to_csv(f, index=False, sep=';', encoding='utf-8-sig')

# --- AUTHENTIFICATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    user = st.sidebar.text_input("Identifiant")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    if st.sidebar.button("Connexion"):
        if user == "admin" and pwd == "GORA2026":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- DATES ---
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois_c = st.sidebar.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee_c = st.sidebar.number_input("Année", value=2026)

def obtenir_periode(m, a):
    if m == 1: return datetime(a, 1, 1), datetime(a, 1, 25)
    return datetime(a, m-1, 26), datetime(a, m, 25)

d_debut, d_fin = obtenir_periode(mois_c, annee_c)

# --- ACTION DE SAUVEGARDE FORCÉE ---
def executer_sauvegarde(nom_groupe, donnees_editees, d_inv, d_deb, d_f):
    df_all = charger_df('pointage.csv')
    if 'Date' not in df_all.columns:
        df_all = pd.DataFrame(columns=['Date', 'Semaine', 'Nom', 'Heures'])
    
    df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
    noms_groupe = donnees_editees.index.tolist()
    
    # Nettoyage
    mask = (df_all['Nom'].isin(noms_groupe)) & (df_all['Date'] >= d_deb) & (df_all['Date'] <= d_f)
    df_all = df_all[~mask].dropna(subset=['Date'])
    
    nouveaux = []
    for nom in donnees_editees.index:
        for col_jjmm in donnees_editees.columns:
            try:
                h = int(donnees_editees.at[nom, col_jjmm])
                if h > 0:
                    date_reelle = d_inv[col_jjmm]
                    dt_obj = pd.to_datetime(date_reelle)
                    nouveaux.append({
                        'Date': date_reelle, 
                        'Semaine': dt_obj.isocalendar()[1], 
                        'Nom': nom, 
                        'Heures': h
                    })
            except: continue
    
    if nouveaux:
        df_final = pd.concat([df_all, pd.DataFrame(nouveaux)], ignore_index=True)
        sauvegarder_df(df_final, 'pointage.csv')
        st.toast(f"✅ Groupe {nom_groupe} enregistré !", icon="💾")

# --- INTERFACE ---
st.markdown('<div class="main-title">GESTION DES POINTAGES - ETS GORA MBAYE</div>', unsafe_allow_html=True)
df_o = charger_df('ouvriers.csv')

if not df_o.empty:
    grps = sorted(df_o['groupe'].unique())
    choix_g = st.selectbox("🎯 CHOISIR LE GROUPE :", grps)
    
    # Préparation données
    noms_g = df_o[df_o['groupe'] == choix_g]['nom'].tolist()
    dates_p = pd.date_range(d_debut, d_fin)
    dict_dates = {d.strftime("%Y-%m-%d"): d.strftime("%d/%m") for d in dates_p}
    dict_inv = {v: k for k, v in dict_dates.items()}
    
    grille = pd.DataFrame(0, index=noms_g, columns=list(dict_dates.values()))
    
    # Chargement existant
    df_p = charger_df('pointage.csv')
    if not df_p.empty and 'Date' in df_p.columns:
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
        for _, r in df_p[df_p['Nom'].isin(noms_g)].iterrows():
            d_reel = r['Date'].strftime("%Y-%m-%d")
            if d_reel in dict_dates:
                grille.at[r['Nom'], dict_dates[d_reel]] = int(r['Heures'])

    st.subheader(f"Saisie : {choix_g}")
    # Clé unique pour éviter les blocages
    edits = st.data_editor(grille, use_container_width=True, key=f"editor_{choix_g}_{mois_c}")

    # BOUTON AVEC APPEL DE FONCTION DIRECT
    if st.button(f"💾 ENREGISTRER {choix_g}", type="primary", use_container_width=True):
        executer_sauvegarde(choix_g, edits, dict_inv, d_debut, d_fin)
        st.rerun()

# --- BILAN ---
st.divider()
df_p_view = charger_df('pointage.csv')
if not df_p_view.empty and 'Date' in df_p_view.columns:
    df_p_view['Date'] = pd.to_datetime(df_p_view['Date'], errors='coerce')
    df_m = df_p_view.dropna(subset=['Date'])
    df_m = df_m[(df_m['Date'] >= d_debut) & (df_m['Date'] <= d_fin)]
    
    if not df_m.empty:
        df_res = df_m.merge(df_o, left_on='Nom', right_on='nom')
        recap = df_res.groupby(['groupe', 'Nom']).agg({'Heures':'sum'}).reset_index()
        
        for g in sorted(recap['groupe'].unique()):
            st.markdown(f'<div class="group-header">🏢 GROUPE : {g}</div>', unsafe_allow_html=True)
            st.table(recap[recap['groupe'] == g][['Nom', 'Heures']])
