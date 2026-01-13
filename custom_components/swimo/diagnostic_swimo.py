#!/usr/bin/env python3
"""
Script de diagnostic pour l'intégration Swimo
Exécutez ce script pour voir exactement ce que l'API retourne
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# CONFIGUREZ VOS IDENTIFIANTS ICI
EMAIL = "michel.gasquez@live.fr"  # <-- CHANGEZ ICI
PASSWORD = "michel"    # <-- CHANGEZ ICI

BASE_URL = "https://socket.swimo.io/cgi-bin"

async def diagnostic():
    """Effectue un diagnostic complet de l'API Swimo."""
    
    print("=" * 70)
    print("🔍 DIAGNOSTIC INTÉGRATION SWIMO")
    print("=" * 70)
    print()
    
    session = aiohttp.ClientSession()
    
    try:
        # ===== ÉTAPE 1 : OBTENTION DU TOKEN =====
        print("📡 ÉTAPE 1/3 : Obtention du token...")
        headers = {"user": EMAIL, "code": PASSWORD}
        
        async with session.get(
            f"{BASE_URL}/get_token",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                token_data = await response.json()
                print(f"   ✅ Token obtenu: {str(token_data.get('token', 'N/A'))[:30]}...")
                token = token_data.get("token") or token_data.get("appid")
                
                # Afficher toute la réponse
                print("\n   📋 Réponse complète get_token:")
                print(json.dumps(token_data, indent=4, ensure_ascii=False))
            else:
                text = await response.text()
                print(f"   ❌ ERREUR: {text}")
                await session.close()
                return
        
        print()
        
        # ===== ÉTAPE 2 : RÉCUPÉRATION DES DONNÉES =====
        print("📡 ÉTAPE 2/3 : Récupération des données...")
        
        async with session.get(
            f"{BASE_URL}/get_all",
            headers={"appid": token},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                print(f"   ✅ Données reçues")
                
                # Afficher la structure complète
                print("\n" + "=" * 70)
                print("📋 STRUCTURE COMPLÈTE DES DONNÉES")
                print("=" * 70)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("=" * 70)
                
                # ===== ÉTAPE 3 : ANALYSE DES DONNÉES =====
                print("\n📊 ÉTAPE 3/3 : Analyse des données...")
                print()
                
                # Clés principales
                print("🔑 Clés principales trouvées:")
                for key in data.keys():
                    print(f"   - {key}: {type(data[key]).__name__}")
                print()
                
                # Capteurs
                sensors = data.get("sensors", [])
                if isinstance(sensors, list):
                    print(f"📏 CAPTEURS: {len(sensors)} trouvé(s)")
                    if sensors:
                        print("   Exemple de capteur:")
                        print(json.dumps(sensors[0], indent=6, ensure_ascii=False))
                        print()
                        print("   Clés disponibles dans un capteur:")
                        for key in sensors[0].keys():
                            print(f"      - {key}")
                    else:
                        print("   ⚠️  Aucun capteur dans la liste")
                else:
                    print(f"   ⚠️  'sensors' n'est pas une liste: {type(sensors)}")
                print()
                
                # Devices
                devices = data.get("devices", [])
                if isinstance(devices, list):
                    print(f"🔌 DEVICES: {len(devices)} trouvé(s)")
                    if devices:
                        print("   Exemple de device:")
                        print(json.dumps(devices[0], indent=6, ensure_ascii=False))
                        print()
                        print("   Clés disponibles dans un device:")
                        for key in devices[0].keys():
                            print(f"      - {key}")
                    else:
                        print("   ⚠️  Aucun device dans la liste")
                else:
                    print(f"   ⚠️  'devices' n'est pas une liste: {type(devices)}")
                print()
                
                # Actions
                actions = data.get("actions", [])
                if isinstance(actions, list):
                    print(f"⚡ ACTIONS: {len(actions)} trouvée(s)")
                    if actions:
                        print("   Exemple d'action:")
                        print(json.dumps(actions[0], indent=6, ensure_ascii=False))
                        print()
                        print("   Clés disponibles dans une action:")
                        for key in actions[0].keys():
                            print(f"      - {key}")
                    else:
                        print("   ⚠️  Aucune action dans la liste")
                else:
                    print(f"   ⚠️  'actions' n'est pas une liste: {type(actions)}")
                print()
                
                # System
                system = data.get("system", {})
                if system:
                    print(f"⚙️  SYSTEM:")
                    if isinstance(system, list) and len(system) > 0:
                        print("   (system est une liste, premier élément:)")
                        print(json.dumps(system[0], indent=6, ensure_ascii=False))
                    else:
                        print(json.dumps(system, indent=6, ensure_ascii=False))
                print()
                
                # ===== DIAGNOSTIC FINAL =====
                print("=" * 70)
                print("🎯 DIAGNOSTIC FINAL")
                print("=" * 70)
                
                issues = []
                
                if not sensors:
                    issues.append("❌ Aucun capteur trouvé - Vérifiez que votre système a des capteurs configurés")
                else:
                    print(f"✅ {len(sensors)} capteur(s) détecté(s)")
                    
                if not devices and not actions:
                    issues.append("⚠️  Aucun device/action trouvé - Normal si votre système n'a pas d'équipements")
                else:
                    if devices:
                        print(f"✅ {len(devices)} device(s) détecté(s)")
                    if actions:
                        print(f"✅ {len(actions)} action(s) détectée(s)")
                
                if issues:
                    print()
                    for issue in issues:
                        print(issue)
                
                print()
                print("=" * 70)
                print("📝 PROCHAINES ÉTAPES")
                print("=" * 70)
                print("1. Copiez la sortie complète de ce script")
                print("2. Partagez-la pour que je corrige les fichiers de l'intégration")
                print("3. Je vais adapter le code en fonction de la structure exacte")
                print("=" * 70)
                
            else:
                text = await response.text()
                print(f"   ❌ ERREUR: {text}")
    
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await session.close()
    
    print()

if __name__ == "__main__":
    if EMAIL == "votre_email@example.com":
        print("❌ ERREUR: Configurez vos identifiants dans le script!")
        print("   Éditez le fichier et changez EMAIL et PASSWORD")
        exit(1)
    
    asyncio.run(diagnostic())