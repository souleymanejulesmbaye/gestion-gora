import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. PRÉPARATION DES FICHIERS ---
def init_csv():
    # On force la création des fichiers s'ils n'existent pas
    for f, cols in {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures']
    }.items():
        if not os.path.exists(f):
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

init_csv()

# --- 2. CONFIGURATION PÉRIODE ---
st.title("📝 ETS GORA MBAYE - POINTAGE")

mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
m_col, a_col = st.columns(2)
mois = m_col.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee = a_col.number_input("Année", value=2026)

def get_range(m, a):
    # Période du 26 au 25
    start = datetime(a, 1, 1) if m == 1 else datetime(a, m-1, 26)
    end = datetime(a, m, 25)
    return start, end

d_start, d_end = get_range(mois, annee)

# --- 3. SELECTION DU GROUPE ---
df_o = pd.read_csv('ouvriers.csv', sep=';', encoding='utf-8-sig')

if df_o.empty:
    st.error("⚠️ Le fichier ouvriers.csv est vide. Ajoutez des ouvriers dans la barre latérale.")
    with st.sidebar.form("add"):
        n = st.text_input("Nom")
        g = st.text_input("Groupe")
        if st.form_submit_button("Ajouter"):
            pd.concat([df_o, pd.DataFrame([[n, 'Ouvrier', g.upper(), 0, 0]], columns=df_o.columns)]).to_csv('ouvriers.csv', index=False, sep=';', encoding='utf-8-sig')
            st.rerun()
else:
    groupes = sorted(df_o['groupe'].unique())
    choix_g = st.selectbox("🎯 CHOISIR LE GROUPE :", groupes)
    
    # Préparation de la grille
    noms_groupe = df_o[df_o['groupe'] == choix_g]['nom'].tolist()
    dates_plage = pd.date_range(d_start, d_end)
    cols_jjmm = [d.strftime("%d/%m") for d in dates_plage]
    map_dates = {d.strftime("%d/%m"): d.strftime("%Y-%m-%d") for d in dates_plage}
    
    grille = pd.DataFrame(0, index=noms_groupe, columns=cols_jjmm)
    
    # Charger les heures existantes (sécurité : try/except)
    try:
        df_exist = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
        df_exist['Date'] = pd.to_datetime(df_exist['Date'], errors='coerce')
        for _, r in df_exist[df_exist['Nom'].isin(noms_groupe)].iterrows():
            if pd.notnull(r['Date']):
                fmt = r['Date'].strftime("%d/%m")
                if fmt in grille.columns:
                    grille.at[r['Nom'], fmt] = int(r['Heures'])
    except:
        pass

    st.write(f"Saisie pour **{choix_g}**")
    # Utilisation d'une KEY unique pour ne pas bloquer le bouton
    edited_data = st.data_editor(grille, use_container_width=True, key=f"saisie_{choix_g}")

    # --- LE BOUTON D'ENREGISTREMENT ---
    if st.button(f"💾 ENREGISTRER MAINTENANT : {choix_g}", type="primary"):
        # 1. Charger tout le fichier actuel
        df_all = pd.read_csv('pointage.csv', sep=';', encoding='utf-8-sig')
        df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        
        # 2. Supprimer SEULEMENT les lignes du groupe actuel pour cette période
        mask = (df_all['Nom'].isin(noms_groupe)) & (df_all['Date'] >= d_start) & (df_all['Date'] <= d_end)
        df_all = df_all[~mask].dropna(subset=['Date'])
        
        # 3. Récupérer les nouvelles données du tableau
        nouveaux_pointages = []
        for nom in edited_data.index:
            for jjmm in edited_data.columns:
                valeur = edited_data.at[nom, jjmm]
                if valeur > 0:
                    date_iso = map_dates[jjmm]
                    nouveaux_pointages.append({
                        'Date': date_iso,
                        'Semaine': pd.to_datetime(date_iso).isocalendar()[1],
                        'Nom': nom,
                        'Heures': int(valeur)
                    })
        
        # 4. Fusionner et Sauvegarder
        if nouveaux_pointages:
            df_final = pd.concat([df_all, pd.DataFrame(nouveaux_pointages)], ignore_index=True)
            df_final.to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Enregistré avec succès pour le groupe {choix_g} !")
            st.rerun()
        else:
            st.warning("⚠️ Aucune heure n'a été saisie dans le tableau.")
