import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION ET STYLE ---
st.set_page_config(page_title="ETS GORA MBAYE", layout="wide")

st.markdown("""
    <style>
    .main-title { color: white; background-color: #1E3A8A; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .group-banner { background-color: #f0f2f6; padding: 10px; border-left: 5px solid #1E3A8A; font-weight: bold; margin-top: 20px; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; height: 3em; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTION DES FICHIERS (BASE DE DONNÉES) ---
def init_system():
    fichiers = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in fichiers.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')
        else:
            # Vérification de sécurité des colonnes
            df_test = pd.read_csv(f, sep=';', encoding='utf-8-sig')
            if f == 'pointage.csv' and 'Date' not in df_test.columns:
                pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

init_system()

# --- 3. SÉCURITÉ ACCÈS ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h2 style='text-align:center;'>🔐 CONNEXION</h2>", unsafe_allow_html=True)
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if u == "admin" and p == "GORA2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Identifiant ou mot de passe incorrect")
    st.stop()

# --- 4. PARAMÈTRES DE LA PÉRIODE ---
st.sidebar.header("📅 Période de Paie")
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois_sel = st.sidebar.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee_sel = st.sidebar.number_input("Année", value=2026)

# Période du 26 au 25
def get_dates(m, a):
    if m == 1: start = datetime(a, 1, 1) # Janvier commence au 1er
    else: start = datetime(a, m-1, 26)
    end = datetime(a, m, 25)
    return start, end

date_start, date_end = get_dates(mois_sel, annee_sel)

# --- 5. LOGIQUE D'ENREGISTREMENT ---
def sauvegarder_pointage(nom_groupe, donnees_grille, mapping_inv, d_s, d_e):
    # Charger l'existant
    df_p = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
    df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
    
    # Supprimer l'ancien pour ce groupe et cette période
    noms_groupe = donnees_grille.index.tolist()
    mask = (df_p['Nom'].isin(noms_groupe)) & (df_p['Date'] >= d_s) & (df_p['Date'] <= d_e)
    df_p = df_p[~mask]
    
    # Préparer les nouvelles lignes
    nouvelles_lignes = []
    for nom in donnees_grille.index:
        for col_jjmm in donnees_grille.columns:
            heures = donnees_grille.at[nom, col_jjmm]
            if heures > 0:
                date_iso = mapping_inv[col_jjmm]
                nouvelles_lignes.append({
                    'Date': date_iso,
                    'Semaine': pd.to_datetime(date_iso).isocalendar()[1],
                    'Nom': nom,
                    'Heures': int(heures)
                })
    
    if nouvelles_lignes:
        df_final = pd.concat([df_p, pd.DataFrame(nouvelles_lignes)], ignore_index=True)
        df_final.to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
        return True
    return False

# --- 6. INTERFACE PRINCIPALE ---
st.markdown('<div class="main-title"><h1>ETS GORA MBAYE - GESTION ADMINISTRATIVE</h1></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 POINTAGE QUOTIDIEN", "📊 BILAN & PAIES"])

with tab1:
    df_o = pd.read_csv('ouvriers.csv', sep=';', encoding='utf-8-sig')
    if df_o.empty:
        st.warning("Veuillez d'abord ajouter des ouvriers dans le menu de gauche.")
    else:
        grps = sorted(df_o['groupe'].unique())
        choix_g = st.selectbox("🎯 Sélectionner le Groupe", grps)
        
        # Préparation de la grille JJ/MM
        liste_noms = df_o[df_o['groupe'] == choix_g]['nom'].tolist()
        plage_dates = pd.date_range(date_start, date_end)
        cols_jjmm = [d.strftime("%d/%m") for d in plage_dates]
        mapping_inv = {d.strftime("%d/%m"): d.strftime("%Y-%m-%d") for d in plage_dates}
        
        grille_saisie = pd.DataFrame(0, index=liste_noms, columns=cols_jjmm)
        
        # Charger les heures déjà enregistrées
        df_p_load = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
        df_p_load['Date'] = pd.to_datetime(df_p_load['Date'], errors='coerce')
        for _, row in df_p_load[df_p_load['Nom'].isin(liste_noms)].iterrows():
            if pd.notnull(row['Date']):
                d_fmt = row['Date'].strftime("%d/%m")
                if d_fmt in grille_saisie.columns:
                    grille_saisie.at[row['Nom'], d_fmt] = int(row['Heures'])

        st.info(f"Saisie pour le groupe **{choix_g}** du {date_start.strftime('%d/%m')} au {date_end.strftime('%d/%m')}")
        
        # Le tableau de saisie
        saisie_edit = st.data_editor(grille_saisie, use_container_width=True, key=f"grid_{choix_g}")

        if st.button(f"💾 ENREGISTRER {choix_g}"):
            if sauvegarder_pointage(choix_g, saisie_edit, mapping_inv, date_start, date_end):
                st.success("Données sauvegardées !")
                st.rerun()
            else:
                st.warning("Aucune donnée à enregistrer.")

with tab2:
    st.header(f"Bilan : {mois_noms[mois_sel-1]} {annee_sel}")
    df_p_bilan = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
    df_p_bilan['Date'] = pd.to_datetime(df_p_bilan['Date'], errors='coerce')
    
    # Filtrer sur le mois
    df_m = df_p_bilan[(df_p_bilan['Date'] >= date_start) & (df_p_bilan['Date'] <= date_end)]
    
    if df_m.empty:
        st.info("Aucun pointage enregistré pour cette période.")
    else:
        # Fusion avec ouvriers pour les tarifs et groupes
        df_res = df_m.merge(df_o, left_on='Nom', right_on='nom')
        
        # Calcul HN / HS (Base 48h par semaine)
        df_res['Cumul_Semaine'] = df_res.groupby(['Nom', 'Semaine'])['Heures'].transform('cumsum')
        
        def h_normales(row):
            prec = row['Cumul_Semaine'] - row['Heures']
            if prec >= 48: return 0
            if row['Cumul_Semaine'] > 48: return 48 - prec
            return row['Heures']

        df_res['HN'] = df_res.apply(h_normales, axis=1)
        df_res['HS'] = df_res['Heures'] - df_res['HN']
        
        # Calcul financier
        df_res['Total_Brut'] = (df_res['HN'] * df_res['tarif_hn']) + (df_res['HS'] * df_res['tarif_hs'])
        
        # Affichage par groupe
        total_entreprise = 0
        for g in sorted(df_res['groupe'].unique()):
            st.markdown(f'<div class="group-banner">GROUPE : {g}</div>', unsafe_allow_html=True)
            df_g = df_res[df_res['groupe'] == g].groupby(['Nom', 'fonction']).agg({
                'HN': 'sum', 'HS': 'sum', 'Total_Brut': 'sum'
            }).reset_index()
            
            # Formatage des nombres
            df_table = df_g.copy()
            df_table['Total_Brut'] = df_table['Total_Brut'].astype(int).map('{:,}'.format).str.replace(',', ' ')
            st.table(df_table)
            
            total_g = df_g['Total_Brut'].sum()
            st.write(f"**Sous-total {g} : {int(total_g):,} FCFA**".replace(',', ' '))
            total_entreprise += total_g
            
        st.divider()
        st.metric("💰 TOTAL GÉNÉRAL À PAYER", f"{int(total_entreprise):,} FCFA".replace(',', ' '))

# --- 7. MENU ADMINISTRATION (SIDEBAR) ---
with st.sidebar:
    st.divider()
    st.subheader("👥 Gestion Personnel")
    with st.expander("Ajouter un ouvrier"):
        with st.form("new_worker", clear_on_submit=True):
            nom = st.text_input("Nom & Prénom")
            fct = st.text_input("Fonction")
            grp = st.text_input("Groupe (ex: SERVITUDE)")
            thn = st.number_input("Tarif Normal (HN)", value=0)
            ths = st.number_input("Tarif Supp (HS)", value=0)
            if st.form_submit_button("Valider"):
                if nom and grp:
                    df_add = pd.read_csv('ouvriers.csv', sep=';', encoding='utf-8-sig')
                    new_line = pd.DataFrame([[nom, fct, grp.upper(), thn, ths]], columns=df_add.columns)
                    pd.concat([df_add, new_line], ignore_index=True).to_csv('ouvriers.csv', index=False, sep=';', encoding='utf-8-sig')
                    st.success("Ajouté !")
                    st.rerun()

    if st.button("🗑️ Effacer tous les pointages"):
        pd.DataFrame(columns=['Date', 'Semaine', 'Nom', 'Heures']).to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
        st.warning("Historique supprimé.")
        st.rerun()
