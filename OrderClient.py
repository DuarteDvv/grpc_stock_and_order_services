import sys
import grpc
import order_pb2
import order_pb2_grpc
import stock_pb2
import stock_pb2_grpc


def process_commands(stock_server: str, order_server: str) -> None:
    # Conecta aos servidores
    with grpc.insecure_channel(stock_server) as stock_channel, grpc.insecure_channel(order_server) as order_channel:
        stock_stub = stock_pb2_grpc.StockServiceStub(stock_channel)
        order_stub = order_pb2_grpc.OrderServiceStub(order_channel)

        # Listar produtos ao iniciar
        try:
            stock_response = stock_stub.ListProducts(stock_pb2.Empty())
            for product in stock_response.products:
                print(f"{product.product_id} {product.quantity} {product.description}")
        except grpc.RpcError as e:
            print(f"Erro ao listar produtos: {e.details()}")
            return

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            command = line[0]
            args = line[1:].strip()

            if command == "P":
                # Comando P: Criar pedido
                try:
                    items = args.split()
                    if len(items) % 2 != 0:
                        continue  

                    order_items = []
                    for i in range(0, len(items), 2):
                        prod_id = int(items[i])
                        quantity = int(items[i + 1])
                        order_items.append(order_pb2.OrderItem(prod_id=prod_id, quantity=quantity))

                    order_request = order_pb2.CreateOrderRequest(items=order_items)
                    response = order_stub.CreateOrder(order_request)
                    for status in response.items_status:
                        print(f"{status.prod_id} {status.status}")
                except Exception as e:
                    print(f"Erro ao criar pedido: {e}")
                    continue

            elif command == "X":
                # Comando X: Cancelar pedido
                try:
                    order_id = int(args)
                    cancel_request = order_pb2.CancelOrderRequest(order_id=order_id)
                    response = order_stub.CancelOrder(cancel_request)
                    print(response.status)
                except Exception as e:
                    print(f"Erro ao cancelar pedido: {e}")
                    continue

            elif command == "T":
                # Comando T: Terminar servidores
                try:
                    end_request = order_pb2.Empty()
                    response = order_stub.End(end_request)
                    print(f"{response.total_products} {response.total_orders}")
                except Exception as e:
                    print(f"Erro ao terminar servidores: {e}")
                break

            else:
                continue


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <stock_server_address> <order_server_address>")
        sys.exit(1)

    stock_server = sys.argv[1]
    order_server = sys.argv[2]
    process_commands(stock_server, order_server)
