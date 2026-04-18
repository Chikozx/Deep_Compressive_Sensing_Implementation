# Deep Compressive Sensing Implementation

A complete end-to-end **Deep Compressive Sensing (DCS)** system for ECG signal acquisition and reconstruction. The system acquires ECG analog sensor data from AD8232 sensor on an ESP32 microcontroller, applies a learned sensing matrix to compress the signal on-device, transmits the measurements wirelessly via Bluetooth SPP, and reconstructs the original signal on a desktop application using a deep learning decoder.

---

## Table of Contents

- [Overview](#overview)
- [Overview of Compressed Sensing](#overview-of-compressed-sensing)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Firmware (ESP32)](#firmware-esp32)
- [Desktop Application](#desktop-application)
- [Deep Learning Training](#deep-learning-training)
- [Getting Started](#getting-started)
- [Models](#models)
- [Operation Modes](#operation-modes)

---

## Overview

Traditional Compressive Sensing relies on random measurement matrices. This project implements **Deep Compressive Sensing**, where the sensing matrix (encoder) and the reconstruction algorithm (decoder) are jointly trained as a neural network. The trained binary sensing matrix is deployed directly on the ESP32 to compress 256-sample windows into a much smaller set of measurements before transmission, reducing Bluetooth bandwidth and power consumption.

Key highlights:
- On-device compression using a binary antipodal sensing matrix (±1 weights)
- Two model architectures supported: **Modified MFFSE** (Multi-Feature Frequency-domain Sparse Encoder) and **TCSSO**
- Real-time visualization and configuration from a desktop GUI

---
## Overview of Compressed Sensing

Compressed Sensing (CS) is a signal processing technique that allows for the efficient acquisition and reconstruction of a signal from far fewer samples than traditionally required by the Nyquist-Shannon theorem. It achieves this by finding solutions to underdetermined linear systems, provided the underlying signal is sparse. 

#### **1. The Measurement Model**
CS aims to recover a high-dimensional, $N$-dimensional original signal vector $x$ using a smaller, $M$-dimensional measurement vector $y$. This relationship is modeled as a linear transformation using an $M \times N$ sensing matrix $\Phi$:

$$y = \Phi x$$

Because $M < N$, this system is underdetermined. The relationship between the number of measurements and the total signal size is quantified by the **Sensing Rate (SR)**:

$$SR = \frac{M}{N}$$

#### **2. Sparse Recovery**
For CS to work, the original signal $x$ must be *sparse*. A signal is considered sparse if it contains only $k$ non-zero values, where $k \ll N$. If this condition is met, $x$ can be successfully reconstructed from the undersampled measurements $y$ by finding the sparsest possible solution. This is mathematically defined as an $L_1$-norm minimization problem:

$$\hat{x} = \arg\min_{x} ||x||_1 \text{ s.t. } y = \Phi x$$

#### **3. The General CS Reconstruction Process**
Most real-world physical signals are not naturally sparse in their original domain. However, they can often be transformed into a sparse representation using a specific mathematical transformation basis $\Psi$ (such as Fourier or Wavelet transforms). 

The relationship between the original signal $x$ and its sparse representation $\xi$ is defined as:

$$x = \Psi \xi$$

By substituting this transformation into the measurement model, the general Compressed Sensing reconstruction process aims to recover the sparse coefficients $\xi$ rather than the signal itself:

$$\hat{\xi} = \arg\min_{\xi} ||\xi||_1 \text{ s.t. } y = \Phi \Psi \xi$$

Once $\hat{\xi}$ is accurately recovered, the original signal can be easily reconstructed using the inverse transformation.

In this project, the deep learning model is jointly learn both the encoding process (learning the best sensing matrix $\Phi$) and the decoding process (sparse recovery). 

---

## Architecture

```
[Analog Sensor] → [ESP32 ADC] → [Sensing Matrix Multiplication] → [Bluetooth SPP] → [Desktop App] → [DL Decoder] → [Reconstructed Signal]
```

The system has three main components:

1. **Firmware** — Runs on the ESP32, handles ADC sampling, compression, and Bluetooth transmission.
2. **Desktop App** — Python/PySide6 GUI for Bluetooth connectivity, real-time visualization, and signal reconstruction.
3. **DL Training** — Jupyter notebook for training the MFFSE model on your dataset.

---

## Project Structure

```
Deep_Compressive_Sensing_Implementation/
├── Firmware/                          # ESP32 firmware (PlatformIO / ESP-IDF)
│   ├── src/
│   │   ├── main.c                     # Main application: ADC, task scheduler, compression
│   │   ├── Bluetooth.c / Bluetooth.h  # Bluetooth SPP communication & config handling
│   │   ├── matrix.c                   # Matrix multiplication utilities
│   │   ├── Kconfig.projbuild          # ESP-IDF menuconfig options
│   │   └── CMakeLists.txt
│   ├── platformio.ini                 # PlatformIO build configuration
│   └── sdkconfig.esp32doit-devkit-v1  # ESP-IDF SDK config
│
├── Desktop_app/                       # Python desktop application
│   ├── someapp.py                     # Application entry point
│   ├── tab_1.py                       # Main tab: Bluetooth, visualization, reconstruction
│   ├── tab_2.py                       # Secondary tab (additional views)
│   ├── bluetooth.py                   # Bluetooth connection and data worker threads
│   ├── model_obj.py                   # Model loader and signal reconstruction logic
│   ├── config.py                      # Global configuration flags (e.g., UI_ONLY mode)
│   ├── config_popup.py                # Configuration popup dialog
│   ├── __models/                      # Pre-trained Keras models (.keras files)
│   │   ├── MFFSE_SR_0_41_fix.keras
│   │   ├── MFFSE_SR_0_5_fix.keras
│   │   ├── SR_03_MFFSE_MOD_Normalized_Train_fix.keras
│   │   ├── SR_05_MFFSE_MOD_Normalized_Train_fix.keras
│   │   └── TCSSO_SR_0_5_fix.keras
│   └── Data_set/                      # Sample CSV datasets for testing
│
└── DL_training/
    └── MFF_SE_MODIFIED_modeltraining.ipynb   # Model training notebook
```

---

## Hardware Requirements

- **ESP32 DOIT DevKit V1** (or compatible ESP32 board)
- **AD8232** Single-Lead, Heart Rate Monitor Front End 
- Analog sensor connected to **ADC2 Channel 3** (GPIO 15)
- Host computer with Bluetooth support

---

## [Firmware (ESP32)](Firmware)

### Build & Flash

The firmware is built with [PlatformIO](https://platformio.org/) using the ESP-IDF framework.

```bash
# Install PlatformIO CLI or use the VS Code extension
cd Firmware

# Build
pio run

# Flash
pio run --target upload

# Monitor serial output
pio device monitor
```

**Board:** `esp32doit-devkit-v1`  
**Framework:** `espidf`  
**Debug tool:** `jlink`

### Firmware Design

The firmware uses FreeRTOS with four concurrent tasks:

| Task | Core | Description |
|---|---|---|
| `send_data` | 0 | Sends compressed data over Bluetooth SPP |
| `compression_data_task` | 1 | Collects 256 samples, normalizes, applies sensing matrix |
| `continous_data_task` | 1 | Passes raw 64-sample windows [(mode 3)](#operation-modes) |
| `config_data` | 1 | Receives configuration commands from the desktop app |

An **ESP timer ISR** fires at the configured sampling rate and reads from ADC2 Ch3, routing samples to either the compression queue or the raw data queue depending on the active mode.

**Compression on the MCU:**
The sensing matrix is received from the desktop app as a packed bitfield (1 bit per entry, `+1` if bit=1, `-1` if bit=0). After normalizing the 256-sample window to [0,1], the firmware computes the matrix–vector product in fixed-point arithmetic and transmits the resulting measurement vector along with the min/max values needed for denormalization on the receiver side.

---

## [Desktop Application](desktop_app)

### Requirements

```bash
pip install PySide6 pyqtgraph tensorflow keras pywavelets numpy
```

### Run

```bash
cd Desktop_app
python someapp.py
```

Set `UI_ONLY = True` in `config.py` to run the GUI without TensorFlow (for UI development or systems without a GPU).

### Features

- **Bluetooth SPP connection** — Scan, pair, and connect to the ESP32
- **Real-time signal plot** — Live visualization using pyqtgraph with automatic downsampling
- **Model selection** — Load any `.keras` model from the `__models/` directory
- **Configuration push** — Send the sensing matrix and sampling parameters to the firmware over Bluetooth
- **Signal reconstruction** — Run the decoder in a background QThread to avoid blocking the UI
- **Data saving** — Export raw and reconstructed signals to CSV
---


## [Deep Learning Training](dl_training)

Open the training notebook:

```bash
cd DL_training
jupyter notebook MFF_SE_MODIFIED_modeltraining.ipynb
```

The notebook trains the **Modified MFFSE** (Multi-Feature Frequency-domain Sparse Encoder) model, which jointly learns:
- A binary antipodal sensing matrix (weights constrained to ±1 via `AntipodalConstraint`)
- A decoder network that predicts the wavelet-domain support of the signal

**Loss function:** `ClippedCrossEntropyLoss` — a numerically stable binary cross-entropy that handles near-zero/near-one predictions without NaN.

Training data obtained from [MIT-BIH Arrhythmia Database](https://physionet.org/content/mitdb/1.0.0/)

Testing data using several data from the MIT-BIH database and some data is collected from real subject using the sensor, placed in `Desktop_app/Data_set/` as `.csv` files. Several example datasets collected from real subjects (named `Carlos_*`, `Hisyam_*`, etc.) are already included.

---

## Models

Pre-trained models are included in `Desktop_app/__models/`:

| File | Architecture | Sampling Ratio |
|---|---|---|
| `MFFSE_SR_0_41_fix.keras` | MFFSE | ~0.41 |
| `MFFSE_SR_0_5_fix.keras` | MFFSE | 0.5 |
| `SR_03_MFFSE_MOD_Normalized_Train_fix.keras` | Modified MFFSE (normalized training) | ~0.3 |
| `SR_05_MFFSE_MOD_Normalized_Train_fix.keras` | Modified MFFSE (normalized training) | 0.5 |
| `TCSSO_SR_0_5_fix.keras` | TCSSO | 0.5 |

**Sampling Ratio (SR)** = number of measurements / 256. A lower SR means more compression.

---

## Operation Modes

The system supports three modes, selectable from the desktop app:

| Mode | Description |
|---|---|
| `0` (Raw) | Send 256 raw ADC samples as-is (no compression) in configurable step |
| `1` (DCS) | Normalize, apply sensing matrix, send compressed measurements |
| `3` (Continuous) | Stream 64-sample raw windows continuously |

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.