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

Herramienta interactiva y fácil de usar para migrar sitios de WordPress entre dominios y hostings. Diseñada especialmente para manejar entornos restringidos y asegurar la integridad de la base de datos.

### 🚀 ¿Por qué esta herramienta?

La mayoría de los plugins de migración fallan en hostings compartidos con restricciones (como cPanel sin acceso shell completo). Este script usa una estrategia de varias capas para saltar esos bloqueos:
1.  **Migración con Serialización**: Reemplaza URLs de forma segura sin romper datos serializados de PHP (ideal para Elementor y otros plugins complejos).
2.  **Conexión Anti-Bloqueo**: Si la terminal SSH está bloqueada, el script activa automáticamente un túnel PHP y descarga los archivos vía SFTP recursivo.
3.  **Soporte de Resumen**: Si se corta la conexión, el asistente recuerda por dónde iba.
4.  **Configuración Automática**: Actualiza tu archivo `wp-config.php` de forma automática.

### 🛠 Requisitos

*   **Python 3.x** instalado en tu computadora local.
*   **Acceso SSH/SFTP** tanto en el servidor de origen como en el de destino.

### 📖 Cómo usar (Guía para Novatos)

#### 1. Preparar tus Llaves SSH
Para conectarte de forma segura, necesitas una llave SSH. Hay dos formas comunes de obtenerla:

**Opción A: Tú generas la llave (Recomendado)**
1.  **En tu computadora**, corre: `ssh-keygen -t rsa -b 4096 -f misitio.pem`
2.  Abre el archivo `misitio.pem.pub` (la Llave Pública) y copia el texto.
3.  **En tu servidor**, pega ese texto dentro del archivo `~/.ssh/authorized_keys`.

**Opción B: El Servidor genera la llave (Común en cPanel)**
1.  **En tu Panel de Hosting**, busca "Acceso SSH" y dale a "Generar nueva llave".
2.  **Descarga la Llave Privada** a tu computadora (ej: como `llave.pem`).
3.  **Muy Importante**: En tu panel de hosting, debes darle al botón "Administrar" o "Autorizar" para que el servidor active la llave pública dentro del archivo `authorized_keys`.

#### 2. Instalación
1.  Descarga o clona este repositorio.
2.  Abre una terminal en la carpeta del proyecto.
3.  Instala las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```

#### 3. Ejecutar el Asistente
Simplemente corre:
```bash
python3 migrate_assistant.py
```

#### Opcional: Pre-configuración
Si prefieres, puedes llenar tus datos antes de correr el script creando un archivo llamado `migration_config.json`. Puedes usar el ejemplo `migration_config.json.example` como plantilla:

```json
{
    "source": {
        "host": "oldsite.com",
        "user": "oldsite",
        "pass": null,
        "key_file": "/home/miusuario/sitio_viejo.pem",
        "key_pass": "PASSWORD",
        "wp_path": "/home/oldsite/public_html",
        "db_name": null
    },
    "target": {
        "host": "newsite.com",
        "user": "newsite",
        "pass": null,
        "key_file": "/home/miusuario/sitio_nuevo.pem",
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
El asistente guardará tus respuestas en este archivo automáticamente. Si algo falla, vuelve a correrlo y presiona **Enter** para reusar tus datos anteriores.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
