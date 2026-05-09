# Local Patches

`xbox_teleop_local.patch` is the local patch applied to the copied XLeRobot Xbox teleoperation example at:

```text
lerobot/examples/xlerobot/5_xlerobot_teleop_xbox.py
```

Regenerate it after editing the local example:

```bash
cd /Users/shaw/Project/ant510
diff -u \
  robot/XLeRobot/software/examples/5_xlerobot_teleop_xbox.py \
  robot/lerobot/examples/xlerobot/5_xlerobot_teleop_xbox.py \
  > robot/patches/xbox_teleop_local.patch || true
```

Reapply it after resyncing XLeRobot into LeRobot:

```bash
cd /Users/shaw/Project/ant510
patch robot/lerobot/examples/xlerobot/5_xlerobot_teleop_xbox.py \
  robot/patches/xbox_teleop_local.patch
```
