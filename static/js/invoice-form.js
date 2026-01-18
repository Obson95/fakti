// Enhanced Invoice Form JavaScript
class InvoiceFormManager {
    constructor() {
        this.lineItemCount = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeExistingItems();
        this.updateTotals();
    }

    bindEvents() {
        // Add line item button
        const addButton = document.getElementById('add-line-item');
        if (addButton) {
            addButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.addLineItem();
            });
        }

        // Form submission
        const form = document.getElementById('invoice-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                this.validateForm(e);
            });
        }

        // Real-time calculation on input changes
        document.addEventListener('input', (e) => {
            if (e.target.matches('.quantity, .rate, .tax-rate, .discount')) {
                this.updateTotals();
            }
        });

        // Delete line item events (delegated)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.delete-line-item')) {
                e.preventDefault();
                this.deleteLineItem(e.target);
            }
        });
    }

    initializeExistingItems() {
        const existingItems = document.querySelectorAll('.line-item-row');
        this.lineItemCount = existingItems.length;

        // Add delete buttons to existing items
        existingItems.forEach((item, index) => {
            this.addDeleteButton(item, index);
        });
    }

    addLineItem() {
        const container = document.getElementById('line-items-container');
        if (!container) return;

        const lineItem = this.createLineItemHTML(this.lineItemCount);
        container.insertAdjacentHTML('beforeend', lineItem);

        // Focus on the description field of the new item
        const newItem = container.lastElementChild;
        const descriptionField = newItem.querySelector('.description');
        if (descriptionField) {
            descriptionField.focus();
        }

        this.lineItemCount++;
        this.updateTotals();
    }

    createLineItemHTML(index) {
        return `
            <div class="line-item-row border-b pb-4 mb-4" data-index="${index}">
                <div class="grid grid-cols-12 gap-4 items-start">
                    <div class="col-span-12 md:col-span-4">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Description
                        </label>
                        <textarea 
                            name="items-${index}-description" 
                            class="description w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows="2"
                            placeholder="Item description..."
                            required
                        ></textarea>
                    </div>
                    
                    <div class="col-span-6 md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Quantity
                        </label>
                        <input 
                            type="number" 
                            name="items-${index}-quantity" 
                            class="quantity w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="0"
                            step="0.01"
                            value="1"
                            required
                        >
                    </div>
                    
                    <div class="col-span-6 md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Rate ($)
                        </label>
                        <input 
                            type="number" 
                            name="items-${index}-rate" 
                            class="rate w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="0"
                            step="0.01"
                            placeholder="0.00"
                            required
                        >
                    </div>
                    
                    <div class="col-span-6 md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Tax (%)
                        </label>
                        <input 
                            type="number" 
                            name="items-${index}-tax_rate" 
                            class="tax-rate w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="0"
                            max="100"
                            step="0.01"
                            value="0"
                        >
                    </div>
                    
                    <div class="col-span-6 md:col-span-1">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Total
                        </label>
                        <div class="line-total font-semibold text-gray-900 py-2">
                            $0.00
                        </div>
                    </div>
                    
                    <div class="col-span-12 md:col-span-1 flex items-end">
                        <button 
                            type="button" 
                            class="delete-line-item w-full md:w-auto px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                            title="Delete item"
                        >
                            <svg class="w-4 h-4 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    addDeleteButton(item, index) {
        const deleteButton = item.querySelector('.delete-line-item');
        if (!deleteButton) {
            const buttonContainer = item.querySelector('.col-span-12.md\\:col-span-1');
            if (buttonContainer) {
                buttonContainer.innerHTML = `
                    <button 
                        type="button" 
                        class="delete-line-item w-full md:w-auto px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                        title="Delete item"
                    >
                        <svg class="w-4 h-4 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                `;
            }
        }
    }

    deleteLineItem(button) {
        const lineItem = button.closest('.line-item-row');
        if (lineItem) {
            // Confirm deletion
            if (confirm('Are you sure you want to delete this item?')) {
                lineItem.remove();
                this.updateTotals();
                this.reindexItems();
            }
        }
    }

    reindexItems() {
        const items = document.querySelectorAll('.line-item-row');
        items.forEach((item, index) => {
            item.setAttribute('data-index', index);

            // Update form field names
            const inputs = item.querySelectorAll('input, textarea');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    const newName = name.replace(/items-\d+-/, `items-${index}-`);
                    input.setAttribute('name', newName);
                }
            });
        });

        this.lineItemCount = items.length;
    }

    updateTotals() {
        let subtotal = 0;
        let totalTax = 0;
        let totalDiscount = 0;

        // Calculate line item totals
        document.querySelectorAll('.line-item-row').forEach(row => {
            const quantity = parseFloat(row.querySelector('.quantity')?.value || 0);
            const rate = parseFloat(row.querySelector('.rate')?.value || 0);
            const taxRate = parseFloat(row.querySelector('.tax-rate')?.value || 0);

            const lineSubtotal = quantity * rate;
            const lineTax = lineSubtotal * (taxRate / 100);
            const lineTotal = lineSubtotal + lineTax;

            // Update line total display
            const lineTotalElement = row.querySelector('.line-total');
            if (lineTotalElement) {
                lineTotalElement.textContent = `$${lineTotal.toFixed(2)}`;
            }

            subtotal += lineSubtotal;
            totalTax += lineTax;
        });

        // Get global discount
        const discountElement = document.querySelector('.discount');
        if (discountElement) {
            totalDiscount = parseFloat(discountElement.value || 0);
        }

        const total = subtotal + totalTax - totalDiscount;

        // Update summary displays
        this.updateSummaryElement('.subtotal-amount', subtotal);
        this.updateSummaryElement('.tax-amount', totalTax);
        this.updateSummaryElement('.discount-amount', totalDiscount);
        this.updateSummaryElement('.total-amount', total);
    }

    updateSummaryElement(selector, amount) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = `$${amount.toFixed(2)}`;
        }
    }

    validateForm(e) {
        const lineItems = document.querySelectorAll('.line-item-row');

        if (lineItems.length === 0) {
            e.preventDefault();
            alert('Please add at least one line item to the invoice.');
            return false;
        }

        // Validate each line item
        let isValid = true;
        lineItems.forEach((item, index) => {
            const description = item.querySelector('.description')?.value.trim();
            const quantity = parseFloat(item.querySelector('.quantity')?.value || 0);
            const rate = parseFloat(item.querySelector('.rate')?.value || 0);

            if (!description) {
                isValid = false;
                alert(`Please enter a description for item ${index + 1}.`);
                return;
            }

            if (quantity <= 0) {
                isValid = false;
                alert(`Please enter a valid quantity for item ${index + 1}.`);
                return;
            }

            if (rate < 0) {
                isValid = false;
                alert(`Please enter a valid rate for item ${index + 1}.`);
                return;
            }
        });

        if (!isValid) {
            e.preventDefault();
            return false;
        }

        return true;
    }

    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    // Auto-save functionality (optional)
    enableAutoSave() {
        let saveTimeout;
        document.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                this.saveAsDraft();
            }, 2000); // Save after 2 seconds of inactivity
        });
    }

    saveAsDraft() {
        const formData = new FormData(document.getElementById('invoice-form'));
        const data = Object.fromEntries(formData.entries());

        // Save to localStorage as backup
        localStorage.setItem('invoice_draft', JSON.stringify(data));

        // Show save indicator
        this.showSaveIndicator();
    }

    showSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        indicator.textContent = 'Draft saved';
        document.body.appendChild(indicator);

        setTimeout(() => {
            indicator.remove();
        }, 2000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.invoiceForm = new InvoiceFormManager();
});