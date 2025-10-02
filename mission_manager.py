import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

st.set_page_config(
    page_title="Gestionnaire de Missions Universitaires",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .mission-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Gestionnaire de Missions Universitaires</h1>', unsafe_allow_html=True)

if 'missions_declarees' not in st.session_state:
    st.session_state.missions_declarees = []
if 'referentiel_df' not in st.session_state:
    st.session_state.referentiel_df = None

# Fonction pour charger le référentiel
def load_referentiel(file_source):
    try:
        if isinstance(file_source, str):
            # Charger depuis un fichier local
            df = pd.read_excel(file_source, sheet_name=0)
        else:
            # Charger depuis un fichier uploadé
            df = pd.read_excel(file_source, sheet_name=0)
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        
        # Supprimer les colonnes vides
        df = df.loc[:, df.columns.notna() & (df.columns != '')]
        
        # Supprimer les lignes vides
        df = df.dropna(how='all')
        
        # Convertir les colonnes texte en string
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        
        return df, None
    except Exception as e:
        return None, str(e)

# Chargement automatique du référentiel si présent
if st.session_state.referentiel_df is None and os.path.exists('referentiel.xlsx'):
    df, error = load_referentiel('referentiel.xlsx')
    if df is not None:
        st.session_state.referentiel_df = df
        st.success("✅ Référentiel chargé automatiquement !")
    else:
        st.warning("⚠️ Erreur lors du chargement automatique du référentiel")

# Option de chargement manuel
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader(
    "Charger un autre référentiel (optionnel)",
    type=['xlsx', 'xls'],
    help="Uploadez un fichier référentiel personnalisé"
)

if uploaded_file is not None:
    df, error = load_referentiel(uploaded_file)
    if df is not None:
        st.session_state.referentiel_df = df
        st.sidebar.success(f"✅ Référentiel personnalisé chargé : {len(df)} lignes")
    else:
        st.sidebar.error(f"❌ Erreur : {error}")

# Interface principale
if st.session_state.referentiel_df is not None:
    df = st.session_state.referentiel_df
    
    st.header("Rechercher une mission")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Décrivez votre mission (ex: j'ai encadré 3 stages)",
            placeholder="Ex: jury these, 5 stages master, direction mémoire...",
            key="search_box"
        )
    
    with col2:
        search_button = st.button("Rechercher", use_container_width=True)
    
    if search_query or search_button:
        if search_query.strip():
            # Extraire le nombre de la phrase
            import re
            nombre_match = re.search(r'\b(\d+)\b', search_query)
            quantite = int(nombre_match.group(1)) if nombre_match else 1
            
            query_lower = search_query.lower()
            
            # Dictionnaire de mots-clés
            keywords_mapping = {
                'stage': ['stage', 'stages', 'stagiaire'],
                'jury': ['jury', 'jurys', 'soutenance', 'soutenances'],
                'thèse': ['thèse', 'theses', 'these', 'doctorat', 'phd'],
                'master': ['master', 'm1', 'm2', 'master 1', 'master 2'],
                'licence': ['licence', 'l1', 'l2', 'l3', 'bachelor'],
                'encadrement': ['encadrement', 'encadrer', 'encadré', 'superviser', 'supervision'],
                'tutorat': ['tutorat', 'tuteur', 'tutoré'],
                'direction': ['direction', 'diriger', 'dirigé', 'directeur'],
                'projet': ['projet', 'projets'],
                'mémoire': ['mémoire', 'memoire'],
                'alternance': ['alternance', 'apprenti'],
                'enseignement': ['enseignement', 'cours', 'td', 'tp', 'cm'],
            }
            
            # Extraire les mots-clés
            extracted_keywords = []
            for main_keyword, synonyms in keywords_mapping.items():
                for synonym in synonyms:
                    if synonym in query_lower:
                        extracted_keywords.append(main_keyword)
                        break
            
            if not extracted_keywords:
                search_terms = [search_query]
            else:
                search_terms = extracted_keywords
            
            # Afficher les informations détectées
            info_parts = []
            if extracted_keywords:
                info_parts.append(f"Mots-clés : {', '.join(extracted_keywords)}")
            if quantite > 1:
                info_parts.append(f"Quantité : {quantite}")
            if info_parts:
                st.info(f"🔍 Détecté → {' | '.join(info_parts)}")
            
            # Recherche
            mask = pd.Series([False] * len(df))
            
            for search_term in search_terms:
                for col in df.columns:
                    if df[col].dtype == 'object':
                        try:
                            mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
                        except:
                            pass
            
            resultats = df[mask]
            
            if len(resultats) > 0:
                st.success(f"✨ {len(resultats)} résultat(s) trouvé(s)")
                
                for idx, row in resultats.iterrows():
                    # Déterminer les colonnes
                    libelle_col = None
                    libelle_court_col = None
                    domaine_col = None
                    heures_col = None
                    
                    for col in df.columns:
                        col_lower = col.lower()
                        if 'libelle' in col_lower and 'court' not in col_lower and libelle_col is None:
                            libelle_col = col
                        elif 'libelle' in col_lower and 'court' in col_lower:
                            libelle_court_col = col
                        elif 'domaine' in col_lower:
                            domaine_col = col
                        elif 'hetd' in col_lower or 'heure' in col_lower:
                            heures_col = col
                    
                    titre = row[libelle_col] if libelle_col and pd.notna(row[libelle_col]) else f"Activité {idx}"
                    
                    with st.expander(f"📌 {titre}", expanded=True):
                        col_info, col_action = st.columns([3, 1])
                        
                        with col_info:
                            if libelle_court_col and pd.notna(row[libelle_court_col]):
                                st.write(f"**Libellé court :** {row[libelle_court_col]}")
                            if domaine_col and pd.notna(row[domaine_col]):
                                st.write(f"**Domaine :** {row[domaine_col]}")
                            if heures_col and pd.notna(row[heures_col]):
                                st.write(f"**Heures unitaires :** {row[heures_col]}")
                        
                        with col_action:
                            # Gérer les heures max
                            heures_max_val = row[heures_col] if heures_col else None
                            if heures_max_val and str(heures_max_val).replace('.','').isdigit():
                                heures_max = float(heures_max_val)
                            else:
                                heures_max = 10.0
                                if heures_max_val:
                                    st.info(f"Heures: {heures_max_val}")
                            
                            # Calculer les heures totales
                            heures_totales = heures_max * quantite
                            
                            if quantite > 1:
                                st.write(f"**Calcul:** {heures_max}h × {quantite} = {heures_totales}h")
                            
                            heures_reelles = st.number_input(
                                "Heures réelles",
                                min_value=0.0,
                                max_value=999.0,
                                value=heures_totales,
                                step=0.5,
                                key=f"heures_{idx}"
                            )
                            
                            if st.button("➕ Ajouter", key=f"add_{idx}", use_container_width=True):
                                mission = {
                                    'libelle': titre,
                                    'libelle_court': row[libelle_court_col] if libelle_court_col and pd.notna(row[libelle_court_col]) else '',
                                    'domaine': row[domaine_col] if domaine_col and pd.notna(row[domaine_col]) else '',
                                    'heures_max': heures_max,
                                    'heures_reelles': heures_reelles,
                                    'quantite': quantite,
                                    'reference': ''
                                }
                                st.session_state.missions_declarees.append(mission)
                                st.success("✅ Mission ajoutée !")
                                st.rerun()
            else:
                st.warning("⚠️ Aucune activité trouvée")
                st.info("💡 Essayez des mots-clés simples : jury, stage, encadrement...")
        else:
            st.info("💡 Entrez des mots-clés pour rechercher")
    
    st.markdown("---")
    st.header("📋 Mes missions déclarées")
    
    if len(st.session_state.missions_declarees) > 0:
        total_heures = sum(m['heures_reelles'] for m in st.session_state.missions_declarees)
        
        col_total, col_export, col_clear = st.columns([2, 1, 1])
        
        with col_total:
            st.metric("Total des heures", f"{total_heures:.1f}h")
        
        with col_export:
            if st.button("📥 Exporter Excel", use_container_width=True):
                export_df = pd.DataFrame(st.session_state.missions_declarees)
                export_df = export_df.rename(columns={
                    'libelle': 'Libellé',
                    'libelle_court': 'Libellé court',
                    'domaine': 'Domaine fonctionnel',
                    'heures_max': 'Heures unitaires',
                    'heures_reelles': 'Heures déclarées',
                    'quantite': 'Quantité',
                    'reference': 'Référence'
                })
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Missions')
                
                output.seek(0)
                
                st.download_button(
                    label="💾 Télécharger",
                    data=output,
                    file_name=f"missions_declarees_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col_clear:
            if st.button("🗑️ Tout effacer", use_container_width=True, type="secondary"):
                st.session_state.missions_declarees = []
                st.rerun()
        
        st.markdown("### Détail des missions")
        for i, mission in enumerate(st.session_state.missions_declarees):
            col_mission, col_delete = st.columns([5, 1])
            
            with col_mission:
                quantite_text = f" (×{mission.get('quantite', 1)})" if mission.get('quantite', 1) > 1 else ""
                st.markdown(f"""
                <div class="mission-card">
                    <strong>{mission['libelle']}</strong>{quantite_text}<br>
                    📍 {mission['domaine']} | 
                    ⏱️ {mission['heures_reelles']:.1f}h
                </div>
                """, unsafe_allow_html=True)
            
            with col_delete:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.missions_declarees.pop(i)
                    st.rerun()
    else:
        st.info("👆 Aucune mission déclarée. Utilisez la recherche ci-dessus pour ajouter des missions.")

else:
    st.info("""
    👋 **Bienvenue !**
    
    Pour commencer, chargez votre fichier **référentiel.xlsx** dans la barre latérale.
    """)
    
    st.markdown("---")
    st.markdown("""
    ### 📖 Comment utiliser cet outil ?
    
    - **🔍 Recherche intelligente** : Décrivez votre mission en langage naturel
    - **🔢 Calcul automatique** : Tapez "3 stages" et les heures sont calculées automatiquement
    - **➕ Ajout simple** : Cliquez sur "Ajouter" pour chaque mission
    - **📊 Suivi en temps réel** : Visualisez votre total d'heures
    - **💾 Export Excel** : Téléchargez votre déclaration complète
    """)
