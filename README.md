# 🔐 LANCryptor

**LANCryptor** is a simple and secure LAN file transfer app with a modern UI built on [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). It encrypts files using RSA + AES and allows sending/receiving with confirmation dialogs and progress tracking — either via GUI or from the command line.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
![Linted with Ruff](https://img.shields.io/badge/linter-ruff-success?logo=python)
![Formatted with Black](https://img.shields.io/badge/code%20style-black-000000)
[![Build & Release](https://github.com/yar2000T/LANCryptor/actions/workflows/release.yaml/badge.svg)](https://github.com/yar2000T/LANCryptor/actions/workflows/release.yaml)
[![Build Portable EXE](https://github.com/yar2000T/LANCryptor/actions/workflows/build.yml/badge.svg)](https://github.com/yar2000T/LANCryptor/actions/workflows/build.yml)
[![Code Style Check](https://github.com/yar2000T/LANCryptor/actions/workflows/format.yaml/badge.svg)](https://github.com/yar2000T/LANCryptor/actions/workflows/format.yaml)

---

## 📆 Features

* 📁 Send and receive files over LAN
* 🔒 End-to-end encryption (RSA + AES)
* 💻 GUI built with CustomTkinter
* 🥪 CLI mode for headless transfers
* 🎛️ Theme switcher and tabbed interface
* 📡 IP auto-detection and sender confirmation dialogs
* 📜 Transfer progress and history

---

## 🚀 Getting Started

### ✅ Requirements

* Python 3.10 or newer
* Windows, macOS, or Linux

### 📦 Install dependencies

```bash
pip install -r requirements.txt
```

---

## 💾 Run the App

### 💻 GUI Mode

```bash
python src/main.py
```

Or explicitly:

```bash
python src/main.py gui
```

---

### ⚙️ Command Line Mode

You can also use LANCryptor directly in terminal without GUI:

#### 📄 Send file

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

#### 📅 Receive file

```bash
python src/main.py receive
```

> You will be prompted to confirm sender's key hash before receiving the file.

---

## 📂 Downloaded Files

After receiving, files are extracted to the local folder:

```
./Received/
```

Make sure this folder exists or will be created by the app.

---

## 🧹 Format & Lint

LANCryptor uses [Ruff](https://docs.astral.sh/ruff/) and [Black](https://black.readthedocs.io/) for clean, modern Python code.

### ✨ Format with Black

```bash
black .
```

### 🥪 Check with Ruff

```bash
ruff check .
```

### 🔧 Auto-fix with Ruff

```bash
ruff check . --fix
```

---

## 📄 License

This project is licensed under the CC BY-NC 4.0 License – see the [LICENSE](LICENSE) file for details.
