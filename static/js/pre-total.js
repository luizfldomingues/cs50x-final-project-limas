document.addEventListener('DOMContentLoaded', function() {
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const preTotal = document.getElementById('pre-total');

    function calculateTotal() {
        let totalInCents = 0;
        quantityInputs.forEach(input => {
            // Parse as integer since we're dealing with cents
            const priceInCents = parseInt(input.dataset.price);
            const quantity = parseInt(input.value) || 0;
            // Just multiply price by quantity, no need for additional conversion
            totalInCents += priceInCents * quantity;
        });
        
        preTotal.textContent = formatBRL(totalInCents);
    }

    // Add event listeners to all quantity inputs
    quantityInputs.forEach(input => {
        input.addEventListener('input', calculateTotal);
    });
});
