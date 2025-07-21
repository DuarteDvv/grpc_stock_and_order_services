# Variáveis
PROTO_FILES = stock.proto order.proto
STUB_FILES = stock_pb2.py stock_pb2_grpc.py order_pb2.py order_pb2_grpc.py
PYTHON = python3

# Regras principais
all: stubs

clean:
	rm -f $(STUB_FILES)

stubs: $(STUB_FILES)

# Geração dos stubs em Python
stock_pb2.py stock_pb2_grpc.py: stock.proto
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. stock.proto

order_pb2.py order_pb2_grpc.py: order.proto
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. order.proto

# Regras de execução
run_serv_estoque: stubs
	$(PYTHON) StockServer.py $(arg1)

run_cli_estoque: stubs
	$(PYTHON) StockClient.py $(arg1)

run_serv_pedidos: stubs
	$(PYTHON) OrderServer.py $(arg1) $(arg2)

run_cli_pedidos: stubs
	$(PYTHON) OrderClient.py $(arg1) $(arg2)

# Evita erros se clean for chamado sem arquivos para remover
.PHONY: clean stubs run_serv_estoque run_cli_estoque run_serv_pedidos run_cli_pedidos
