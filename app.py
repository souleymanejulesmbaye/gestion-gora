import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
    try:
        return pd.read_csv(f, sep=';', encoding='utf-8-sig')
    except:
        return pd.DataFrame()

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

# --- INTERFACE PRINCIPALE (SIDEBAR) ---
st.markdown('<div class="main-title">🏗️ SYSTÈME DE GESTION - ETS GORA MBAYE</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Administration")
    mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    mois_c = st.selectbox("Mois de Paie", range(1, 13), index=datetime.now().month-1, format_func=lambda x: mois_noms[x-1])
    annee_c = st.number_input("Année", value=datetime.now().year)
    date_debut, date_fin = obtenir_periode(mois_c, annee_c)
    st.info(f"📅 Période : {date_debut.strftime('%d/%m')} au {date_fin.strftime('%d/%m/%Y')}")

    st.divider()
    t1, t2, t3 = st.tabs(["➕ Ajouter", "✏️ Gérer", "💵 Acomptes"])
    
    with t1: # AJOUTER UN OUVRIER
        with st.form("o", clear_on_submit=True):
            n = st.text_input("Nom & Prénom")
            f = st.text_input("Fonction (ex: Électricien)")
            g = st.text_input("Groupe / Équipe")
            hn, hs = st.number_input("Tarif HN", 0), st.number_input("Tarif HS", 0)
            if st.form_submit_button("Ajouter"):
                if n and g:
                    df = charger_df('ouvriers.csv')
                    sauvegarder_df(pd.concat([df, pd.DataFrame([[n.strip(), f.strip(), g.strip(), hn, hs]], columns=df.columns)], ignore_index=True), 'ouvriers.csv')
                    st.rerun()

    with t2: # MODIFIER OU SUPPRIMER
        df_edit = charger_df('ouvriers.csv')
        if not df_edit.empty:
            nom_sel = st.selectbox("Choisir un ouvrier", df_edit['nom'].tolist())
            info = df_edit[df_edit['nom'] == nom_sel].iloc[0]
            with st.form("edit_f"):
                new_f = st.text_input("Fonction", value=info['fonction'])
                new_g = st.text_input("Groupe", value=info['groupe'])
                new_hn = st.number_input("Tarif HN", value=int(info['tarif_hn']))
                new_hs = st.number_input("Tarif HS", value=int(info['tarif_hs']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Sauver"):
                    df_edit.loc[df_edit['nom'] == nom_sel, ['fonction', 'groupe', 'tarif_hn', 'tarif_hs']] = [new_f, new_g, new_hn, new_hs]
                    sauvegarder_df(df_edit, 'ouvriers.csv')
                    st.rerun()
                if c2.form_submit_button("🗑️ Suppr."):
                    df_edit = df_edit[df_edit['nom'] != nom_sel]
                    sauvegarder_df(df_edit, 'ouvriers.csv')
                    st.rerun()

    with t3: # ACOMPTES
        df_o = charger_df('ouvriers.csv')
        if not df_o.empty:
            with st.form("a", clear_on_submit=True):
                nom_a = st.selectbox("Ouvrier", sorted(df_o['nom'].tolist()))
                mont_a = st.number_input("Montant", 0)
                if st.form_submit_button("Valider"):
                    df = charger_df('acomptes.csv')
                    sauvegarder_df(pd.concat([df, pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), nom_a, mont_a]], columns=df.columns)], ignore_index=True), 'acomptes.csv')
                    st.success("Acompte enregistré")

# --- GRILLE DE POINTAGE ---
df_ouvriers = charger_df('ouvriers.csv')
df_pointage = charger_df('pointage.csv')

if not df_ouvriers.empty:
    grps = sorted(df_ouvriers['groupe'].unique())
    choix_g = st.selectbox("🎯 Sélectionner le groupe à pointer :", grps)
    noms_f = df_ouvriers[df_ouvriers['groupe'] == choix_g]['nom'].tolist()
    liste_dates = pd.date_range(date_debut, date_fin)
    
    grille = pd.DataFrame(0.0, index=noms_f, columns=[d.strftime("%Y-%m-%d") for d in liste_dates])
    if not df_pointage.empty:
        df_p = df_pointage.copy()
        df_p['Date'] = pd.to_datetime(df_p['Date'], errors='coerce').dt.strftime("%Y-%m-%d")
        for _, r in df_p[df_p['Nom'].isin(noms_f)].iterrows():
            if r['Date'] in grille.columns: grille.at[r['Nom'], r['Date']] = r['Heures']

    grille_visuelle = grille.copy()
    grille_visuelle.columns = [d.strftime("%d/%m") for d in liste_dates]
    st.subheader(f"📝 Pointage : {choix_g}")
    edits = st.data_editor(grille_visuelle, use_container_width=True)

    if st.button("💾 ENREGISTRER LE POINTAGE", type="primary"):
        df_base = charger_df('pointage.csv')
        df_base['Date'] = pd.to_datetime(df_base['Date'], errors='coerce')
        df_base = df_base[~((df_base['Date'] >= date_debut) & (df_base['Date'] <= date_fin) & (df_base['Nom'].isin(noms_f)))]
        nouveaux = []
        for nom in edits.index:
            for i, h in enumerate(edits.loc[nom]):
                if h > 0:
                    d_reelle = liste_dates[i]
                    nouveaux.append({'Date': d_reelle.strftime("%Y-%m-%d"), 'Semaine': d_reelle.isocalendar()[1], 'Nom': nom, 'Heures': h})
        sauvegarder_df(pd.concat([df_base, pd.DataFrame(nouveaux)], ignore_index=True), 'pointage.csv')
        st.toast("Enregistré !")
        st.rerun()

# --- BILAN FINAL ---
st.divider()
st.header("📊 BILAN PAR GROUPE ET FONCTION")

if not df_pointage.empty and not df_ouvriers.empty:
    df_c = charger_df('pointage.csv')
    df_c['Date'] = pd.to_datetime(df_c['Date'], errors='coerce')
    df_c = df_c[(df_c['Date'] >= date_debut) & (df_c['Date'] <= date_fin)]
    
    if not df_c.empty:
        df_c = df_c.merge(df_ouvriers, left_on='Nom', right_on='nom')
        df_c['Cumul_Semaine'] = df_c.groupby(['Nom', 'Semaine'])['Heures'].transform('cumsum')
        def calcul_hn_hs(row):
            prec = row['Cumul_Semaine'] - row['Heures']
            if prec >= 48: return 0, row['Heures']
            if row['Cumul_Semaine'] > 48: return (48 - prec), (row['Cumul_Semaine'] - 48)
            return row['Heures'], 0
        
        df_c[['HN', 'HS']] = df_c.apply(lambda r: pd.Series(calcul_hn_hs(r)), axis=1)
        df_c['Brut'] = (df_c['HN'] * df_c['tarif_hn']) + (df_c['HS'] * df_c['tarif_hs'])
        
        df_ac = charger_df('acomptes.csv')
        df_ac['Date'] = pd.to_datetime(df_ac['Date'], errors='coerce')
        ac_mois = df_ac[(df_ac['Date'] >= date_debut) & (df_ac['Date'] <= date_fin)].groupby('Nom')['Montant'].sum()

        bilan = df_c.groupby(['groupe', 'Nom', 'fonction']).agg({'HN':'sum', 'HS':'sum', 'Brut':'sum'}).reset_index()
        bilan['Acomptes'] = bilan['Nom'].map(ac_mois).fillna(0)
        bilan['Net'] = bilan['Brut'] - bilan['Acomptes']

        total_general = 0
        for g in sorted(bilan['groupe'].unique()):
            st.markdown(f'<div class="group-header">🏢 GROUPE : {g}</div>', unsafe_allow_html=True)
            df_g = bilan[bilan['groupe'] == g]
            
            st.markdown('<div class="function-sub">Détail Individuel</div>', unsafe_allow_html=True)
            st.table(df_g.drop(columns='groupe').assign(HN=df_g['HN'].astype(int), HS=df_g['HS'].astype(int), Brut=df_g['Brut'].map('{:,.0f}'.format), Net=df_g['Net'].map('{:,.0f}'.format)))

            st.markdown('<div class="function-sub">Sous-total par Fonction</div>', unsafe_allow_html=True)
            bilan_f = df_g.groupby('fonction').agg({'HN':'sum', 'HS':'sum', 'Net':'sum'}).reset_index()
            st.table(bilan_f.assign(HN=bilan_f['HN'].astype(int), HS=bilan_f['HS'].astype(int), Net=bilan_f['Net'].map('{:,.0f} FCFA'.format)))
            
            total_g = df_g['Net'].sum()
            st.write(f"**Total Net {g} : {int(total_g):,} FCFA**".replace(',', ' '))
            total_general += total_g

        st.divider()
        st.metric("🏗️ TOTAL GÉNÉRAL À PAYER", f"{int(total_general):,} FCFA".replace(',', ' '))
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            bilan.to_excel(writer, index=False, sheet_name='Paie_Gora_Mbaye')
        st.download_button("📥 EXPORTER EXCEL", buffer.getvalue(), f"Bilan_Gora_{mois_noms[mois_c-1]}.xlsx")
