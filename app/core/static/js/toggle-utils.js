/**
 * Reusable Toggle Utility
 *
 * Usage: Add onclick="toggleElement(this, 'target-id')" to any button.
 * The target element must have class="hidden" initially if you want it collapsed on load.
 *
 * Examples:
 * <button onclick="toggleElement(this, 'my-section')" data-hidden="true">Toggle</button>
 * <div id="my-section" class="hidden">Content</div>
 */

function toggleElement(button, target) {
    const targetElement = document.getElementById(target);
    if (!targetElement) return;
    const isHidden = targetElement.classList.contains("hidden");
    if (isHidden) {
        _showElement(button, targetElement);
    } else {
        _hideElement(button, targetElement);
    }
}

function _hideElement(button, targetElement) {
    targetElement.classList.add("hidden");
    button.dataset.hidden = "true";
    const color = _getIconColor(button);
    button.innerHTML = _chevronRight(color);
}

function _showElement(button, targetElement) {
    targetElement.classList.remove("hidden");
    button.dataset.hidden = "false";
    const color = _getIconColor(button);
    button.innerHTML = _chevronDown(color);
}

function _getIconColor(button) {
    if (!button.dataset.iconColor) {
        const svgClass = button.querySelector("svg")?.getAttribute("class") || "";
        const colorClass = svgClass.split(" ").find((cls) => cls.startsWith("text-")) || "text-gray-600";
        button.dataset.iconColor = colorClass;
    }
    return button.dataset.iconColor;
}

function _chevronRight(colorClass) {
    return `<svg fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true" width="20" height="20" class="${colorClass}">
        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"></path>
    </svg>`;
}

function _chevronDown(colorClass) {
    return `<svg fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true" width="20" height="20" class="${colorClass}">
        <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5"></path>
    </svg>`;
}
