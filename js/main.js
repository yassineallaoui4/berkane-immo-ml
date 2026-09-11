// Shared interactions for the static interface.

function showConfirmation(event) {
  event.preventDefault();
  const confirmation = document.getElementById('confirmation');
  if (confirmation) {
    confirmation.style.display = 'block';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  // The contact form is a local interface demonstration; it sends no data.
  const form = document.querySelector('.contact-container form');
  if (form) {
    form.addEventListener('submit', showConfirmation);
  }

});
