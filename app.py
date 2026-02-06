import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import os
import io

# --- CONFIGURATION DU DESIGN ---
st.set_page_config(
    page_title="ÉTABLISSEMENT GORA MBAYE - Système de Pointage",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS pour un look "Établissement" sérieux et pro
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
        'ouvriers.csv': ['nom', 'groupe', 'tarif_hn', 'tarif_hs'],
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
    mois_c = st.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
    annee_c = st.number_input("Année", value=datetime.now().year)

    st.divider()
    tab1, tab2 = st.tabs(["👤 Ouvriers", "💵 Acomptes"])
    
    with tab1:
        with st.form("o", clear_on_submit=True):
            n = st.text_input("Nom & Prénom")
            g = st.text_input("Équipe / Chantier")
            hn = st.number_input("Tarif HN", 0)
            hs = st.number_input("Tarif HS", 0)
            if st.form_submit_button("➕ Ajouter l'Ouvrier"):
                if n and g:
                    df = charger_df('ouvriers.csv')
                    pd.concat([df, pd.DataFrame([[n.strip(), g.strip(), hn, hs]], columns=df.columns)], ignore_index=True).to_csv('ouvriers.csv', index=False, sep=';', encoding='utf-8-sig')
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
    col_t1, col_t2, col_t3 = st.columns([1.5, 1, 1.5])
    with col_t1:
        st.subheader("📝 Fiche de Pointage")
    with col_t2:
        grps = sorted(df_ouvriers['groupe'].unique())
        choix_grp = st.selectbox("Équipe :", grps)
    with col_t3:
        search = st.text_input("🔍 Rechercher...", placeholder="Nom de l'ouvrier...")

    # Filtrage
    mask = df_ouvriers['groupe'] == choix_grp
    if search:
        mask = mask & (df_ouvriers['nom'].str.contains(search, case=False, na=False))
    
    noms_f = df_ouvriers[mask]['nom'].tolist()
    jours = [f"{d:02d}" for d in range(1, calendar.monthrange(annee_c, mois_c)[1] + 1)]
    
    df_grille = pd.DataFrame(0.0, index=noms_f, columns=jours)
    if not df_pointage.empty:
        df_p = df_pointage.copy()
        df_p['Date'] = pd.to_datetime(df_p['Date'], format='mixed')
        pts = df_p[(df_p['Date'].dt.month == mois_c) & (df_p['Date'].dt.year == annee_c) & (df_p['Nom'].isin(noms_f))]
        for _, r in pts.iterrows():
            if r['Nom'] in df_grille.index: 
                df_grille.at[r['Nom'], f"{r['Date'].day:02d}"] = r['Heures']

    grille_editee = st.data_editor(df_grille, use_container_width=True)
    
    if st.button("💾 ENREGISTRER LE POINTAGE - ETABLISSEMENT GORA MBAYE", type="primary"):
        df_gb = charger_df('pointage.csv')
        df_gb['Date'] = pd.to_datetime(df_gb['Date'], format='mixed')
        df_gb = df_gb[~((df_gb['Date'].dt.month == mois_c) & (df_gb['Date'].dt.year == annee_c) & (df_gb['Nom'].isin(noms_f)))]
        
        news = []
        for n in grille_editee.index:
            for j in grille_editee.columns:
                h = grille_editee.loc[n, j]
                if h > 0:
                    dt = datetime(annee_c, mois_c, int(j))
                    news.append({'Date': dt.strftime("%Y-%m-%d"), 'Semaine': dt.isocalendar()[1], 'Nom': n, 'Heures': h})
        
        pd.concat([df_gb, pd.DataFrame(news)], ignore_index=True).to_csv('pointage.csv', index=False, sep=';', encoding='utf-8-sig')
        st.toast("Pointage validé !", icon="🏗️")
        st.rerun()

    # --- RAPPORTS ---
    st.divider()
    st.header("📊 Bilan Mensuel des Salaires")

    def f_int(x): return f"{int(x):,}".replace(",", " ")

    if not df_pointage.empty:
        df_c = charger_df('pointage.csv')
        df_c['Date'] = pd.to_datetime(df_c['Date'], format='mixed')
        df_c = df_c.merge(df_ouvriers, left_on='Nom', right_on='nom')
        df_c['Cumul_Sem'] = df_c.groupby(['Nom', 'Semaine'])['Heures'].cumsum()
        
        def split_hs(r):
            p = r['Cumul_Sem'] - r['Heures']
            if p >= 48: return 0, r['Heures']
            if r['Cumul_Sem'] > 48: return 48-p, r['Heures']-(48-p)
            return r['Heures'], 0
        
        df_c[['HN', 'HS']] = df_c.apply(lambda r: pd.Series(split_hs(r)), axis=1)
        df_c['Brut'] = (df_c['HN'] * df_c['tarif_hn']) + (df_c['HS'] * df_c['tarif_hs'])
        df_r = df_c[(df_c['Date'].dt.month == mois_c) & (df_c['Date'].dt.year == annee_c)]
        
        df_ac = charger_df('acomptes.csv')
        ac_sum = pd.Series(dtype=float)
        if not df_ac.empty:
            df_ac['Date'] = pd.to_datetime(df_ac['Date'], format='mixed')
            ac_sum = df_ac[(df_ac['Date'].dt.month == mois_c) & (df_ac['Date'].dt.year == annee_c)].groupby('Nom')['Montant'].sum()

        if not df_r.empty:
            bilan = df_r.groupby(['groupe', 'Nom']).agg({'HN':'sum', 'HS':'sum', 'Brut':'sum'}).reset_index()
            bilan['Acomptes'] = bilan['Nom'].map(ac_sum).fillna(0)
            bilan['Net'] = bilan['Brut'] - bilan['Acomptes']

            for g in sorted(bilan['groupe'].unique()):
                with st.expander(f"📁 Équipe : {g}", expanded=True):
                    b_g = bilan[bilan['groupe'] == g].set_index('Nom').drop(columns='groupe')
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Heures HN", f"{int(b_g['HN'].sum())} h")
                    m2.metric("Total Heures HS", f"{int(b_g['HS'].sum())} h")
                    m3.metric("Net à Régler", f"{f_int(b_g['Net'].sum())}")
                    st.dataframe(b_g.map(f_int), use_container_width=True)

            st.divider()
            col_ex1, col_ex2 = st.columns([3, 1])
            with col_ex1:
                st.metric("💰 TOTAL GLOBAL À PAYER", f"{f_int(bilan['Net'].sum())}")
            with col_ex2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    bilan.to_excel(writer, index=False, sheet_name='Paie_Gora_Mbaye')
                st.download_button("📥 EXPORT EXCEL", buffer, f"Paie_Ets_Gora_Mbaye_{mois_c}.xlsx")
