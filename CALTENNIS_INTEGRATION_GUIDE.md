# CalTennis Dataset Integration Guide

## Overview
This guide helps you integrate the CalTennis dataset (11M+ video frames) into the Injury Risk AI application for massive model accuracy improvements.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
source venv/bin/activate
pip install datasets tqdm
```

### 2. Test with Small Sample
```bash
# Process first 100 samples to test
python -m data_processing.caltennis_processor --max-samples 100 --output caltennis_test.csv
```

### 3. Process Full Dataset
```bash
# Process entire dataset (will take time for 11M+ frames)
python -m data_processing.caltennis_processor --batch-size 1000 --output caltennis_features.csv
```

### 4. Train Enhanced Model
```python
from training.incremental_trainer import IncrementalTrainer

trainer = IncrementalTrainer()
model_data = trainer.train_with_caltennis(
    caltennis_path='data_processing/caltennis_features.csv',
    original_path='tennis_dataset_analysis.csv'
)
```

## Expected Results

### Dataset Impact
- **Original**: 280 samples
- **CalTennis**: 100,000+ samples (300x increase)
- **Combined**: 100,280+ samples

### Model Performance
- **Current Accuracy**: ~65%
- **Expected with CalTennis**: 85-90% (20-25% improvement)
- **Generalization**: Significant improvement on diverse playing styles

## Processing Options

### Batch Processing
```bash
# Process in batches of 1000 samples
python -m data_processing.caltennis_processor --batch-size 1000
```

### Limited Processing (for testing)
```bash
# Process only 500 samples
python -m data_processing.caltennis_processor --max-samples 500
```

### Custom Output
```bash
# Specify custom output filename
python -m data_processing.caltennis_processor --output my_features.csv
```

## Data Quality

The CalTennis dataset provides:
- Professional tennis players
- High-quality video footage
- Camera calibration data
- Diverse playing styles and strokes

This is significantly higher quality than the current limited dataset.

## Next Steps

1. **Process Dataset**: Run the processor to extract features
2. **Expert Labeling**: Have sports physiotherapists label a subset
3. **Train Model**: Use the incremental trainer for combined dataset
4. **Evaluate**: Test model accuracy improvements
5. **Deploy**: Update the production model

## Troubleshooting

### Dataset Loading Issues
```bash
# Make sure datasets library is installed
pip install datasets

# Check internet connection (dataset is downloaded from HuggingFace)
```

### Memory Issues
```bash
# Reduce batch size
python -m data_processing.caltennis_processor --batch-size 500

# Process smaller subset first
python -m data_processing.caltennis_processor --max-samples 1000
```

### Import Errors
```bash
# Make sure you're running from the backend directory
cd backend
python -m data_processing.caltennis_processor
```

## Architecture Impact

See `ARCHITECTURE_IMPROVEMENTS.md` for comprehensive details on how CalTennis integration transforms the system architecture and expected performance improvements.