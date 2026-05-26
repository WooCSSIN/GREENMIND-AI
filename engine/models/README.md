# GREENMIND Project

## Cấu trúc Dự án

```
GREENMIND/
├── data/                           # Dữ liệu
│   ├── raw/                       # Dữ liệu gốc (không chỉnh sửa)
│   ├── processed/                 # Dữ liệu đã làm sạch
│   └── external/                  # Dữ liệu bên ngoài
│
├── notebooks/                      # Jupyter Notebooks
│   ├── exploratory/               # EDA (Exploratory Data Analysis)
│   └── modeling/                  # Model development
│
├── src/                           # Source code
│   ├── data/                      # Data processing modules
│   ├── models/                    # ML/AI models
│   ├── features/                  # Feature engineering
│   ├── visualization/             # Plotting functions
│   └── utils/                     # Utilities
│
├── models/                        # Trained models
│   ├── saved/                     # .pkl, .joblib files
│   └── checkpoints/               # Training checkpoints
│
├── outputs/                       # Kết quả
│   ├── figures/                   # Charts, plots
│   ├── reports/                   # Reports, summaries
│   └── predictions/               # Forecast results
│
├── tests/                         # Unit tests
├── docs/                          # Documentation
├── configs/                       # Configuration files
└── README.md                      # This file
```

## Quick Start

### 1. Setup môi trường

```bash
# Cài đặt dependencies (khi có requirements.txt)
pip install -r requirements.txt
```

### 2. Xử lý dữ liệu

```bash
# Chạy notebook preprocessing
jupyter notebook notebooks/01_data_preprocessing.ipynb
```

### 3. Training mô hình

```bash
# Sẽ update sau khi có script forecasting
python src/models/train_forecasting.py
```

## Workflow

1. **Data Collection** → `data/raw/`
2. **Data Cleaning** → `notebooks/exploratory/` → `data/processed/`
3. **Model Training** → `src/models/` → `models/saved/`
4. **Evaluation** → `outputs/reports/`
5. **Prediction** → `outputs/predictions/`

## Ghi chú quan trọng

- **KHÔNG** commit file trong `data/raw/` và `models/saved/` lên Git (đã có trong `.gitignore`)
- Mọi thay đổi trong code phải có unit test tương ứng trong `tests/`
- Notebook chỉ dùng cho exploration, code production phải ở trong `src/`
