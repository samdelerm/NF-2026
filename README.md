# NF-2026
Application pour le nouveau festival 2026 du club de robotique.

## Lancement backend + frontend

1. Installer les dependances Python:

```bash
pip install -r requirements.txt
```

2. Lancer le serveur Flask (sert aussi les fichiers front):

```bash
python3 backend.py
```

Le site est ensuite disponible sur http://localhost:3000.

## Page admin cachee (par tablette)

URL cachee: `/admin-pilotage-rsk`

Cette page permet de definir, pour la tablette courante:
- `host` du robot
- `color` (`green` ou `blue`)
- `id` (`1` ou `2`)

La configuration est conservee cote backend et associee a la tablette via cookie.

## Pilotage robot

Le joystick envoie en continu des commandes `dx`, `dy`, `dalpha` vers l'API backend:

`POST /api/control`

Le backend execute ensuite:

`rsk.Client(host=...).robots[color][id].control(dx, dy, dalpha)`
