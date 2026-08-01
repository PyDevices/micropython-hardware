"""MicroPython SAM -> audiodev -> SDL2 speaker demo."""

from sam_sdl import speak


def main():
    audio_out = speak(
        "Hello Brad. Micro Python audio is working. I am speaking through S D L two."
    )
    audio_out.close()


if __name__ == "__main__":
    main()
