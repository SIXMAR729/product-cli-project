import grpc
import argparse

import order_api_pb2
import order_api_pb2_grpc


def add_product(stub, args):
    """ฟังก์ชันสำหรับคำสั่ง 'add' """
    print("--- Calling CreateProduct ---")
    product_request = order_api_pb2.CreateProductRequest(
        name=args.name,
        description=args.description,
        price=args.price
    )
    response = stub.CreateProduct(product_request)
    print("CreateProduct response received:")
    print(response)

def list_products(stub, args):
    """ฟังก์ชันสำหรับคำสั่ง 'list' """
    print("--- Calling ListProducts ---")
    list_request = order_api_pb2.ListProductsRequest()
    product_stream = stub.ListProducts(list_request)
    print("All products in database:")
    for product in product_stream:
        print(f"  - ID: {product.product_id}, Name: {product.name}, Price: {product.price}")

def edit_product(stub, args):
    """ฟังก์ชันสำหรับคำสั่ง 'edit' """
    print(f"--- Calling EditProduct for ID: {args.id} ---")
    edit_request = order_api_pb2.EditProductRequest(
        product_id=args.id,
        name=args.name,
        description=args.description,
        price=args.price if args.price is not None else 0.0
    )
    response = stub.EditProduct(edit_request)
    print("EditProduct response received:")
    print(response)

def delete_product(stub, args):
    """ฟังก์ชันสำหรับคำสั่ง 'delete' """
    print(f"--- Calling DeleteProduct for ID: {args.id} ---")
    delete_request = order_api_pb2.DeleteProductRequest(product_id=args.id)
    response = stub.DeleteProduct(delete_request)
    print("DeleteProduct response received:")
    print(f"  Success: {response.success}")
    print(f"  Message: {response.message}")

def count_products(stub, args):
    """ฟังก์ชันสำหรับคำสั่ง 'count' """
    print("--- Calling CountProducts ---")
    count_request = order_api_pb2.CountRequest()
    response = stub.CountProducts(count_request)
    print(f"Total products in DB: {response.count}")


def main():
    # Main parser
    parser = argparse.ArgumentParser(description="A CLI tool to manage Products via gRPC.")
    subparsers = parser.add_subparsers(dest='command', required=True, help="Available commands")

    # --- Define parser for 'add' ---
    parser_add = subparsers.add_parser('add', help="Add a new product")
    parser_add.add_argument("--name", type=str, required=True, help="Name of the product.")
    parser_add.add_argument("--price", type=float, required=True, help="Price of the product.")
    parser_add.add_argument("--description", type=str, default="", help="Description of the product.")
    parser_add.set_defaults(func=add_product)

    # --- Define parser for 'list' ---
    parser_list = subparsers.add_parser('list', help="List all products")
    parser_list.set_defaults(func=list_products)
    
    # --- Define parser for 'edit' ---
    parser_edit = subparsers.add_parser('edit', help="Edit an existing product")
    parser_edit.add_argument("--id", type=str, required=True, help="ID of the product to edit.")
    parser_edit.add_argument("--name", type=str, help="New name of the product.")
    parser_edit.add_argument("--description", type=str, help="New description of the product.")
    parser_edit.add_argument("--price", type=float, help="New price of the product.")
    parser_edit.set_defaults(func=edit_product)
    
    # --- Define parser for 'delete' ---
    parser_delete = subparsers.add_parser('delete', help="Delete a product")
    parser_delete.add_argument("--id", type=str, required=True, help="ID of the product to delete.")
    parser_delete.set_defaults(func=delete_product)

    # --- Define parser for 'count' ---
    parser_count = subparsers.add_parser('count', help="Count all products")
    parser_count.set_defaults(func=count_products)

    # Read from command line
    args = parser.parse_args()

    # Connect gRPC 
    with grpc.insecure_channel('localhost:50051') as channel:
        product_stub = order_api_pb2_grpc.ProductServiceStub(channel)
        # Call function connected with sub-command
        args.func(product_stub, args)


if __name__ == '__main__':
    main()