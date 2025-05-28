let ingredientCount = 0;
let utensilCount = 0;
let jsInstructionCounter = 0;

const svgIconMinus = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/></svg>`;

function createRemoveButton() {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'action-list-button remove-item-btn';
    button.title = 'Retirer cet élément';
    button.innerHTML = svgIconMinus;
    button.onclick = function () {
        this.closest('.list-item').remove();
    };
    return button;
}

function addIngredient() { /* ... inchangé ... */
    ingredientCount++;
    const div = document.createElement('div');
    div.className = 'list-item ingredient-item';
    div.innerHTML = `
                <input type="text" name="ingredient_quantity_${ingredientCount}" placeholder="Quantité (ex: 200g, 1)">
                <input type="text" name="ingredient_name_${ingredientCount}" placeholder="Nom de l'ingrédient">
            `;
    div.appendChild(createRemoveButton());
    document.getElementById('ingredients-list').appendChild(div);
}

function addUtensil() { /* ... inchangé ... */
    utensilCount++;
    const div = document.createElement('div');
    div.className = 'list-item utensil-item';
    div.innerHTML = `
                <input type="text" name="utensil_name_${utensilCount}" placeholder="Nom de l'ustensile">
            `;
    div.appendChild(createRemoveButton());
    document.getElementById('utensils-list').appendChild(div);
}

function addInstruction() { /* ... inchangé ... */
    jsInstructionCounter++;
    const div = document.createElement('div');
    div.className = 'list-item instruction-item';
    div.innerHTML = `
                <textarea name="instruction_step_${jsInstructionCounter}" placeholder="Description de l'étape"></textarea>
            `;
    div.appendChild(createRemoveButton());
    document.getElementById('instructions-list').appendChild(div);
}

addIngredient();
addUtensil();
addInstruction();

document.getElementById('recipe-form').addEventListener('submit', function (event) { /* ... inchangé ... */
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    const recipeJson = {
        name: data.name || "", type: data.type === "default" ? "" : data.type,
        description: data.description || "",
        image_filename: data.image_filename || (data.image_url ? data.image_url : ""),
        durations: {
            total: data.total_duration || "", preparation: data.prep_duration || "",
            cooking: data.cook_duration || "", rest: data.rest_duration || ""
        },
        ingredients: {serves: data.serves || "", list: []},
        utensils: [], instructions: []
    };
    document.querySelectorAll('#ingredients-list .list-item').forEach(item => {
        const q = item.querySelector('input[name^="ingredient_quantity_"]');
        const n = item.querySelector('input[name^="ingredient_name_"]');
        if ((n && n.value.trim() !== "") || (q && q.value.trim() !== "")) {
            recipeJson.ingredients.list.push({quantity: q ? q.value.trim() : "", name: n ? n.value.trim() : ""});
        }
    });
    document.querySelectorAll('#utensils-list .list-item input[name^="utensil_name_"]').forEach(i => {
        if (i.value.trim() !== "") recipeJson.utensils.push(i.value.trim());
    });
    document.querySelectorAll('#instructions-list .list-item textarea[name^="instruction_step_"]').forEach(textarea => {
        if (textarea.value.trim() !== "") recipeJson.instructions.push(textarea.value.trim());
    });
    for (const key in recipeJson.durations) if (!recipeJson.durations[key].trim()) recipeJson.durations[key] = "";
    if (!recipeJson.image_filename) recipeJson.image_filename = "";
    document.getElementById('json-output').value = JSON.stringify(recipeJson, null, 2);
});

// NOUVEAU: JavaScript pour le bouton Copier
const copyButton = document.getElementById('copy-json-button');
const jsonTextarea = document.getElementById('json-output');
const copyFeedback = document.getElementById('copy-feedback');

copyButton.addEventListener('click', function () {
    if (!jsonTextarea.value) {
        copyFeedback.textContent = 'Rien à copier !';
        setTimeout(() => {
            copyFeedback.textContent = '';
        }, 2000);
        return;
    }
    jsonTextarea.select(); // Sélectionne le contenu de la textarea
    jsonTextarea.setSelectionRange(0, 99999); // Pour les appareils mobiles

    try {
        const successful = document.execCommand('copy'); // Ancienne méthode, mais large support
        if (successful) {
            copyFeedback.textContent = 'Copié !';
        } else {
            // Essayer avec l'API Clipboard plus moderne si execCommand échoue ou n'est pas supporté
            navigator.clipboard.writeText(jsonTextarea.value).then(function () {
                copyFeedback.textContent = 'Copié !';
            }, function (err) {
                copyFeedback.textContent = 'Erreur copie';
                console.error('Async: Could not copy text: ', err);
            });
        }
    } catch (err) {
        navigator.clipboard.writeText(jsonTextarea.value).then(function () {
            copyFeedback.textContent = 'Copié !';
        }, function (err) {
            copyFeedback.textContent = 'Erreur copie';
            console.error('Fallback Async: Could not copy text: ', err);
        });
    }

    // Enlever le message après quelques secondes
    setTimeout(() => {
        copyFeedback.textContent = '';
    }, 2000);

    window.getSelection().removeAllRanges(); // Désélectionne le texte
});

