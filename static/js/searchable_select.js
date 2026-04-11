/**
 * Searchable Select Component Logic
 * Centralized logic for the reusable searchable dropdown widget.
 * Refactored to be robust against ID duplication (e.g. in dynamic formsets).
 */

/**
 * Toggle the visibility of the dropdown
 * @param {string|HTMLElement} target - The prefix ID or the element itself
 */
function toggleSearchableDropdown(target) {
    let container;
    if (typeof target === 'string') {
        container = document.getElementById(`${target}-selector-container`);
    } else {
        container = target.closest('.searchable-select-container');
    }
    
    if (!container) return;

    const dropdown = container.querySelector('[id$="-dropdown"]');
    const arrow = container.querySelector('[id$="-selector-arrow"]');
    if (!dropdown || !arrow) return;

    const isHidden = dropdown.classList.contains('hidden');
    
    // Close other dropdowns first
    document.querySelectorAll('.searchable-select-container [id$="-dropdown"]').forEach(d => {
        if (d !== dropdown) {
            d.classList.add('hidden');
            const otherContainer = d.closest('.searchable-select-container');
            const otherArrow = otherContainer.querySelector('[id$="-selector-arrow"]');
            if (otherArrow) otherArrow.classList.remove('rotate-180');
        }
    });

    if (isHidden) {
        dropdown.classList.remove('hidden');
        arrow.classList.add('rotate-180');
        const searchInput = dropdown.querySelector('input[type="text"]');
        if (searchInput) {
            searchInput.value = ''; // Clear on open
            searchInput.focus();
            // Trigger filter to reset view
            filterSearchableOptions(container);
        }
    } else {
        dropdown.classList.add('hidden');
        arrow.classList.remove('rotate-180');
    }
}

/**
 * Filter options based on search input
 * @param {HTMLElement|string} target - The prefix ID or the container element
 */
function filterSearchableOptions(target) {
    let container;
    if (typeof target === 'string') {
        container = document.getElementById(`${target}-selector-container`);
    } else {
        container = target.closest('.searchable-select-container');
    }
    
    if (!container) return;

    const searchInput = container.querySelector('input[type="text"]');
    if (!searchInput) return;

    const search = searchInput.value.toLowerCase();
    const items = container.querySelectorAll('.option-item');
    const noResults = container.querySelector('[id$="-no-results"]');
    let hasResults = false;

    items.forEach(item => {
        const label = (item.dataset.label || '').toLowerCase();
        if (label.includes(search)) {
            item.style.display = 'flex';
            hasResults = true;
        } else {
            item.style.display = 'none';
        }
    });

    if (noResults) {
        noResults.classList.toggle('hidden', hasResults);
    }
}

/**
 * Handle option selection
 */
function selectSearchableOption(target, id, label) {
    let container;
    if (typeof target === 'string' && !document.getElementById(target)) {
         // If target is an ID but doesn't exist (might be a cloned ID), try to find by context if possible
         // But usually we pass 'this' now
         container = document.querySelector(`.searchable-select-container:has(#${target}-selector-container)`);
    } else if (typeof target === 'string') {
        container = document.getElementById(`${target}-selector-container`);
    } else {
        container = target.closest('.searchable-select-container');
    }
    
    if (!container) return;

    const labelDisplay = container.querySelector('[id$="-selector-label"]');
    const dropdown = container.querySelector('[id$="-dropdown"]');
    const arrow = container.querySelector('[id$="-selector-arrow"]');
    const nativeSelect = container.querySelector('select');

    if (nativeSelect) {
        nativeSelect.value = id;
        nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    if (labelDisplay) labelDisplay.textContent = label;
    if (dropdown) dropdown.classList.add('hidden');
    if (arrow) arrow.classList.remove('rotate-180');
}

// Close on click outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.searchable-select-container')) {
        document.querySelectorAll('.searchable-select-container [id$="-dropdown"]').forEach(d => {
            d.classList.add('hidden');
            const arrow = d.closest('.searchable-select-container').querySelector('[id$="-selector-arrow"]');
            if (arrow) arrow.classList.remove('rotate-180');
        });
    }
});
