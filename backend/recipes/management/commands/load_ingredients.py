from django.core.management.base import BaseCommand, CommandError
import json
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file',
                            type=str, help='The JSON file to load')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)

            for item in data:
                name = item.get('name')
                measurement_unit = item.get('measurement_unit')

                if name and measurement_unit:
                    Ingredient.objects.update_or_create(
                        name=name,
                        defaults={'measurement_unit': measurement_unit}
                    )

            self.stdout.write(
                self.style.SUCCESS('Successfully loaded ingredients'))
        except Exception as e:
            raise CommandError(f"An error occurred: {str(e)}")
