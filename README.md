# gRPC AI-Powered Order API

This project is a complete backend system for managing products and orders, built with Python and gRPC. It features a command-line interface (CLI) for administration and an intelligent AI agent for processing natural language commands.



## ✨ Features

* **High-Performance API:** Built with gRPC for efficient and fast client-server communication.
* **Two Core Services:** A `ProductService` for inventory management and an `OrderService` for customer orders.
* **Full CRUD Functionality:** Supports Create, Read, Update, and Delete operations.
* **Persistent Storage:** Uses a lightweight SQLite database to store all data.
* **Command-Line Interface:** A powerful CLI (`product_cli.py`) for direct database management.
* **AI Agent:** An interactive agent (`run_agent.py`) powered by the Google Gemini API that uses the gRPC services as tools.

## 🛠️ Technologies Used

* **Backend:** Python
* **API Framework:** gRPC, Protobuf
* **Database:** SQLite
* **AI:** Google Gemini API (`google-generativai`)
* **CLI:** `argparse`

## 🚀 Getting Started

Follow these steps to get the project running on your local machine.

### 1. Prerequisites

* Python 3.8+
* `pip` and `venv`

### 2. Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-folder>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install grpcio grpcio-tools google-generativeai python-dotenv
    ```

4.  **Generate gRPC Code:**
    Run the following command from the project's root directory to generate the necessary Python code from the `.proto` file.
    ```bash
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. order_api.proto
    ```

5.  **Set Up Environment Variables:**
    Create a file named `.env` in the same directory as `run_agent.py` and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

### 3. Usage

You will need two separate terminals to run the server and a client.

1.  **Start the Server:**
    In your first terminal, start the gRPC server. It will initialize the database and wait for connections.
    ```bash
    python server.py
    ```

2.  **Use the CLI Client:**
    In a second terminal, you can manage products using the CLI.
    ```bash
    # List all products
    python product_cli.py list

    # Add a new product
    python product_cli.py add --name "New Item" --price 19.99 --description "A test item"
    ```

3.  **Run the AI Agent:**
    Alternatively, you can run the interactive AI agent in the second terminal.
    ```bash
    python run_agent.py
    ```
    You can then type commands like `list all products` or `create an order for user-123 with one prod-abc`.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.