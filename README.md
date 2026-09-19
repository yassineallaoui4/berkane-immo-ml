# Berkane Immo ML

## Structure

- `app.py`: Flask application, API endpoints and page routing
- `web/templates/`: server-rendered HTML pages
- `web/static/`: CSS and JavaScript assets
- `ml/`: validation, training and inference
- `data/`: documented datasets
- `models/`: generated model metadata and artifacts
- `scripts/`: reproducible data-generation commands
- `tests/`: automated tests

## Run

```bash
pip install -r requirements.txt
python -m scripts.generate_demo_data
python -m ml.modeling --data data/demo_properties.csv --model models/berkane_price_model.joblib --metrics models/metrics.json --data-kind synthetic-demo
python app.py
```

Open `http://127.0.0.1:5000/` or `/estimation.html`.

The included dataset is synthetic and the output is not a professional valuation.
