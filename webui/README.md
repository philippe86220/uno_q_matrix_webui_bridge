# Documentation complète – `webui/index.html`

Ce document explique **en détail** le fonctionnement du fichier `index.html` utilisé dans le projet UNO Q pour piloter la matrice 13×8 via WebUI.

Il couvre :
- la structure HTML,
- le style CSS,
- la logique JavaScript,
- la génération des 4 mots `uint32_t`,
- l’envoi des données vers la UNO Q via une requête REST.

---

# 🔷 1. Objectif du fichier `index.html`

Ce fichier joue le rôle d’**interface Web locale** dans Arduino App Lab.  
Il permet à l’utilisateur :

1. de cliquer sur des cellules représentant les LEDs,  
2. de visualiser le motif,  
3. de générer les mots `uint32_t` correspondant au motif,  
4. d’envoyer le motif à la UNO Q via un appel HTTP interne (`/set_frame/...`).

L'interface repose uniquement sur **HTML + CSS + JavaScript** (sans librairie externe).

---

# 🔷 2. Structure HTML

Le fichier comporte :

- un titre
- une sous-description
- une grille `<div id="matrix">` de 13×8 cellules
- des boutons (`Générer`, `Effacer`, `Copier`, `Envoyer`)
- une zone d'affichage `<pre id="output">`

Structure simplifiée :

```html
<h1>UNO Q – Éditeur de matrice 13×8</h1>
<div id="matrix"></div>

<div class="buttons">
    <button id="btn-generate">Générer les 4 mots</button>
    <button id="btn-clear">Effacer</button>
    <button id="btn-copy">Copier</button>
    <button id="btn-send">Envoyer vers UNO Q</button>
</div>

<pre id="output"></pre>
```

La grille `#matrix` est remplie dynamiquement par JavaScript.

---

# 🔷 3. Le style CSS

Le CSS définit :

- une interface sombre moderne,
- la grille en 13 colonnes × 8 lignes,
- l’apparence des cellules (LEDs),
- l’état “on” et “off”.

Points clés :

- `.cell` = une LED
- `.cell.on` = LED allumée (bleue)
- `#matrix` = `display: grid` avec 13 colonnes, 8 lignes
- transition visuelle lors du clic

---

# 🔷 4. La logique JavaScript

Le cœur du fonctionnement se trouve dans un ensemble de fonctions :

---

## ✔️ 4.1. Structure de la matrice

```js
const MATRIX_WIDTH = 13;
const MATRIX_HEIGHT = 8;

const ledState = [];
for (let y = 0; y < MATRIX_HEIGHT; y++) {
    const row = [];
    for (let x = 0; x < MATRIX_WIDTH; x++) {
        row.push(false);
    }
    ledState.push(row);
}
```

`ledState[y][x]` contient l’état logique (true = LED allumée).

---

## ✔️ 4.2. Création dynamique de la grille

```js
function createGrid() {
    for (let y = 0; y < MATRIX_HEIGHT; y++) {
        for (let x = 0; x < MATRIX_WIDTH; x++) {
            const cell = document.createElement("div");
            cell.className = "cell";
            cell.dataset.x = x;
            cell.dataset.y = y;

            cell.addEventListener("click", () => {
                const cx = parseInt(cell.dataset.x);
                const cy = parseInt(cell.dataset.y);
                ledState[cy][cx] = !ledState[cy][cx];
                cell.classList.toggle("on", ledState[cy][cx]);
            });

            matrixDiv.appendChild(cell);
        }
    }
}
```

Chaque clic :

- inverse l’état dans `ledState`,
- change l’apparence visuelle via `.classList.toggle("on")`.

---

## ✔️ 4.3. Calcul des 4 mots `uint32_t`

C’est la partie essentielle.

Chaque LED correspond à un bit dans un tableau de 4 mots :

- 104 LEDs = 104 bits  
- 104 bits / 32 = 4 mots de 32 bits (reste 24 bits inutilisés)

Fonction de calcul :

```js
function computeFrameWords() {
    const out = [0, 0, 0, 0];

    for (let y = 0; y < MATRIX_HEIGHT; y++) {
        for (let x = 0; x < MATRIX_WIDTH; x++) {
            if (!ledState[y][x]) continue;

            const index = y * MATRIX_WIDTH + x; // 0..103
            const mot = Math.floor(index / 32); // 0..3
            const bit = index % 32;             // 0..31

            out[mot] = (out[mot] | (1 << bit)) >>> 0;
        }
    }
    return out;
}
```

### Explication :

Pour une LED allumée à (x,y) :

```
index = y * 13 + x
mot = index / 32
bit = index % 32
```

Exemple : LED (0,0) ⇒ index 0 ⇒ mot 0, bit 0 ⇒ out[0] |= 1<<0.

---

## ✔️ 4.4. Génération du code C++

Le bouton “Générer les 4 mots” convertit les valeurs en hexadécimal :

```js
function generateWords() {
    const out = computeFrameWords();
    let text = "const uint32_t frame[4] = {
";
    ...
    output.textContent = text;
}
```

---

## ✔️ 4.5. Envoi des données à la UNO Q

Voilà la partie la plus importante côté communication :

```js
async function sendFrameToUnoQ() {
    const out = computeFrameWords();
    const url = `/set_frame/${out[0]}/${out[1]}/${out[2]}/${out[3]}`;
    await fetch(url);
}
```

Ce `fetch()` appelle :

```
/set_frame/w0/w1/w2/w3
```

Cette API est exposée dans `main.py`, puis Python transmet la trame au STM32 via :

```python
bridge.call("set_matrix_frame", w0, w1, w2, w3)
```

---

# 🔷 5. Boutons et actions

Chaque bouton correspond à :

- `btn-generate` → transforme `ledState` en tableau `frame[4]`.
- `btn-clear` → réinitialise la matrice.
- `btn-copy` → copie le code généré.
- `btn-send` → envoie la trame à la UNO Q.

Exemple de liaison :

```js
btnSend.addEventListener("click", sendFrameToUnoQ);
```

---

# 🔷 6. Initialisation

À la fin du script :

```js
createGrid();
```

La grille est générée lors du chargement de la page.

---

# 🔷 7. Résumé du fonctionnement général

1. L’utilisateur clique : `ledState` change.
2. Les bits correspondants sont positionnés dans 4 mots `uint32_t`.
3. Le bouton “Envoyer vers UNO Q” appelle :
   - `/set_frame/w0/w1/w2/w3`
4. Python reçoit ces valeurs et appelle :
   - `bridge.call("set_matrix_frame", ...)`
5. Le STM32 écrit ces valeurs dans :
   - `matrixWrite(frame)`
6. La matrice s’allume en temps réel.

---

# ✔️ Conclusion

Le fichier `index.html` :

- fait l’interface interactive complète,
- calcule toutes les données nécessaires,
- utilise WebUI comme passerelle HTTP interne,
- constitue l’une des démonstrations les plus claires de l’usage combiné :
  - HTML,
  - JavaScript,
  - Python App Lab,
  - Bridge RPC,
  - STM32 + matrixWrite().

Il est autonome, lisible, et peut être réutilisé comme base pour des animations, du scrolling texte ou un éditeur de sprites.


