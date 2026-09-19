async function submitContact(event) {
  event.preventDefault();
  const confirmation = document.getElementById('confirmation');
  if (confirmation) confirmation.hidden = false;
}
