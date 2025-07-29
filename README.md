# Product Service gRPC CLI

A Command-Line Interface (CLI) for managing product data (add, delete, edit, list) via a gRPC API.

---
## Features

* **Add** a new product
* **Edit** an existing product's information
* **Delete** a product
* **List** all products
* **Count** the total number of products

---
## Installation

1.  Clone this repository to your local machine.
2.  Install the project in editable mode (recommended for development):

    ```bash
    pip install -e .
    ```

---
## Usage

After installation, you can use the `product-cli` command from anywhere in your terminal.

### **1. Add a new product**

```bash
product-cli add --name "Product Name" --price <price> --description "Product description"

product-cli add --name "Wireless Mouse" --price 899.50 --description "A silent wireless mouse."

product-cli list

product-cli edit --id "prod-xxxxxxxx" [--name "New Name"] [--price <new_price>] [--description "New Description"]

product-cli edit --id "prod-1234abcd" --price 950.00

product-cli delete --id "prod-xxxxxxxx"

product-cli count