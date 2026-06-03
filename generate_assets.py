# generate_assets.py - Genera la música y los efectos 8-bit del juego.
#
# Usa SOLO la librería estándar (wave, struct, math, random): no requiere
# numpy ni pygame. Produce archivos .wav en assets/ que el juego carga con
# pygame.mixer.  Para regenerar:  python generate_assets.py
#
# Estética chiptune: ondas cuadradas (square wave) + ruido para explosiones.

import wave
import struct
import math
import random
import os

SR = 22050  # frecuencia de muestreo (suficiente para 8-bit)

ASSETS = os.path.join(os.path.dirname(__file__), 'assets')


# ---------------------------------------------------------------------------
# Síntesis básica
# ---------------------------------------------------------------------------

def midi_freq(m):
    """Frecuencia (Hz) de una nota MIDI."""
    return 440.0 * (2 ** ((m - 69) / 12.0))


def _env(i, n, attack=0.01, release=0.04):
    """Envolvente simple ataque/decaimiento (0..1) para evitar clics."""
    t = i / SR
    dur = n / SR
    if t < attack:
        return t / attack
    if t > dur - release:
        return max(0.0, (dur - t) / release)
    return 1.0


def square(freq, n, vol=0.3, duty=0.5):
    """Onda cuadrada de `n` muestras."""
    if freq <= 0:
        return [0.0] * n
    period = SR / freq
    out = [0.0] * n
    for i in range(n):
        phase = (i % period) / period
        out[i] = (vol if phase < duty else -vol) * _env(i, n)
    return out


def sweep(f0, f1, dur, vol=0.3, duty=0.5):
    """Onda cuadrada con barrido de frecuencia (para disparos)."""
    n = int(dur * SR)
    out = [0.0] * n
    phase = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        phase += f / SR
        ph = phase - math.floor(phase)
        out[i] = (vol if ph < duty else -vol) * max(0.0, 1 - i / n)
    return out


def noise(dur, vol=0.4, decay=True):
    """Ruido blanco con decaimiento (para explosiones)."""
    n = int(dur * SR)
    out = [0.0] * n
    for i in range(n):
        s = random.uniform(-1, 1) * vol
        if decay:
            s *= max(0.0, 1 - i / n)
        out[i] = s
    return out


def track(notes, bpm, vol=0.25, duty=0.5):
    """Convierte [(midi|None, beats)] en muestras de onda cuadrada."""
    beat = 60.0 / bpm
    out = []
    for midi, beats in notes:
        n = int(beat * beats * SR)
        if midi is None:
            out += [0.0] * n
        else:
            out += square(midi_freq(midi), n, vol, duty)
    return out


def mix(*tracks):
    """Suma varias pistas (mono), recortando a [-1, 1]."""
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i in range(len(t)):
            out[i] += t[i]
    return [max(-1.0, min(1.0, s)) for s in out]


def write_wav(name, samples):
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for s in samples:
            frames += struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32000))
        w.writeframes(bytes(frames))
    print(f"  {name:18} {len(samples)/SR:5.2f}s  ({len(samples)*2} bytes)")


# ---------------------------------------------------------------------------
# Música del menú (La menor, tono tranquilo/marcial)
# ---------------------------------------------------------------------------

def make_menu_music():
    mel = [
        (69, 1), (72, 1), (76, 1), (72, 1),
        (74, 1), (71, 1), (67, 2),
        (69, 1), (72, 1), (76, 1), (81, 1),
        (76, 1), (72, 1), (69, 2),
    ]
    bass = [
        (45, 4),   # A2
        (50, 4),   # D3
        (40, 4),   # E2
        (45, 4),
    ]
    m = track(mel,  bpm=120, vol=0.22, duty=0.5)
    b = track(bass, bpm=120, vol=0.18, duty=0.25)
    write_wav('music_menu.wav', mix(m, b))


# ---------------------------------------------------------------------------
# Música de partida (más rápida y enérgica)
# ---------------------------------------------------------------------------

def make_game_music():
    mel = [
        (69, .5), (76, .5), (69, .5), (72, .5), (71, .5), (67, .5), (71, .5), (69, .5),
        (74, .5), (69, .5), (74, .5), (77, .5), (76, 1), (72, 1),
        (69, .5), (76, .5), (69, .5), (72, .5), (71, .5), (67, .5), (71, .5), (74, .5),
        (76, .5), (72, .5), (69, .5), (64, .5), (69, 2),
    ]
    bass = [
        (45, 1), (45, 1), (52, 1), (45, 1),
        (50, 1), (50, 1), (45, 1), (40, 1),
        (45, 1), (45, 1), (52, 1), (45, 1),
        (40, 1), (40, 1), (45, 2),
    ]
    m = track(mel,  bpm=160, vol=0.20, duty=0.5)
    b = track(bass, bpm=160, vol=0.20, duty=0.25)
    write_wav('music_game.wav', mix(m, b))


# ---------------------------------------------------------------------------
# Efectos de sonido
# ---------------------------------------------------------------------------

def make_sfx():
    # Disparo: "pew" descendente rápido
    write_wav('shoot.wav', sweep(900, 200, 0.12, vol=0.30, duty=0.5))

    # Explosión de tanque: ruido con cuerpo grave
    body = square(110, int(0.30 * SR), vol=0.20, duty=0.5)
    write_wav('explosion.wav', mix(noise(0.40, vol=0.45), body))

    # Destrucción de base: explosión más larga + barrido grave
    write_wav('base_destroy.wav',
              mix(noise(0.70, vol=0.45), sweep(300, 40, 0.70, vol=0.25)))


if __name__ == '__main__':
    print("Generando assets de audio 8-bit en", ASSETS)
    make_menu_music()
    make_game_music()
    make_sfx()
    print("Listo.")
