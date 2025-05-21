#!/bin/bash
# EthiViz - Setup Script
# Creates a virtual environment and installs all dependencies

# Set up colors for pretty output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}
███████╗████████╗██╗  ██╗██╗██╗   ██╗██╗███████╗
██╔════╝╚══██╔══╝██║  ██║██║██║   ██║██║╚══███╔╝
█████╗     ██║   ███████║██║██║   ██║██║  ███╔╝ 
██╔══╝     ██║   ██╔══██║██║╚██╗ ██╔╝██║ ███╔╝  
███████╗   ██║   ██║  ██║██║ ╚████╔╝ ██║███████╗
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝╚══════╝
                                                 
Cultural Bias Analysis Platform - Setup Script
${NC}"

echo -e "${YELLOW}This script will set up a virtual environment for EthiViz.${NC}"
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "${BLUE}Detected Python version: $PYTHON_VERSION${NC}"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo -e "${RED}Error: Python 3.8+ is required.${NC}"
    echo "Please upgrade your Python installation and try again."
    exit 1
fi

# Check if virtualenv is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is required but not installed.${NC}"
    echo "Please install pip for Python 3 and try again."
    exit 1
fi

# Check for virtual environment tool
echo -e "${BLUE}Checking for virtual environment tools...${NC}"
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}Python venv module not found. Trying to install...${NC}"
    pip3 install virtualenv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to install virtualenv.${NC}"
        echo "Please install virtualenv manually with 'pip3 install virtualenv'."
        exit 1
    fi
    VENV_COMMAND="virtualenv"
else
    VENV_COMMAND="python3 -m venv"
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment directory 'venv' already exists.${NC}"
    read -p "Do you want to remove it and create a new one? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf venv
    else
        echo -e "${YELLOW}Using existing virtual environment.${NC}"
    fi
fi

if [ ! -d "venv" ]; then
    if [ "$VENV_COMMAND" = "virtualenv" ]; then
        virtualenv -p python3 venv
    else
        python3 -m venv venv
    fi

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install requirements
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    echo "Please check the error messages above."
    exit 1
fi

# Install SpaCy model
echo -e "${BLUE}Installing SpaCy language model...${NC}"
python -m spacy download en_core_web_md

if [ $? -ne 0 ]; then
    echo -e "${RED}Warning: Failed to install SpaCy language model.${NC}"
    echo "You can try installing it manually with 'python -m spacy download en_core_web_md'"
fi

# Optional dependencies
echo -e "${BLUE}Checking for optional dependencies...${NC}"

# Check if TensorFlow is installed
python -c "import tensorflow" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}TensorFlow not found. Advanced image analysis features will be limited.${NC}"
    read -p "Do you want to install TensorFlow? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installing TensorFlow...${NC}"
        pip install tensorflow
    else
        echo -e "${YELLOW}Skipping TensorFlow installation.${NC}"
    fi
else
    echo -e "${GREEN}TensorFlow is installed.${NC}"
fi

# Check if OpenCV is installed
python -c "import cv2" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}OpenCV not found. Medium-level image analysis features will be limited.${NC}"
    read -p "Do you want to install OpenCV? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installing OpenCV...${NC}"
        pip install opencv-python
    else
        echo -e "${YELLOW}Skipping OpenCV installation.${NC}"
    fi
else
    echo -e "${GREEN}OpenCV is installed.${NC}"
fi

# Create activation script
echo -e "${BLUE}Creating convenience activation script...${NC}"
cat > activate-ethiviz.sh << 'EOF'
#!/bin/bash
# EthiViz - Activation Script
source venv/bin/activate
echo "EthiViz virtual environment activated!"
echo "Run 'streamlit run app.py' to start the EthiViz application"
EOF

chmod +x activate-ethiviz.sh

# Success message
echo
echo -e "${GREEN}EthiViz setup completed successfully!${NC}"
echo
echo -e "To activate the virtual environment in the future, run:"
echo -e "  ${BLUE}source activate-ethiviz.sh${NC}"
echo
echo -e "To start the EthiViz application, run:"
echo -e "  ${BLUE}streamlit run app.py${NC}"
echo
echo -e "Happy analyzing!"