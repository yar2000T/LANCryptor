<p align="center">
  <img src="assets/banner.png" alt="LANCryptor Banner" width="400"/>
</p>

[//]: # (<h1 align="center">LANCryptor</h1>)
<p align="center"><em>
  A simple, secure LAN file transfer app with a modern GUI built using <a href="https://github.com/TomSchimansky/CustomTkinter">CustomTkinter</a>.
  Featuring RSA + AES encryption, confirmation dialogs, and progress tracking — available via GUI or CLI.
</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"/>
  <a href="https://creativecommons.org/licenses/by-nc/4.0/">
    <img src="https://img.shields.io/badge/license-CC--BY--NC--4.0-lightgrey.svg" alt="License: CC BY-NC 4.0"/>
  </a>
  <img src="https://img.shields.io/badge/linter-ruff-success?logo=python" alt="Linter: Ruff"/>
  <img src="https://img.shields.io/badge/code%20style-black-000000" alt="Formatter: Black"/>
  <a href="https://github.com/yar2000T/LANCryptor/actions/workflows/release.yaml">
  <img src="https://github.com/yar2000T/LANCryptor/actions/workflows/release.yaml/badge.svg" alt="Build & Release"/>
  [![Build Portable EXE](https://github.com/yar2000T/LANCryptor/actions/workflows/build.yml/badge.svg)](https://github.com/yar2000T/LANCryptor/actions/workflows/build.yml)
  [![Code Style Check](https://github.com/yar2000T/LANCryptor/actions/workflows/format.yaml/badge.svg)](https://github.com/yar2000T/LANCryptor/actions/workflows/format.yaml)

  </a>
</p>

---

## ✨ Features

* 📁 Send and receive files over LAN
* 🔒 End-to-end encryption (RSA + AES)
* 🖥️ Clean GUI with tabbed layout
* 💻 CLI mode for headless environments
* 🎨 Light/dark themes with CustomTkinter
* 🔎 Auto-detect IP & confirm sender key
* 📊 Real-time progress bar & history log

---

## 🚀 Getting Started

### ✅ Requirements

* Python 3.10 or newer
* Windows, macOS, or Linux

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 💾 Running the App

### 🖥️ GUI Mode

```bash
python src/main.py
```

Or explicitly:

```bash
python src/main.py gui
```

### ⚙️ Command-Line Mode

#### 📄 Send a File

```bash
python src/main.py send --ip <RECEIVER_IP> --file "<PATH_TO_FILE>"
```

Examples:

```bash
python src/main.py send --ip 192.168.1.42 --file "test.txt"
```

```bash
python src/main.py send --ip 192.168.0.42 --file "C:\somefolder\test.txt"
```

#### 📅 Receive a File

```bash
python src/main.py receive
```

> You'll be prompted to approve the sender's public key hash.

---

## 📁 Received Files Location

All received files are auto-extracted to:

```
./Received/
```

The folder is created if it doesn't already exist.

---

## 🧹 Code Quality

LANCryptor follows modern Python standards using [Ruff](https://docs.astral.sh/ruff/) and [Black](https://black.readthedocs.io/).

### 🖤 Format with Black

```bash
black .
```

### 🔍 Check with Ruff

```bash
ruff check .
```

### 💪 Auto-fix with Ruff

```bash
ruff check . --fix
```

---

## 📜 License

This project is licensed under the **Creative Commons BY-NC 4.0**.
See the [LICENSE](LICENSE) file for full terms.
