#!/usr/bin/env python3
"""Print raw Xbox controller inputs for mapping checks."""

from __future__ import annotations

import time

import pygame


BUTTON_NAMES_DPAD = {
    0: "A",
    1: "B",
    2: "X",
    3: "Y",
    4: "View/Back",
    5: "Xbox/Guide",
    6: "Menu",
    7: "Left Stick Press",
    8: "Right Stick Press",
    9: "LB",
    10: "RB",
    11: "D-pad Up",
    12: "D-pad Down",
    13: "D-pad Left",
    14: "D-pad Right",
}

AXIS_NAMES = {
    0: "Left Stick X",
    1: "Left Stick Y",
    2: "Left Trigger or Right Stick X",
    3: "Right Stick X or Y",
    4: "Right Stick Y or Left Trigger",
    5: "Right Trigger",
}


def main() -> None:
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        raise SystemExit("No controller detected by pygame.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"name={joystick.get_name()}")
    print(f"guid={joystick.get_guid()}")
    print(f"axes={joystick.get_numaxes()} buttons={joystick.get_numbuttons()} hats={joystick.get_numhats()}")
    print("Press buttons or move sticks/triggers. Ctrl+C to exit.")

    last_buttons = [0] * joystick.get_numbuttons()
    last_axes = [0.0] * joystick.get_numaxes()
    last_hats = [(0, 0)] * joystick.get_numhats()

    try:
        while True:
            pygame.event.pump()

            for i in range(joystick.get_numbuttons()):
                value = joystick.get_button(i)
                if value != last_buttons[i]:
                    name = BUTTON_NAMES_DPAD.get(i, f"button {i}")
                    print(f"button {i:02d} {name}: {value}")
                    last_buttons[i] = value

            for i in range(joystick.get_numaxes()):
                value = joystick.get_axis(i)
                if abs(value - last_axes[i]) > 0.2:
                    name = AXIS_NAMES.get(i, f"axis {i}")
                    print(f"axis {i:02d} {name}: {value:+.3f}")
                    last_axes[i] = value

            for i in range(joystick.get_numhats()):
                value = joystick.get_hat(i)
                if value != last_hats[i]:
                    print(f"hat {i}: {value}")
                    last_hats[i] = value

            time.sleep(0.03)
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
