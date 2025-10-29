/**
 * Reusable Loading Button Functionality
 *
 * Usage: Add class 'loading-btn' to any button and optionally data-loading-text="Custom loading text"
 *
 * Examples:
 * <button type="submit" class="loading-btn">Submit</button>
 * <button type="button" class="loading-btn" data-loading-text="Processing...">Process Data</button>
 */
document.addEventListener("DOMContentLoaded", function () {
  const loadingButtons = document.querySelectorAll(".loading-btn");

  loadingButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      try {
        // Only proceed if button is not already disabled
        if (this.disabled) {
          e.preventDefault();
          return;
        }

        // For submit buttons, let the form validation run first
        if (this.type === "submit") {
          const form = this.closest("form");
          if (form && !form.checkValidity()) {
            return; // Don't show loading if form is invalid
          }
        }

        // For submit buttons, let the form submit first, then show loading
        if (this.type === "submit") {
          const button = this;
          const originalHTML = this.innerHTML;
          const loadingText = this.dataset.loadingText || "Loading...";
          const disableElements = this.dataset.disableElements;

          // Small delay to allow form submission to start
          setTimeout(() => {
            // Store original content
            button.dataset.originalHtml = originalHTML;

            // Create spinner SVG
            const spinner = `
                        <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    `;

            // Update button content with spinner
            button.innerHTML = spinner + loadingText;

            // Disable the button
            button.disabled = true;

            // Add opacity to show disabled state
            button.style.opacity = "0.7";
            button.style.cursor = "not-allowed";

            // Disable additional elements if specified
            if (disableElements) {
              // Split the selector string by spaces and handle each selector
              const selectors = disableElements.trim().split(/\s+/);
              const allElements = [];
              
              selectors.forEach(selector => {
                if (selector.trim()) {
                  const elements = document.querySelectorAll(selector.trim());
                  allElements.push(...Array.from(elements));
                }
              });
              
              // Remove duplicates and disable all found elements
              const uniqueElements = [...new Set(allElements)];
              uniqueElements.forEach((element) => {
                // For anchor tags, we can't use disabled property
                if (element.tagName === "A") {
                  element.style.opacity = "0.5";
                  element.style.cursor = "not-allowed";
                  element.style.pointerEvents = "none";
                  element.setAttribute("aria-disabled", "true");
                } else {
                  element.disabled = true;
                  element.style.opacity = "0.5";
                  element.style.cursor = "not-allowed";
                  element.style.pointerEvents = "none";
                }
              });
            }
          }, 10);
        } else {
          // For non-submit buttons, disable immediately
          const disableElements = this.dataset.disableElements;

          // Store original content
          const originalHTML = this.innerHTML;
          this.dataset.originalHtml = originalHTML;

          // Get loading text
          const loadingText = this.dataset.loadingText || "Loading...";

          // Create spinner SVG
          const spinner = `
                    <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                `;

          // Update button content with spinner
          this.innerHTML = spinner + loadingText;

          // For anchor tags, we can't use disabled property
          if (this.tagName === "A") {
            this.style.opacity = "0.5";
            this.style.cursor = "not-allowed";
            this.style.pointerEvents = "none";
            this.setAttribute("aria-disabled", "true");
          } else {
            // Disable the button
            this.disabled = true;
            this.style.opacity = "0.7";
            this.style.cursor = "not-allowed";
          }

          // Disable additional elements if specified
          if (disableElements) {
            // Split the selector string by spaces and handle each selector
            const selectors = disableElements.trim().split(/\s+/);
            const allElements = [];
            
            selectors.forEach(selector => {
              if (selector.trim()) {
                const elements = document.querySelectorAll(selector.trim());
                allElements.push(...Array.from(elements));
              }
            });
            
            // Remove duplicates and disable all found elements
            const uniqueElements = [...new Set(allElements)];
            uniqueElements.forEach((element) => {
              // For anchor tags, we can't use disabled property
              if (element.tagName === "A") {
                element.style.opacity = "0.5";
                element.style.cursor = "not-allowed";
                element.style.pointerEvents = "none";
                element.setAttribute("aria-disabled", "true");
              } else {
                element.disabled = true;
                element.style.opacity = "0.5";
                element.style.cursor = "not-allowed";
                element.style.pointerEvents = "none";
              }
            });
          }
        }
      } catch (error) {
        console.error("Error in loading button functionality:", error);
        alert("Error in loading button functionality: " + error);
      }
    });
  });
});

/**
 * Function to restore button to original state
 * Useful for AJAX requests that need to re-enable the button
 */
function restoreLoadingButton(button) {
  if (button && button.dataset.originalHtml) {
    button.innerHTML = button.dataset.originalHtml;
    button.disabled = false;
    button.style.opacity = "1";
    button.style.cursor = "pointer";
    delete button.dataset.originalHtml;

    // Restore additional elements if specified
    const disableElements = button.dataset.disableElements;
    if (disableElements) {
      const elements = document.querySelectorAll(disableElements);
      elements.forEach((element) => {
        // For anchor tags, we can't use disabled property
        if (element.tagName === "A") {
          element.style.opacity = "1";
          element.style.cursor = "pointer";
          element.style.pointerEvents = "auto";
          element.removeAttribute("aria-disabled");
        } else {
          element.disabled = false;
          element.style.opacity = "1";
          element.style.cursor = "pointer";
          element.style.pointerEvents = "auto";
        }
      });
    }
  }
}

/**
 * Function to restore all loading buttons on the page
 */
function restoreAllLoadingButtons() {
  const loadingButtons = document.querySelectorAll(".loading-btn[disabled]");
  loadingButtons.forEach((button) => {
    restoreLoadingButton(button);
  });
}
