# WordPress Migrator (Python)

An interactive, user-friendly tool to migrate WordPress sites between domains and hosts. Specially designed to handle restricted hosting environments and ensure database integrity.

## 🚀 Why this tool?

Most WordPress migration plugins fail on restricted hosting environments (like cPanel without full SSH access). This tool uses a multi-layered strategy to bypass these blocks:
1.  **Serialization-Aware Migration**: Safely replaces URLs in the database without breaking PHP serialized data (perfect for Elementor and other complex plugins).
2.  **Anti-Block Connection**: If SSH shell commands are blocked, it automatically switches to a PHP-based tunnel and SFTP recursive download.
3.  **Resume Support**: If the connection breaks, it remembers where it left off.
4.  **Automatic Config**: Updates your `wp-config.php` automatically.

---

## 🛠 Prerequisites

*   **Python 3.x** installed on your local machine.
*   **SSH/SFTP Access** on both source and target servers.

---

## 📖 How to Use (Novice Guide)

### 1. Prepare your SSH Keys (The hardest part!)
To connect securely without a password, you need an SSH Key:
1.  On your computer, run: `ssh-keygen -t rsa -b 4096`
2.  When it asks for a file, you can press Enter for default or name it (e.g., `mysite.pem`).
3.  **Very Important**: You must add your **Public Key** (the one ending in `.pub`) to the `authorized_keys` file on your server (usually in the `.ssh/` folder).

### 2. Installation
1.  Download or clone this repository.
2.  Open a terminal in the project folder.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Run the Assistant
Simply run:
```bash
python3 migrate_assistant.py
```
The assistant will ask you for:
*   Old and New domains.
*   SSH details for both servers.
*   Database names and passwords.

**Don't worry!** The assistant saves your answers in `migration_config.json`. If it fails, just run it again and press **Enter** to reuse your previous answers.

---

## 🇪🇸 Manual en Español

### ¿Cómo usar este Migrador?

Esta herramienta está diseñada para migrar sitios de WordPress de forma automática, incluso si tu hosting tiene restricciones de seguridad (como terminales bloqueadas).

### Pasos para principiantes:

1.  **Instala Python**: Asegúrate de tener Python 3 en tu computadora.
2.  **Prepara tus llaves SSH**: Necesitas una llave privada para conectarte. Asegúrate de que tu **llave pública** esté dentro del archivo `authorized_keys` en la carpeta `.ssh` de tus dos servidores.
3.  **Ejecuta el asistente**:
    ```bash
    pip install -r requirements.txt
    python3 migrate_assistant.py
    ```
4.  **Sigue las instrucciones**: El script te irá pidiendo los datos del sitio viejo y el nuevo.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
