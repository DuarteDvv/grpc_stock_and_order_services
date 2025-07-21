import sys
import grpc
import stock_pb2
import stock_pb2_grpc


def process_commands(server_address: str) -> None:
    # Conecta ao servidor
    with grpc.insecure_channel(server_address) as channel:
        stub = stock_pb2_grpc.StockServiceStub(channel)

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            command = line[0]
            args = line[1:].strip()

            if command == "P":
                # Comando P: Adicionar produto
                try:
                    quantidade, descricao = args.split(" ", 1)
                    quantidade = int(quantidade)
                    response = stub.AddProduct(stock_pb2.AddProductRequest(description=descricao, quantity=quantidade))
                    print(response.product_id)
                except ValueError:
                    # Ignorar erros de parsing
                    continue

            elif command == "Q":
                # Comando Q: Alterar quantidade de produto
                try:
                    prod_id, valor = map(int, args.split(" "))
                    response = stub.ChangeQuantity(stock_pb2.ChangeQuantityRequest(product_id=prod_id, value=valor))
                    print(response.status)
                except ValueError:
                    continue

            elif command == "L":
                # Comando L: Listar produtos
                response = stub.ListProducts(stock_pb2.Empty())
                for product in response.products:
                    print(f"{product.product_id} {product.quantity} {product.description}")

            elif command == "F":
                # Comando F: Finalizar servidor
                response = stub.Exit(stock_pb2.Empty())
                print(response.total_products)
                break
            
            else:
                continue


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python client.py <server_address>")
        sys.exit(1)

    server_address = sys.argv[1]
    process_commands(server_address)
