# Complément logiciel — Microscope FPM

---

## ⚠️ AVANT-PROPOS — À LIRE AVANT TOUTE UTILISATION

> ### 🚧 VERSION DE TEST — NON FINALISÉE 🚧
>
> **CE CODE N'EST PAS UNE VERSION FINALE.**
> Il s'agit d'une version de test réalisée rapidement en raison
> d'un manque de temps. **Tout doit être relu, vérifié et retesté
> avant toute utilisation sérieuse.**

Dans la théorie, les codes présents fonctionnent. Cependant,
il est impératif de tout vérifier. Initialement, le projet était
fragmenté en plusieurs parties avec une interface très simpliste.
Une utilisation de l'intelligence artificielle a été employée pour
améliorer le visuel de l'interface et regrouper l'ensemble du code.

Deux choses sont également à prendre en compte :
- L'affichage des leds n'est pas bon mais est en "miroir", c'est du détail dans la théorie puisque l'axe optique est centré au milieu des leds mais une symetrie est donc a prévoir.
- L'ensemble des informations avec le fichier `metadata.json` ne fonctionne pas, il faut revoir et corriger ça.

**Il faut donc impérativement revoir et revérifier ce code dans
son intégralité. Ce n'est pas une version finale.**

### Raspberry Pi

Il existe également un code présent sur la Raspberry Pi regroupant
les fonctions déjà présentes sur ce repo GitHub. Au moment de
l'écriture de ce README, la Raspberry est configurée en SSH —
les identifiants et l'adresse IP sont disponibles dans le carnet
associé. Si besoin, il suffit de la réinitialiser et de remettre
en place un programme avec les fonctions nécessaires.

---

## Contenu

- `app.py` : interface graphique (tkinter) pour piloter le microscope
  - Connexion au Raspberry Pi via réseau (ou mode simulation)
  - Contrôle manuel des LEDs sur le tableau 16×16
  - Acquisition automatique des 256 images en ordre serpentin
  - Sauvegarde des images et des métadonnées

- `fpm_config.json` : paramètres optiques du microscope
  (NA, grossissement, longueur d'onde, taille pixel, etc.)

---

## Utilisation

```bash
python app.py
```

Connecter le Raspberry Pi via "Setup Raspberry" ou utiliser
le mode simulation. Lancer l'acquisition automatique, puis
cliquer sur "SAVE images + paramètres".

Les images et le fichier `metadata.json` sont sauvegardés
dans le dossier défini dans les paramètres (par défaut : `Images/`).

---

## Dépendances

```bash
pip install numpy pillow
```

---

## Configuration

Modifier `fpm_config.json` ou utiliser directement l'interface
pour ajuster les paramètres optiques avant l'acquisition. (à vérifier si ça fonctionne vraiment également)

| Paramètre     | Description                        |
|---------------|------------------------------------|
| `NA`          | Ouverture numérique de l'objectif  |
| `Mag`         | Grossissement                      |
| `lambda_um`   | Longueur d'onde (µm)               |
| `h_mm`        | Distance LED–échantillon (mm)      |
| `D_LED_mm`    | Espacement entre LEDs (mm)         |
| `pixel_um`    | Taille du pixel caméra (µm)        |
| `expo`        | Temps d'exposition (µs)            |
| `dossier`     | Dossier de sauvegarde des images   |
