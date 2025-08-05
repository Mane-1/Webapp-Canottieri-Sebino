import os


def export_project_to_file(project_path, output_file_path):
    """
    Esporta i file .py di un progetto in un singolo file markdown,
    includendo la directory del progetto in cima.
    """
    # Converte il percorso in un percorso assoluto per chiarezza
    abs_project_path = os.path.abspath(project_path)

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        # --- MODIFICA RICHIESTA ---
        # Scrive la directory principale del progetto all'inizio del file.
        outfile.write(f"# Directory del Progetto: {abs_project_path}\n\n")
        outfile.write("---\n\n")  # Aggiunge un separatore per chiarezza

        for root, dirs, files in os.walk(abs_project_path):
            # Ignora le cartelle comuni che non contengono codice utile
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.idea']]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, abs_project_path)

                    # Usa un titolo di livello 2 per ogni file
                    outfile.write(f"## File: `{relative_path}`\n\n")

                    # Miglioramento: usa blocchi di codice Markdown per il syntax highlighting
                    outfile.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"# Errore nella lettura del file: {e}")
                    outfile.write("\n```\n\n")


# --- Configurazione ---
# Sostituisci con il percorso del tuo progetto.
# Puoi anche usare '.' se questo script si trova nella cartella principale del progetto.
project_dir = '/Users/gabrielemanenti/PycharmProjects/Webapp_Canottieri_2'
output_file = 'codice_progetto.md'

if __name__ == "__main__":
    export_project_to_file(project_dir, output_file)
    print(f"✅ Codice del progetto esportato con successo in '{output_file}'")