const form = document.getElementById('house-estimation-form');
const resultBox = document.getElementById('estimation-result');
const loader = document.getElementById('estimation-loader');
const modelStatus = document.getElementById('model-status');

const money = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'MAD', maximumFractionDigits: 0,
});

function formPayload(formData) {
  return {
    district: formData.get('district'), property_type: formData.get('property_type'),
    condition: formData.get('condition'), area_m2: Number(formData.get('area_m2')),
    bedrooms: Number(formData.get('bedrooms')), bathrooms: Number(formData.get('bathrooms')),
    floor: Number(formData.get('floor')), age_years: Number(formData.get('age_years')),
    balcony: formData.has('balcony'), garden: formData.has('garden'),
    garage: formData.has('garage'), air_conditioning: formData.has('air_conditioning'),
  };
}

function showResult(html, kind = 'success') {
  resultBox.className = `result-box ${kind}`;
  resultBox.innerHTML = html;
  resultBox.style.display = 'block';
}

async function loadModelStatus() {
  try {
    const response = await fetch('/api/model-info');
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || 'Model unavailable');
    const label = payload.model.data_kind === 'synthetic-demo' ? 'Synthetic demonstration model' : 'Trained model';
    modelStatus.textContent = `${label} · ${payload.model.rows} rows · Random Forest`;
    modelStatus.classList.add(payload.model.data_kind === 'synthetic-demo' ? 'warning' : 'ready');
  } catch (error) {
    modelStatus.textContent = 'Model not ready. Follow the training steps in README.md.';
    modelStatus.classList.add('warning');
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  loader.style.display = 'block';
  resultBox.style.display = 'none';
  try {
    const response = await fetch('/api/predict', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(formPayload(new FormData(form))),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Prediction failed');
    const warning = payload.model.data_kind === 'synthetic-demo'
      ? '<p><strong>Demo only:</strong> this model was trained on synthetic data and is not a market valuation.</p>'
      : '<p>The interval uses validation MAE; it is not a guaranteed appraisal range.</p>';
    showResult(`<h2>${money.format(payload.estimated_price_mad)}</h2><p>Indicative range: ${money.format(payload.lower_bound_mad)} – ${money.format(payload.upper_bound_mad)}</p>${warning}`);
  } catch (error) {
    showResult(`<strong>Unable to estimate:</strong> ${error.message}`, 'error');
  } finally {
    loader.style.display = 'none';
  }
});

loadModelStatus();

