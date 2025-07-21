from concurrent import futures
import grpc
import threading
import stock_pb2
import stock_pb2_grpc
import order_pb2
import order_pb2_grpc
import sys
import threading


class OrderService(order_pb2_grpc.OrderServiceServicer):
    def __init__(self, stock_server_address: str):
        self.orders = {}  # Armazena pedidos, cada um com itens e status
        self.order_locks = {}  # Dicionário de locks individuais para cada pedido
        self.next_id = 1  # ID único para novos pedidos
        self._shutdown = threading.Event()  # Evento sinalizador para encerrar o servidor

        # Configura o cliente gRPC para se comunicar com o servidor de estoque
        self.stock_channel = grpc.insecure_channel(stock_server_address)
        self.stock_stub = stock_pb2_grpc.StockServiceStub(self.stock_channel)

    def CreateOrder(self, request, context):
        order_id = self.next_id  # Gera um novo ID de pedido
        order_status = []  # Lista para armazenar status de itens no pedido

        # Criação do pedido com lock global para evitar inconsistência no ID
        with threading.Lock():
            self.orders[order_id] = {"items": [], "status": []}
            self.order_locks[order_id] = threading.Lock()
            self.next_id += 1

        # Bloqueia apenas o pedido atual durante o processamento
        with self.order_locks[order_id]:
            for item in request.items:
                # Solicita ao servidor de estoque para reduzir a quantidade do produto
                response = self.stock_stub.ChangeQuantity(
                    stock_pb2.ChangeQuantityRequest(
                        product_id=item.prod_id,
                        value=-item.quantity  # Remove quantidade
                    )
                )

                # Define o status do item com base na resposta do servidor de estoque
                status = response.status if response.status >= 0 else -1
                order_status.append(order_pb2.OrderStatus(
                    prod_id=item.prod_id,
                    status=status
                ))

            # Armazena os itens e seus status no pedido
            self.orders[order_id] = {
                "items": request.items,
                "status": order_status
            }

        return order_pb2.CreateOrderResponse(items_status=order_status)

    def CancelOrder(self, request, context):
        order_id = request.order_id
        if order_id not in self.orders:
            # Retorna erro caso o pedido não exista
            return order_pb2.CancelOrderResponse(status=-1)

        # Bloqueia o pedido durante a operação de cancelamento
        with self.order_locks[order_id]:
            order = self.orders.pop(order_id)  # Remove o pedido da lista
            items = order["items"]
            statuses = order["status"]

            for item, status in zip(items, statuses):
                if status.status == 0:  # Reverte apenas se o item foi retirado com sucesso
                    self.stock_stub.ChangeQuantity(
                        stock_pb2.ChangeQuantityRequest(
                            product_id=item.prod_id,
                            value=item.quantity  # Devolve a quantidade
                        )
                    )

        del self.order_locks[order_id]  # Remove o lock do pedido cancelado
        return order_pb2.CancelOrderResponse(status=0)

    def End(self, request, context):
        total_orders = len(self.orders)  # Total de pedidos restantes
        total_products = self.stock_stub.Exit(stock_pb2.Empty()).total_products
        self._shutdown.set()  # Sinaliza o encerramento do servidor
        return order_pb2.EndResponse(
            total_products=total_products,
            total_orders=total_orders
        )


        
def serve(port, stock_service_addr):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  
    order_service = OrderService(stock_service_addr)  # Instancia o serviço de pedidos
    order_pb2_grpc.add_OrderServiceServicer_to_server(order_service, server)
    server.add_insecure_port(f"[::]:{port}")  # Escuta na porta especificada
    server.start()
    order_service._shutdown.wait()  # Espera o sinal de encerramento
    server.stop(0)  


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    stock_service_addr = sys.argv[2]
    
    if not (2048 <= port <= 65535):
        print("Port must be between 2048 and 65535")
        sys.exit(1)

    serve(port,stock_service_addr)