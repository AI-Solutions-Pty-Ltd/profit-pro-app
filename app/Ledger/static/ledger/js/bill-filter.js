/**
 * Bill filtering functionality for transaction forms
 * Provides structure and search filtering for bill selectors
 */

class BillFilter {
    constructor(structureFilterId, billSearchId, billSelectId) {
        this.structureFilter = document.getElementById(structureFilterId);
        this.billSearch = document.getElementById(billSearchId);
        this.billSelect = document.getElementById(billSelectId);
        
        if (!this.structureFilter || !this.billSearch || !this.billSelect) {
            console.warn('BillFilter: Required elements not found');
            return;
        }
        
        this.init();
    }
    
    init() {
        // Store initial options
        this.allOptions = Array.from(this.billSelect.options).map((option) => ({
            value: option.value,
            text: option.text,
            structureId: option.dataset.structureId || "",
            searchText: option.dataset.searchText || "",
        }));
        
        // Set up event listeners
        this.structureFilter.addEventListener("change", () => this.refreshBillOptions());
        this.billSearch.addEventListener("input", () => this.refreshBillOptions());
        
        // Initial filter
        this.refreshBillOptions();
    }
    
    refreshBillOptions() {
        const selectedStructure = this.structureFilter.value;
        const searchTerm = this.billSearch.value.trim().toLowerCase();
        const selectedValueBefore = this.billSelect.value;
        const blankOption = this.allOptions.find((option) => option.value === "");

        // Clear current options
        this.billSelect.innerHTML = "";

        // Add blank option back
        if (blankOption) {
            const optionEl = document.createElement("option");
            optionEl.value = blankOption.value;
            optionEl.text = blankOption.text;
            this.billSelect.appendChild(optionEl);
        }

        // Filter and add valid options
        const filteredOptions = this.allOptions
            .filter((option) => option.value !== "")
            .filter((option) => {
                if (selectedStructure && option.structureId !== selectedStructure) {
                    return false;
                }
                if (searchTerm && !option.searchText.includes(searchTerm)) {
                    return false;
                }
                return true;
            });

        filteredOptions.forEach((option) => {
            const optionEl = document.createElement("option");
            optionEl.value = option.value;
            optionEl.text = option.text;
            optionEl.dataset.structureId = option.structureId;
            optionEl.dataset.searchText = option.searchText;
            if (option.value === selectedValueBefore) {
                optionEl.selected = true;
            }
            this.billSelect.appendChild(optionEl);
        });

        // Restore selection if possible
        const canKeepSelection = Array.from(this.billSelect.options).some(
            (option) => option.value === selectedValueBefore
        );
        this.billSelect.value = canKeepSelection ? selectedValueBefore : "";
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BillFilter;
}
