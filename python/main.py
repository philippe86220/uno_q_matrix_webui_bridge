from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI

print("Starting UNO Q Matrix WebUI app...")

# Bridge vers le STM32
bridge = Bridge()

# Web UI
ui = WebUI()


def on_set_frame(w0: str, w1: str, w2: str, w3: str):
    """
    Handler API appele par l'URL:
      /set_frame/{w0}/{w1}/{w2}/{w3}

    Les valeurs arrivent en texte, on les convertit en int,
    puis on appelle la fonction C++ 'set_matrix_frame'
    exposee cote STM32 via RouterBridge.
    """
    try:
        v0 = int(w0)
        v1 = int(w1)
        v2 = int(w2)
        v3 = int(w3)
    except ValueError:
        print("Invalid frame values:", w0, w1, w2, w3)
        return {"status": "error", "message": "invalid integers"}

    print("Sending frame to STM32:", v0, v1, v2, v3)

    # Appel RPC vers le microcontroleur
    bridge.call("set_matrix_frame", v0, v1, v2, v3)

    return {"status": "ok"}


# Endpoint REST pour le WebUI (GET avec 4 parametres dans l'URL)
ui.expose_api("GET", "/set_frame/{w0}/{w1}/{w2}/{w3}", on_set_frame)

# Boucle principale
App.run()

