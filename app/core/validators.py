"""
Validateurs internationaux avec support pour les pays OHADA et autres
"""

import re
from typing import Optional, Dict, Tuple
from datetime import datetime
import unicodedata


# Configuration des pays supportés
COUNTRY_CONFIGS = {
    # France
    "FR": {
        "name": "France",
        "phone_regex": r"^(\+33|0)[1-9](\d{2}){4}$",
        "phone_format": "0123456789 ou +33123456789",
        "company_id_name": "SIRET",
        "company_id_length": 14,
        "company_id_validator": "validate_siret_fr",
        "vat_number_format": "FR + 2 chiffres + 9 chiffres SIREN",
        "iban_length": 27,
        "iban_prefix": "FR",
        "currency": "EUR",
        "date_format": "DD/MM/YYYY"
    },
    
    # Cameroun
    "CM": {
        "name": "Cameroun",
        "phone_regex": r"^(\+237|237)?[26]\d{8}$",
        "phone_format": "237612345678 ou +237612345678",
        "company_id_name": "RCCM / NUI",
        "company_id_length": 14,
        "company_id_validator": "validate_rccm_nui_cm",
        "vat_number_format": "RCCM: CM-DLA-2024-B-12345",
        "iban_length": 27,
        "iban_prefix": "CM",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Sénégal
    "SN": {
        "name": "Sénégal",
        "phone_regex": r"^(\+221|221)?[37]\d{8}$",
        "phone_format": "221771234567 ou +221771234567",
        "company_id_name": "NINEA / RCCM",
        "company_id_length": 9,
        "company_id_validator": "validate_ninea_rccm_sn",
        "vat_number_format": "NINEA: 9 chiffres, RCCM: SN-DKR-2024-B-12345",
        "iban_length": 28,
        "iban_prefix": "SN",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Côte d'Ivoire
    "CI": {
        "name": "Côte d'Ivoire",
        "phone_regex": r"^(\+225|225)?[0-9]\d{8}$",
        "phone_format": "225071234567 ou +225071234567",
        "company_id_name": "RCCM / CC",
        "company_id_length": 16,
        "company_id_validator": "validate_rccm_cc_ci",
        "vat_number_format": "RCCM: CI-ABJ-2024-B-12345",
        "iban_length": 28,
        "iban_prefix": "CI",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Gabon
    "GA": {
        "name": "Gabon",
        "phone_regex": r"^(\+241|241)?[0-9]\d{7}$",
        "phone_format": "24101234567 ou +24101234567",
        "company_id_name": "RCCM / NUI",
        "company_id_length": 13,
        "company_id_validator": "validate_rccm_nui_ga",
        "vat_number_format": "RCCM: GA-LBV-2024-B-12345",
        "iban_length": 27,
        "iban_prefix": "GA",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Burkina Faso
    "BF": {
        "name": "Burkina Faso",
        "phone_regex": r"^(\+226|226)?[567]\d{7}$",
        "phone_format": "22670123456 ou +22670123456",
        "company_id_name": "IFU",
        "company_id_length": 12,
        "company_id_validator": "validate_ifu_bf",
        "vat_number_format": "12 chiffres",
        "iban_length": 27,
        "iban_prefix": "BF",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Mali
    "ML": {
        "name": "Mali",
        "phone_regex": r"^(\+223|223)?[567]\d{7}$",
        "phone_format": "22370123456 ou +22370123456",
        "company_id_name": "NIF",
        "company_id_length": 9,
        "company_id_validator": "validate_nif_ml",
        "vat_number_format": "9 chiffres",
        "iban_length": 28,
        "iban_prefix": "ML",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Togo
    "TG": {
        "name": "Togo",
        "phone_regex": r"^(\+228|228)?[9]\d{7}$",
        "phone_format": "22890123456 ou +22890123456",
        "company_id_name": "NIF",
        "company_id_length": 13,
        "company_id_validator": "validate_nif_tg",
        "vat_number_format": "13 caractères",
        "iban_length": 28,
        "iban_prefix": "TG",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Bénin
    "BJ": {
        "name": "Bénin",
        "phone_regex": r"^(\+229|229)?[4569]\d{7}$",
        "phone_format": "22990123456 ou +22990123456",
        "company_id_name": "IFU",
        "company_id_length": 13,
        "company_id_validator": "validate_ifu_bj",
        "vat_number_format": "13 caractères",
        "iban_length": 28,
        "iban_prefix": "BJ",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Congo Brazzaville
    "CG": {
        "name": "Congo",
        "phone_regex": r"^(\+242|242)?[0-9]\d{8}$",
        "phone_format": "242061234567 ou +242061234567",
        "company_id_name": "NIU",
        "company_id_length": 14,
        "company_id_validator": "validate_niu_cg",
        "vat_number_format": "14 caractères",
        "iban_length": 27,
        "iban_prefix": "CG",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Tchad
    "TD": {
        "name": "Tchad",
        "phone_regex": r"^(\+235|235)?[6]\d{7}$",
        "phone_format": "23560123456 ou +23560123456",
        "company_id_name": "NIF",
        "company_id_length": 13,
        "company_id_validator": "validate_nif_td",
        "vat_number_format": "13 caractères",
        "iban_length": 27,
        "iban_prefix": "TD",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # République Centrafricaine
    "CF": {
        "name": "République Centrafricaine",
        "phone_regex": r"^(\+236|236)?[7]\d{7}$",
        "phone_format": "23670123456 ou +23670123456",
        "company_id_name": "NIF",
        "company_id_length": 12,
        "company_id_validator": "validate_nif_cf",
        "vat_number_format": "12 caractères",
        "iban_length": 27,
        "iban_prefix": "CF",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Guinée Équatoriale
    "GQ": {
        "name": "Guinée Équatoriale",
        "phone_regex": r"^(\+240|240)?[2]\d{8}$",
        "phone_format": "240222123456 ou +240222123456",
        "company_id_name": "NIF",
        "company_id_length": 12,
        "company_id_validator": "validate_nif_gq",
        "vat_number_format": "12 caractères",
        "iban_length": 27,
        "iban_prefix": "GQ",
        "currency": "XAF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Niger
    "NE": {
        "name": "Niger",
        "phone_regex": r"^(\+227|227)?[9]\d{7}$",
        "phone_format": "22790123456 ou +22790123456",
        "company_id_name": "NIF",
        "company_id_length": 12,
        "company_id_validator": "validate_nif_ne",
        "vat_number_format": "12 caractères",
        "iban_length": 28,
        "iban_prefix": "NE",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Guinée-Bissau
    "GW": {
        "name": "Guinée-Bissau",
        "phone_regex": r"^(\+245|245)?[5-7]\d{6}$",
        "phone_format": "245955123456 ou +245955123456",
        "company_id_name": "NIF",
        "company_id_length": 10,
        "company_id_validator": "validate_nif_gw",
        "vat_number_format": "10 caractères",
        "iban_length": 25,
        "iban_prefix": "GW",
        "currency": "XOF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Comores
    "KM": {
        "name": "Comores",
        "phone_regex": r"^(\+269|269)?[3]\d{6}$",
        "phone_format": "269321234 ou +269321234",
        "company_id_name": "NIF",
        "company_id_length": 10,
        "company_id_validator": "validate_nif_km",
        "vat_number_format": "10 caractères",
        "iban_length": 27,
        "iban_prefix": "KM",
        "currency": "KMF",
        "date_format": "DD/MM/YYYY"
    },
    
    # Guinée (Conakry) - 17ème membre OHADA
    "GN": {
        "name": "Guinée",
        "phone_regex": r"^(\+224|224)?[6]\d{8}$",
        "phone_format": "224622123456 ou +224622123456",
        "company_id_name": "NIF",
        "company_id_length": 9,
        "company_id_validator": "validate_nif_gn",
        "vat_number_format": "9 caractères",
        "iban_length": 27,
        "iban_prefix": "GN",
        "currency": "GNF",
        "date_format": "DD/MM/YYYY"
    },
    
    # RDC (République Démocratique du Congo) - aussi membre OHADA
    "CD": {
        "name": "RD Congo",
        "phone_regex": r"^(\+243|243)?[89]\d{8}$",
        "phone_format": "243812345678 ou +243812345678",
        "company_id_name": "NIF",
        "company_id_length": 14,
        "company_id_validator": "validate_nif_cd",
        "vat_number_format": "14 caractères",
        "iban_length": 27,
        "iban_prefix": "CD",
        "currency": "CDF",
        "date_format": "DD/MM/YYYY"
    }
}


def validate_phone(phone: str, country_code: str = "FR") -> bool:
    """
    Valide un numéro de téléphone selon le pays
    """
    if country_code not in COUNTRY_CONFIGS:
        return False
    
    config = COUNTRY_CONFIGS[country_code]
    phone_cleaned = re.sub(r"\s+", "", phone.strip())
    
    return bool(re.match(config["phone_regex"], phone_cleaned))


def validate_company_id(company_id: str, country_code: str = "FR") -> bool:
    """
    Valide un identifiant d'entreprise selon le pays
    """
    if country_code not in COUNTRY_CONFIGS:
        return False
    
    config = COUNTRY_CONFIGS[country_code]
    validator_name = config["company_id_validator"]
    
    # Appel dynamique du validateur spécifique
    if validator_name in globals():
        return globals()[validator_name](company_id)
    
    # Validation basique par défaut (longueur)
    company_id_cleaned = re.sub(r"\D", "", company_id)
    return len(company_id_cleaned) == config["company_id_length"]


def validate_iban(iban: str, country_code: Optional[str] = None) -> bool:
    """
    Valide un IBAN selon le pays
    """
    # Nettoyage
    iban = iban.replace(" ", "").upper()
    
    # Extraction du code pays si non fourni
    if not country_code and len(iban) >= 2:
        country_code = iban[:2]
    
    if country_code not in COUNTRY_CONFIGS:
        return False
    
    config = COUNTRY_CONFIGS[country_code]
    
    # Vérification du format de base
    if not iban.startswith(config["iban_prefix"]):
        return False
    
    # Vérification de la longueur
    if len(iban) != config["iban_length"]:
        return False
    
    # Algorithme de validation IBAN
    # Déplace les 4 premiers caractères à la fin
    rearranged = iban[4:] + iban[:4]
    
    # Remplace les lettres par des nombres
    numeric_iban = ""
    for char in rearranged:
        if char.isdigit():
            numeric_iban += char
        else:
            numeric_iban += str(ord(char) - ord('A') + 10)
    
    # Vérifie que le modulo 97 est égal à 1
    return int(numeric_iban) % 97 == 1


# Validateurs spécifiques par pays

def validate_siret_fr(siret: str) -> bool:
    """
    Valide un SIRET français (algorithme de Luhn)
    """
    siret_digits = re.sub(r"\D", "", siret)
    
    if len(siret_digits) != 14:
        return False
    
    # Algorithme de Luhn
    total = 0
    for i, digit in enumerate(siret_digits):
        n = int(digit)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


def validate_ninea_rccm_sn(identifier: str) -> bool:
    """
    Valide un NINEA ou RCCM sénégalais
    NINEA: 9 chiffres
    RCCM format: SN-DKR-2024-B-12345
    """
    identifier = identifier.upper().strip()
    
    # Vérifier si c'est un RCCM
    if identifier.startswith("SN-"):
        parts = identifier.split("-")
        if len(parts) == 5:
            if (parts[0] == "SN" and 
                len(parts[1]) == 3 and  # Code ville (DKR, etc.)
                parts[2].isdigit() and len(parts[2]) == 4 and  # Année
                parts[3] in ['A', 'B'] and  # Type
                parts[4].isdigit()):  # Numéro
                return True
    
    # Sinon vérifier si c'est un NINEA (9 chiffres)
    else:
        ninea_cleaned = re.sub(r"\D", "", identifier)
        if len(ninea_cleaned) == 9:
            return True
    
    return False


def validate_rccm_nui_cm(identifier: str) -> bool:
    """
    Valide un RCCM ou NUI camerounais
    RCCM format: CM-[VILLE]-[ANNEE]-[TYPE]-[NUMERO]
    Exemple: CM-DLA-2024-B-12345
    NUI: Numéro unique d'identification (14 caractères alphanumériques)
    """
    identifier = identifier.upper().strip()
    
    # Vérifier si c'est un RCCM
    if identifier.startswith("CM-"):
        parts = identifier.split("-")
        if len(parts) == 5:
            # Vérifier le format RCCM
            if (parts[0] == "CM" and 
                len(parts[1]) == 3 and  # Code ville (DLA, YDE, etc.)
                parts[2].isdigit() and len(parts[2]) == 4 and  # Année
                parts[3] in ['A', 'B'] and  # Type (A=personne physique, B=société)
                parts[4].isdigit()):  # Numéro
                return True
    
    # Sinon vérifier si c'est un NUI (14 caractères)
    elif len(identifier) == 14 and identifier.isalnum():
        return True
    
    return False


def validate_ifu_bf(ifu: str) -> bool:
    """
    Valide un IFU burkinabé
    """
    ifu_cleaned = re.sub(r"\D", "", ifu)
    return len(ifu_cleaned) == 12 and ifu_cleaned.isdigit()


def validate_rccm_generic(identifier: str, country_code: str) -> bool:
    """
    Validateur générique pour le format RCCM OHADA
    Format: [PAYS]-[VILLE]-[ANNEE]-[TYPE]-[NUMERO]
    """
    identifier = identifier.upper().strip()
    
    if identifier.startswith(f"{country_code}-"):
        parts = identifier.split("-")
        if len(parts) == 5:
            if (parts[0] == country_code and 
                len(parts[1]) >= 3 and  # Code ville
                parts[2].isdigit() and len(parts[2]) == 4 and  # Année
                parts[3] in ['A', 'B'] and  # Type
                parts[4].isdigit()):  # Numéro
                return True
    
    return False


def validate_rccm_cc_ci(identifier: str) -> bool:
    """
    Valide un RCCM ou CC ivoirien
    RCCM format: CI-ABJ-2024-B-12345
    """
    return validate_rccm_generic(identifier, "CI")


def validate_rccm_nui_ga(identifier: str) -> bool:
    """
    Valide un RCCM ou NUI gabonais
    RCCM format: GA-LBV-2024-B-12345
    """
    identifier = identifier.upper().strip()
    
    # Vérifier RCCM
    if validate_rccm_generic(identifier, "GA"):
        return True
    
    # Vérifier NUI (13 caractères alphanumériques)
    elif len(identifier) == 13 and identifier.isalnum():
        return True
    
    return False


def validate_ifu_bj(ifu: str) -> bool:
    """
    Valide un IFU béninois ou RCCM
    RCCM format: BJ-COT-2024-B-12345
    """
    identifier = ifu.upper().strip()
    
    # Vérifier RCCM
    if validate_rccm_generic(identifier, "BJ"):
        return True
    
    # Vérifier IFU (13 caractères)
    ifu_cleaned = re.sub(r"\s+", "", identifier)
    if len(ifu_cleaned) == 13:
        return True
    
    return False


def validate_nif_gn(nif: str) -> bool:
    """
    Valide un NIF guinéen
    """
    nif_cleaned = re.sub(r"\D", "", nif)
    return len(nif_cleaned) == 9 and nif_cleaned.isdigit()


def validate_nif_cd(nif: str) -> bool:
    """
    Valide un NIF de la RD Congo
    """
    nif_cleaned = re.sub(r"\D", "", nif)
    return len(nif_cleaned) == 14 and nif_cleaned.isdigit()


def get_country_info(country_code: str) -> Optional[Dict]:
    """
    Retourne les informations de configuration d'un pays
    """
    return COUNTRY_CONFIGS.get(country_code)


def get_supported_countries() -> Dict[str, str]:
    """
    Retourne la liste des pays supportés avec leurs noms
    """
    return {code: config["name"] for code, config in COUNTRY_CONFIGS.items()}


def format_phone_number(phone: str, country_code: str = "FR") -> Optional[str]:
    """
    Formate un numéro de téléphone selon les standards du pays
    """
    if not validate_phone(phone, country_code):
        return None
    
    phone_cleaned = re.sub(r"\D", "", phone)
    
    # Formatage spécifique par pays
    if country_code == "FR":
        if phone_cleaned.startswith("33"):
            phone_cleaned = "0" + phone_cleaned[2:]
        # Format: 01 23 45 67 89
        return f"{phone_cleaned[0:2]} {phone_cleaned[2:4]} {phone_cleaned[4:6]} {phone_cleaned[6:8]} {phone_cleaned[8:10]}"
    
    elif country_code in ["CM", "SN", "CI", "GA"]:
        # Format: +XXX XX XX XX XX
        if not phone_cleaned.startswith(COUNTRY_CONFIGS[country_code]["iban_prefix"]):
            phone_cleaned = COUNTRY_CONFIGS[country_code]["iban_prefix"] + phone_cleaned
        return f"+{phone_cleaned[0:3]} {phone_cleaned[3:5]} {phone_cleaned[5:7]} {phone_cleaned[7:9]} {phone_cleaned[9:11]}"
    
    return phone_cleaned


def sanitize_string(text: str, max_length: int = 255) -> str:
    """
    Nettoie une chaîne de caractères (compatible avec tous les pays)
    """
    if not text:
        return ""
    
    # Supprime les caractères de contrôle mais garde les accents
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    
    # Limite la longueur
    text = text[:max_length]
    
    # Supprime les espaces multiples
    text = " ".join(text.split())
    
    return text.strip()


def validate_date_format(date_str: str, country_code: str = "FR") -> bool:
    """
    Valide le format d'une date selon le pays
    """
    config = COUNTRY_CONFIGS.get(country_code, COUNTRY_CONFIGS["FR"])
    date_format = config["date_format"]
    
    # Conversion du format pour strptime
    if date_format == "DD/MM/YYYY":
        format_str = "%d/%m/%Y"
    elif date_format == "MM/DD/YYYY":
        format_str = "%m/%d/%Y"
    elif date_format == "YYYY-MM-DD":
        format_str = "%Y-%m-%d"
    else:
        format_str = "%d/%m/%Y"  # Par défaut
    
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def get_currency_symbol(country_code: str = "FR") -> str:
    """
    Retourne le symbole de la devise du pays
    """
    currency = COUNTRY_CONFIGS.get(country_code, {}).get("currency", "EUR")
    
    currency_symbols = {
        "EUR": "€",
        "XAF": "FCFA",  # Franc CFA CEMAC
        "XOF": "FCFA",  # Franc CFA UEMOA
        "KMF": "FC",    # Franc comorien
        "GNF": "FG",    # Franc guinéen
        "CDF": "FC"     # Franc congolais
    }
    
    return currency_symbols.get(currency, currency)