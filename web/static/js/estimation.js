document.getElementById('estimate-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  ['area_m2', 'bedrooms', 'bathrooms', 'floor', 'age_years'].forEach((key) => { payload[key] = Number(payload[key]); });
  ['balcony', 'garden', 'garage', 'air_conditioning'].forEach((key) => { payload[key] = form.has(key); });
  const result = document.getElementById('result');
  try {
    const response = await fetch('/api/predict', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Prediction failed');
    result.textContent = `Estimated price: ${data.estimated_price_mad} MAD (${data.lower_bound_mad}–${data.upper_bound_mad} MAD)`;
  } catch (error) {
    result.textContent = error.message;
  }
});
