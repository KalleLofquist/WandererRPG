# sounds.py — Procedurally generated sound effects and ambient music.
#
# All sounds are synthesised at runtime using numpy arrays so no external
# audio files are needed.  If numpy is unavailable every function degrades
# to a no-op — the game remains fully playable, just silent.
#
# Usage:
#   import sounds
#   pygame.mixer.pre_init(44100, -16, 1, 512)   # BEFORE pygame.init()
#   pygame.init()
#   sounds.init()                                 # generate all assets

import pygame

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:
    _NUMPY_OK = False

# ---- Audio constants ---------------------------------------------------
_SAMPLE_RATE = 44100   # Hz — must match pre_init
_SFX_VOL     = 0.4     # 0.0 – 1.0
_MUSIC_VOL   = 0.15    # quieter than SFX

# ---- Cached Sound objects (None until init() is called) ----------------
_swing         = None
_hit_enemy     = None
_hit_player    = None
_potion        = None
_dialogue      = None
_level_up_sound = None
_town_drone    = None
_dungeon_drone = None
_music_channel = None   # pygame.mixer.Channel reserved for ambient music


# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #

def _to_sound(arr) -> pygame.Sound:
    """
    Convert a 1-D int16 numpy array to a pygame Sound.

    pygame-ce initialises the mixer as stereo (2 channels) regardless of the
    pre_init channel argument, so make_sound always needs a (n_samples, 2)
    array.  We duplicate the mono signal into both channels.
    """
    arr = np.ascontiguousarray(arr, dtype=np.int16)
    # Always produce stereo — duplicate mono into left + right channels
    stereo = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(stereo)


def _sweep_sound(freq_start: float, freq_end: float, duration: float,
                 decay_rate: float = 10.0, vol: float = 1.0):
    """
    Sine wave with a linear frequency sweep and exponential decay envelope.

    Args:
        freq_start:  Start frequency (Hz).
        freq_end:    End frequency (Hz).
        duration:    Length in seconds.
        decay_rate:  Controls how quickly the sound fades (higher = faster).
        vol:         Peak volume (0.0 – 1.0).
    """
    n   = int(_SAMPLE_RATE * duration)
    t   = np.linspace(0, duration, n, endpoint=False, dtype=np.float32)
    # Instantaneous frequency at each sample
    inst_freq = freq_start + (freq_end - freq_start) * (t / duration)
    # Phase via cumulative sum of instantaneous frequency
    phase = 2.0 * np.pi * np.cumsum(inst_freq) / _SAMPLE_RATE
    env   = np.exp(-t * decay_rate).astype(np.float32)
    wave  = np.sin(phase).astype(np.float32) * env * vol
    return (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)


def _sine_sound(freq: float, duration: float, decay_rate: float = 10.0,
                vol: float = 1.0):
    """Constant-frequency sine with exponential decay."""
    return _sweep_sound(freq, freq, duration, decay_rate, vol)


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #

def init() -> None:
    """
    Generate all sound assets.  Must be called once after pygame.init().
    Safe to call even if numpy is unavailable — does nothing in that case.
    """
    global _swing, _hit_enemy, _hit_player, _potion, _dialogue
    global _level_up_sound, _town_drone, _dungeon_drone, _music_channel

    if not _NUMPY_OK:
        return

    sr = _SAMPLE_RATE

    # ---- swing — 0.12 s, swoosh: 400 Hz → 200 Hz, linear fade out ------
    try:
        n    = int(sr * 0.12)
        t    = np.linspace(0, 0.12, n, endpoint=False, dtype=np.float32)
        freq = 400.0 - (200.0 / 0.12) * t          # linear sweep
        phase = 2.0 * np.pi * np.cumsum(freq) / sr
        env  = np.linspace(1.0, 0.0, n, dtype=np.float32)
        wave = (np.sin(phase).astype(np.float32) * env * 32767).astype(np.int16)
        _swing = _to_sound(wave)
        _swing.set_volume(_SFX_VOL)
    except Exception:
        pass

    # ---- hit_enemy — 0.1 s, low thud: 120 Hz + white noise, fast decay -
    try:
        n   = int(sr * 0.10)
        t   = np.linspace(0, 0.10, n, endpoint=False, dtype=np.float32)
        rng = np.random.default_rng(seed=1)
        decay = np.exp(-t * 35.0).astype(np.float32)
        noise = (rng.random(n).astype(np.float32) * 2.0 - 1.0) * 0.35
        wave  = (np.sin(2.0 * np.pi * 120.0 * t).astype(np.float32) + noise) * decay
        wave  = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
        _hit_enemy = _to_sound(wave)
        _hit_enemy.set_volume(_SFX_VOL)
    except Exception:
        pass

    # ---- hit_player — 0.15 s, hurt sound: 300 Hz → 150 Hz, moderate decay
    try:
        wave = _sweep_sound(300.0, 150.0, 0.15, decay_rate=12.0, vol=_SFX_VOL)
        _hit_player = _to_sound(wave)
        _hit_player.set_volume(_SFX_VOL)
    except Exception:
        pass

    # ---- potion — 0.2 s, chime: C5 (523 Hz) + E5 (659 Hz), bell envelope
    try:
        n   = int(sr * 0.20)
        t   = np.linspace(0, 0.20, n, endpoint=False, dtype=np.float32)
        # Fast attack (1 % of samples), then exponential decay
        env = np.exp(-t * 8.0).astype(np.float32)
        att = max(1, int(n * 0.01))
        env[:att] = np.linspace(0.0, 1.0, att, dtype=np.float32)
        wave = ((np.sin(2.0 * np.pi * 523.0 * t) +
                 np.sin(2.0 * np.pi * 659.0 * t)).astype(np.float32)
                * env * 0.5)
        wave = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
        _potion = _to_sound(wave)
        _potion.set_volume(_SFX_VOL)
    except Exception:
        pass

    # ---- dialogue — 0.08 s, 440 Hz square-ish bleep (odd harmonics) -----
    try:
        n   = int(sr * 0.08)
        t   = np.linspace(0, 0.08, n, endpoint=False, dtype=np.float32)
        wave = (np.sin(2.0 * np.pi * 440.0  * t)
              + 0.33 * np.sin(2.0 * np.pi * 1320.0 * t)
              + 0.20 * np.sin(2.0 * np.pi * 2200.0 * t)).astype(np.float32)
        env  = np.linspace(1.0, 0.0, n, dtype=np.float32)
        wave = (np.clip(wave * env, -1.0, 1.0) * 32767).astype(np.int16)
        _dialogue = _to_sound(wave)
        _dialogue.set_volume(_SFX_VOL)
    except Exception:
        pass

    # ---- level_up — 0.4 s ascending arpeggio: C5(523)+E5(659)+G5(784) ----
    try:
        n = int(sr * 0.4)
        t = np.linspace(0, 0.4, n, endpoint=False, dtype=np.float32)
        n3 = n // 3
        wave = np.zeros(n, dtype=np.float32)
        for i, freq in enumerate([523.0, 659.0, 784.0]):
            start = i * n3
            end   = min(start + n3, n)
            seg_t = t[start:end] - t[start]
            env   = np.exp(-seg_t * 12.0).astype(np.float32)
            wave[start:end] += np.sin(2.0 * np.pi * freq * seg_t).astype(np.float32) * env
        wave = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
        _level_up_sound = _to_sound(wave)
        _level_up_sound.set_volume(_SFX_VOL)
    except Exception:
        _level_up_sound = None

    # ---- town drone — 2 s loop, 110 Hz + 220 Hz gentle blend -----------
    try:
        n = int(sr * 2.0)
        t = np.linspace(0, 2.0, n, endpoint=False, dtype=np.float32)
        wave = (0.6 * np.sin(2.0 * np.pi * 110.0 * t)
              + 0.4 * np.sin(2.0 * np.pi * 220.0 * t)).astype(np.float32)
        # Gentle amplitude modulation at 0.5 Hz for warmth
        wave *= (1.0 + 0.08 * np.sin(2.0 * np.pi * 0.5 * t))
        wave  = np.clip(wave, -1.0, 1.0)
        wave  = (wave * 32767).astype(np.int16)
        _town_drone = _to_sound(wave)
        _town_drone.set_volume(_MUSIC_VOL)
    except Exception:
        pass

    # ---- dungeon drone — 2 s loop, 80 Hz + 160 Hz darker ---------------
    try:
        n = int(sr * 2.0)
        t = np.linspace(0, 2.0, n, endpoint=False, dtype=np.float32)
        wave = (0.7 * np.sin(2.0 * np.pi *  80.0 * t)
              + 0.3 * np.sin(2.0 * np.pi * 160.0 * t)).astype(np.float32)
        # Slightly ominous 0.3 Hz modulation
        wave *= (1.0 + 0.12 * np.sin(2.0 * np.pi * 0.3 * t))
        wave  = np.clip(wave, -1.0, 1.0)
        wave  = (wave * 32767).astype(np.int16)
        _dungeon_drone = _to_sound(wave)
        _dungeon_drone.set_volume(_MUSIC_VOL)
    except Exception:
        pass

    # Reserve channel 0 exclusively for ambient music
    try:
        pygame.mixer.set_reserved(1)
        _music_channel = pygame.mixer.Channel(0)
    except Exception:
        pass


# ---- Sound-effect play functions -------------------------------------

def play_swing() -> None:
    """Short swoosh on player attack."""
    if _swing:
        try:
            _swing.play()
        except Exception:
            pass


def play_hit_enemy() -> None:
    """Punchy thud when an enemy takes damage."""
    if _hit_enemy:
        try:
            _hit_enemy.play()
        except Exception:
            pass


def play_hit_player() -> None:
    """Hurt sound when the player takes damage."""
    if _hit_player:
        try:
            _hit_player.play()
        except Exception:
            pass


def play_potion() -> None:
    """Chime when a health potion is collected."""
    if _potion:
        try:
            _potion.play()
        except Exception:
            pass


def play_dialogue() -> None:
    """Short bleep when dialogue advances."""
    if _dialogue:
        try:
            _dialogue.play()
        except Exception:
            pass


def play_level_up() -> None:
    """Ascending arpeggio chime on player level-up."""
    if _level_up_sound:
        try:
            _level_up_sound.play()
        except Exception:
            pass


# ---- Music control ---------------------------------------------------

def play_music_town() -> None:
    """Start (or restart) the town ambient drone loop."""
    if _music_channel and _town_drone:
        try:
            _music_channel.stop()
            _music_channel.play(_town_drone, loops=-1)
        except Exception:
            pass


def play_music_dungeon() -> None:
    """Start (or restart) the dungeon ambient drone loop."""
    if _music_channel and _dungeon_drone:
        try:
            _music_channel.stop()
            _music_channel.play(_dungeon_drone, loops=-1)
        except Exception:
            pass


def stop_music() -> None:
    """Stop ambient music playback."""
    if _music_channel:
        try:
            _music_channel.stop()
        except Exception:
            pass
