# 🏊 Intégration Swimo pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/USERNAME/ha-swimo.svg)](https://github.com/USERNAME/ha-swimo/releases)
[![License](https://img.shields.io/github/license/USERNAME/ha-swimo.svg)](LICENSE)

Intégration Home Assistant pour les automates de piscine **Swimo**, **Maestro** et **Solo** d'Orkestron.

## ✨ Fonctionnalités

- 📊 **Capteurs en temps réel** : pH, température, chlore, redox, pression, débit, niveau d'eau
- 🎛️ **Contrôle complet** : Filtration, éclairage, chauffage, pompes doseuses
- ⚡ **WebSocket temps réel** : Mises à jour instantanées via wss://now.swimo.io
- 🔄 **Reconnexion automatique** : Fiabilité maximale avec fallback sur polling HTTP
- 🌐 **Multi-langues** : Français et Anglais
- 🔐 **Sécurisé** : Gestion automatique des tokens (30 jours)

## 📦 Installation

### Via HACS (Recommandé)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur "Intégrations"
3. Cliquez sur le menu (3 points) et "Dépôts personnalisés"
4. Ajoutez l'URL : `https://github.com/USERNAME/ha-swimo`
5. Catégorie : "Integration"
6. Cliquez sur "Télécharger"
7. Redémarrez Home Assistant

### Installation Manuelle

1. Copiez le dossier `custom_components/swimo` dans votre dossier `config/custom_components/`
2. Redémarrez Home Assistant

## ⚙️ Configuration

1. Allez dans **Configuration** → **Intégrations**
2. Cliquez sur **+ Ajouter une intégration**
3. Recherchez "**Swimo**"
4. Entrez vos identifiants Swimo
5. Terminé ! 🎉

## 🎯 Entités créées

### Capteurs
- `sensor.swimo_ph` - Niveau de pH
- `sensor.swimo_temperature` - Température de l'eau
- `sensor.swimo_chlore` - Niveau de chlore
- `sensor.swimo_redox` - Potentiel redox
- Et plus selon votre configuration...

### Switches
- `switch.swimo_filtration` - Pompe de filtration
- `switch.swimo_eclairage` - Éclairage
- `switch.swimo_chauffage` - Chauffage
- Et plus selon vos équipements...

### Contrôles
- `number.swimo_temperature_cible` - Température cible

### Capteurs binaires
- `binary_sensor.swimo_connexion_temps_reel` - État du WebSocket

## 📱 Exemple d'utilisation

### Carte Lovelace simple

```yaml
type: entities
title: 🏊 Piscine
entities:
  - entity: binary_sensor.swimo_connexion_temps_reel
    name: Mode temps réel
  - entity: sensor.swimo_temperature
  - entity: sensor.swimo_ph
  - entity: switch.swimo_filtration
```

### Automation - Filtration automatique

```yaml
automation:
  - alias: "Piscine - Filtration matin"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.swimo_filtration
```

## 🔧 Support

- **Documentation complète** : [Wiki](https://github.com/USERNAME/ha-swimo/wiki)
- **Issues** : [GitHub Issues](https://github.com/USERNAME/ha-swimo/issues)
- **Discussions** : [GitHub Discussions](https://github.com/USERNAME/ha-swimo/discussions)

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

## 🙏 Remerciements

- [Home Assistant](https://www.home-assistant.io/)
- [Orkestron/Swimo](https://www.orkestron.com/)
