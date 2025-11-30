#include <Arduino.h>
#include <Arduino_RouterBridge.h>

extern "C" void matrixWrite(const uint32_t *buf);
extern "C" void matrixBegin();

static uint32_t currentFrame[4];

// Fonction appellee depuis Linux via Bridge.call("set_matrix_frame", ...)
void set_matrix_frame(uint32_t w0, uint32_t w1, uint32_t w2, uint32_t w3) {
  currentFrame[0] = w0;
  currentFrame[1] = w1;
  currentFrame[2] = w2;
  currentFrame[3] = w3;

  matrixWrite(currentFrame);
}

void setup() {
  // Initialisation de la matrice
  matrixBegin();

  // Initialisation de la Bridge RPC cote MCU
  Bridge.begin();

  // On expose la fonction 'set_matrix_frame' au monde Python
  Bridge.provide("set_matrix_frame", set_matrix_frame);
}

void loop() {
  // Rien a faire ici, le MCU attend simplement les appels Bridge
}

