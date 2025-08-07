from django.core.management.base import BaseCommand
from leads.models import Client

class Command(BaseCommand):
    help = 'Display webhook URLs for all clients'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=int,
            help='Get webhook URL for specific client ID',
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='http://127.0.0.1:8000',
            help='Domain to use in webhook URL (default: http://127.0.0.1:8000)',
        )

    def handle(self, *args, **options):
        domain = options['domain']
        client_id = options.get('client_id')
        
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                clients = [client]
            except Client.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Client with ID {client_id} does not exist')
                )
                return
        else:
            clients = Client.objects.all()
        
        if not clients:
            self.stdout.write(self.style.WARNING('No clients found'))
            return
            
        self.stdout.write(self.style.SUCCESS('Webhook URLs:'))
        self.stdout.write('-' * 80)
        
        for client in clients:
            webhook_url = f"{domain}/webhook/{client.webhook_token}/"
            self.stdout.write(f"Client ID: {client.id}")
            self.stdout.write(f"Business: {client.business_name}")
            self.stdout.write(f"User: {client.user.username if client.user else 'No user'}")
            self.stdout.write(f"Webhook URL: {webhook_url}")
            self.stdout.write('-' * 80)
