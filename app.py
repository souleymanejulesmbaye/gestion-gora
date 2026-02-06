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

# --- FONCTIONS FICHIERS AVEC AUTO-RÉPARATION ---
def initialiser_fichiers():
    colonnes = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in colonnes.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

def charger_df(f):
    initialiser_fichiers()
    try:
        df = pd.read_csv(f, sep=';', encoding='utf-8-sig')
        # Sécurité : Si le fichier est vide ou corrompu (KeyError), on renvoie un DF vide avec les bonnes colonnes
        if f == 'pointage.csv' and 'Date' not in df.columns:
            return pd.DataFrame(columns=['Date', 'Semaine', 'Nom', 'Heures'])
        return df
    except:
        return pd.DataFrame()

def sauvegarder_df(df, f):
    df.to_csv(f, index=False, sep=';', encoding='utf-8-sig')

# Lancer l'initialisation au démarrage
initialiser_fichiers()

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
    
    dict_dates = {d.strftime("%Y-%m-%d"): d.strftime("%d/%m") for d in dates_periode}
    dict_inv = {v: k for k, v in dict_dates.items()}
    
    grille = pd.DataFrame(0, index=noms_g, columns=list(dict_dates.values()))
    
    df_p = charger_df('pointage.csv')
    if not df_p.empty and 'Date' in df_p.columns:
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce')
        df_p_valide = df_p.dropna(subset=['Date'])
        for _, r in df_p_valide[df_p_valide['Nom'].isin(noms_g)].iterrows():
            d_reel = r['Date'].strftime("%Y-%m-%d")
            if d_reel in dict_dates:
                grille.at[r['Nom'], dict_dates[d_reel]] = int(r['Heures'])

    st.subheader(f"Saisie : {choix_g} ({d_debut.strftime('%d/%m')} au {d_fin.strftime('%d/%m')})")
    edits = st.data_editor(grille, use_container_width=True, key=f"ed_{choix_g}_{mois_c}")

    if st.button(f"💾 ENREGISTRER LE POINTAGE : {choix_g}", type="primary", use_container_width=True):
        df_all = charger_df('pointage.csv')
        
        # Sécurité renforcée pour KeyError
        if 'Date' not in df_all.columns:
            df_all = pd.DataFrame(columns=['Date', 'Semaine', 'Nom', 'Heures'])
        else:
            df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        
        mask = (df_all['Nom'].isin(noms_g)) & (df_all['Date'] >= d_debut) & (df_all['Date'] <= d_fin)
        df_all = df_all[~mask].dropna(subset=['Date'])
        
        nouveaux = []
        for nom in edits.index:
            for col_jjmm in edits.columns:
                try:
                    h = int(edits.at[nom, col_jjmm])
                    if h > 0:
                        date_reelle = dict_inv[col_jjmm]
                        dt_obj = pd.to_datetime(date_reelle)
                        nouveaux.append({
                            'Date': date_reelle, 
                            'Semaine': dt_obj.isocalendar()[1], 
                            'Nom': nom, 
                            'Heures': h
                        })
                except: continue
        
        df_final = pd.concat([df_all, pd.DataFrame(nouveaux)], ignore_index=True)
        sauvegarder_df(df_final, 'pointage.csv')
        st.success(f"✅ Enregistré avec succès !")
        st.rerun()

# --- BILAN ---
st.divider()
df_p_view = charger_df('pointage.csv')
if not df_p_view.empty and 'Date' in df_p_view.columns and not df_o.empty:
    df_p_view['Date'] = pd.to_datetime(df_p_view['Date'], errors='coerce')
    df_m = df_p_view.dropna(subset=['Date'])
    df_m = df_m[(df_m['Date'] >= d_debut) & (df_m['Date'] <= d_fin)]
    
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
            total_paye += dg['Brut'].sum()
        
        st.metric("💰 TOTAL GÉNÉRAL", f"{int(total_paye):,} FCFA".replace(',', ' '))
