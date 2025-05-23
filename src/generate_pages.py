from datetime import datetime
import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML as WeasyHTML, CSS as WeasyCSS
from weasyprint.text.fonts import FontConfiguration
import traceback

# Constants for paths
SRC_ROOT = Path(__file__).resolve().parent
RECIPES_DATA_DIR = SRC_ROOT / "recipe_data"
MASTER_JSON_FILENAME = "all_recipes.json"
SOURCE_RECIPE_IMAGES_DIR = SRC_ROOT / "source_recipe_images"
TEMPLATES_DIR = SRC_ROOT / "templates"
TEMPLATE_RECIPE_PAGE_FILENAME = "base_recipe.html"
TEMPLATE_HOMEPAGE_FILENAME = "index.html"
TEMPLATE_NEW_RECIPE_FILENAME = "new_recipe.html"  # NOUVELLE CONSTANTE

# Output directories (relative to parent of SRC_ROOT for a 'website' folder sibling to src)
OUTPUT_DIR = SRC_ROOT.parent / "website"
OUTPUT_RECIPE_IMAGES_DIR = OUTPUT_DIR / "recipe_images"
OUTPUT_CSS_DIR = OUTPUT_DIR / "css"
OUTPUT_FONTS_DIR = OUTPUT_DIR / "fonts"
OUTPUT_PDF_DIR = OUTPUT_DIR / "pdf_recipes"

SOURCE_STATIC_CSS_DIR = SRC_ROOT / "static" / "css"
SOURCE_STATIC_FONTS_DIR = SRC_ROOT / "static" / "fonts"


def generate_homepage(all_recipes_data, env):
    print("\nGenerating homepage...")
    try:
        homepage_template = env.get_template(TEMPLATE_HOMEPAGE_FILENAME)
    except Exception as e:
        print(f"  Error loading homepage template '{TEMPLATE_HOMEPAGE_FILENAME}': {e}")
        return

    recipes_summary_list = []
    for recipe_data in all_recipes_data:
        if not isinstance(recipe_data, dict):
            continue

        recipe_name = recipe_data.get("name", "untitled")
        html_filename = generate_safe_filename(recipe_name, extension="html")

        image_path = None
        # Handle local images and URLs for the homepage.
        image_filename_val = recipe_data.get("image_filename")
        if image_filename_val:
            if image_filename_val.startswith(("http://", "https://")):
                image_path = image_filename_val
            else:
                image_path = f"{OUTPUT_RECIPE_IMAGES_DIR.name}/{image_filename_val}"

        summary = {
            "name": recipe_name,
            "html_filename": html_filename,
            "image_path": image_path,
            "description": recipe_data.get("description", ""),
            "type": recipe_data.get("type", "default"),
        }
        recipes_summary_list.append(summary)

    homepage_context = {
        "site_title": "Le Grimoire de Véro",
        "site_tagline": "Joyeuse fête des mères !",
        "recipes_summary_list": recipes_summary_list,
        "current_year": datetime.now().year,
    }

    try:
        homepage_html_content = homepage_template.render(homepage_context)
        output_homepage_path = OUTPUT_DIR / "index.html"
        output_homepage_path.write_text(homepage_html_content, encoding="utf-8")
        print(
            f"  Homepage générée : {output_homepage_path.relative_to(SRC_ROOT.parent)}"
        )
    except Exception as e:
        print(f"  Erreur lors de la génération de la page d'accueil : {e}")
        traceback.print_exc()


def generate_new_recipe_page(env):
    print("\nGenerating New Recipe page...")
    try:
        form_template = env.get_template(TEMPLATE_NEW_RECIPE_FILENAME)
    except Exception as e:
        print(
            f"  Error loading new recipe page template '{TEMPLATE_NEW_RECIPE_FILENAME}': {e}"
        )
        return

    try:
        form_html_content = form_template.render()
        output_form_page_path = OUTPUT_DIR / "new_recipe.html"
        output_form_page_path.write_text(form_html_content, encoding="utf-8")
        print(
            f"  New Recipe page generated: {output_form_page_path.relative_to(SRC_ROOT.parent)}"
        )
    except Exception as e:
        print(f"  Error when generating new recipe page: {e}")
        traceback.print_exc()


def generate_safe_filename(title_fr: str, extension: str = "html") -> str:
    name = title_fr.lower()
    name = name.replace(" ", "_")
    # Allow accented characters common in French, and underscore, alphanumeric
    name = "".join(c for c in name if c.isalnum() or c == "_" or ord(c) > 127)
    name = name[:70]  # Truncate if too long
    if not name:  # Handle empty names after sanitization
        name = "untitled_recipe"
    return f"{name}.{extension}"


def needs_de_separator(quantity_str):
    """
    Détermine si la chaîne de quantité nécessite un " de " avant le nom de l'ingrédient.
    Retourne False si la quantité est purement numérique (ex: "3", "1.5"),
    indiquant que l'ingrédient lui-même sert d'unité (ex: "3 oeufs").
    Retourne True si la quantité contient une unité textuelle (ex: "200g", "1 cuillère").
    """
    s = str(quantity_str).strip()
    if not s:
        return False
    try:
        float(s.replace(",", "."))  # Gérer la virgule décimale française
        return False
    except ValueError:
        return True


def copy_static_assets():
    print("\nCopying static assets...")
    # CSS
    if OUTPUT_CSS_DIR.exists():
        shutil.rmtree(OUTPUT_CSS_DIR)
    OUTPUT_CSS_DIR.mkdir(parents=True, exist_ok=True)
    if SOURCE_STATIC_CSS_DIR.exists() and SOURCE_STATIC_CSS_DIR.is_dir():
        shutil.copytree(SOURCE_STATIC_CSS_DIR, OUTPUT_CSS_DIR, dirs_exist_ok=True)
        print(f"  CSS files copied to: {OUTPUT_CSS_DIR.relative_to(SRC_ROOT.parent)}")
    else:
        print(f"Warning: Source CSS directory '{SOURCE_STATIC_CSS_DIR}' not found.")

    # Fonts
    if OUTPUT_FONTS_DIR.exists():
        shutil.rmtree(OUTPUT_FONTS_DIR)
    OUTPUT_FONTS_DIR.mkdir(
        parents=True, exist_ok=True
    )  # Ensure it's created before copytree
    if SOURCE_STATIC_FONTS_DIR.exists() and SOURCE_STATIC_FONTS_DIR.is_dir():
        shutil.copytree(SOURCE_STATIC_FONTS_DIR, OUTPUT_FONTS_DIR, dirs_exist_ok=True)
        print(f"  Fonts copied to: {OUTPUT_FONTS_DIR.relative_to(SRC_ROOT.parent)}")
    else:
        print(f"Warning: Source Fonts directory '{SOURCE_STATIC_FONTS_DIR}' not found.")


def main():
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_RECIPE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

    copy_static_assets()

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    recipe_page_template = env.get_template(TEMPLATE_RECIPE_PAGE_FILENAME)

    font_config = FontConfiguration()

    master_json_path = RECIPES_DATA_DIR / MASTER_JSON_FILENAME
    try:
        all_recipes_data = json.loads(master_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: Master JSON file '{master_json_path}' not found.")
        return
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
        f"\nFound {len(all_recipes_data)} recipe(s) in '{master_json_path}'. Processing individual recipes..."
    )

    # Prepare list of stylesheets for WeasyPrint (loaded once)
    weasy_stylesheets = []
    main_css_path = OUTPUT_CSS_DIR / "style_base.css"
    print_css_path = OUTPUT_CSS_DIR / "print.css"

    if main_css_path.exists():
        weasy_stylesheets.append(
            WeasyCSS(filename=main_css_path, font_config=font_config)
        )
    else:
        print(f"Warning: Main CSS file not found at {main_css_path}")
    if print_css_path.exists():
        weasy_stylesheets.append(
            WeasyCSS(
                filename=print_css_path, font_config=font_config, media_type="print"
            )
        )
    else:
        print(f"Warning: Print CSS file not found at {print_css_path}")

    # Process each recipe
    for i, recipe_data in enumerate(all_recipes_data):
        if not isinstance(recipe_data, dict):
            print(f"  Skipping item {i + 1}: not a valid recipe object.")
            continue

        recipe_name_fr = recipe_data.get("name", f"untitled_recipe_{i + 1}")
        print(f"\nProcessing recipe: {recipe_name_fr}")

        # Ensure default values and apply transformations
        recipe_data["name"] = recipe_name_fr
        recipe_data.setdefault("type", "default")
        recipe_data.setdefault("description", "Une délicieuse recette à découvrir.")

        if "ingredients" in recipe_data and "list" in recipe_data["ingredients"]:
            for ingredient_item in recipe_data["ingredients"]["list"]:
                original_quantity = ingredient_item.get("quantity")
                current_quantity_str = ""
                if original_quantity is not None:
                    current_quantity_str = str(original_quantity).strip()

                needs_de = needs_de_separator(current_quantity_str)
                ingredient_item["quantity"] = current_quantity_str + " de" * needs_de

        # Image copying
        image_filename_val = recipe_data.get("image_filename")
        if image_filename_val and not image_filename_val.startswith(
            ("http://", "https://")
        ):  # Process only local images
            source_image_path = SOURCE_RECIPE_IMAGES_DIR / image_filename_val
            dest_image_path = OUTPUT_RECIPE_IMAGES_DIR / image_filename_val
            if source_image_path.exists() and source_image_path.is_file():
                try:
                    shutil.copy2(source_image_path, dest_image_path)
                    # print(f"    Image '{image_filename_val}' copied to '{dest_image_path}'")
                except Exception as e:
                    print(
                        f"    Error copying image '{source_image_path}' to '{dest_image_path}': {e}"
                    )
                    recipe_data["image_filename"] = None  # Nullify if copy failed
            else:
                print(
                    f"    Warning: Local image '{source_image_path}' for recipe '{recipe_name_fr}' not found."
                )
                recipe_data["image_filename"] = None  # Nullify if not found
        elif image_filename_val and image_filename_val.startswith(
            ("http://", "https://")
        ):
            # print(f"    Image for '{recipe_name_fr}' is a URL: {image_filename_val}")
            pass  # Keep the URL as is

        output_html_filename_str = generate_safe_filename(
            recipe_name_fr, extension="html"
        )
        output_pdf_filename_str = generate_safe_filename(
            recipe_name_fr, extension="pdf"
        )
        # Chemin relatif depuis la page HTML (dans OUTPUT_DIR) vers le PDF (dans OUTPUT_PDF_DIR)
        recipe_data["pdf_path"] = f"{OUTPUT_PDF_DIR.name}/{output_pdf_filename_str}"

        # Context for rendering the individual recipe page
        recipe_page_context = {
            "recipe": recipe_data,
            "site_title": "Le Grimoire de Véro",  # Pass site title for consistency in <title>
        }

        # Generate HTML page
        try:
            html_content = recipe_page_template.render(recipe_page_context)
            output_html_path = OUTPUT_DIR / output_html_filename_str
            output_html_path.write_text(html_content, encoding="utf-8")
            print(
                f"  HTML page generated: {output_html_path.relative_to(SRC_ROOT.parent)}"
            )
        except Exception as e:
            print(f"  Error rendering HTML template for '{recipe_name_fr}': {e}")
            traceback.print_exc()
            continue

        # Generate PDF page
        try:
            html_for_pdf = WeasyHTML(
                filename=output_html_path, base_url=str(OUTPUT_DIR.resolve())
            )

            # Add recipe-type-specific CSS for PDF if it exists
            current_stylesheets_for_pdf = list(weasy_stylesheets)
            if recipe_data["type"] != "default":
                type_css_filename = f"style_{recipe_data['type']}.css"
                type_css_path = OUTPUT_CSS_DIR / type_css_filename
                if type_css_path.exists():
                    current_stylesheets_for_pdf.append(
                        WeasyCSS(filename=type_css_path, font_config=font_config)
                    )

            output_pdf_path = OUTPUT_PDF_DIR / output_pdf_filename_str
            html_for_pdf.write_pdf(
                output_pdf_path, stylesheets=current_stylesheets_for_pdf
            )
            print(
                f"  PDF page generated : {output_pdf_path.relative_to(SRC_ROOT.parent)}"
            )
        except Exception as e:
            print(f"  Error generating PDF for '{recipe_name_fr}': {e}")
            traceback.print_exc()

    # Generate homepage after all individual pages and PDFs are processed
    if all_recipes_data:
        generate_homepage(all_recipes_data, env)

    # APPEL À LA NOUVELLE FONCTION
    generate_new_recipe_page(env)

    print(
        f"\nProcessing complete. Output in: '{OUTPUT_DIR.relative_to(SRC_ROOT.parent)}'"
    )


if __name__ == "__main__":
    main()
