# Local Patches

Patches are applied automatically by `scripts/sync_xlerobot_into_lerobot.sh`
after syncing XLeRobot sources into the lerobot tree.

## xbox_teleop_local.patch

Local tweaks to the Xbox teleoperation example at
`lerobot/examples/xlerobot/5_xlerobot_teleop_xbox.py`.

## joycon_shared_handle.patch

Replaces the three separate HID handles (JoyCon + GyroTrackingJoyCon +
ButtonEventJoyCon) with a single `SharedJoyCon` handle. macOS does not allow
opening the same HID device multiple times.

## Regenerating a patch

```bash
diff -u \
  XLeRobot/software/joyconrobotics/joyconrobotics.py \
  lerobot/src/joyconrobotics/joyconrobotics.py \
  > patches/joycon_shared_handle.patch || true
```
