import paramiko
import os
import shutil
import time
import re
import json
from stat import S_ISDIR
from wp_migrate import WPMigrator

class MigrationAssistant:
    def __init__(self):
        self.source = {}
        self.target = {}
        self.migration = {}
        self.temp_dir = "migration_temp"
        self.config_file = "migration_config.json"
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump({
                'source': self.source,
                'target': self.target,
                'migration': self.migration
            }, f, indent=4)

    def ask(self, category, key, question, default=None):
        # Try to get existing value from loaded config
        existing = self.config.get(category, {}).get(key)
        if existing:
            default = existing
        
        prompt = f"{question} [{default}]: " if default else f"{question}: "
        val = input(prompt)
        res = val if val else default
        
        # Auto-expand paths if the question implies a path
        if any(word in question.lower() for word in ['path', 'file', 'key']):
            if res:
                res = os.path.expanduser(res)
        
        return res

    def collect_info(self):
        print("\n=== WordPress Migration Assistant ===\n")
        print("Note: Your answers are saved locally to migration_config.json")
        
        print("\n--- Source Site (Old Site) ---")
        self.source['host'] = self.ask('source', 'host', "SSH Host")
        self.source['user'] = self.ask('source', 'user', "SSH User")
        self.source['pass'] = self.ask('source', 'pass', "SSH Password (leave blank for key auth)")
        if not self.source['pass']:
            self.source['key_file'] = self.ask('source', 'key_file', "SSH Private Key Path", os.path.expanduser("~/.ssh/id_rsa"))
            self.source['key_pass'] = self.ask('source', 'key_pass', "Key Passphrase (leave blank if none)")
        else:
            self.source['key_file'] = None
            self.source['key_pass'] = None
        
        self.source['wp_path'] = self.ask('source', 'wp_path', "WordPress Path (e.g., /var/www/html)")
        self.source['db_name'] = self.ask('source', 'db_name', "DB Name (optional, will try to read from wp-config)")
        self.save_config()

        print("\n--- Target Site (New Site) ---")
        self.target['host'] = self.ask('target', 'host', "SSH Host")
        self.target['user'] = self.ask('target', 'user', "SSH User")
        self.target['pass'] = self.ask('target', 'pass', "SSH Password (leave blank for key auth)")
        if not self.target['pass']:
            self.target['key_file'] = self.ask('target', 'key_file', "SSH Private Key Path", os.path.expanduser("~/.ssh/id_rsa"))
            self.target['key_pass'] = self.ask('target', 'key_pass', "Key Passphrase (leave blank if none)")
        else:
            self.target['key_file'] = None
            self.target['key_pass'] = None
            
        self.target['wp_path'] = self.ask('target', 'wp_path', "WordPress Path")
        self.target['db_name'] = self.ask('target', 'db_name', "NEW DB Name")
        self.target['db_user'] = self.ask('target', 'db_user', "NEW DB User")
        self.target['db_pass'] = self.ask('target', 'db_pass', "NEW DB Password")
        self.target['db_host'] = self.ask('target', 'db_host', "NEW DB Host", "localhost")
        self.save_config()
        
        print("\n--- Migration Details ---")
        self.migration['old_domain'] = self.ask('migration', 'old_domain', "Old Domain")
        self.migration['new_domain'] = self.ask('migration', 'new_domain', "New Domain")
        self.save_config()

    def run_ssh_cmd(self, client, cmd, desc):
        print(f"  [SSH] {desc}...")
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Read output to check for restriction messages
        out_content = stdout.read().decode()
        err_content = stderr.read().decode()
        exit_status = stdout.channel.recv_exit_status()
        
        if "Shell access is not enabled" in out_content or "Shell access is not enabled" in err_content:
            print(f"  [DEBUG] Command blocked by restricted shell: {desc}")
            return False
            
        if exit_status != 0:
            print(f"  [ERROR] {err_content}")
            return False
        return True

    def connect(self, info):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if info.get('pass'):
                client.connect(info['host'], username=info['user'], password=info['pass'], 
                               allow_agent=False, look_for_keys=False)
            elif info.get('key_file'):
                # Force loading as RSA key to avoid issues with other key types
                key = paramiko.RSAKey.from_private_key_file(info['key_file'], password=info.get('key_pass'))
                client.connect(info['host'], username=info['user'], pkey=key, 
                               allow_agent=False, look_for_keys=False)
            else:
                client.connect(info['host'], username=info['user'], 
                               allow_agent=False, look_for_keys=False)
            return client
        except Exception as e:
            print(f"Connection failed to {info['host']}: {e}")
            return None

    def find_remote_command(self, client, name, extra_paths=[]):
        print(f"  [SSH] Probing for {name}...")
        paths = [name, f"/usr/bin/{name}", f"/usr/local/bin/{name}", f"/bin/{name}"] + extra_paths
        for p in paths:
            _, stdout, _ = client.exec_command(f"{p} --help")
            if stdout.channel.recv_exit_status() == 0:
                print(f"  [DEBUG] Found {name} at: {p}")
                return p
        return None

    def sftp_download_recursive(self, sftp, remote_dir, local_dir):
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        for item in sftp.listdir_attr(remote_dir):
            remote_path = f"{remote_dir}/{item.filename}"
            local_path = os.path.join(local_dir, item.filename)
            
            if any(p in remote_path for p in ['wp-content/cache', 'wp-content/backups']):
                continue
            
            if S_ISDIR(item.st_mode):
                self.sftp_download_recursive(sftp, remote_path, local_path)
            else:
                print(f"    Downloading {item.filename}...")
                sftp.get(remote_path, local_path)

    def php_bridge(self, sftp, action, remote_path, domain, creds=None):
        print(f"  [PHP] Attempting {action} via PHP bridge...")
        
        if action == "dump" and creds:
            php_logic = f"""
            $cmd = "mysqldump -h {creds['DB_HOST']} -u {creds['DB_USER']} -p'{creds['DB_PASSWORD']}' {creds['DB_NAME']} > db_temp.sql 2>&1";
            exec($cmd, $output, $return);
            echo ($return === 0) ? "SUCCESS" : "FAILED: " . implode("\\n", $output);
            """
        elif action == "zip":
            php_logic = """
            $cmd = "zip -r wp_backup.zip . -x './wp-content/cache/*' 2>&1";
            exec($cmd, $output, $return);
            echo ($return === 0) ? "SUCCESS" : "FAILED: " . implode("\\n", $output);
            """
        elif action == "tar":
            php_logic = """
            $cmd = "tar -cvzf wp_backup.tar.gz . --exclude='./wp-content/cache/*' 2>&1";
            exec($cmd, $output, $return);
            echo ($return === 0) ? "SUCCESS" : "FAILED: " . implode("\\n", $output);
            """
        else:
            return False

        php_script = f"<?php {php_logic} ?>"
        bridge_file = f"{remote_path}/migrate_bridge.php"
        with sftp.file(bridge_file, 'w') as f:
            f.write(php_script)
        
        try:
            import requests
            url = f"http://{domain}/migrate_bridge.php"
            resp = requests.get(url, timeout=60)
            if "SUCCESS" in resp.text:
                print(f"    {action} successful!")
                return True
            else:
                print(f"    PHP Bridge {action} failed: {resp.text}")
        except Exception as e:
            print(f"    Failed to trigger PHP bridge for {action}: {e}")
        finally:
            try: sftp.remove(bridge_file)
            except: pass
        return False

    def get_db_creds(self, client, wp_path):
        print(f"  [SSH] Reading {wp_path}/wp-config.php for database credentials...")
        cmd = f"cat {wp_path}/wp-config.php"
        stdin, stdout, stderr = client.exec_command(cmd)
        content = stdout.read().decode()
        
        # If shell is restricted, try SFTP
        if not content or "Shell access is not enabled" in content:
            print("  [INFO] SSH Shell restricted. Trying SFTP fallback...")
            try:
                sftp = client.open_sftp()
                with sftp.open(f"{wp_path}/wp-config.php", "r") as f:
                    content = f.read().decode()
                sftp.close()
            except Exception as e:
                print(f"  [ERROR] SFTP fallback failed: {e}")
                return {}

        creds = {}
        for key in ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']:
            # Handle both single and double quotes, and flexible spacing
            pattern = rf"define\s*\(\s*['\"]{key}['\"]\s*,\s*['\"](.*?)['\"]\s*\)\s*;"
            match = re.search(pattern, content)
            if match:
                creds[key] = match.group(1)
        
        return creds

    def execute(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # Resume Support: Check for Phase 1 results
        skip_phase1 = False
        files_extracted_locally = False
        archive_ready = False
        archive_type = None
        sql_file = "db_backup.sql"
        zip_file = "wp_backup.zip"
        # Try both zip and tar extensions
        if not os.path.exists(f"{self.temp_dir}/{zip_file}"):
            if os.path.exists(f"{self.temp_dir}/wp_backup.tar.gz"):
                zip_file = "wp_backup.tar.gz"
                archive_ready = True
        else:
            archive_ready = True

        if os.path.exists(f"{self.temp_dir}/wp_files"):
            files_extracted_locally = True

        if os.path.exists(f"{self.temp_dir}/{sql_file}") and (archive_ready or files_extracted_locally):
            ans = input(f"\n[RESUME] Phase 1 files found in {self.temp_dir}. Skip download? [Y/n]: ")
            if ans.lower() != 'n':
                skip_phase1 = True
                print("  Skipping Phase 1 (Download).")

        s_client = None
        creds = {}
        archive_ready = False
        archive_type = None

        if not skip_phase1:
            s_client = self.connect(self.source)
            if not s_client: return

            # Source Phase
            print("\n--- Phase 1: Exporting from Source ---")
            
            # Get DB Credentials
            creds = self.get_db_creds(s_client, self.source['wp_path'])
            if not creds: return

            # Try to find commands
            zip_path = self.find_remote_command(s_client, "zip")
            tar_path = self.find_remote_command(s_client, "tar")
            dump_path = self.find_remote_command(s_client, "mysqldump")
        
            # Files logic (ZIP -> TAR)
            if zip_path:
                if self.run_ssh_cmd(s_client, f"cd {self.source['wp_path']} && {zip_path} -r {zip_file} . -x 'wp-content/cache/*'", "Compressing WP files (ZIP)"):
                    archive_ready, archive_type = True, "zip"
            
            if not archive_ready and tar_path:
                if self.run_ssh_cmd(s_client, f"cd {self.source['wp_path']} && {tar_path} -cvzf wp_backup.tar.gz . --exclude='wp-content/cache/*'", "Compressing WP files (TAR)"):
                    archive_ready, archive_type = True, "tar"
                    zip_file = "wp_backup.tar.gz"

            # SFTP Transfer
            sftp = s_client.open_sftp()
            
            # PHP Bridge fallback for files
            if not archive_ready:
                if self.php_bridge(sftp, "zip", self.source['wp_path'], self.migration['old_domain']):
                    archive_ready, archive_type = True, "zip"
                elif self.php_bridge(sftp, "tar", self.source['wp_path'], self.migration['old_domain']):
                    archive_ready, archive_type = True, "tar"
                    zip_file = "wp_backup.tar.gz"

            # Download SQL logic
            db_dump_ready = False
            if dump_path:
                dump_cmd = f"{dump_path} -h {creds['DB_HOST']} -u {creds['DB_USER']} -p'{creds['DB_PASSWORD']}' {creds['DB_NAME']} > {self.source['wp_path']}/{sql_file}"
                if self.run_ssh_cmd(s_client, dump_cmd, "Dumping database"):
                    db_dump_ready = True

            print("  [SFTP] Downloading database backup...")
            db_downloaded = False
            try:
                sftp.get(f"{self.source['wp_path']}/{sql_file}", f"{self.temp_dir}/{sql_file}")
                db_downloaded = True
            except:
                print("    SQL backup not found on server. Trying PHP bridge...")
                if self.php_bridge(sftp, "dump", self.source['wp_path'], self.migration['old_domain'], creds):
                    try:
                        sftp.get(f"{self.source['wp_path']}/db_temp.sql", f"{self.temp_dir}/{sql_file}")
                        db_downloaded = True
                    except: pass

            if not db_downloaded:
                print("  [ERROR] Database export failed via both SSH and PHP bridge.")
                return

            # Download Files
            print("  [SFTP] Downloading site files...")
            files_extracted_locally = False
            if archive_ready:
                try:
                    sftp.get(f"{self.source['wp_path']}/{zip_file}", f"{self.temp_dir}/{zip_file}")
                    print(f"    Successfully downloaded archive.")
                except:
                    archive_ready = False

            if not archive_ready:
                print("    Archive not found on server. Switching to recursive SFTP download...")
                self.sftp_download_recursive(sftp, self.source['wp_path'], f"{self.temp_dir}/wp_files")
                files_extracted_locally = True
            
            sftp.get(f"{self.source['wp_path']}/wp-config.php", f"{self.temp_dir}/wp-config.php")
            sftp.close()
            s_client.close()

        # Conversion Phase
        skip_phase2 = False
        migrated_sql = f"{self.temp_dir}/migrated_{sql_file}"
        if os.path.exists(migrated_sql):
            ans = input(f"\n[RESUME] Phase 2 (migrated SQL) found. Skip reconfiguration? [Y/n]: ")
            if ans.lower() != 'n':
                skip_phase2 = True
                print("  Skipping Phase 2 (Reconfiguration).")

        if not skip_phase2:
            print("\n--- Phase 2: Reconfiguring ---")
            migrator = WPMigrator(self.migration['old_domain'], self.migration['new_domain'])
            migrator.migrate_sql_file(f"{self.temp_dir}/{sql_file}", migrated_sql)
            
            # Migrate wp-config.php
            migrator.migrate_config(f"{self.temp_dir}/wp-config.php", 
                                    db_name=self.target['db_name'],
                                    db_user=self.target['db_user'],
                                    db_pass=self.target['db_pass'],
                                    db_host=self.target['db_host'])
        
        # Target Phase
        print("\n--- Phase 3: Deploying to Target ---")
        t_client = self.connect(self.target)
        if not t_client: return

        sftp = t_client.open_sftp()
        
        # If we have a ZIP, upload and unzip. Otherwise, upload folder recursively.
        if not files_extracted_locally:
            sftp.put(f"{self.temp_dir}/{zip_file}", f"{self.target['wp_path']}/{zip_file}")
            self.run_ssh_cmd(t_client, f"cd {self.target['wp_path']} && unzip -o {zip_file}", "Extracting files on target")
        else:
            print("  [SFTP] Uploading files recursively (since no ZIP was available)...")
            # Implement recursive upload if needed, or just tell user.
            # For now, let's assume we can at least zip locally and upload.
            local_zip = f"{self.temp_dir}/local_wp.zip"
            shutil.make_archive(f"{self.temp_dir}/local_wp", 'zip', f"{self.temp_dir}/wp_files")
            sftp.put(local_zip, f"{self.target['wp_path']}/local_wp.zip")
            self.run_ssh_cmd(t_client, f"cd {self.target['wp_path']} && unzip -o local_wp.zip", "Extracting files on target")

        sftp.put(f"{self.temp_dir}/migrated_{sql_file}", f"{self.target['wp_path']}/{sql_file}")
        sftp.put(f"{self.temp_dir}/wp-config.php", f"{self.target['wp_path']}/wp-config.php")
        sftp.close()

        # Import DB on Target
        import_cmd = f"mysql -h {self.target['db_host']} -u {self.target['db_user']} -p'{self.target['db_pass']}' {self.target['db_name']} < {self.target['wp_path']}/{sql_file}"
        self.run_ssh_cmd(t_client, import_cmd, "Importing database on target")
        
        t_client.close()
        print("\n=== Migration Completed! ===")

if __name__ == "__main__":
    assistant = MigrationAssistant()
    assistant.collect_info()
    assistant.execute()
