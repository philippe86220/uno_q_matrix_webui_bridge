# Documentation complète – `mcu/sketch.ino`

Ce document explique **en détail** le fonctionnement du fichier `sketch.ino` utilisé dans le projet UNO Q pour recevoir les données envoyées par Python via Bridge, puis mettre à jour la matrice LED 13×8 grâce à `matrixWrite()`.

Ce fichier s’exécute sur le **microcontrôleur STM32 U585** de la UNO Q.

---

# 🔷 1. Rôle général de `sketch.ino`

Le code firmware :

1. initialise la matrice LED,
2. configure la communication Bridge,
3. expose une fonction RPC (`set_matrix_frame`) que Python peut appeler,
4. reçoit 4 mots `uint32_t` envoyés par Python,
5. applique ces mots à la matrice via `matrixWrite()`.

Ce fichier représente la partie **temps réel** de l’architecture UNO Q :

```
HTML/JS → Python → Bridge → STM32 → matrixWrite()
```

---

# 🔷 2. Les includes principaux

```cpp
#include <Arduino.h>
#include <Arduino_RouterBridge.h>

extern "C" void matrixWrite(const uint32_t *buf);
extern "C" void matrixBegin();
```

### Explications :

- **Arduino.h** : base de l’API Arduino.
- **Arduino_RouterBridge.h** : permet d’exposer des fonctions RPC que Python peut appeler.
- Les fonctions `matrixWrite()` et `matrixBegin()` viennent du firmware interne de la UNO Q.
  - `matrixBegin()` : initialise la matrice Q-Matrix.
  - `matrixWrite(buf)` : affiche 104 bits contenus dans `buf[4]`.

---

# 🔷 3. Stockage de la trame LED

```cpp
static uint32_t currentFrame[4];
```

Ce tableau contient les **4 mots de 32 bits** correspondant aux 104 LEDs.

- `currentFrame[0]` → bits 0 à 31  
- `currentFrame[1]` → bits 32 à 63  
- `currentFrame[2]` → bits 64 à 95  
- `currentFrame[3]` → bits 96 à 103 (seulement 8 bits utiles)

---

# 🔷 4. Fonction RPC : `set_matrix_frame()`

C’est **la fonction la plus importante du fichier**.

Elle est appelée depuis Python grâce à :

```python
bridge.call("set_matrix_frame", v0, v1, v2, v3)
```

Définition dans `sketch.ino` :

```cpp
void set_matrix_frame(uint32_t w0, uint32_t w1, uint32_t w2, uint32_t w3) {
  currentFrame[0] = w0;
  currentFrame[1] = w1;
  currentFrame[2] = w2;
  currentFrame[3] = w3;

  matrixWrite(currentFrame);
}
```

### Explication :

1. Les quatre valeurs reçues sont copiées dans `currentFrame[4]`.
2. La fonction `matrixWrite(currentFrame)` est appelée.
3. La matrice LED s’actualise immédiatement.

Cette fonction ne retourne rien : elle agit directement sur le matériel.

---

# 🔷 5. Initialisation : `setup()`

```cpp
void setup() {
  matrixBegin();       // initialise la matrice LED
  Bridge.begin();      // initialise la communication RPC Linux ↔ STM32
  Bridge.provide("set_matrix_frame", set_matrix_frame);
}
```

### Détail :

- `matrixBegin()` :
  - configure la Q-Matrix de la UNO Q,
  - doit impérativement être appelée avant `matrixWrite()`.

- `Bridge.begin()` :
  - active la couche de communication interne (MsgPack),
  - prépare le microcontrôleur à recevoir des appels RPC.

- `Bridge.provide(...)` :
  - expose la fonction `set_matrix_frame()` sous un nom public,
  - ce nom doit correspondre à celui utilisé par Python :
    ```python
    bridge.call("set_matrix_frame", ...)
    ```

---

# 🔷 6. Boucle principale : `loop()`

```cpp
void loop() {
  // Rien à faire ici.
}
```

Ce firmware fonctionne **uniquement à l’aide des RPC**.

Pas besoin de :

- scruter des entrées,
- gérer des timers,
- mettre à jour l’affichage en boucle.

Tout se passe à l’appel de `matrixWrite()`.

---

# 🔷 7. Résumé du fonctionnement de `sketch.ino`

1. Le STM32 démarre.
2. La matrice LED est initialisée (`matrixBegin()`).
3. Le microcontrôleur expose `set_matrix_frame` via Bridge.
4. Le cœur Linux exécute Python (App Lab).
5. Le JavaScript appelle `/set_frame/...`.
6. Python convertit les paramètres en entiers et fait :
   ```
   bridge.call("set_matrix_frame", w0, w1, w2, w3)
   ```
7. Le STM32 reçoit les valeurs et les applique immédiatement :
   ```
   matrixWrite(currentFrame)
   ```
8. La matrice affiche le motif choisi par l’utilisateur.

---

# ✔️ Conclusion

Le fichier `sketch.ino` :

- représente la couche **firmware temps réel** de la UNO Q,
- utilise `Bridge.provide()` pour exposer une fonction RPC callable depuis Linux,
- reçoit les données envoyées par la WebUI via Python,
- affiche les LEDs grâce à `matrixWrite()`.

C’est un modèle minimal, clair et efficace pour comprendre la liaison :

**Interface Web → Python → STM32 → Hardware**

