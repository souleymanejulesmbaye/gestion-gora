import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ETS GORA MBAYE", layout="wide")

# --- 2. RÉPARATION ET INITIALISATION DE TOUS LES FICHIERS ---
def initialiser_tous_les_fichiers():
    structures = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for fichier, colonnes in structures.items():
        # Si le fichier n'existe pas ou est vide, on le crée proprement
        if not os.path.exists(fichier) or os.stat(fichier).st_size == 0:
            pd.DataFrame(columns=colonnes).to_csv(fichier, index=False, sep=';', encoding='utf-8-sig')
        else:
            # Vérification : si une colonne manque (ex: 'Date'), on répare
            try:
                df_test = pd.read_csv(fichier, sep=';', encoding='utf-8-sig')
                for col in colonnes:
                    if col not in df_test.columns:
                        st.warning(f"Réparation du fichier {fichier}...")
                        pd.DataFrame(columns=colonnes).to_csv(fichier, index=False, sep=';', encoding='utf-8-sig')
                        break
            except:
                pd.DataFrame(columns=colonnes).to_csv(fichier, index=False, sep=';', encoding='utf-8-sig')

initialiser_tous_les_fichiers()

# --- 3. FONCTIONS DE CHARGEMENT / SAUVEGARDE ---
def charger(nom_fichier):
    return pd.read_csv(nom_fichier, sep=';', encoding='utf-8-sig')

def sauver(df, nom_fichier):
    df.to_csv(nom_fichier, index=False, sep=';', encoding='utf-8-sig')

# --- 4. AUTHENTIFICATION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.header("🔐 ETS GORA MBAYE")
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if u == "admin" and p == "GORA2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 5. LOGIQUE DES DATES (Période 26 au 25) ---
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois_sel = st.sidebar.selectbox("Mois de Paie", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee_sel = st.sidebar.number_input("Année", value=2026)

def calcul_dates(m, a):
    if m == 1: debut = datetime(a, 1, 1)
    else: debut = datetime(a, m-1, 26)
    fin = datetime(a, m, 25)
    return debut, fin

d_start, d_end = calcul_dates(mois_sel, annee_sel)

# --- 6. INTERFACE À 3 ONGLETS ---
st.title("🏗️ Système de Gestion Intégral")

tab_pointage, tab_acomptes, tab_ouvriers, tab_bilan = st.tabs([
    "📝 Pointage", "💵 Acomptes", "👥 Ouvriers", "📊 Bilan Final"
])

# --- ONGLET 1 : POINTAGE ---
with tab_pointage:
    df_o = charger('ouvriers.csv')
    if df_o.empty:
        st.warning("Ajoutez des ouvriers pour commencer.")
    else:
        choix_g = st.selectbox("Groupe à pointer", sorted(df_o['groupe'].unique()))
        noms_g = df_o[df_o['groupe'] == choix_g]['nom'].tolist()
        
        # Grille JJ/MM
        jours = pd.date_range(d_start, d_end)
        cols_jjmm = [d.strftime("%d/%m") for d in jours]
        map_inv = {d.strftime("%d/%m"): d.strftime("%Y-%m-%d") for d in jours}
        
        grille = pd.DataFrame(0, index=noms_g, columns=cols_jjmm)
        
        # Charger existant
        df_p = charger('pointage.csv')
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
        for _, r in df_p[df_p['Nom'].isin(noms_g)].iterrows():
            if pd.notnull(r['Date']):
                d_fmt = r['Date'].strftime("%d/%m")
                if d_fmt in grille.columns: grille.at[r['Nom'], d_fmt] = int(r['Heures'])
        
        edit_p = st.data_editor(grille, use_container_width=True, key=f"p_{choix_g}")
        
        if st.button(f"💾 Enregistrer Pointage {choix_g}"):
            df_p = df_p[~((df_p['Nom'].isin(noms_g)) & (df_p['Date'] >= d_start) & (df_p['Date'] <= d_end))]
            new_data = []
            for n in edit_p.index:
                for c in edit_p.columns:
                    if edit_p.at[n, c] > 0:
                        real_d = map_inv[c]
                        new_data.append({'Date': real_d, 'Semaine': pd.to_datetime(real_d).isocalendar()[1], 'Nom': n, 'Heures': int(edit_p.at[n, c])})
            sauver(pd.concat([df_p, pd.DataFrame(new_data)], ignore_index=True), 'pointage.csv')
            st.success("Pointage enregistré !")
            st.rerun()

# --- ONGLET 2 : ACOMPTES ---
with tab_acomptes:
    st.subheader("Enregistrer un acompte")
    df_o = charger('ouvriers.csv')
    with st.form("form_acompte", clear_on_submit=True):
        nom_ac = st.selectbox("Ouvrier", sorted(df_o['nom'].tolist()))
        montant_ac = st.number_input("Montant (FCFA)", min_value=0, step=500)
        date_ac = st.date_input("Date de versement")
        if st.form_submit_button("Valider l'acompte"):
            df_ac = charger('acomptes.csv')
            nouvel_ac = pd.DataFrame([[date_ac, nom_ac, montant_ac]], columns=df_ac.columns)
            sauver(pd.concat([df_ac, nouvel_ac], ignore_index=True), 'acomptes.csv')
            st.success("Acompte enregistré !")

# --- ONGLET 3 : GESTION OUVRIERS ---
with tab_ouvriers:
    st.subheader("Ajouter un nouvel ouvrier")
    with st.form("add_worker", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        n = c1.text_input("Nom & Prénom")
        f = c2.text_input("Fonction")
        g = c3.text_input("Groupe (ex: SERVITUDE)")
        thn = c1.number_input("Tarif HN", value=0)
        ths = c2.number_input("Tarif HS", value=0)
        if st.form_submit_button("Ajouter à la base"):
            if n and g:
                df_w = charger('ouvriers.csv')
                sauver(pd.concat([df_w, pd.DataFrame([[n, f, g.upper(), thn, ths]], columns=df_w.columns)], ignore_index=True), 'ouvriers.csv')
                st.success(f"{n} ajouté !")
                st.rerun()

    st.divider()
    st.subheader("Liste du personnel")
    df_w_list = charger('ouvriers.csv')
    st.dataframe(df_w_list, use_container_width=True)
    if st.button("🗑️ Vider toute la liste (Action irréversible)"):
        sauver(pd.DataFrame(columns=['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs']), 'ouvriers.csv')
        st.rerun()

# --- ONGLET 4 : BILAN FINAL ---
with tab_bilan:
    st.header(f"Bilan {mois_noms[mois_sel-1]} {annee_sel}")
    df_p = charger('pointage.csv')
    df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
    df_m = df_p[(df_p['Date'] >= d_start) & (df_p['Date'] <= d_end)].dropna(subset=['Date'])
    
    if df_m.empty:
        st.info("Aucune donnée pour ce mois.")
    else:
        df_o = charger('ouvriers.csv')
        df_ac = charger('acomptes.csv')
        df_ac['Date'] = pd.to_datetime(df_ac['Date'], errors='coerce')
        
        # Calcul HN/HS
        df_res = df_m.merge(df_o, left_on='Nom', right_on='nom')
        df_res['Cumul_S'] = df_res.groupby(['Nom', 'Semaine'])['Heures'].transform('cumsum')
        df_res['HN'] = df_res.apply(lambda r: (48 - (r['Cumul_S'] - r['Heures'])) if r['Cumul_S'] > 48 and (r['Cumul_S'] - r['Heures']) < 48 else (0 if (r['Cumul_S'] - r['Heures']) >= 48 else r['Heures']), axis=1)
        df_res['HS'] = df_res['Heures'] - df_res['HN']
        
        # Recap final
        bilan = df_res.groupby(['groupe', 'Nom']).agg({'HN':'sum', 'HS':'sum'}).reset_index()
        bilan = bilan.merge(df_o[['nom', 'tarif_hn', 'tarif_hs']], left_on='Nom', right_on='nom')
        bilan['Salaire_Brut'] = (bilan['HN'] * bilan['tarif_hn']) + (bilan['HS'] * bilan['tarif_hs'])
        
        # Acomptes du mois
        ac_mois = df_ac[(df_ac['Date'] >= d_start) & (df_ac['Date'] <= d_end)].groupby('Nom')['Montant'].sum()
        bilan['Acomptes'] = bilan['Nom'].map(ac_mois).fillna(0)
        bilan['Net_à_Payer'] = bilan['Salaire_Brut'] - bilan['Acomptes']
        
        for g in sorted(bilan['groupe'].unique()):
            st.subheader(f"🏢 Groupe : {g}")
            df_g = bilan[bilan['groupe'] == g]
            st.table(df_g[['Nom', 'HN', 'HS', 'Salaire_Brut', 'Acomptes', 'Net_à_Payer']])
