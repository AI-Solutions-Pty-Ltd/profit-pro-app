/**
 * Searchable Select Component Logic
 * Handles filtering, selection, and dynamic quick-creation across the application.
 * All logic uses relative DOM traversal to support dynamic formsets.
 */

let activeQuickCreateSelectId = null;

/**
 * Toggles a searchable select dropdown.
 * @param {HTMLElement} btn - The button that triggered the toggle.
 */
function toggleSearchableSelect(btn) {
    const container = btn.closest('.searchable-select-container');
    if (!container) return;

    const dropdown = container.querySelector('.searchable-dropdown') || container.querySelector('[id$="-dropdown"]');
    const arrow = container.querySelector('[id$="-selector-arrow"]');
    
    if (!dropdown) return;

    const isHidden = dropdown.classList.contains('hidden');

    // Close all other dropdowns
    document.querySelectorAll('.searchable-dropdown').forEach(d => {
        if (d !== dropdown && !d.classList.contains('hidden')) {
            d.classList.add('scale-95', 'opacity-0');
            setTimeout(() => d.classList.add('hidden'), 200);
            const a = d.closest('.searchable-select-container').querySelector('[id$="-selector-arrow"]');
            if (a) a.classList.remove('rotate-180');
        }
    });

    if (isHidden) {
        dropdown.classList.remove('hidden');
        // Force reflow for animation
        dropdown.offsetHeight;
        dropdown.classList.remove('scale-95', 'opacity-0');
        dropdown.classList.add('scale-100', 'opacity-100');
        
        if (arrow) arrow.classList.add('rotate-180');
        const searchInput = dropdown.querySelector('input[type="text"]');
        if (searchInput) {
            searchInput.value = '';
            filterSearchableOptions(searchInput);
            setTimeout(() => searchInput.focus(), 100);
        }
    } else {
        dropdown.classList.add('scale-95', 'opacity-0');
        dropdown.classList.remove('scale-100', 'opacity-100');
        if (arrow) arrow.classList.remove('rotate-180');
        setTimeout(() => dropdown.classList.add('hidden'), 200);
    }
}

/**
 * Filters the list based on user search input.
 * @param {HTMLElement} input - The search input element.
 */
function filterSearchableOptions(input) {
    const container = input.closest('.searchable-select-container');
    if (!container) return;

    const query = input.value.toLowerCase();
    const items = container.querySelectorAll('.option-item');
    const sections = container.querySelectorAll('.searchable-section');
    const noResults = container.querySelector('[id$="-no-results"]');
    
    let hasResults = false;

    items.forEach(item => {
        const label = item.dataset.label || '';
        if (label.includes(query)) {
            item.classList.remove('hidden');
            hasResults = true;
        } else {
            item.classList.add('hidden');
        }
    });

    if (noResults) {
        noResults.classList.toggle('hidden', hasResults);
    }

    // Hide sections that have no visible children
    sections.forEach(section => {
        const visibleItems = section.querySelectorAll('.option-item:not(.hidden)');
        section.classList.toggle('hidden', visibleItems.length === 0);
    });
}

/**
 * Updates the visible label and hidden input for a selectable item.
 */
function selectSearchableOption(target, id, label) {
    const container = target.closest('.searchable-select-container');
    if (!container) {
        console.error("Could not find searchable select container for option selection");
        return;
    }

    const hiddenInput = container.querySelector('input[type="hidden"]') || container.querySelector('select');
    const displayLabel = container.querySelector('.selected-label') || container.querySelector('[id$="-selector-label"]');
    const dropdown = container.querySelector('.searchable-dropdown') || container.querySelector('[id$="-dropdown"]');
    const arrow = container.querySelector('[id$="-selector-arrow"]');

    if (hiddenInput) {
        hiddenInput.value = id;
        hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    if (displayLabel) displayLabel.textContent = label;

    // Close the dropdown
    if (dropdown) dropdown.classList.add('hidden');
    if (arrow) arrow.classList.remove('rotate-180');
}

/**
 * Opens a dynamic quick-create modal for a specific resource type.
 */
function openQuickCreateModal(selectId, resourceType) {
    activeQuickCreateSelectId = selectId;
    const modal = document.getElementById('dynamic-quick-create-modal');
    const contentArea = document.getElementById('dynamic-modal-content');
    const titleArea = document.getElementById('dynamic-modal-title');
    const errorContainer = document.getElementById('dynamic-modal-errors');

    if (!modal) {
        console.error("Dynamic modal not found in DOM");
        return;
    }

    // Reset and show loader
    contentArea.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12 space-y-4">
            <div class="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Loading Form...</p>
        </div>`;
    if (errorContainer) errorContainer.classList.add('hidden');

    modal.showModal();

    // Fetch the form HTML via AJAX
    fetch(`/quick-create/form/?resource_type=${resourceType}`)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                contentArea.innerHTML = data.html;
                if (titleArea) titleArea.textContent = data.title;
            } else {
                contentArea.innerHTML = `<div class="p-4 text-red-600">Failed to load form.</div>`;
            }
        })
        .catch(err => {
            console.error("Error loading form:", err);
            contentArea.innerHTML = `<div class="p-4 text-red-600">Error communication with server.</div>`;
        });
}

function closeDynamicQuickCreateModal() {
    const modal = document.getElementById('dynamic-quick-create-modal');
    if (modal) modal.close();
}

/**
 * Submits the dynamic quick-create form via AJAX.
 */
function submitDynamicQuickCreate(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('dynamic-modal-submit');
    const submitText = document.getElementById('dynamic-submit-text');
    const submitSpinner = document.getElementById('dynamic-submit-spinner');
    const errorContainer = document.getElementById('dynamic-modal-errors');
    const errorList = document.getElementById('dynamic-error-list');

    // Project context
    const projectMatch = window.location.pathname.match(/\/project\/(\d+)\//);
    if (projectMatch) {
        formData.append('project_pk', projectMatch[1]);
    }

    // Loading state
    if (submitBtn) submitBtn.disabled = true;
    if (submitText) submitText.textContent = 'Saving...';
    if (submitSpinner) submitSpinner.classList.remove('hidden');
    if (errorContainer) errorContainer.classList.add('hidden');

    fetch('/quick-create/submit/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const widgetId = activeQuickCreateSelectId;
            const optionsList = document.getElementById(`${widgetId}-options-list`);
            
            if (optionsList) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'w-full text-left flex items-center px-4 py-2.5 rounded-lg hover:bg-indigo-50/80 group transition-all duration-200 option-item';
                btn.dataset.id = data.id;
                btn.dataset.label = data.name.toLowerCase();
                btn.onclick = (e) => selectSearchableOption(e.target.closest('button'), data.id, data.name);
                btn.innerHTML = `
                    <div class="flex-1">
                        <span class="block text-sm font-semibold text-gray-700 group-hover:text-indigo-900">${data.name}</span>
                    </div>
                    <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                        <svg class="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>`;
                optionsList.insertBefore(btn, optionsList.firstChild);
            }

            // Also append to the native select to ensure value persistence
            const nativeSelect = document.getElementById(widgetId);
            if (nativeSelect && nativeSelect.tagName === 'SELECT') {
                const opt = document.createElement('option');
                opt.value = data.id;
                opt.textContent = data.name;
                opt.selected = true;
                nativeSelect.appendChild(opt);
            }

            // Select the new option immediately
            const widgetContainer = document.getElementById(`${widgetId}-selector-container`);
            if (widgetContainer) {
                selectSearchableOption(widgetContainer, data.id, data.name);
            }
            
            closeDynamicQuickCreateModal();
            
            if (typeof showToast === 'function') {
                showToast('Created and selected successfully!', 'success');
            }
        } else {
            if (errorContainer && errorList) {
                errorContainer.classList.remove('hidden');
                errorList.innerHTML = '';
                for (const [field, errors] of Object.entries(data.errors)) {
                    errorList.innerHTML += `<p class="font-bold uppercase text-[10px] tracking-tight mt-1">${field}:</p> ${errors.join(', ')}<br>`;
                }
            }
        }
    })
    .finally(() => {
        if (submitBtn) submitBtn.disabled = false;
        if (submitText) submitText.textContent = 'Create & Select';
        if (submitSpinner) submitSpinner.classList.add('hidden');
    });
}

// Global click handler to close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.searchable-select-container')) {
        document.querySelectorAll('.searchable-dropdown, [id$="-dropdown"]').forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
        document.querySelectorAll('[id$="-selector-arrow"]').forEach(arrow => {
            arrow.classList.remove('rotate-180');
        });
    }
});

// Polyfill for closest if needed (though modern browsers support it)
if (window.Element && !Element.prototype.closest) {
    Element.prototype.closest = function(s) {
        var matches = (this.document || this.ownerDocument).querySelectorAll(s),
            i,
            el = this;
        do {
            i = matches.length;
            while (--i >= 0 && matches.item(i) !== el) {};
        } while ((i < 0) && (el = el.parentElement));
        return el;
    };
}
