import grpc
import argparse
import sys
import json
from google.protobuf import empty_pb2

# Assume the client library is installed or in the python path
import order_api_pb2
import order_api_pb2_grpc

class ProductClient:
    """A resilient client for the ProductService gRPC API with error handling."""
    def __init__(self, target='localhost:50051'):
        self.stub = None
        try:
            self.channel = grpc.insecure_channel(target)
            grpc.channel_ready_future(self.channel).result(timeout=1)
            self.stub = order_api_pb2_grpc.ProductServiceStub(self.channel)
            print(f"🔌 Connected to gRPC server at {target}")
        except grpc.FutureTimeoutError:
            print(f"❌ Error: Could not connect to the server at {target}.", file=sys.stderr)

    def _execute_rpc(self, rpc_call):
        """A helper to execute RPCs with built-in error handling."""
        if not self.stub:
            return None
        try:
            return rpc_call()
        except grpc.RpcError as e:
            print(f"❌ RPC Error: {e.code()} - {e.details()}", file=sys.stderr)
            return None

    def add_product(self, args):
        print("--- Calling CreateProduct ---")
        def rpc():
            request = order_api_pb2.CreateProductRequest(
                name=args.name, description=args.description, price=args.price
            )
            return self.stub.CreateProduct(request)
        
        response = self._execute_rpc(rpc)
        if response:
            print("✅ Product created successfully:")
            print(response)

    def list_products(self, args):
        print("--- Calling ListProducts ---")
        def rpc():
            # CORRECTED: Use Empty for parameter-less requests
            return list(self.stub.ListProducts(empty_pb2.Empty()))

        response = self._execute_rpc(rpc)
        if response is not None:
            print("📦 All products in database:")
            if not response:
                print("  (No products found)")
            for product in response:
                print(f"  - ID: {product.product_id}, Name: {product.name}, Price: {product.price}")

    def update_product(self, args):
        print(f"--- Calling UpdateProduct for ID: {args.id} ---")
        def rpc():
            # NOTE: Your server-side logic for update is smart, it uses old values
            # if new ones aren't provided. This client sends all values.
            request = order_api_pb2.UpdateProductRequest(
                product_id=args.id,
                name=args.name,
                description=args.description,
                price=args.price
            )
            return self.stub.UpdateProduct(request)
        
        response = self._execute_rpc(rpc)
        if response:
            print("✅ Product updated successfully:")
            print(response)

    def delete_product(self, args):
        print(f"--- Calling DeleteProduct for ID: {args.id} ---")
        def rpc():
            request = order_api_pb2.DeleteProductRequest(product_id=args.id)
            return self.stub.DeleteProduct(request)

        response = self._execute_rpc(rpc)
        if response:
            if response.success:
                print(f"✅ Success: Product {response.success} was deleted")
            else:
                print(f"❌ Fail: Could not delete product {args.id}. It may not exist.")

    def count_products(self, args):
        print("--- Calling CountProducts ---")
        def rpc():
            # CORRECTED: Use Empty for parameter-less requests
            return self.stub.CountProducts(empty_pb2.Empty())

        response = self._execute_rpc(rpc)
        if response:
            print(f"📊 Total products in DB: {response.count}")

    def export_products(self, args):
        print("--- Calling ExportProducts ---")
        def rpc():
            # CORRECTED: Use Empty for parameter-less requests
            return self.stub.ExportProducts(empty_pb2.Empty())

        response = self._execute_rpc(rpc)
        if response:
            with open("products_export.json", "w", encoding="utf-8") as f:
                f.write(response.json_data)
            print("✅ All products exported to products_export.json")
    
    def import_from_json(self, args):
        print(f"--- Importing products from {args.file} ---")
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                products_to_import = json.load(f)
            
            count = 0
            for product in products_to_import:
                # This lambda creates a unique request for each product in the loop
                def rpc(p=product):
                    request = order_api_pb2.CreateProductRequest(
                        name=p.get('name'),
                        description=p.get('description', ''),
                        price=p.get('price')
                    )
                    return self.stub.CreateProduct(request)

                response = self._execute_rpc(rpc)
                if response:
                    print(f"  -> Imported '{response.name}'")
                    count += 1
            
            # CORRECTED: Moved the summary message outside the loop
            print(f"\n✅ Successfully imported {count} products.")

        except FileNotFoundError:
            print(f"❌ Error: File not found at {args.file}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"❌ Error: Could not decode JSON from {args.file}", file=sys.stderr)

def setup_parsers():
    parser = argparse.ArgumentParser(description="A CLI tool to manage Products via gRPC.")
    subparsers = parser.add_subparsers(dest='command', required=True, help="Available commands")

    # Add command
    parser_add = subparsers.add_parser('add', help="Add a new product")
    parser_add.add_argument("--name", type=str, required=True)
    parser_add.add_argument("--price", type=float, required=True)
    parser_add.add_argument("--description", type=str, default="")

    # List command
    subparsers.add_parser('list', help="List all products")

    # Update command
    parser_update = subparsers.add_parser('update', help="Update an existing product")
    parser_update.add_argument("--id", type=str, required=True)
    parser_update.add_argument("--name", type=str, required=True)
    parser_update.add_argument("--description", type=str, required=True)
    parser_update.add_argument("--price", type=float, required=True)

    # Delete command
    parser_delete = subparsers.add_parser('delete', help="Delete a product")
    parser_delete.add_argument("--id", type=str, required=True)

    # Count command
    subparsers.add_parser('count', help="Count all products")
    
    # Export command
    subparsers.add_parser('export', help="Export all products to JSON")

    # Import command
    parser_import = subparsers.add_parser('import_json', help="Import products from a JSON file")
    parser_import.add_argument("--file", type=str, required=True)

    return parser

def main():
    parser = setup_parsers()
    args = parser.parse_args()
    client = ProductClient()
    
    if not client.stub:
        sys.exit(1)

    command_functions = {
        'add': client.add_product,
        'list': client.list_products,
        'update': client.update_product,
        'delete': client.delete_product,
        'count': client.count_products,
        'export': client.export_products,
        'import_json': client.import_from_json,
    }

    func = command_functions.get(args.command)
    if func:
        func(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()