# Documentation complète – `python/main.py`

Ce document explique **en détail** le fonctionnement du fichier `main.py` utilisé dans le projet UNO Q pour relier :

**WebUI (HTML/JS) → Python (App Lab) → Bridge RPC → STM32**

---

# 🔷 1. Rôle général de `main.py`

Le fichier `main.py` s’exécute sur le **cœur Linux** de la UNO Q (sous App Lab).  
Il joue un double rôle :

1. **Serveur WebUI** : il expose une API HTTP locale, appelée par le fichier `index.html` (via `fetch()`).
2. **Client Bridge** : il transmet les données reçues au microcontrôleur STM32 via `Bridge.call()`.

Il est donc situé **au milieu de la chaîne** :

```
HTML/JS  →  main.py (WebUI + Bridge)  →  STM32
```

---

# 🔷 2. Import des modules

Le fichier commence par importer les utilitaires Arduino :

```python
from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
```

- `App` : point d’entrée pour lancer l’application App Lab.
- `Bridge` : objet permettant d’envoyer des appels RPC vers le STM32.
- `WebUI` : brique qui permet d’exposer des routes HTTP (API) utilisées par `index.html`.

---

# 🔷 3. Création des objets principaux

```python
print("Starting UNO Q Matrix WebUI app...")

bridge = Bridge()
ui = WebUI()
```

- `bridge = Bridge()` : prépare la connexion RPC avec le microcontrôleur.
- `ui = WebUI()` : initialise le serveur Web pour la partie WebUI.

Ces deux objets sont utilisés tout au long du programme.

---

# 🔷 4. La fonction de handler `on_set_frame(...)`

C’est la fonction appelée lorsque la WebUI fait une requête HTTP `GET` sur l’URL :

```
/set_frame/{w0}/{w1}/{w2}/{w3}
```

Définition typique :

```python
def on_set_frame(w0: str, w1: str, w2: str, w3: str):
    try:
        v0 = int(w0)
        v1 = int(w1)
        v2 = int(w2)
        v3 = int(w3)
    except ValueError:
        print("Invalid frame values:", w0, w1, w2, w3)
        return {"status": "error", "message": "invalid integers"}

    print("Sending frame to STM32:", v0, v1, v2, v3)

    bridge.call("set_matrix_frame", v0, v1, v2, v3)

    return {"status": "ok"}
```

### Explications :

- Les arguments `w0, w1, w2, w3` sont reçus **sous forme de chaînes** (paramètres d’URL).
- On les convertit en `int` Python (`v0..v3`) avec gestion d’erreur (`ValueError`).
- En cas d’erreur, la fonction retourne un dictionnaire JSON :  
  `{"status": "error", "message": "invalid integers"}`.
- Si tout est correct, on appelle :

```python
bridge.call("set_matrix_frame", v0, v1, v2, v3)
```

Ce qui déclenche l’exécution de la fonction `set_matrix_frame(...)` côté STM32 (prévue dans `sketch.ino` via `Bridge.provide(...)`).

- La fonction renvoie enfin une réponse JSON simple : `{"status": "ok"}`.
  
# 🔷 5. Transmission au STM32 avec `Bridge.call(...)`

La communication avec le microcontrôleur se fait par :

```python
bridge.call("set_matrix_frame", v0, v1, v2, v3)
```

- `"set_matrix_frame"` : nom de la fonction publiée côté STM32 via `Bridge.provide("set_matrix_frame", ...)`.
- `v0..v3` : valeurs numériques correspondant aux 4 mots `uint32_t`.

Le Bridge se charge :

- de sérialiser les données (MsgPack),
- de les transmettre au microcontrôleur,
- d’appeler la fonction correspondante côté STM32,
- éventuellement de remonter une réponse (si la fonction STM32 en retourne une).

Dans ce projet, la fonction STM32 applique directement `matrixWrite()` puis se termine, il n’y a donc pas de valeur de retour particulière.

---

---

# 🔷 6. Exposition de l’API WebUI

Pour que `index.html` puisse appeler `/set_frame/...`, il faut déclarer cette route dans WebUI :

```python
ui.expose_api("GET", "/set_frame/{w0}/{w1}/{w2}/{w3}", on_set_frame)
```

- Méthode HTTP : `"GET"`
- Chemin : `"/set_frame/{w0}/{w1}/{w2}/{w3}"`
  - Les parties `{w0}`, `{w1}`, `{w2}`, `{w3}` sont des **variables d’URL**.
- Handler : `on_set_frame` sera appelé avec ces paramètres.

Ainsi, dans `index.html`, l’appel :

```js
fetch(`/set_frame/${out[0]}/${out[1]}/${out[2]}/${out[3]}`)
```

est routé directement vers la fonction Python `on_set_frame(...)`.

---


# 🔷 7. Boucle principale de l’application

À la fin de `main.py`, on trouve :

```python
App.run()
```

Cette ligne :

- lance l’application App Lab,
- démarre la boucle d’événements nécessaire au WebUI,
- maintient l’application en fonctionnement tant que le projet est en cours d’exécution.

Sans `App.run()`, l’application se terminerait immédiatement.

---

# 🔷 8. Résumé du flux dans `main.py`

1. `WebUI` reçoit une requête HTTP `GET /set_frame/w0/w1/w2/w3`.
2. `on_set_frame(w0, w1, w2, w3)` est exécuté.
3. Les paramètres sont convertis en entiers (`v0..v3`).
4. `bridge.call("set_matrix_frame", v0, v1, v2, v3)` envoie les valeurs au STM32.
5. Le STM32 met à jour sa matrice LED via `matrixWrite(frame)`.
6. `on_set_frame` renvoie une réponse JSON (`{"status": "ok"}`) au navigateur Web.

---

# ✔️ Conclusion

Le fichier `main.py` :

- constitue le **cœur logique** côté Linux,
- relie l’interface Web (JavaScript) à la logique embarquée STM32,
- illustre l’utilisation combinée de :
  - `WebUI` pour exposer une API HTTP locale,
  - `Bridge` pour envoyer des appels RPC au microcontrôleur,
  - `App.run()` pour faire tourner l’application App Lab.

Il sert de modèle pour tout projet UNO Q nécessitant :

- une interface Web locale,
- et une liaison temps réel avec le firmware STM32.

