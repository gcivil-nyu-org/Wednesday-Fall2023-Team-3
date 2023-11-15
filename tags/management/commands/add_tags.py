from django.core.management.base import BaseCommand
from tags.models import Tag


class Command(BaseCommand):
    help = "Adds predefined tags to the database."

    def handle(self, *args, **options):
        # Creating instances of the Tag model for the specified tags only if they don't exist
        tags_to_create = [
            "Hobbies",
            "Food & Drink",
            "Sports",
            "Nightlife",
            "Arts",
            "Academics",
        ]

        for tag_create in tags_to_create:
            tag = Tag(tag_name=tag_create)
            tag.save()
