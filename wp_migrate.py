import re
import os

class WPMigrator:
    def __init__(self, old_domain, new_domain, old_path=None, new_path=None):
        self.replacements = {
            old_domain: new_domain,
        }
        if old_path and new_path:
            self.replacements[old_path] = new_path
        
        # Prepare escaped versions for JSON etc.
        extra_replaces = {}
        for old, new in self.replacements.items():
            # JSON escaped /
            extra_replaces[old.replace('/', '\\/')] = new.replace('/', '\\/')
        self.replacements.update(extra_replaces)

    def fix_serialization(self, match):
        """
        Regex callback to fix s:len:"value" patterns.
        """
        orig_len = int(match.group(1))
        content = match.group(2)
        
        # Apply replacements to the content
        new_content = content
        for old, new in self.replacements.items():
            new_content = new_content.replace(old, new)
        
        return f's:{len(new_content)}:"{new_content}";'

    def migrate_string(self, text):
        """
        Replaces domains/paths in a string, being aware of PHP serialization.
        """
        # First fix serialized strings: s:<length>:"<string>"
        text = re.sub(r's:(\d+):"(.*?)";', self.fix_serialization, text)
        
        # Then catch any remaining non-serialized occurrences
        for old, new in self.replacements.items():
            text = text.replace(old, new)
        
        return text

    def migrate_sql_file(self, input_file, output_file):
        """
        Streams a SQL file and performs migration.
        """
        print(f"Migrating SQL: {input_file} -> {output_file}...")
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in:
            with open(output_file, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    f_out.write(self.migrate_string(line))
        print("Done!")

    def migrate_config(self, file_path, db_name=None, db_user=None, db_pass=None, db_host=None):
        """
        Updates wp-config.php with new database credentials.
        """
        print(f"Updating config: {file_path}...")
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if db_name:
            content = re.sub(r"define\(\s*'DB_NAME',\s*'.*?'\s*\);", f"define( 'DB_NAME', '{db_name}' );", content)
        if db_user:
            content = re.sub(r"define\(\s*'DB_USER',\s*'.*?'\s*\);", f"define( 'DB_USER', '{db_user}' );", content)
        if db_pass:
            content = re.sub(r"define\(\s*'DB_PASSWORD',\s*'.*?'\s*\);", f"define( 'DB_PASSWORD', '{db_pass}' );", content)
        if db_host:
            content = re.sub(r"define\(\s*'DB_HOST',\s*'.*?'\s*\);", f"define( 'DB_HOST', '{db_host}' );", content)

        # Also update site URL and Home URL if they are defined in wp-config
        content = re.sub(r"define\(\s*'WP_HOME',\s*'.*?'\s*\);", f"define( 'WP_HOME', 'http://{self.replacements.get(list(self.replacements.keys())[0], '')}' );", content)
        content = re.sub(r"define\(\s*'WP_SITEURL',\s*'.*?'\s*\);", f"define( 'WP_SITEURL', 'http://{self.replacements.get(list(self.replacements.keys())[0], '')}' );", content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Config updated!")

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) < 5:
        print("Usage: python wp_migrate.py <old_domain> <new_domain> <input_sql> <output_sql>")
        sys.exit(1)
    
    migrator = WPMigrator(sys.argv[1], sys.argv[2])
    migrator.migrate_sql_file(sys.argv[3], sys.argv[4])
