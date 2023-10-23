# myapp/management/commands/load_data.py

import csv
from location.models import Location as locat
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load data from a CSV file into the database'

    def handle(self, *args, **options):
        csv_file = r'C:\Users\dhire\OneDrive\Desktop\NYU\SE\Project\CheerUp\exported_data.csv'  # Provide the path to your CSV file

        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                locat.objects.create(
                    location_name=row[1],
                    latitude=row[2],
                    longitude=row[3],
                    zipcode=row[7],
                    address=row[4],
                    url=row[5],
                    category=row[6]
                )
        self.stdout.write(self.style.SUCCESS('Data loaded successfully'))
