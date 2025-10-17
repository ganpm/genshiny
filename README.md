# Genshiny
![Python](https://img.shields.io/badge/python-3.12.2-blue.svg)
![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)

A desktop application for managing and analyzing your pulls in Genshin Impact.

## 📋 Overview

Genshiny helps players track their gacha resources and simulate pull outcomes using the best known approximation of the Genshin Impact gacha model. The application provides offline data management with a clean, user-friendly interface.

## ✨ Features

- **Resource Tracking**: Monitor Primogems, Intertwined Fates, Masterless Starglitter, and Genesis Crystals
- **Offline Storage**: Save and load your currency data locally, no online connection needed
- **Pull Calculator**: Calculate your total available pulls from your resources
- **Guarantee Counter**: Determine how many guaranteed 5-star characters you can obtain
- **Gacha Simulation**: Simulate pulls using an approximate gacha model including the effect of Capturing Radiance
- **Dark Theme**: Modern UI with dark theme support

## 🛠️ Prerequisites

- Python 3.12.2

## 📦 Installation

1. **Clone the repository**

    ```sh
    git clone https://github.com/ganpm/genshiny
    cd genshiny
    ```

2. **Create and activate virtual environment**

    Windows
    ```sh
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    Linux
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    pip install pyqtdarktheme==2.1.0 --ignore-requires-python
    ```

    > **Note:** The second command is required due to a known issue with `pyqtdarktheme` installation.
    >
    > See [PyQtDarkTheme GitHub Issue #252](https://github.com/5yutan5/PyQtDarkTheme/issues/252) for details.

## 🚀 Usage

Run the application:
```sh
python Genshiny.py
```

## 🔨 Building Executable

To create a standalone executable:

```sh
python -m nuitka Genshiny.py
```

The build configuration is already specified in the `Genshiny.py` file.

## 📚 Technical References

The gacha simulation models are based on the following:

- **Wish Model**: [Statistical model for Genshin Impact's droprates | HoYoLAB](https://www.hoyolab.com/article/497840)
- **Capturing Radiance Model**: [Understanding Genshin Impact’s Capturing Radiance: In-Depth Analysis of 4 Million Pulls : r/Genshin_Impact](https://www.reddit.com/r/Genshin_Impact/comments/1hd1sqa/understanding_genshin_impacts_capturing_radiance/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This application is not affiliated with HoYoverse. Genshin Impact is a trademark of HoYoverse.