from django.core.management.base import BaseCommand
from core.models import WasteGuideItem

DATA = [
    ("banana peel", "WET", "Put in wet bin. Can compost."),
    ("vegetable scraps", "WET", "Wet bin. Drain excess water if possible."),
    ("tea bags", "WET", "Wet bin. Remove staples if any."),
    ("eggshell", "WET", "Wet bin. Compostable."),
    ("milk packet", "DRY", "Dry bin. Rinse & dry first."),
    ("chips packet", "DRY", "Dry bin. Keep clean and dry."),
    ("newspaper", "DRY", "Dry bin. Bundle if possible."),
    ("cardboard", "DRY", "Dry bin. Flatten for easy pickup."),
    ("glass bottle", "DRY", "Dry bin. Wrap if broken."),
    ("aluminium can", "DRY", "Dry bin. Rinse and crush lightly."),
    ("battery", "HAZARD", "Hazard. Store separately. Never in wet bin."),
    ("tube light", "HAZARD", "Hazard. Handle carefully; return to collection center."),
    ("medicine strip", "HAZARD", "Hazard. Seal in bag; do not mix with wet."),
    ("sanitary waste", "HAZARD", "Hazard. Wrap in paper, label, separate."),
    ("old phone", "EWASTE", "E-waste. Give to authorized e-waste pickup."),
    ("charger", "EWASTE", "E-waste. Keep together in a bag."),
    ("earphones", "EWASTE", "E-waste. Send to e-waste collection."),
    ("broken appliance", "EWASTE", "E-waste. Do not dismantle; send as-is."),
]

class Command(BaseCommand):
    help = "Seeds WasteGuideItem table with common segregation items."

    def handle(self, *args, **kwargs):
        created = 0
        for name, cat, inst in DATA:
            _, was_created = WasteGuideItem.objects.get_or_create(
                item_name=name,
                defaults={"category": cat, "instructions": inst},
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded. New items created: {created}"))
