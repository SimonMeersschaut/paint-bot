# Diff Report

Source: `diff.txt`

## Summary

- Files changed: 4
- Additions: 7
- Deletions: 9

| File | Status | + | - |
| --- | --- | ---: | ---: |
| .gitignore | modified | 5 | 5 |
| Marlin/src/pins/pins.h | modified | 0 | 2 |
| ini/avr.ini | modified | 1 | 1 |
| ini/samd21.ini | modified | 1 | 1 |

## File Details

## .gitignore

- Status: modified
- Additions: 5
- Deletions: 5

<details>
<summary>Patch metadata</summary>

```text
old mode 100755
new mode 100644
index 0e22a1a0ab..bbf1e495db 100644
--- a/Marlin/Configuration.h
+++ b/Marlin/Configuration.h
```

</details>

<details open>
<summary>Unified diff</summary>

```diff
diff --git a/.gitignore b/.gitignore
old mode 100755
new mode 100644
index 0e22a1a0ab..bbf1e495db 100644
--- a/Marlin/Configuration.h
+++ b/Marlin/Configuration.h
@@ -1196,7 +1196,7 @@
  * Override with M92
  *                                      X, Y, Z [, I [, J [, K...]]], E0 [, E1[, E2...]]
  */
-#define DEFAULT_AXIS_STEPS_PER_UNIT   { 80, 80, 400, 500 }
+#define DEFAULT_AXIS_STEPS_PER_UNIT   { 93, 93, 400, 500}
 
 /**
  * Default Max Feed Rate (linear=mm/s, rotational=┬░/s)
@@ -1651,7 +1651,7 @@
 // WARNING: When motors turn off there is a chance of losing position accuracy!
 //#define DISABLE_X
 //#define DISABLE_Y
-//#define DISABLE_Z
+#define DISABLE_Z
 //#define DISABLE_I
 //#define DISABLE_J
 //#define DISABLE_K
@@ -1724,8 +1724,8 @@
 // @section geometry
 
 // The size of the printable area
-#define X_BED_SIZE 200
-#define Y_BED_SIZE 200
+#define X_BED_SIZE 220
+#define Y_BED_SIZE 220
 
 // Travel limits (linear=mm, rotational=┬░) after homing, corresponding to endstop positions.
 #define X_MIN_POS 0
@@ -1733,7 +1733,7 @@
 #define Z_MIN_POS 0
 #define X_MAX_POS X_BED_SIZE
 #define Y_MAX_POS Y_BED_SIZE
-#define Z_MAX_POS 200
+#define Z_MAX_POS 220
 //#define I_MIN_POS 0
 //#define I_MAX_POS 50
 //#define J_MIN_POS 0
```

</details>

## Marlin/src/pins/pins.h

- Status: modified
- Additions: 0
- Deletions: 2

<details>
<summary>Patch metadata</summary>

```text
index a59ef36d77..626a52a571 100644
--- a/Marlin/src/pins/pins.h
+++ b/Marlin/src/pins/pins.h
```

</details>

<details open>
<summary>Unified diff</summary>

```diff
diff --git a/Marlin/src/pins/pins.h b/Marlin/src/pins/pins.h
index a59ef36d77..626a52a571 100644
--- a/Marlin/src/pins/pins.h
+++ b/Marlin/src/pins/pins.h
@@ -670,8 +670,6 @@
   #include "stm32f4/pins_RUMBA32_BTT.h"             // STM32F4                              env:rumba32
 #elif MB(BLACK_STM32F407VE)
   #include "stm32f4/pins_BLACK_STM32F407VE.h"       // STM32F4                              env:STM32F407VE_black
-#elif MB(BTT_SKR_MINI_E3_V3_0_1)
-  #include "stm32f4/pins_BTT_SKR_MINI_E3_V3_0_1.h"  // STM32F4                              env:STM32F401RC_btt env:STM32F401RC_btt_xfer
 #elif MB(BTT_SKR_PRO_V1_1)
   #include "stm32f4/pins_BTT_SKR_PRO_V1_1.h"        // STM32F4                              env:BIGTREE_SKR_PRO env:BIGTREE_SKR_PRO_usb_flash_drive
 #elif MB(BTT_SKR_PRO_V1_2)
```

</details>

## ini/avr.ini

- Status: modified
- Additions: 1
- Deletions: 1

<details>
<summary>Patch metadata</summary>

```text
index 5e7861037d..a0c6014481 100644
--- a/ini/avr.ini
+++ b/ini/avr.ini
```

</details>

<details open>
<summary>Unified diff</summary>

```diff
diff --git a/ini/avr.ini b/ini/avr.ini
index 5e7861037d..a0c6014481 100644
--- a/ini/avr.ini
+++ b/ini/avr.ini
@@ -13,7 +13,7 @@
 # AVR (8-bit) Common Environment values
 #
 [common_avr8]
-platform          = atmelavr@~4.0.1
+platform          = atmelavr@*
 build_flags       = ${common.build_flags} -std=gnu++1z -Wl,--relax
 build_unflags     = -std=gnu++11
 board_build.f_cpu = 16000000L
```

</details>

## ini/samd21.ini

- Status: modified
- Additions: 1
- Deletions: 1

<details>
<summary>Patch metadata</summary>

```text
index 8652f13ba9..f2acf829ff 100644
--- a/ini/samd21.ini
+++ b/ini/samd21.ini
```

</details>

<details open>
<summary>Unified diff</summary>

```diff
diff --git a/ini/samd21.ini b/ini/samd21.ini
index 8652f13ba9..f2acf829ff 100644
--- a/ini/samd21.ini
+++ b/ini/samd21.ini
@@ -10,7 +10,7 @@
 #################################
 
 #
-# ReprapWorld Minitronics (Atmel SAMD21J18 ARM Cortex-M0+)
+# Adafruit Grand Central M4 (Atmel SAMD51P20A ARM Cortex-M4)
 #
 [env:SAMD21_minitronics20]
 platform         = atmelsam
```

</details>
