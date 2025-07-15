#!/usr/bin/env python3
"""
Démonstration des validateurs internationaux (pays OHADA et autres)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.validators import (
    validate_phone,
    validate_company_id,
    validate_iban,
    format_phone_number,
    get_country_info,
    get_supported_countries,
    get_currency_symbol,
    COUNTRY_CONFIGS
)

def demo_international_validators():
    print("🌍 Démonstration des Validateurs Internationaux\n")
    print("=" * 70)
    
    # Afficher les pays supportés
    print("📍 Pays supportés:")
    countries = get_supported_countries()
    
    # Grouper par zone
    zones = {
        "CEMAC (Zone FCFA XAF)": ["CM", "GA", "CG", "TD", "CF", "GQ"],
        "UEMOA (Zone FCFA XOF)": ["SN", "CI", "BF", "ML", "TG", "BJ", "NE", "GW"],
        "Europe": ["FR"],
        "Autres pays OHADA": ["KM", "GN", "CD"]
    }
    
    print(f"\n📊 Total: 17 pays membres OHADA + France")
    
    for zone, codes in zones.items():
        print(f"\n  {zone}:")
        for code in codes:
            if code in countries:
                info = get_country_info(code)
                print(f"    • {info['name']} ({code}) - {info['currency']} - {info['company_id_name']}")
    
    print("\n" + "=" * 70)
    
    # Tests par pays
    test_countries = ["FR", "CM", "SN", "CI"]
    
    for country_code in test_countries:
        info = get_country_info(country_code)
        print(f"\n🇦🇩 {info['name']} ({country_code})")
        print("-" * 50)
        
        # Test téléphone
        print(f"\n📞 Validation téléphone (format: {info['phone_format']}):")
        test_phones = {
            "FR": ["0123456789", "+33623456789", "01 23 45 67 89", "123456789"],
            "CM": ["237691234567", "+237691234567", "691234567", "237212345678"],
            "SN": ["221771234567", "+221771234567", "771234567", "331234567"],
            "CI": ["225071234567", "+225071234567", "071234567", "225271234567"]
        }
        
        for phone in test_phones.get(country_code, []):
            valid = validate_phone(phone, country_code)
            formatted = format_phone_number(phone, country_code) if valid else None
            status = "✅" if valid else "❌"
            print(f"  {status} {phone:20} → {formatted if formatted else 'Invalide'}")
        
        # Test identifiant entreprise
        print(f"\n🏢 Validation {info['company_id_name']} ({info['company_id_length']} caractères):")
        test_company_ids = {
            "FR": ["80314979300020", "12345678901234", "803 149 793 00020"],
            "CM": ["M1234567890123", "P1234567890123", "1234567890123", "X1234567890123"],
            "SN": ["123456789", "12345678", "1234567890"],
            "CI": ["CI12345678901234", "1234567890123456", "AB12345678901234"]
        }
        
        for company_id in test_company_ids.get(country_code, []):
            valid = validate_company_id(company_id, country_code)
            status = "✅" if valid else "❌"
            print(f"  {status} {company_id}")
        
        # Test IBAN
        print(f"\n💳 Validation IBAN (préfixe: {info['iban_prefix']}, longueur: {info['iban_length']}):")
        test_ibans = {
            "FR": ["FR1420041010050500013M02606", "FR14 2004 1010 0505 0001 3M02 606", "FR1420041010050500013M02607"],
            "CM": ["CM21100110012345678901234567", "CM2110011001234567890123456", "CM21100110012345678901234568"],
            "SN": ["SN12K00100152000025690007542", "SN12K0010015200002569000754", "SN12K00100152000025690007543"],
            "CI": ["CI93CI0080111301134291200589", "CI93CI008011130113429120058", "CI93CI0080111301134291200590"]
        }
        
        for iban in test_ibans.get(country_code, []):
            valid = validate_iban(iban, country_code)
            status = "✅" if valid else "❌"
            print(f"  {status} {iban}")
        
        # Afficher devise
        print(f"\n💰 Devise: {get_currency_symbol(country_code)} ({info['currency']})")
    
    print("\n" + "=" * 70)
    
    # Exemple d'utilisation dans une API
    print("\n📝 Exemple d'utilisation dans une API:")
    print("""
from app.core.validators import validate_phone, validate_company_id, get_country_info

@router.post("/clients")
async def create_client(
    client_data: ClientCreate,
    cabinet: Cabinet = Depends(get_current_cabinet)
):
    # Utiliser le pays du cabinet
    country_code = cabinet.pays_code
    
    # Valider le téléphone
    if not validate_phone(client_data.telephone, country_code):
        country_info = get_country_info(country_code)
        raise HTTPException(
            status_code=400,
            detail=f"Format de téléphone invalide. Format attendu: {country_info['phone_format']}"
        )
    
    # Valider l'identifiant d'entreprise
    if not validate_company_id(client_data.company_id, country_code):
        country_info = get_country_info(country_code)
        raise HTTPException(
            status_code=400,
            detail=f"{country_info['company_id_name']} invalide"
        )
    
    # Créer le client...
    """)
    
    print("\n✅ Démonstration terminée!")

if __name__ == "__main__":
    demo_international_validators()