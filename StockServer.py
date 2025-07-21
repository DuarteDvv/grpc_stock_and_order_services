from concurrent import futures
import grpc
import stock_pb2
import stock_pb2_grpc
import sys
import threading


class StockService(stock_pb2_grpc.StockServiceServicer):
    def __init__(self):
        self.products = {}  # Armazena produtos, cada um com ID, descrição e quantidade
        self.product_locks = {}  # Dicionário para associar locks individuais a cada produto
        self.next_id = 1  # ID único para novos produtos
        self._shutdown = threading.Event()  # Evento sinalizador para encerrar o servidor

    def AddProduct(self, request, context):
        # Bloqueio global para criar produtos ou verificar existência
        with threading.Lock():
            for prod_id, product in self.products.items():
                if product["description"] == request.description:
                    # Se o produto já existir, aumenta a quantidade com lock específico
                    with self.product_locks[prod_id]:
                        product["quantity"] += request.quantity
                        return stock_pb2.AddProductResponse(product_id=prod_id)

            # Caso contrário, cria um novo produto com um lock associado
            prod_id = self.next_id
            self.products[prod_id] = {
                "description": request.description,
                "quantity": request.quantity
            }
            self.product_locks[prod_id] = threading.Lock()
            self.next_id += 1

        return stock_pb2.AddProductResponse(product_id=prod_id)

    def ChangeQuantity(self, request, context):
        if request.product_id not in self.products:
            # Retorna erro caso o ID do produto não exista
            return stock_pb2.ChangeQuantityResponse(status=-2)

        # Bloqueia alterações apenas no produto específico
        with self.product_locks[request.product_id]:
            product = self.products[request.product_id]
            new_quantity = product["quantity"] + request.value
            if new_quantity < 0:
                # Retorna erro se a quantidade ficar negativa
                return stock_pb2.ChangeQuantityResponse(status=-1)

            # Atualiza a quantidade do produto
            product["quantity"] = new_quantity
            return stock_pb2.ChangeQuantityResponse(status=new_quantity)

    def ListProducts(self, request, context):
        # Protege a leitura de produtos com um lock global para consistência
        with threading.Lock():
            product_list = [
                stock_pb2.Product(
                    product_id=prod_id,
                    description=product["description"],
                    quantity=product["quantity"]
                )
                for prod_id, product in sorted(self.products.items())
            ]
        return stock_pb2.ProductList(products=product_list)

    def Exit(self, request, context):
        # Finaliza o servidor, retornando o número total de produtos
        with threading.Lock():
            total_products = len(self.products)
            self._shutdown.set()  # Sinaliza que o servidor deve ser encerrado
            return stock_pb2.ExitResponse(total_products=total_products)




def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10)) 
    stock_service = StockService()  # Instancia o serviço de estoque
    stock_pb2_grpc.add_StockServiceServicer_to_server(stock_service, server)
    server.add_insecure_port(f"[::]:{port}")  # Escuta na porta especificada
    server.start()
    stock_service._shutdown.wait()  # Espera o sinal de encerramento
    server.stop(0) 



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    if not (2048 <= port <= 65535):
        print("Port must be between 2048 and 65535")
        sys.exit(1)

    serve(port)
