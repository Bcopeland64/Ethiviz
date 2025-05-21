# EthiViz - Cultural Bias Analysis Platform

## Setup Guide

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ethiviz.git
cd ethiviz
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Configuration

1. Create a `.env` file in the root directory with the following variables:
```
API_KEY=your_api_key
DATABASE_URL=your_database_url
```

### Running the Application

```bash
python app.py
```

The application will be available at http://localhost:5000

### Development

To run the application in development mode:
```bash
python app.py --debug
```