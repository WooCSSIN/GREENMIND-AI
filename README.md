# 🌱 GreenMind AI - Intelligent Warehouse Management System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-WooCSSIN-black.svg)](https://github.com/WooCSSIN/GREENMIND-AI)

> **AI-powered inventory optimization with real-time forecasting and ESG impact tracking**

GreenMind is an intelligent warehouse management system that combines machine learning forecasting with environmental sustainability metrics. It helps businesses optimize inventory levels, reduce waste, and track their carbon footprint.

---

## 🎯 Key Features

### 📊 **AI-Powered Forecasting**
- **3 ML Models**: SARIMAX, Prophet, XGBoost
- **Champion Selection**: Automatic model selection based on MAE
- **30-Day Demand Forecast**: Real-time predictions with confidence intervals
- **Demand-Based Pipeline**: Forecasts actual demand, not just stock levels

### 🏭 **Inventory Optimization**
- **Safety Stock Calculation**: Dynamic safety stock based on demand variance
- **Reorder Point (ROP)**: Automated reorder recommendations
- **Stock Level Monitoring**: Real-time alerts for critical inventory
- **Warehouse Heatmap**: Visual representation of stock distribution

### 🌍 **ESG & Green Metrics**
- **CO₂ Impact Tracking**: Energy-based model for warehouse storage emissions
- **Annual Savings**: Quantified environmental impact of AI optimization
- **Trees Equivalent**: Visualize carbon savings as tree equivalents
- **Baseline vs Optimized**: Compare emissions before/after AI

### 🔐 **Enterprise Security**
- **JWT Authentication**: Secure API endpoints
- **RBAC (Role-Based Access Control)**: Admin, Manager, Viewer roles
- **Audit Logging**: Complete action trail for compliance
- **Error Sanitization**: Secure error handling without info leakage

### 📈 **Real-Time Dashboard**
- **Dark Mode UI**: Modern, eye-friendly interface
- **Interactive Charts**: Plotly-powered visualizations
- **Live Updates**: Real-time data refresh
- **Multi-SKU Support**: Manage thousands of products

---

## 🏗️ Architecture

### 3-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Presentation Layer (Django + Plotly)            │
│  Dashboard | API | Templates | Real-time Charts         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│      Intelligence Layer (Python ML Engine)              │
│  SARIMAX | Prophet | XGBoost | Feature Engineering      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         Data Layer (SQL Server)                         │
│  Dim_Products | Fact_Inventory | AI_Predictions | Logs  │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Django Templates, Tailwind CSS, Plotly.js |
| **Backend** | Django 5.0, Django REST Framework, SQLAlchemy |
| **ML/AI** | XGBoost, Prophet, SARIMAX, Scikit-learn, Pandas |
| **Database** | Microsoft SQL Server, SQLite (dev) |
| **Auth** | JWT (SimpleJWT), Django Groups |
| **Deployment** | Gunicorn, Docker-ready |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- SQL Server (or SQLite for development)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/WooCSSIN/GREENMIND-AI.git
cd GREENMIND-AI
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start development server**
```bash
python manage.py runserver
```

Access the dashboard at: **http://localhost:8000**

---

## 📖 Usage

### Dashboard Views

#### 🏠 **Home - Forecasting Dashboard**
- Select SKU from dropdown
- View historical stock vs AI forecast
- See model comparison (MAE, RMSE)
- Check inventory status (Safe/Warning/Critical)
- View CO₂ savings potential

#### 📦 **Catalog - Product Management**
- Add/Edit/Delete products
- Set emission factors
- Configure safety stock levels
- Manage warehouse locations

#### 🎮 **Simulator - Transaction Testing**
- Simulate inbound/outbound transactions
- Test inventory impact
- Verify forecast updates
- Validate business rules

#### 📊 **Monitoring - System Health**
- View recent transactions
- Check audit logs
- Monitor CO₂ warnings
- Warehouse heatmap

#### 🌱 **ESG - Environmental Impact**
- Annual CO₂ savings
- Baseline vs optimized emissions
- Quarterly trend analysis
- Trees equivalent visualization

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_SERVER=your-sql-server
DB_NAME=GreenMind
DB_USER=sa
DB_PASSWORD=your-password

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# AI Engine
STORAGE_KWH_PER_UNIT=0.002
GRID_EMISSION_VN=0.4937

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 📊 Database Schema

### Key Tables

**Dim_Products** - Product Master Data
- ItemID, ProductName, Category, Unit
- EmissionFactor, SafetyStockLevel
- ShelfRow, ShelfColumn, IsActive

**Fact_Inventory_History** - Transaction Log
- HistoryID, ItemID, UserID, Timestamp
- Price, StockQuantity, SoldQuantity

**Fact_AI_Predictions** - Forecast Results
- PredictionID, ItemID, PredictionDate
- ForecastedQuantity, ModelUsed

**Green_Impact_Logs** - ESG Metrics
- LogID, ItemID, AnualCO2Saving
- TreesEquivalent, ChampionModel

---

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Run Security Tests
```bash
python manage.py test tests.test_security
```

### Run Inventory Tests
```bash
python manage.py test tests.test_inventory_update
```

---

## 🔐 Security Features

✅ **JWT Authentication** - Stateless API auth  
✅ **RBAC** - Role-based access control  
✅ **CSRF Protection** - Django CSRF middleware  
✅ **SQL Injection Prevention** - Parameterized queries  
✅ **XSS Protection** - Template auto-escaping  
✅ **Audit Logging** - Complete action trail  
✅ **Error Sanitization** - No sensitive info in errors  
✅ **Rate Limiting** - DDoS protection  
✅ **HTTPS Ready** - Production security headers  

---

## 📈 Performance

### Optimization Techniques
- **Global Engine Cache**: Reusable ML model instances
- **Database Indexing**: Optimized queries
- **Lazy Loading**: On-demand data fetching
- **Batch Processing**: Efficient bulk operations
- **Connection Pooling**: Reused DB connections

### Benchmarks
- Dashboard load: ~2-3 seconds (with 3 ML models)
- Forecast generation: ~1-2 seconds per SKU
- API response: <500ms (cached)

---

## 🐛 Known Issues & Roadmap

### Current Issues
- [ ] Chart cache not updating after transactions (Fix in progress)
- [ ] Dual authentication with Dim_Users (Refactoring)
- [ ] Performance bottleneck with 3 concurrent ML models

### Roadmap
- [ ] Redis caching for distributed systems
- [ ] Real-time WebSocket updates
- [ ] Mobile app (React Native)
- [ ] Advanced analytics (Tableau integration)
- [ ] Multi-warehouse support
- [ ] Supplier integration API

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**GreenMind AI Development Team**
- Lead: WooCSSIN
- Contributors: Open to community

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/WooCSSIN/GREENMIND-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/WooCSSIN/GREENMIND-AI/discussions)
- **Email**: dev@greenmind.ai

---

## 🙏 Acknowledgments

- **Prophet** - Facebook's time series forecasting library
- **XGBoost** - Gradient boosting framework
- **Django** - Web framework
- **Plotly** - Interactive visualization

---

**Made with ❤️ for sustainable logistics**

Last updated: May 26, 2026
