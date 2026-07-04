# Diff Report

## Summary

- Files changed: 4
- Additions: 11
- Deletions: 13

| File | Status | + | - |
| --- | --- | ---: | ---: |
| Marlin/Configuration.h | modified | 9 | 9 |
| Marlin/src/pins/pins.h | modified | 0 | 2 |
| ini/avr.ini | modified | 1 | 1 |
| ini/samd21.ini | modified | 1 | 1 |

## File Details

### Marlin/Configuration.h

- Additions: 9
- Deletions: 9

```diff
diff --git a/Marlin/Configuration.h b/Marlin/Configuration.h
index 0e22a1a0ab..55c3962a91 100644
--- a/Marlin/Configuration.h
+++ b/Marlin/Configuration.h
@@ -161,9 +161,9 @@
  *          TMC5130, TMC5130_STANDALONE, TMC5160, TMC5160_STANDALONE
  * :['A4988', 'A5984', 'DRV8825', 'LV8729', 'TB6560', 'TB6600', 'TMC2100', 'TMC2130', 'TMC2130_STANDALONE', 'TMC2160', 'TMC2160_STANDALONE', 'TMC2208', 'TMC2208_STANDALONE', 'TMC2209', 'TMC2209_STANDALONE', 'TMC26X', 'TMC26X_STANDALONE', 'TMC2660', 'TMC2660_STANDALONE', 'TMC5130', 'TMC5130_STANDALONE', 'TMC5160', 'TMC5160_STANDALONE']
  */
-#define X_DRIVER_TYPE  A4988
-#define Y_DRIVER_TYPE  A4988
-#define Z_DRIVER_TYPE  A4988
+#define X_DRIVER_TYPE  TMC2208
+#define Y_DRIVER_TYPE  TMC2208
+#define Z_DRIVER_TYPE  TMC2208
 //#define X2_DRIVER_TYPE A4988
 //#define Y2_DRIVER_TYPE A4988
 //#define Z2_DRIVER_TYPE A4988
@@ -175,7 +175,7 @@
 //#define U_DRIVER_TYPE  A4988
 //#define V_DRIVER_TYPE  A4988
 //#define W_DRIVER_TYPE  A4988
-#define E0_DRIVER_TYPE A4988
+#define E0_DRIVER_TYPE TMC2208
 //#define E1_DRIVER_TYPE A4988
 //#define E2_DRIVER_TYPE A4988
 //#define E3_DRIVER_TYPE A4988
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
+#define DISABLE_Z // powr off when not used
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

### Marlin/src/pins/pins.h

- Additions: 0
- Deletions: 2

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

### ini/avr.ini

- Additions: 1
- Deletions: 1

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

### ini/samd21.ini

- Additions: 1
- Deletions: 1

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
