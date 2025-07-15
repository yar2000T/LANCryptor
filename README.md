# 🔐 LANCryptor

**LANCryptor** is a simple and secure LAN file transfer app with a modern UI built on [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). It encrypts files using RSA + AES and allows sending/receiving with confirmation dialogs and progress tracking.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
![Linted with Ruff](https://img.shields.io/badge/linter-ruff-success?logo=python)
![Formatted with Black](https://img.shields.io/badge/code%20style-black-000000)

---

## 📦 Features

* 📁 Send and receive files over LAN
* 🔒 End-to-end encryption (RSA + AES)
* 🎛️ GUI with theme switcher and tabs
* 📡 IP auto-detection and confirmation dialogs
* 📜 Transfer history

---

## 🚀 Getting Started

### ✅ Requirements

* Python 3.10 or newer
* Windows, macOS, or Linux

### 🥪 Install dependencies

```bash
pip install -r requirements.txt
```

---

## 💾 Run the App

```bash
python src/main.py
```

---

## 🥹 Format & Lint

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

> You can also configure both tools via `pyproject.toml`.

---

## ⚙️ Project Structure

```
LANCryptor/
├── src/
│   ├── main.py
│   ├── gui.py
│   └── transfer.py
├── Received/
├── requirements.txt
└── README.md
```

---

## ⚙️ Maintainer Tips

* Use `venv` to isolate dependencies:

  ```bash
  python -m venv .venv
  .venv\Scripts\activate  # Windows
  source .venv/bin/activate  # Unix
  ```
* Enable formatting and linting on save in your IDE (e.g. VS Code with Python extension)

---

## 📅 Downloads

After receiving, files are extracted to the local folder:

```
./Received/
```

Make sure this folder exists or will be created by the app.

---

## 📄 License

This project is licensed under the CC BY-NC 4.0 License – see the [LICENSE](LICENSE) file for details.
