# API Automation Framework

API testing framework built with Python, pytest, requests and Allure reporting for testing shipment management APIs.


## 📁 Project Structure

```
backend_pytest_task/
├── config/
│   ├── config.ini                 # Configuration settings
│   ├── configmanager.py          # Singleton config manager
│   └── api_config_manager.py     # API configuration manager
├── utils/
│   ├── api_client.py             # HTTP client with retry logic and standardized responses
│   ├── auth_client.py            # Authentication client
│   ├── shipment_client.py        # Shipment API client
│   ├── base_utils.py             # Base utility classes with common patterns
│   ├── common_utils.py           # Common utility functions
│   ├── file_utils.py             # File operations and CSV/JSON handling
│   ├── generic_contract_validator.py # JSON schema validation
│   ├── logger_utils.py           # Centralized logging
│   ├── request_utils.py          # Request building utilities
│   └── response_utils.py         # Response parsing utilities
├── schemas/
│   ├── create_shipment_schema.json # JSON schema for contract validation
│   └── schema_loader.py          # Schema loading utilities
├── test_data/
│   ├── generic_data_manager.py   # Test data management and generation
│   ├── csv/                      # CSV test data files
│   └── json/                     # JSON test data files
├── tests/
│   ├── helpers/
│   │   ├── common_helper.py      # Common test helper functions
│   │   └── create_shipment_helper.py # Shipment-specific helpers
│   └── test_create_shipment.py # Comprehensive parameterized tests
├── logs/                         # Log files
├── allure-results/              # Allure results
├── conftest.py                  # Pytest fixtures and configuration
├── pytest.ini                  # Pytest configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd backend_pytest_task
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Allure** (for reporting):
   ```bash
   # macOS
   brew install allure
   
   # Linux
   sudo apt-get install allure
   
   # Windows
   # Download from https://github.com/allure-framework/allure2/releases
   ```

5. **Configure settings**:
   Edit `config/config.ini` with your API endpoints and credentials:
   ```ini
   [API]
   base_url = https://api.uat.scmz5.de
   
   [CREDENTIALS]
   username = your_username@domain.com
   password = your_password
   ```

## 🧪 Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Smoke tests
pytest -m smoke

# Regression tests
pytest -m regression

# Shipment tests
pytest -m shipment
```

## 📊 Reporting

### Allure Reports
Generate beautiful Allure reports for detailed test analysis:

#### Quick Start
```bash
# Run tests with Allure results collection
pytest tests/ --alluredir=allure-results

# Generate Allure report
allure generate allure-results --clean -o allure-report

# Serve report locally
allure serve allure-results
```

## Report Screenshots

![alt text](<Report_screenshot_suite.png>)


![alt text](<Report_screenshot_test.png>)

## 📝 Test Data Management

### JSON Test Data
Place test data files in `test_data/json/`:g
- `create_shipment_base_data.json`: Base shipment data
- Custom test data files as needed

### CSV Test Data
Place CSV files in `test_data/csv/` for data-driven tests.

### Dynamic Test Data
Use the `GenericDataManager` for generating random test data:
```python
from test_data.generic_data_manager import GenericDataManager

data_manager = GenericDataManager()
random_data = data_manager.generate_random_shipment_data()
```

## 🏷️ Test Markers

The framework uses pytest markers for test organization:

- `@pytest.mark.smoke`: Critical functionality tests
- `@pytest.mark.regression`: Comprehensive regression tests
- `@pytest.mark.shipment`: Shipment API tests


## 🚨 Error Handling

The framework includes comprehensive error handling:

### Logging and Reporting
- Detailed error logging with stack traces
- Allure attachments for failed tests
- Centralized logging through base utility classes

## 🤝 Contributing

1. Clone the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 🔮 Future Enhancements

- [ ] Database integration for test data
- [ ] Docker containerization
- [ ] Kubernetes deployment support
