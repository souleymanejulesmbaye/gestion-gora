import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import os
import io

# --- CONFIGURATION DU DESIGN ---
st.set_page_config(
    page_title="ÉTABLISSEMENT GORA MBAYE - Système de Pointage",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 5px; height: 3em; width: 100%; font-weight: bold; background-color: #1E3A8A; color: white; }
    .main-title {
        color: #1E3A8A;
        font-size: 38px;
        font-weight: bold;
        text-align: center;
        padding: 15px;
        border: 2px solid #1E3A8A;
        border-radius: 10px;
        margin-bottom: 25px;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS SYSTÈME ---
def initialiser_fichiers():
    fichiers = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in fichiers.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

def charger_df(f): return pd.read_csv(f, sep=';', encoding='utf-8-sig')

initialiser_fichiers()

# --- TITRE OFFICIEL ---
st.markdown('<div class="main-title">🏗️ SYSTÈME DE POINTAGE - ÉTABLISSEMENT GORA MBAYE</div>', unsafe_allow_html=True)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Administration")
    
    st.subheader("📅 Période de Paie")
    mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    mois_c = st.selectbox("Mois de calcul", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
    annee_c = st.number_input("Année", value=datetime.now().year)

    # Logique du cycle comptable : du 26 au 25
    if mois_c == 1:
        date_debut = datetime(annee_c - 1, 12, 26)
    else:
        date_debut = datetime(annee_c, mois_c - 1, 26)
    date_fin = datetime(annee_c, mois_c, 25)

    st.info(f"Période comptable : \n**{date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}**")

    st.divider()
    tab1, tab2 = st.tabs(["👤 Ouvriers", "💵 Acomptes"])
    
    with tab1:
        with st.form("o", clear_on_submit=True):
            n = st.text_input("Nom & Prénom")
            fct = st.text_input("Fonction") # Ajout de la colonne fonction
            g = st.text_input("Équipe / Chantier")
            hn = st.number_input("Tarif HN", 0)
            hs = st.number_input("Tarif HS", 0)
            if st.form_submit_button("➕ Ajouter l'Ouvrier"):
                if n and g:
                    df = charger_df('ouvriers.csv')
                    pd.concat([df, pd.DataFrame([[n.strip(), fct.strip(), g.strip(), hn, hs]], columns=df.columns)], ignore_index=True).to_csv('ouvriers.csv', index=False, sep=';', encoding='utf-8-sig')
                    st.rerun()

    with tab2:
        df_o = charger_df('ouvriers.csv')
        if not df_o.empty:
            with st.form("a", clear_on_submit=True):
                nom_a = st.selectbox("Ouvrier", sorted(df_o['nom'].tolist()))
                mont_a = st.number_input("Montant Acompte", 0, step=1000)
                if st.form_submit_button("💸 Valider l'Acompte"):
                    df = charger_df('acomptes.csv')
                    new = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), nom_a, mont_a]], columns=df.columns)
                    pd.concat([df, new], ignore_index=True).to_csv('acomptes.csv', index=False, sep=';', encoding='utf-8-sig')
                    st.success("Acompte enregistré")

# --- CHARGEMENT DES DONNÉES ---
df_ouvriers = charger_df('ouvriers.csv')
df_pointage = charger_df('pointage.csv')

# --- SECTION PRINCIPALE ---
if df_ouvriers.empty:
    st.info("👋 Bienvenue. Veuillez enregistrer vos premiers ouvriers dans le menu de gauche.")
else:
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.subheader("📝 Fiche de Pointage")
    with col_t2:
        grps = sorted(df_ouvriers['groupe'].unique())
        choix_grp = st.selectbox("Sélectionner Équipe :", grps)

    # Filtrage des noms
    noms_f = df_ouvriers[df_ouvriers['groupe'] == choix_grp]['nom'].tolist()
    
    # Génération des colonnes JJ/MM pour la période du 26 au 25
    plage_dates = pd.date_range(date_debut, date_fin)
    jours_cols = [d.strftime("%d/%m") for d in plage_dates]
    
    df_grille = pd.DataFrame(0.0, index=noms_f, columns=jours_cols)
    
    # Chargement des pointages existants dans la grille
    if not df_pointage.empty:
        df_p = df_pointage.copy()
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
        pts = df_p[(df_p['Date'] >= date_debut) & (df_p['Date'] <= date_fin) & (df_p['Nom'].isin(noms_f))]
        for _, r in pts.iterrows():
            col_name = r['Date'].strftime("%d/%m")
            if r['Nom'] in df_grille.index and col_name in df_grille.columns:
                df_grille.at[r['Nom'], col_name] = r['Heures']

    grille_editee = st.data_editor(df_grille, use_container_width=True, key=f"editor_{choix_grp}_{mois_c}")
    
    if st.button("💾 ENREGISTRER LE POINTAGE - ETABLISSEMENT GORA MBAYE", type="primary"):
        df_gb = charger_df('pointage.csv')
        df_gb['Date'] = pd.to_datetime(df_gb['Date'], errors='coerce')
        
        # Supprimer les anciens enregistrements pour ce groupe sur cette période précise
        df_gb = df_gb[~((df_gb['Date'] >= date_debut) & (df_gb['Date'] <= date_fin) & (df_gb['Nom'].isin(noms_f)))]
        
        news = []
        for n in grille_editee.index:
            for j_col in grille_editee.columns:
                h = grille_editee.loc[n, j_col]
                if h > 0:
                    # Retrouver la date réelle à partir de JJ/MM
                    jour, mois_d = map(int, j_col.split('/'))
                    # Déterminer si le jour appartient au mois précédent (26-31) ou actuel (01-25)
                    annee_d = annee_c
                    if mois_c == 1 and mois_d == 12: annee_d = annee_c - 1
                    elif mois_d < mois_c and not (mois_c == 1): annee_d = annee_c
                    
                    dt = datetime(annee_d, mois_d, jour)
                    news.append({'Date': dt.strftime("%Y-%m-%d"), 'Semaine': dt.isocalendar()[1], 'Nom': n, 'Heures': h})
        
        if news:
            df_final = pd.concat([df_gb, pd.DataFrame(news)], ignore_index=True)
            df_final.to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
            st.toast("Pointage validé !", icon="🏗️")
            st.rerun()

    # --- RAPPORTS ---
    st.divider()
    st.header(f"📊 Bilan Salaires : {mois_noms[mois_c-1]} {annee_c}")

    def f_int(x): return f"{int(x):,}".replace(",", " ")

    if not df_pointage.empty:
        df_c = charger_df('pointage.csv')
        df_c['Date'] = pd.to_datetime(df_c['Date'], errors='coerce')
        # Fusion avec ouvriers pour avoir fonction et tarifs
        df_c = df_c.merge(df_ouvriers, left_on='Nom', right_on='nom')
        
        # Calcul des HS par semaine (seuil 48h)
        df_c = df_c.sort_values(['Nom', 'Date'])
        df_c['Cumul_Sem'] = df_c.groupby(['Nom', 'Semaine'])['Heures'].cumsum()
        
        def split_hs(r):
            p = r['Cumul_Sem'] - r['Heures']
            if p >= 48: return 0, r['Heures']
            if r['Cumul_Sem'] > 48: return 48-p, r['Heures']-(48-p)
            return r['Heures'], 0
        
        df_c[['HN', 'HS']] = df_c.apply(lambda r: pd.Series(split_hs(r)), axis=1)
        df_c['Brut'] = (df_c['HN'] * df_c['tarif_hn']) + (df_c['HS'] * df_c['tarif_hs'])
        
        # Filtrage sur la période comptable
        df_r = df_c[(df_c['Date'] >= date_debut) & (df_c['Date'] <= date_fin)]
        
        df_ac = charger_df('acomptes.csv')
        ac_sum = pd.Series(dtype=float)
        if not df_ac.empty:
            df_ac['Date'] = pd.to_datetime(df_ac['Date'], errors='coerce')
            ac_sum = df_ac[(df_ac['Date'] >= date_debut) & (df_ac['Date'] <= date_fin)].groupby('Nom')['Montant'].sum()

        if not df_r.empty:
            bilan = df_r.groupby(['groupe', 'Nom', 'fonction']).agg({'HN':'sum', 'HS':'sum', 'Brut':'sum'}).reset_index()
            bilan['Acomptes'] = bilan['Nom'].map(ac_sum).fillna(0)
            bilan['Net'] = bilan['Brut'] - bilan['Acomptes']

            for g in sorted(bilan['groupe'].unique()):
                with st.expander(f"📁 Équipe : {g}", expanded=True):
                    b_g = bilan[bilan['groupe'] == g].drop(columns='groupe')
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total HN", f"{int(b_g['HN'].sum())} h")
                    m2.metric("Total HS", f"{int(b_g['HS'].sum())} h")
                    m3.metric("Total Net", f"{f_int(b_g['Net'].sum())}")
                    st.dataframe(b_g.set_index('Nom').map(f_int), use_container_width=True)

            st.divider()
            col_ex1, col_ex2 = st.columns([3, 1])
            with col_ex1:
                st.metric("💰 TOTAL GLOBAL À PAYER", f"{f_int(bilan['Net'].sum())} FCFA")
            with col_ex2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    bilan.to_excel(writer, index=False, sheet_name='Paie_Gora_Mbaye')
                st.download_button("📥 EXPORT EXCEL", buffer, f"Paie_Ets_Gora_Mbaye_{mois_c}.xlsx")
