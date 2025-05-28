let ingredientCount = 0;
let utensilCount = 0;
let jsInstructionCounter = 0;

const svgIconMinus = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/></svg>`;

function createRemoveButton() {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'list-action-button remove-item-button';
    button.title = 'Retirer cet élément';
    button.innerHTML = svgIconMinus;
    button.onclick = function () {
        const listItemDiv = this.closest('.list-item'); // C'est la div qui contient le bouton et le champ
        if (listItemDiv) {
            const parentLi = listItemDiv.parentElement;
            // Vérifier si le parent de listItemDiv est un LI et si ce LI est dans #instructions-list
            if (parentLi && parentLi.tagName === 'LI' && parentLi.parentElement && parentLi.parentElement.id === 'instructions-list') {
                parentLi.remove(); // Supprimer le LI pour les instructions
            } else {
                listItemDiv.remove(); // Supprimer la div.list-item pour les ingrédients/ustensiles
            }
        }
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

function addInstruction() {
    jsInstructionCounter++;
    const listItemDiv = document.createElement('div');
    listItemDiv.className = 'list-item instruction-item';
    listItemDiv.innerHTML = `
                <textarea name="instruction_step_${jsInstructionCounter}" placeholder="Description de l'étape"></textarea>
            `;
    listItemDiv.appendChild(createRemoveButton());

    const li = document.createElement('li');
    li.appendChild(listItemDiv);
    document.getElementById('instructions-list').appendChild(li);
}

addIngredient();
addUtensil();
addInstruction();

document.getElementById('recipe-form').addEventListener('submit', function (event) {
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
    document.querySelectorAll('#instructions-list .instruction-item textarea[name^="instruction_step_"]').forEach(textarea => { // Modifié le sélecteur
        if (textarea.value.trim() !== "") recipeJson.instructions.push(textarea.value.trim());
    });
    for (const key in recipeJson.durations) if (!recipeJson.durations[key].trim()) recipeJson.durations[key] = "";
    if (!recipeJson.image_filename) recipeJson.image_filename = "";
    document.getElementById('json-output').value = JSON.stringify(recipeJson, null, 2);
});

// NOUVEAU: JavaScript pour le bouton Copier
const copyButton = document.getElementById('copy-json-button');
const jsonTextarea = document.getElementById('json-output');
const copyFeedback = document.getElementById('copy-feedback'); // Conservé pour les messages d'erreur
const originalCopyButtonSVGHTML = copyButton.querySelector('svg') ? copyButton.querySelector('svg').outerHTML : '';
const checkIconSVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-icon lucide-check"><path d="M20 6 9 17l-5-5"/></svg>';

copyButton.addEventListener('click', function () {
    function showCopySuccessIconAndFinalize() {
        const svgElement = copyButton.querySelector('svg');
        if (svgElement && checkIconSVG) {
            svgElement.outerHTML = checkIconSVG;
        }
        setTimeout(() => {
            const currentSvg = copyButton.querySelector('svg');
            if (currentSvg && originalCopyButtonSVGHTML) {
                currentSvg.outerHTML = originalCopyButtonSVGHTML;
            }
        }, 2000);
        window.getSelection().removeAllRanges(); // Désélectionne le texte après la copie
    }

    function showCopyError(errMessage, consoleError) {
        copyFeedback.textContent = errMessage;
        if (consoleError) {
            console.error(consoleError.message || 'Erreur durant la copie.', consoleError);
        }
        setTimeout(() => {
            copyFeedback.textContent = '';
        }, 2000);
    }

    if (!jsonTextarea.value) {
        showCopyError('Rien à copier !');
        return;
    }

    jsonTextarea.select();
    jsonTextarea.setSelectionRange(0, 99999); // Pour les appareils mobiles

    try {
        const successful = document.execCommand('copy'); // Ancienne méthode, mais large support
        if (successful) {
            showCopySuccessIconAndFinalize();
        } else {
            // Essayer avec l'API Clipboard plus moderne
            navigator.clipboard.writeText(jsonTextarea.value).then(
                showCopySuccessIconAndFinalize,
                (err) => showCopyError('Erreur copie', err)
            );
        }
    } catch (err) {
        // Fallback sur l'API Clipboard si execCommand n'est pas supporté/échoue
        navigator.clipboard.writeText(jsonTextarea.value).then(
            showCopySuccessIconAndFinalize,
            (err) => showCopyError('Erreur copie (fallback)', err)
        );
    }
});
