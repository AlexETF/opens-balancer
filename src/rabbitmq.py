
import pika
import json
import sys
from keystoneclient import session
from keystoneclient.auth.identity import v3
from novaclient.v2 import client
from rabbitmq_parse import RabbitMQMessageService
from nova_migrate import AuthService, MigrateService

global num_messages
global rabbitmq_service

keystone_url = "http://172.16.0.2:5000/v3"
username = "admin"
password = "admin"
user_domain_name = "default"
project_name = "admin"
project_domain_name = "default"

exchange_name = 'nova'
queue_name = 'nova_listening_queue'
binding_key = '#'

num_messages = 0

auth_service = AuthService(keystone_url=keystone_url,
                           username=username,
                           password = password,
                           user_domain_name = user_domain_name,
                           project_name=project_name,
                           project_domain_name=project_domain_name)

rabbitmq_service = RabbitMQMessageService(auth_service)

rabbitmq_service.initialize()

parameters = pika.URLParameters('amqp://nova:vBbTF24k@10.20.0.3:5672/%2F')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange=exchange_name, type='topic')
result = channel.queue_declare(queue=queue_name, exclusive=True)
channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_key)

def callback(ch, method, properties, body):
    global num_messages
    num_messages = num_messages + 1
    rabbitmq_service.parse_message(routing_key = method.routing_key, message = body)
    rabbitmq_service.check_overload()
    rabbitmq_service.print_short_info()


channel.basic_consume(callback, queue=queue_name, no_ack=True)

print "Waiting for logs. Press CTRL + C to stop"

channel.start_consuming()
