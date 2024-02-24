
# Configure the development environment

## Install dependencies
    
```bash
pip install uv
uv venv
source venv/bin/activate

uv pip install -r requirements-dev.txt

pre-commit install
``` 

```


# Configure test environment

```bash
# Install dependencies
brew install kwok

kwokctl create cluster
```