import streamlit as st
import pandas as pd
from datetime import datetime
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
    .group-header {
        background-color: #1E3A8A; color: white; padding: 10px;
        border-radius: 5px; margin-top: 25px; font-weight: bold; font-size: 20px;
    }
    .function-sub {
        background-color: #e9ecef; color: #1E3A8A; padding: 5px 10px;
        border-radius: 3px; margin-top: 10px; font-weight: bold; border-left: 5px solid #1E3A8A;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES FICHIERS ---
def initialiser_fichiers():
    fichiers = {
        'ouvriers.csv': ['nom', 'fonction', 'groupe', 'tarif_hn', 'tarif_hs'],
        'pointage.csv': ['Date', 'Semaine', 'Nom', 'Heures'],
        'acomptes.csv': ['Date', 'Nom', 'Montant']
    }
    for f, cols in fichiers.items():
        if not os.path.exists(f) or os.stat(f).st_size == 0:
            pd.DataFrame(columns=cols).to_csv(f, index=False, sep=';', encoding='utf-8-sig')

def charger_df(f): 
    if not os.path.exists(f): return pd.DataFrame()
    return pd.read_csv(f, sep=';', encoding='utf-8-sig')

def sauvegarder_df(df, f): 
    df.to_csv(f, index=False, sep=';', encoding='utf-8-sig')

initialiser_fichiers()

# --- SYSTÈME DE CONNEXION ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background-color:white;padding:2rem;border-radius:10px;border:1px solid #ddd">', unsafe_allow_html=True)
        st.subheader("🔐 Accès Direction - ETS GORA MBAYE")
        user = st.text_input("Identifiant")
        pwd = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if user == "admin" and pwd == "GORA2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Identifiant ou mot de passe incorrect")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- LOGIQUE COMPTABLE ---
def obtenir_periode(mois, annee):
    if mois == 1: debut, fin = datetime(annee, 1, 1), datetime(annee, 1, 25)
    elif mois == 12: debut, fin = datetime(annee, 11, 26), datetime(annee, 12, 31)
    else: debut, fin = datetime(annee, mois-1, 26), datetime(annee, mois, 25)
    return debut, fin

# --- INTERFACE PRINCIPALE ---
st.markdown('<div class="main-title">🏗️ GESTION ADMINISTRATIVE - ETS GORA MBAYE</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Paramètres")
    mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    mois_c = st.selectbox("Mois de Paie", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
    annee_c = st.number_input("Année", value=datetime.now().year)
    date_debut, date_fin = obtenir_periode(mois_c, annee_c)
    
    st.divider()
    t1, t2, t3 = st.tabs(["➕ Ajouter", "✏️ Gérer", "💵 Acomptes"])
    
    with t1:
        with st.form("o", clear_on_submit=True):
            n = st.text_input("Nom & Prénom")
            f = st.text_input("Fonction")
            g = st.text_input("Groupe")
            hn = st.number_input("Tarif HN", 0)
            hs = st.number_input("Tarif HS", 0)
            if st.form_submit_button("Valider"):
                if n and g:
                    df = charger_df('ouvriers.csv')
                    new_o = pd.DataFrame([[n.strip(), f.strip(), g.strip().upper(), int(hn), int(hs)]], columns=df.columns)
                    sauvegarder_df(pd.concat([df, new_o], ignore_index=True), 'ouvriers.csv')
                    st.rerun()

    with t2:
        df_edit = charger_df('ouvriers.csv')
        if not df_edit.empty:
            nom_sel = st.selectbox("Choisir l'ouvrier", df_edit['nom'].tolist())
            idx = df_edit[df_edit['nom'] == nom_sel].index[0]
            with st.form("edit"):
                f_e = st.text_input("Fonction", df_edit.at[idx, 'fonction'])
                g_e = st.text_input("Groupe", df_edit.at[idx, 'groupe'])
                hn_e = st.number_input("Tarif HN", value=int(df_edit.at[idx, 'tarif_hn']))
                hs_e = st.number_input("Tarif HS", value=int(df_edit.at[idx, 'tarif_hs']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Sauver"):
                    df_edit.at[idx, 'fonction'] = f_e.strip()
                    df_edit.at[idx, 'groupe'] = g_e.strip().upper()
                    df_edit.at[idx, 'tarif_hn'] = int(hn_e)
                    df_edit.at[idx, 'tarif_hs'] = int(hs_e)
                    sauvegarder_df(df_edit, 'ouvriers.csv')
                    st.rerun()
                if c2.form_submit_button("🗑️ Suppr."):
                    sauvegarder_df(df_edit.drop(idx), 'ouvriers.csv')
                    st.rerun()

    with t3:
        df_o = charger_df('ouvriers.csv')
        if not df_o.empty:
            nom_a = st.selectbox("Ouvrier", sorted(df_o['nom'].tolist()), key="ac")
            mont_a = st.number_input("Montant", 0)
            if st.button("Valider l'Acompte"):
                df_ac = charger_df('acomptes.csv')
                new_ac = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), nom_a, int(mont_a)]], columns=df_ac.columns)
                sauvegarder_df(pd.concat([df_ac, new_ac], ignore_index=True), 'acomptes.csv')
                st.success("Enregistré")

# --- POINTAGE ---
df_ouvriers = charger_df('ouvriers.csv')
df_pointage = charger_df('pointage.csv')

if not df_ouvriers.empty:
    liste_groupes = sorted(df_ouvriers['groupe'].unique())
    choix_g = st.selectbox("🎯 Sélectionner le Groupe à pointer :", liste_groupes)
    
    ouvriers_groupe = df_ouvriers[df_ouvriers['groupe'] == choix_g]['nom'].tolist()
    jours = pd.date_range(date_debut, date_fin)
    
    # Création grille vide
    grille = pd.DataFrame(0, index=ouvriers_groupe, columns=[d.strftime("%Y-%m-%d") for d in jours])
    
    # Remplir avec l'existant
    if not df_pointage.empty:
        df_p = df_pointage.copy()
        df_p['Date'] = pd.to_datetime(df_p['Date']).dt.strftime("%Y-%m-%d")
        for _, r in df_p[df_p['Nom'].isin(ouvriers_groupe)].iterrows():
            if r['Date'] in grille.columns:
                grille.at[r['Nom'], r['Date']] = int(r['Heures'])

    grille_visuelle = grille.copy()
    grille_visuelle.columns = [d.strftime("%d/%m") for d in jours]
    
    st.subheader(f"📝 Saisie : {choix_g}")
    edits = st.data_editor(grille_visuelle, use_container_width=True)

    if st.button("💾 ENREGISTRER LE POINTAGE", type="primary"):
        df_p_actuel = charger_df('pointage.csv')
        df_p_actuel['Date'] = pd.to_datetime(df_p_actuel['Date'])
        
        # Supprimer l'ancien pour ce groupe/période
        df_p_actuel = df_p_actuel[~((df_p_actuel['Date'] >= date_debut) & (df_p_actuel['Date'] <= date_fin) & (df_p_actuel['Nom'].isin(ouvriers_groupe)))]
        
        nouveaux = []
        for nom in edits.index:
            for i, h in enumerate(edits.loc[nom]):
                if int(h) > 0:
                    d_reelle = jours[i]
                    nouveaux.append({
                        'Date': d_reelle.strftime("%Y-%m-%d"),
                        'Semaine': int(d_reelle.isocalendar()[1]),
                        'Nom': nom,
                        'Heures': int(h)
                    })
        
        if nouveaux:
            df_final = pd.concat([df_p_actuel, pd.DataFrame(nouveaux)], ignore_index=True)
            sauvegarder_df(df_final, 'pointage.csv')
            st.success(f"Pointage {choix_g} enregistré !")
            st.rerun()
        else:
            st.warning("Aucune heure saisie.")

# --- BILAN ---
st.divider()
st.header("📊 BILAN DES PAIES")

df_p_bilan = charger_df('pointage.csv')
if not df_p_bilan.empty and not df_ouvriers.empty:
    df_p_bilan['Date'] = pd.to_datetime(df_p_bilan['Date'])
    df_p_bilan = df_p_bilan[(df_p_bilan['Date'] >= date_debut) & (df_p_bilan['Date'] <= date_fin)]
    
    if not df_p_bilan.empty:
        df_bilan = df_p_bilan.merge(df_ouvriers, left_on='Nom', right_on='nom')
        
        # Calcul HN/HS
        df_bilan['Cumul_Semaine'] = df_bilan.groupby(['Nom', 'Semaine'])['Heures'].transform('cumsum')
        def split_h(r):
            prev = r['Cumul_Semaine'] - r['Heures']
            if prev >= 48: return 0, r['Heures']
            if r['Cumul_Semaine'] > 48: return (48 - prev), (r['Cumul_Semaine'] - 48)
            return r['Heures'], 0
        
        df_bilan[['HN', 'HS']] = df_bilan.apply(lambda x: pd.Series(split_h(x)), axis=1)
        df_bilan['Brut'] = (df_bilan['HN'] * df_bilan['tarif_hn']) + (df_bilan['HS'] * df_bilan['tarif_hs'])
        
        # Acomptes
        df_ac = charger_df('acomptes.csv')
        df_ac['Date'] = pd.to_datetime(df_ac['Date'])
        ac_val = df_ac[(df_ac['Date'] >= date_debut) & (df_ac['Date'] <= date_fin)].groupby('Nom')['Montant'].sum()

        recap = df_bilan.groupby(['groupe', 'Nom', 'fonction']).agg({'HN':'sum', 'HS':'sum', 'Brut':'sum'}).reset_index()
        recap['Acomptes'] = recap['Nom'].map(ac_val).fillna(0).astype(int)
        recap['Net'] = recap['Brut'] - recap['Acomptes']

        total_global = 0
        for g in sorted(recap['groupe'].unique()):
            st.markdown(f'<div class="group-header">🏢 GROUPE : {g}</div>', unsafe_allow_html=True)
            df_g = recap[recap['groupe'] == g]
            
            # Individuel
            st.table(df_g.drop(columns='groupe').assign(
                HN=df_g['HN'].astype(int), HS=df_g['HS'].astype(int),
                Brut=df_g['Brut'].astype(int).map('{:,}'.format).str.replace(',', ' '),
                Net=df_g['Net'].astype(int).map('{:,}'.format).str.replace(',', ' ')
            ))
            
            # Fonctions
            st.markdown('<div class="function-sub">Cumul par Métier</div>', unsafe_allow_html=True)
            st.table(df_g.groupby('fonction').agg({'HN':'sum', 'HS':'sum'}).reset_index().astype(int))
            
            total_g = df_g['Net'].sum()
            st.write(f"**Total Net {g} : {int(total_g):,} FCFA**".replace(',', ' '))
            total_global += total_g
            
        st.divider()
        st.metric("💰 TOTAL GÉNÉRAL", f"{int(total_global):,} FCFA".replace(',', ' '))
