
import pika, sys
import logging, logging.handlers
from time import gmtime, strftime, localtime
from config import credentials
from config import config
from services.auth_service import AuthService
from services.migrate_service import MigrateService
from services.rabbitmq_message_service import RabbitMQMessageService


global rabbitmq_service

def callback(ch, method, properties, body):
    """ Method that will be called for processing rabbitmq messages """
    global rabbitmq_service

    rabbitmq_service.parse_message(routing_key = method.routing_key, message = body)
    rabbitmq_service.check_overload()
    rabbitmq_service.print_short_info()
    # rabbitmq_service.print_all_info()


def setup_logging():
    """ Method for configuring application logger options """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_filename = config.log_directory + str(strftime("%Y-%m-%d %Hh%Mm%Ss", localtime())) + '.log'
    max_bytes = config.log_max_bytes
    backup_count = config.log_backup_count
    handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s| %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def main():
    """ Main method """
    global rabbitmq_service

    logger = setup_logging()

    keystone_url = credentials.keystone_cfg['service_url']
    username = credentials.keystone_cfg['username']
    password = credentials.keystone_cfg['password']
    user_domain_name = credentials.keystone_cfg['user_domain_name']
    project_name = credentials.keystone_cfg['project_name']
    project_domain_name =  credentials.keystone_cfg['project_domain_name']

    auth_service = AuthService(keystone_url = keystone_url,
                               username = username,
                               password = password,
                               user_domain_name = user_domain_name,
                               project_name = project_name,
                               project_domain_name = project_domain_name)

    rabbitmq_service = RabbitMQMessageService(auth_service = auth_service, logger = logger)

    if rabbitmq_service.initialize() == False:
        print('Failed to authenticate, check the log file for more details')
        sys.exit(1)

    rabbitmq_service.start_periodic_check()

    rabbitmq_username = credentials.rabbitmq_cfg['username']
    rabbitmq_password = credentials.rabbitmq_cfg['password']
    rabbitmq_endpoint = credentials.rabbitmq_cfg['server_endpoint']
    rabbitmq_port  = credentials.rabbitmq_cfg['port']
    rabbitmq_vhost = credentials.rabbitmq_cfg['virtual_host']

    exchange_name = credentials.rabbitmq_cfg['listening_options']['exchange_name']
    queue_name = credentials.rabbitmq_cfg['listening_options']['my_queue_name']
    binding_key = credentials.rabbitmq_cfg['listening_options']['binding_key']

    rabbitmq_credentials = pika.PlainCredentials(username = rabbitmq_username, password = rabbitmq_password)
    parameters = pika.ConnectionParameters(host = rabbitmq_endpoint,
                                           port = rabbitmq_port,
                                           virtual_host = rabbitmq_vhost,
                                           credentials  = rabbitmq_credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, type='topic')
    result = channel.queue_declare(queue=queue_name, exclusive=True)
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_key)

    channel.basic_consume(callback, queue=queue_name, no_ack=True)

    print('Waiting for messages. Check the log files in directory %s for information.' % config.log_directory)
    print('Press CTRL + C to stop')

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        connection.close()
        logger.info('Connection closed')
        print('Program exited ...')


if __name__ == '__main__':
    main()
