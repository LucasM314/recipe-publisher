import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML as WeasyHTML, CSS as WeasyCSS  # <-- NOUVEAU
from weasyprint.text.fonts import FontConfiguration  # <-- NOUVEAU pour les polices

# ... (le reste de vos configurations reste identique) ...
PROJECT_ROOT = Path(__file__).resolve().parent

RECIPES_DATA_DIR = PROJECT_ROOT / "recipe_data"
MASTER_JSON_FILENAME = "all_recipes.json"
SOURCE_RECIPE_IMAGES_DIR = PROJECT_ROOT / "source_recipe_images"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
TEMPLATE_FILENAME = "base_recipe.html"

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_RECIPE_IMAGES_DIR = OUTPUT_DIR / "recipe_images"
OUTPUT_CSS_DIR = OUTPUT_DIR / "css"
OUTPUT_FONTS_DIR = OUTPUT_DIR / "fonts"
OUTPUT_PDF_DIR = OUTPUT_DIR / "pdf_recipes"  # <-- NOUVEAU: Dossier pour les PDF

SOURCE_STATIC_CSS_DIR = PROJECT_ROOT / "static" / "css"
SOURCE_STATIC_FONTS_DIR = PROJECT_ROOT / "static" / "fonts"


def generate_safe_filename(
    title_fr: str, extension: str = "html"
) -> str:  # Ajout d'un paramètre extension
    name = title_fr.lower()
    name = name.replace(" ", "_")
    name = "".join(c for c in name if c.isalnum() or c == "_" or ord(c) > 127)
    name = name[:70] if len(name) > 70 else (name if name else "untitled_recipe")
    return f"{name}.{extension}"


def needs_de_separator(quantity_str):
    """
    Détermine si la chaîne de quantité nécessite un " de " avant le nom de l'ingrédient.
    Retourne False si la quantité est purement numérique (ex: "3", "1.5"),
    indiquant que l'ingrédient lui-même sert d'unité (ex: "3 oeufs").
    Retourne True si la quantité contient une unité textuelle (ex: "200g", "1 cuillère").
    """
    s = str(quantity_str).strip()
    if not s:  # Si la quantité est vide
        return False
    try:
        # Essayer de convertir en nombre. Si ça réussit, c'est une quantité "pure".
        float(s.replace(",", "."))  # Gérer la virgule décimale française
        # Si la conversion réussit, cela signifie que la chaîne est un nombre
        # (ex: "3", "100", "0.5"). Dans ce cas, on ne veut PAS de "de".
        return False
    except ValueError:
        # Si la conversion échoue, cela signifie que la chaîne contient du texte
        # (ex: "200g", "1 cuillère", "une pincée", "1-2"). Dans ce cas, on VEUT "de".
        return True


def copy_static_assets():
    # ... (fonction copy_static_assets reste identique) ...
    if OUTPUT_CSS_DIR.exists():
        shutil.rmtree(OUTPUT_CSS_DIR)
    OUTPUT_CSS_DIR.mkdir(parents=True, exist_ok=True)
    if SOURCE_STATIC_CSS_DIR.exists() and SOURCE_STATIC_CSS_DIR.is_dir():
        for item_path in SOURCE_STATIC_CSS_DIR.iterdir():
            if item_path.is_file() and item_path.suffix == ".css":
                destination_path = OUTPUT_CSS_DIR / item_path.name
                shutil.copy2(item_path, destination_path)
    else:
        print(f"Warning: Source CSS directory '{SOURCE_STATIC_CSS_DIR}' not found.")

    if OUTPUT_FONTS_DIR.exists():
        shutil.rmtree(OUTPUT_FONTS_DIR)
    if SOURCE_STATIC_FONTS_DIR.exists() and SOURCE_STATIC_FONTS_DIR.is_dir():
        shutil.copytree(SOURCE_STATIC_FONTS_DIR, OUTPUT_FONTS_DIR)
        print(f"  Fonts copied to: {OUTPUT_FONTS_DIR}")
    else:
        print(f"Warning: Source Fonts directory '{SOURCE_STATIC_FONTS_DIR}' not found.")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_RECIPE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PDF_DIR.mkdir(
        parents=True, exist_ok=True
    )  # <-- NOUVEAU: Créer le dossier PDF

    copy_static_assets()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(TEMPLATE_FILENAME)

    # Configuration des polices pour WeasyPrint (pour qu'il trouve vos polices locales)
    font_config = FontConfiguration()  # Crée une config par défaut
    # Si vos @font-face dans style_base.css sont bien relatifs et pointent vers les polices
    # copiées dans output/fonts, WeasyPrint devrait les trouver.
    # Sinon, vous pouvez explicitement ajouter des règles ici :
    # css_for_fonts = """
    # @font-face {font-family: 'Outfit'; src: url('fonts/outfit/Outfit-VariableFont_wght.ttf');}
    # @font-face {font-family: 'Young Serif'; src: url('fonts/young-serif/YoungSerif-Regular.ttf');}
    # """
    # Cette étape n'est souvent pas nécessaire si les @font-face sont dans le CSS principal.

    master_json_path = RECIPES_DATA_DIR / MASTER_JSON_FILENAME
    try:
        all_recipes_data = json.loads(master_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: Master JSON file '{master_json_path}' not found.")
        return
    # ... (reste de la gestion des erreurs JSON identique) ...
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{master_json_path}'. Please check syntax.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading '{master_json_path}': {e}")
        return

    if not isinstance(all_recipes_data, list):
        print(f"Error: Content of '{master_json_path}' is not a list of recipes.")
        return
    if not all_recipes_data:
        print(f"The file '{master_json_path}' is empty or contains no recipes.")
        return

    print(
        f"Found {len(all_recipes_data)} recipe(s) in '{master_json_path}'. Processing..."
    )

    # Charger les CSS une seule fois pour les utiliser avec WeasyPrint
    # WeasyPrint a besoin des chemins absolus ou des URL pour les CSS externes
    # ou alors on lui passe le contenu.
    # Pour les chemins relatifs dans le HTML, WeasyPrint les résout par rapport au base_url.

    # Lister tous les fichiers CSS qui seront utilisés (pour WeasyPrint)
    # On suppose que style_base.css contient déjà les @font-face
    main_css_file = OUTPUT_CSS_DIR / "style_base.css"
    print_css_file = OUTPUT_CSS_DIR / "print.css"

    stylesheets = []
    if main_css_file.exists():
        stylesheets.append(WeasyCSS(filename=main_css_file, font_config=font_config))
    if print_css_file.exists():
        stylesheets.append(
            WeasyCSS(
                filename=print_css_file, font_config=font_config, media_type="print"
            )
        )

    for i, recipe_data in enumerate(all_recipes_data):
        if not isinstance(recipe_data, dict):
            print(f"  Skipping item {i + 1}: not a valid recipe object.")
            continue
        recipe_name_fr = recipe_data.get("name", f"untitled_recipe_{i + 1}")
        recipe_data["name"] = recipe_name_fr  # Assurer la présence pour le template

        if "type" not in recipe_data or not recipe_data["type"]:
            recipe_data["type"] = "default"

        if "description" not in recipe_data:
            recipe_data["description"] = "Une délicieuse recette à découvrir."

        if "ingredients" in recipe_data and "list" in recipe_data["ingredients"]:
            for ingredient_item in recipe_data["ingredients"]["list"]:
                # Get the original quantity, ensure it's a string, and strip whitespace
                original_quantity = ingredient_item.get(
                    "quantity"
                )  # Use your actual key name

                if original_quantity is None:
                    current_quantity_str = ""
                # Handle if quantity is accidentally an int/float from JSON
                elif isinstance(original_quantity, (int, float)):
                    current_quantity_str = str(original_quantity)
                else:
                    current_quantity_str = str(original_quantity).strip()

                # Now, modify the 'quantity' field for display
                if current_quantity_str and needs_de_separator(current_quantity_str):
                    # Append " de" to the quantity string
                    ingredient_item["quantity"] = current_quantity_str + " de"
                else:
                    # Otherwise, just use the (cleaned) original string
                    ingredient_item["quantity"] = current_quantity_str

        # Copie des images (inchangé)
        image_filename_val = recipe_data.get("image_filename")
        if image_filename_val:
            source_image_path = SOURCE_RECIPE_IMAGES_DIR / image_filename_val
            dest_image_path = OUTPUT_RECIPE_IMAGES_DIR / image_filename_val
            if source_image_path.exists() and source_image_path.is_file():
                try:
                    shutil.copy2(source_image_path, dest_image_path)
                except Exception as e:
                    print(
                        f"    Error copying image '{source_image_path}' to '{dest_image_path}': {e}"
                    )
                    recipe_data["image_filename"] = None
            else:
                print(
                    f"    Warning: Image '{source_image_path}' for recipe '{recipe_name_fr}' not found."
                )
                recipe_data["image_filename"] = None

        # Génération HTML (inchangé)
        try:
            html_content = template.render(recipe=recipe_data)
        except Exception as e:
            print(f"  Error rendering template for '{recipe_name_fr}': {e}")
            continue

        # Sauvegarde du fichier HTML (inchangé)
        output_html_filename_str = generate_safe_filename(
            recipe_name_fr, extension="html"
        )
        output_html_path = OUTPUT_DIR / output_html_filename_str
        try:
            output_html_path.write_text(html_content, encoding="utf-8")
            print(f"  Page HTML générée : {output_html_path}")
        except Exception as e:
            print(f"  Error writing HTML file '{output_html_path}': {e}")
            continue  # On ne peut pas générer de PDF si le HTML a échoué

        # --- NOUVEAU: Génération du PDF avec WeasyPrint ---
        output_pdf_filename_str = generate_safe_filename(
            recipe_name_fr, extension="pdf"
        )
        output_pdf_path = OUTPUT_PDF_DIR / output_pdf_filename_str

        try:
            # WeasyPrint peut prendre le chemin du fichier HTML ou son contenu.
            # Il est souvent plus simple de lui donner le chemin du fichier HTML généré
            # car il pourra résoudre les chemins relatifs des images et CSS plus facilement.
            # Le `base_url` est crucial pour que WeasyPrint trouve les assets (images, CSS)
            # référencés avec des chemins relatifs dans le HTML.
            # Puisque nos CSS et images sont dans des sous-dossiers de OUTPUT_DIR,
            # et que nos HTML sont aussi dans OUTPUT_DIR, le base_url devrait être OUTPUT_DIR.

            html_for_pdf = WeasyHTML(
                filename=output_html_path, base_url=str(OUTPUT_DIR.resolve())
            )

            # On peut aussi passer les stylesheets directement. C'est plus robuste.
            # Si les stylesheets sont passés ici, WeasyPrint n'essaiera pas de les charger depuis les balises <link>
            # ce qui peut éviter des problèmes si les chemins dans <link> ne sont pas parfaits pour WeasyPrint.
            # Cependant, il va quand même lire les <link> pour savoir quels media types s'appliquent si non spécifié ici.

            # On récupère les CSS spécifiques au type de plat
            specific_type_css_list = []
            if recipe_data["type"] != "default":
                type_css_file = OUTPUT_CSS_DIR / f"style_{recipe_data['type']}.css"
                if type_css_file.exists():
                    specific_type_css_list.append(
                        WeasyCSS(filename=type_css_file, font_config=font_config)
                    )

            html_for_pdf.write_pdf(
                output_pdf_path,
                stylesheets=stylesheets
                + specific_type_css_list,  # Concaténer les listes de CSS
            )
            print(f"  Page PDF générée  : {output_pdf_path}")
        except Exception as e:
            print(f"  Erreur lors de la génération du PDF pour '{recipe_name_fr}': {e}")
            import traceback

            traceback.print_exc()  # Imprime la trace complète de l'erreur WeasyPrint

    print(
        f"\nProcessing complete. Check the '{OUTPUT_DIR}' and '{OUTPUT_PDF_DIR}' directories."
    )


if __name__ == "__main__":
    main()
