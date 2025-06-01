// Built with help of AI
function formatBRL(cents) {
  // Ensure we're working with integers
  cents = Math.round(cents);

  // Convert negative numbers properly
  const isNegative = cents < 0;
  cents = Math.abs(cents);

  const reaisStr = Math.floor(cents / 100)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const centsStr = (cents % 100).toString().padStart(2, '0');

  return `${isNegative ? '-' : ''}R$${reaisStr},${centsStr}`;
}
