from itertools import chain
import sys

import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

import requests 
from urllib.parse import urlparse

class Blockchain(object):
    
    difficulty_target = "0000"

    # hash_block codifica un bloque en un array y luego lo hashea
    # hay que asegurarse que el diccionario este ordenado
    # de lo contrario habra hashes inconsistentes luego

    def hash_block(self,block):
        
        block_encoded = json.dumps(block,sort_keys = True).encode()
        return hashlib.sha256(block_encoded).hexdigest()

    # la funcion init es el constructor de la clase
    # aqui guardamos la blockchain completa como una lista
    # como toda blockchain tiene un bloque genesis
    # se necesita inicializar el bloque genesis con el hash
    # del bloque anterior
    # en el ejemplo utilizamos un str "genesis_block" para obtener 
    # mencionado hash
    # una vez encontrado el hash necesitamos el blque nonce
    # usando el metodo llamado proof_of_work() que definiremos luego

    def __init__(self):
        
        self.nodes = set()

        # guarda todos los bloques en la blockchain entera

        self.chain = []

        # guarda temporalmente las transacciones para
        # para el bloque actual

        self.current_transactions = []

        # crea el bloque inicial con un hash especifico fijo
        # de bloque genesis previo comenzando con indice 0

        genesis_hash = self.hash_block("genesis_block")
        self.append_block(
            hash_of_previous_block = genesis_hash,
            nonce =self.proof_of_work(0,genesis_hash,[])
        )




    # el metodo proof_of_work() devolvera el hash con la dificultad deseada
    # en este caso la dificultad esta como que el hash commience con 0000
    # difficulty_target

    # usaremos proof_of_work para obtener nonce bloque actual




    def proof_of_work(self, index, hash_of_previous_block, transactions):
        
        # probamos con 0

        nonce = 0

        # probamos hashear el nonce con el hash del bloque anterior
        # hasta que sea valido

        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            
            nonce += 1

        return nonce




    # en valid_proof hasheamos el contenido del bloque 
    # hasta que se corresponda con la dificultad objetivo



    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):

        # crea un str con el hash del bloque anterios y bloquea  el contenido
        # con el nonce incluido

        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()

        # hashea con sha256

        content_hash = hashlib.sha256(content).hexdigest()

        # chequea si el hash tiene la dificultad deseada

        return  content_hash[:len(self.difficulty_target)] == self.difficulty_target






    # una vez que se encuentra el bloque
    # se puede escribir el metodo para adjuntar el 
    # bloque al blockchain existente, esta es la funcion
    # del metodo append_block





    def append_block(self, nonce, hash_of_previous_block):
        
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        # resetea las transacciones actuales

        self.current_transactions = []

        # agrega un bloque nuevo a la blockchain

        self.chain.append(block)
        return block









    # agregamos a la blockchain el add

    def add_transaction(self, sender, recipient, amount):
        
        self.current_transactions.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender,
        })
        return self.last_block['index'] + 1

    # agrego metodo que guarda la dir del nodo relacinoado







    def add_node(self, address):
        
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        print(parsed_url.netloc)

    # determinar si una blockchain es valida








    def valid_chain(self, chain):

        # bloque genesis
        last_block = chain[0]

        #comienza el segundo bloque
        current_index = 1

        while current_index < len(chain):
            
            block = chain[current_index]
            
            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False

            #  chequear un nonce valido
            if not self.valid_proof(
                current_index,
                block['hash_of_previous_block'],
                block['transactions'],
                block['nonce']):
                return False

            # moverse al proximo bloque de la cadena
            last_block = block
            current_index += 1

        # la cadena es valida
        return True







    def update_blockchain(self):

        # junta los nodos que fueron registrados

        neightbours = self.nodes
        new_chain = None

        # para simplicidad, mirar las chain mas largas que las nuestras
        max_length = len(self.chain)

        # agarrar y verificar todos los eslabones en la cadena
        
        for node in neightbours:
            
            # agarrar la cadena de los otros nodos
            response = requests.get(f'http://{node}/blockchain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            # chequear si la longitud es mass larga que la cadena

            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
            
        # reemplazar nuestra cadena si descubrimos una cadena valida mas larga que la nuestra

        if new_chain:
            self.chain = new_chain
            return True
    
        return False







    @property
    def last_block(self):

        # ultimo bloque del blockchain

        return self.chain[-1]
    
    
    
    
    
    
app = Flask(__name__)

# genera una unica direccion global para este nodo

node_identifier = str(uuid4()).replace('-', '')

#  instancia el blockchain

blockchain = Blockchain()

    
    
    
    
    
    
    
# retorna el blockchain completo

@app.route('/blockchain', methods = ['GET'])

def full_chain():
    
    response = {
        'chain':blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200






# habilita minado

@app.route('/mine', methods=['GET'])

def mine_block():
    
    blockchain.add_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # obtener el hash del ultimo bloque de la blockchain

    last_block_hash = blockchain.hash_block(blockchain.last_block)

    # usando pow, obtener el nonce for quew el nuevo bloque 
    # sea añadido a la blockchain
    
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)

    # agregar el bloque nuevo a la blockchain usando el ultimo bloque
    # hashear el actual nonce

    block = blockchain.append_block(nonce, last_block_hash)
    
    response = {
        'message': "New Block Mined",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transactions': block['transactions'],
    }
    return jsonify(response), 200





# agregar transacciones al bloque actual
@app.route('/transactions/new', methods=['POST'])

def new_transaction():

    # toma el valor ingresado por el cliente

    values = request.get_json()

    # chequea que los campos requeridos esten en los datos del POST

    required_fields = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required_fields):
        return('Missing fields', 400)

    # crear una nueva transaccion
    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    response = {'message':
        f'Transaction will be added to Block {index}'}
    return(jsonify(response), 201)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))

        



# con los metodos agregados a la blockchain ahora definimos routas para la REST API

@app.route('/nodes/add_nodes', methods=['POST'])
def add_nodes():

    # obtener los nodoos recibidos desde el cliente

    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Missing node(s) info",400

    for node in nodes:
        blockchain.add_node(node)
    
    response = {
        'message': 'New nodes added',
        'nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201





@app.route('/nodes/sync', methods=['GET'])
def sync():
    updated = blockchain.update_blockchain()
    if updated:
        response = {
            'message': 'The blockchain has been updated is the latest',
            'blockchain': blockchain.chain
        }
    return jsonify(response), 200