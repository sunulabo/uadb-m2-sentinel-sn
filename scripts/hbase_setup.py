import happybase

def setup_hbase_table():
    # Connexion au serveur Thrift HBase (port par défaut 9090)
    connection = happybase.Connection('localhost')
    
    table_name = b'equipe02_sentinel_realtime'
    
    # Vérification si la table existe déjà
    tables = connection.tables()
    if table_name in tables:
        print(f"La table {table_name.decode('utf-8')} existe déjà.")
    else:
        print(f"Création de la table {table_name.decode('utf-8')}...")
        # Création de la table avec une column family 'info'
        # 'info' contiendra la région, l'âge, le code_pathologie, etc.
        connection.create_table(
            table_name,
            {
                b'info': dict() # Configuration par défaut de la column family
            }
        )
        print("✅ Table HBase créée avec succès.")
    
    connection.close()

if __name__ == "__main__":
    setup_hbase_table()
