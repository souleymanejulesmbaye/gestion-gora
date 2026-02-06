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
    .function-sub { background-color: #f1f3f5; color: #1E3A8A; padding: 5px; border-radius: 3px; font-weight: bold; margin-top: 10px; border-left: 4px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS FICHIERS ---
def charger_df(f):
    if not os.path.exists(f): return pd.DataFrame()
    return pd.read_csv(f, sep=';', encoding='utf-8-sig')

def sauvegarder_df(df, f):
    df.to_csv(f, index=False, sep=';', encoding='utf-8-sig')

# Initialisation
for f, cols in {'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'], 
                'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'], 
                'acomptes.csv': ['Date', 'Nom', 'Montant']}.items():
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

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

# --- GESTION DES DATES ---
mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
mois_c = st.sidebar.selectbox("Mois", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
annee_c = st.sidebar.number_input("Année", value=2026)

def obtenir_periode(m, a):
    if m == 1: return datetime(a, 1, 1), datetime(a, 1, 25)
    return datetime(a, m-1, 26), datetime(a, m, 25)

d_debut, d_fin = obtenir_periode(mois_c, annee_c)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.divider()
    with st.expander("➕ Ajouter un ouvrier"):
        with st.form("add_o", clear_on_submit=True):
            n = st.text_input("Nom")
            f = st.text_input("Fonction")
            g = st.text_input("Groupe")
            hn = st.number_input("Tarif HN", 0)
            hs = st.number_input("Tarif HS", 0)
            if st.form_submit_button("Ajouter"):
                df = charger_df('ouvriers.csv')
                sauvegarder_df(pd.concat([df, pd.DataFrame([[n, f, g.upper(), hn, hs]], columns=df.columns)]), 'ouvriers.csv')
                st.rerun()

# --- INTERFACE DE POINTAGE ---
st.markdown('<div class="main-title">GESTION DES POINTAGES - ETS GORA MBAYE</div>', unsafe_allow_html=True)
df_o = charger_df('ouvriers.csv')

if not df_o.empty:
    grps = sorted(df_o['groupe'].unique())
    choix_g = st.selectbox("🎯 CHOISIR LE GROUPE :", grps)
    
    noms_g = df_o[df_o['groupe'] == choix_g]['nom'].tolist()
    dates_periode = pd.date_range(d_debut, d_fin)
    
    # Création du dictionnaire de correspondance Date réelle <-> Libellé JJ/MM
    dict_dates = {d.strftime("%Y-%m-%d"): d.strftime("%d/%m") for d in dates_periode}
    dict_inv = {v: k for k, v in dict_dates.items()}
    
    # Préparation de la grille avec colonnes au format JJ/MM
    grille = pd.DataFrame(0, index=noms_g, columns=list(dict_dates.values()))
    
    df_p = charger_df('pointage.csv')
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
        for _, r in df_p[df_p['Nom'].isin(noms_g)].iterrows():
            d_reel = r['Date'].strftime("%Y-%m-%d")
            if d_reel in dict_dates:
                col_jjmm = dict_dates[d_reel]
                grille.at[r['Nom'], col_jjmm] = int(r['Heures'])

    st.subheader(f"Saisie des heures : {choix_g} (Période du {d_debut.strftime('%d/%m')} au {d_fin.strftime('%d/%m')})")
    
    # Utilisation d'une clé dynamique pour forcer le rafraîchissement par groupe
    edits = st.data_editor(grille, use_container_width=True, key=f"editor_{choix_g}_{mois_c}")

    if st.button(f"💾 ENREGISTRER LE POINTAGE : {choix_g}", type="primary", use_container_width=True):
        df_all = charger_df('pointage.csv')
        df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        
        # Supprimer les anciens pointages de ce groupe sur cette période
        mask = (df_all['Nom'].isin(noms_g)) & (df_all['Date'] >= d_debut) & (df_all['Date'] <= d_fin)
        df_all = df_all[~mask]
        
        nouveaux = []
        for nom in edits.index:
            for col_jjmm in edits.columns:
                h = edits.at[nom, col_jjmm]
                if h > 0:
                    date_reelle_str = dict_inv[col_jjmm]
                    dt_obj = pd.to_datetime(date_reelle_str)
                    nouveaux.append({
                        'Date': date_reelle_str, 
                        'Semaine': dt_obj.isocalendar()[1], 
                        'Nom': nom, 
                        'Heures': int(h)
                    })
        
        if nouveaux:
            df_final = pd.concat([df_all, pd.DataFrame(nouveaux)], ignore_index=True)
            sauvegarder_df(df_final, 'pointage.csv')
            st.success(f"✅ Pointage du groupe {choix_g} enregistré avec succès !")
            st.rerun()
        else:
            st.warning("Veuillez saisir des heures avant d'enregistrer.")

# --- BILAN DES PAIES ---
st.divider()
st.header("📊 RÉCAPITULATIF DES PAIES")
df_p_view = charger_df('pointage.csv')
if not df_p_view.empty and not df_o.empty:
    df_p_view['Date'] = pd.to_datetime(df_p_view['Date'], errors='coerce')
    df_m = df_p_view[(df_p_view['Date'] >= d_debut) & (df_p_view['Date'] <= d_fin)]
    
    if not df_m.empty:
        df_res = df_m.merge(df_o, left_on='Nom', right_on='nom')
        df_res['Cumul_S'] = df_res.groupby(['Nom', 'Semaine'])['Heures'].transform('cumsum')
        
        def calc_h(r):
            p = r['Cumul_S'] - r['Heures']
            if p >= 48: return 0, r['Heures']
            if r['Cumul_S'] > 48: return (48-p), (r['Cumul_S']-48)
            return r['Heures'], 0
            
        df_res[['HN', 'HS']] = df_res.apply(lambda x: pd.Series(calc_h(x)), axis=1)
        df_res['Brut'] = (df_res['HN'] * df_res['tarif_hn']) + (df_res['HS'] * df_res['tarif_hs'])
        
        recap = df_res.groupby(['groupe', 'Nom', 'fonction']).agg({'HN':'sum', 'HS':'sum', 'Brut':'sum'}).reset_index()
        
        total_paye = 0
        for g in sorted(recap['groupe'].unique()):
            st.markdown(f'<div class="group-header">🏢 GROUPE : {g}</div>', unsafe_allow_html=True)
            dg = recap[recap['groupe'] == g]
            
            st.table(dg.drop(columns='groupe').assign(
                HN=dg['HN'].astype(int), HS=dg['HS'].astype(int),
                Brut=dg['Brut'].astype(int).map('{:,}'.format).str.replace(',', ' ')
            ))
            
            st.markdown('<div class="function-sub">Heures par Métier</div>', unsafe_allow_html=True)
            df_func = dg.groupby('fonction').agg({'HN':'sum', 'HS':'sum'}).reset_index()
            st.table(df_func.assign(HN=df_func['HN'].astype(int), HS=df_func['HS'].astype(int)))
            
            total_paye += dg['Brut'].sum()
        
        st.divider()
        st.metric("🏗️ TOTAL GÉNÉRAL À PAYER", f"{int(total_paye):,} FCFA".replace(',', ' '))
else:
    st.info("Aucun pointage trouvé pour cette période.")
