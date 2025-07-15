"""
Service pour la gestion des déclarations fiscales selon le statut juridique
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.declaration_fiscale import DeclarationFiscale
from app.models.echeance import Echeance
import logging

logger = logging.getLogger(__name__)


def get_declarations_by_statut_juridique(type_entreprise: str) -> list:
    """
    Retourne les types de déclarations selon le statut juridique
    Similaire aux journaux comptables mais pour les déclarations fiscales
    """
    declarations = []
    
    # TVA pour toutes les entreprises (sauf micro-entreprises exonérées)
    if type_entreprise not in ['MICRO_ENTREPRISE_EXONEREE']:
        declarations.append({
            'type': 'TVA',
            'regime': 'MENSUEL',
            'cerfa': '3310-CA3',
            'jour_limite': 15,
            'description': 'Déclaration de TVA'
        })
    
    # Selon le statut juridique
    if type_entreprise in ['SARL', 'EURL', 'SAS', 'SASU', 'SA']:
        # Sociétés soumises à l'IS
        declarations.extend([
            {
                'type': 'IS',
                'regime': 'ANNUEL',
                'cerfa': '2065',
                'mois_limite': 4,
                'jour_limite': 30,
                'description': 'Impôt sur les Sociétés'
            },
            {
                'type': 'LIASSE_FISCALE',
                'regime': 'ANNUEL',
                'cerfa': '2050',
                'mois_limite': 4,
                'jour_limite': 30,
                'description': 'Liasse fiscale'
            },
            {
                'type': 'CVAE',
                'regime': 'ANNUEL',
                'cerfa': '1330-CVAE',
                'mois_limite': 5,
                'jour_limite': 31,
                'description': 'Cotisation sur la Valeur Ajoutée des Entreprises'
            }
        ])
        
    elif type_entreprise in ['EI', 'EIRL']:
        # Entreprises individuelles soumises à l'IR
        declarations.extend([
            {
                'type': 'BIC',
                'regime': 'ANNUEL',
                'cerfa': '2031',
                'mois_limite': 5,
                'jour_limite': 31,
                'description': 'Bénéfices Industriels et Commerciaux'
            }
        ])
        
    elif type_entreprise == 'MICRO_ENTREPRISE':
        # Micro-entreprises
        declarations.extend([
            {
                'type': 'MICRO_BIC',
                'regime': 'TRIMESTRIEL',
                'cerfa': '2042-C-PRO',
                'jour_limite': 30,
                'description': 'Déclaration Micro-entreprise BIC'
            }
        ])
    
    # Cotisation Foncière des Entreprises (CFE) pour tous
    declarations.append({
        'type': 'CFE',
        'regime': 'ANNUEL',
        'cerfa': '1447-C',
        'mois_limite': 12,
        'jour_limite': 15,
        'description': 'Cotisation Foncière des Entreprises'
    })
    
    return declarations


def create_declarations_fiscales(
    db: Session,
    dossier_id: int,
    type_entreprise: str,
    annee_fiscale: int
) -> int:
    """
    Crée toutes les déclarations fiscales pour un dossier selon le statut juridique
    Retourne le nombre de déclarations créées
    """
    mois_noms = [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ]
    
    declarations_config = get_declarations_by_statut_juridique(type_entreprise)
    count_created = 0
    
    logger.info(f"Création de {len(declarations_config)} types de déclarations pour {type_entreprise}")
    
    for config in declarations_config:
        if config['regime'] == 'MENSUEL':
            # Déclarations mensuelles (TVA)
            for mois in range(1, 13):
                debut_mois = date(annee_fiscale, mois, 1)
                if mois == 12:
                    fin_mois = date(annee_fiscale + 1, 1, 1) - timedelta(days=1)
                    date_limite = date(annee_fiscale + 1, 1, config['jour_limite'])
                else:
                    fin_mois = date(annee_fiscale, mois + 1, 1) - timedelta(days=1)
                    date_limite = date(annee_fiscale, mois + 1, config['jour_limite'])
                
                declaration = DeclarationFiscale(
                    dossier_id=dossier_id,
                    type_declaration=config['type'],
                    statut='A_FAIRE',
                    regime=config['regime'],
                    periode_debut=debut_mois,
                    periode_fin=fin_mois,
                    date_limite=date_limite,
                    formulaire_cerfa=config['cerfa'],
                    observations=f"{config['description']} - {mois_noms[mois-1]} {annee_fiscale}"
                )
                db.add(declaration)
                count_created += 1
                
        elif config['regime'] == 'TRIMESTRIEL':
            # Déclarations trimestrielles (Micro-entreprise)
            for trimestre in range(1, 5):
                mois_debut = (trimestre - 1) * 3 + 1
                mois_fin = trimestre * 3
                
                debut_trimestre = date(annee_fiscale, mois_debut, 1)
                fin_trimestre = date(annee_fiscale, mois_fin + 1, 1) - timedelta(days=1) if mois_fin < 12 else date(annee_fiscale, 12, 31)
                
                # Date limite : 30 du mois suivant le trimestre
                if mois_fin == 12:
                    date_limite = date(annee_fiscale + 1, 1, config['jour_limite'])
                else:
                    date_limite = date(annee_fiscale, mois_fin + 1, config['jour_limite'])
                
                declaration = DeclarationFiscale(
                    dossier_id=dossier_id,
                    type_declaration=config['type'],
                    statut='A_FAIRE',
                    regime=config['regime'],
                    periode_debut=debut_trimestre,
                    periode_fin=fin_trimestre,
                    date_limite=date_limite,
                    formulaire_cerfa=config['cerfa'],
                    observations=f"{config['description']} - T{trimestre} {annee_fiscale}"
                )
                db.add(declaration)
                count_created += 1
                
        elif config['regime'] == 'ANNUEL':
            # Déclarations annuelles
            debut_annee = date(annee_fiscale, 1, 1)
            fin_annee = date(annee_fiscale, 12, 31)
            
            if config['type'] == 'CFE':
                # CFE : décembre de l'année en cours
                date_limite = date(annee_fiscale, config['mois_limite'], config['jour_limite'])
            else:
                # Autres : année suivante
                date_limite = date(annee_fiscale + 1, config['mois_limite'], config['jour_limite'])
            
            declaration = DeclarationFiscale(
                dossier_id=dossier_id,
                type_declaration=config['type'],
                statut='A_FAIRE',
                regime=config['regime'],
                periode_debut=debut_annee,
                periode_fin=fin_annee,
                date_limite=date_limite,
                formulaire_cerfa=config['cerfa'],
                observations=f"{config['description']} - Exercice {annee_fiscale}"
            )
            db.add(declaration)
            count_created += 1
    
    # Ajouter les déclarations de l'année précédente dues dans l'année courante
    if type_entreprise in ['SARL', 'SAS', 'SA', 'EURL']:
        # IS de l'année précédente (due en avril de l'année courante)
        debut_annee_prec = date(annee_fiscale - 1, 1, 1)
        fin_annee_prec = date(annee_fiscale - 1, 12, 31)
        date_limite_is_prec = date(annee_fiscale, 4, 30)  # 30 avril année courante
        
        declaration_is_prec = DeclarationFiscale(
            dossier_id=dossier_id,
            type_declaration='IS',
            statut='A_FAIRE',
            regime='ANNUEL',
            periode_debut=debut_annee_prec,
            periode_fin=fin_annee_prec,
            date_limite=date_limite_is_prec,
            formulaire_cerfa='2065',
            observations=f"Impôt sur les Sociétés - Exercice {annee_fiscale - 1}"
        )
        db.add(declaration_is_prec)
        count_created += 1
        
        # Liasse fiscale de l'année précédente (due en avril de l'année courante)
        declaration_liasse_prec = DeclarationFiscale(
            dossier_id=dossier_id,
            type_declaration='LIASSE_FISCALE',
            statut='A_FAIRE',
            regime='ANNUEL',
            periode_debut=debut_annee_prec,
            periode_fin=fin_annee_prec,
            date_limite=date_limite_is_prec,
            formulaire_cerfa='2050',
            observations=f"Liasse fiscale - Exercice {annee_fiscale - 1}"
        )
        db.add(declaration_liasse_prec)
        count_created += 1
    
    logger.info(f"{count_created} déclarations fiscales créées pour le dossier {dossier_id}")
    return count_created


def create_echeances_from_declarations(
    db: Session,
    dossier_id: int,
    type_entreprise: str,
    annee_fiscale: int
) -> int:
    """
    Crée les échéances basées sur les déclarations fiscales
    Retourne le nombre d'échéances créées
    """
    mois_noms = [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
    ]
    
    declarations = db.query(DeclarationFiscale).filter(
        DeclarationFiscale.dossier_id == dossier_id
    ).all()
    
    count_created = 0
    
    for declaration in declarations:
        if declaration.regime == 'MENSUEL':
            # Échéances mensuelles
            mois = declaration.periode_debut.month
            periode_label = f"{declaration.type_declaration} {mois_noms[mois-1]} {annee_fiscale}"
        elif declaration.regime == 'TRIMESTRIEL':
            # Échéances trimestrielles
            trimestre = (declaration.periode_debut.month - 1) // 3 + 1
            periode_label = f"{declaration.type_declaration} T{trimestre} {annee_fiscale}"
        else:
            # Échéances annuelles
            periode_label = f"{declaration.type_declaration} {annee_fiscale}"
        
        echeance = Echeance(
            dossier_id=dossier_id,
            mois=declaration.date_limite.month,
            annee=declaration.date_limite.year,
            periode_label=periode_label,
            date_echeance=declaration.date_limite,
            statut='A_FAIRE',
            notes=f"Échéance pour {declaration.type_declaration} - {declaration.formulaire_cerfa}"
        )
        db.add(echeance)
        count_created += 1
    
    logger.info(f"{count_created} échéances fiscales créées pour le dossier {dossier_id}")
    return count_created