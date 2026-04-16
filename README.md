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

### 1. Prepare your SSH Keys
To connect securely, you need an SSH Key. There are two common ways to do this:

#### Path A: You generate the key (Recommended)
1.  **On your computer**, run: `ssh-keygen -t rsa -b 4096 -f mysite.pem`
2.  Open the file `mysite.pem.pub` (the Public Key) and copy its content.
3.  **On your server**, paste that content into the file `~/.ssh/authorized_keys`.

#### Path B: The Server generates the key (Common in cPanel)
1.  **On your Hosting Panel**, look for "SSH Access" and click "Generate a New Key".
2.  **Download the Private Key** to your computer (e.g., as `key.pem`).
3.  **Very Important**: In the hosting panel, you must click "Manage Indices" or "Authorize" to ensure the public key is added to the `authorized_keys` file.

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

#### Optional: Pre-configuration
If you prefer, you can fill your data before running the script by creating a file named `migration_config.json`. You can use the `migration_config.json.example` as a template:

```json
{
    "source": {
        "host": "oldsite.com",
        "user": "oldsite",
        "pass": null,
        "key_file": "/home/myuser/oldsite.pem",
        "key_pass": "PASSWORD",
        "wp_path": "/home/oldsite/public_html",
        "db_name": null
    },
    "target": {
        "host": "newsite.com",
        "user": "newsite",
        "pass": null,
        "key_file": "/home/myuser/newsite.pem",
        "key_pass": "PASSWORD",
        "wp_path": "/home/newsite/public_html",
        "db_name": "newsite_wp",
        "db_user": "newsite_usr",
        "db_pass": "PASSWORD",
        "db_host": "localhost"
    },
    "migration": {
        "old_domain": "oldsite.com",
        "new_domain": "newsite.com"
    }
}
```
The assistant saves your answers in this file automatically. If it fails, just run it again and press **Enter** to reuse your previous answers.

---

## 🇪🇸 Manual en Español

### ¿Cómo usar este Migrador?

Esta herramienta está diseñada para migrar sitios de WordPress de forma automática, incluso si tu hosting tiene restricciones de seguridad (como terminales bloqueadas).

### Pasos para principiantes:

1.  **Instala Python**: Asegúrate de tener Python 3 en tu computadora.
2.  **Prepara tus llaves SSH**: Necesitas una llave privada para conectarte. Hay dos formas:
    *   **Opción A (Tú la generas)**: Creas la llave en tu PC con `ssh-keygen` y subes la llave pública (`.pub`) al archivo `authorized_keys` del servidor.
    *   **Opción B (El servidor la genera)**: Generas la llave en el cPanel, descargas la llave privada a tu PC y te aseguras de darle a "Autorizar" en el panel para que el servidor active la llave pública.
3.  **Ejecuta el asistente**:
    ```bash
    pip install -r requirements.txt
    python3 migrate_assistant.py
    ```
4.  **Sigue las instrucciones**: El script te irá pidiendo los datos del sitio viejo y el nuevo.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
