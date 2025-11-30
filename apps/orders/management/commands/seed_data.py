from django.core.management.base import BaseCommand
from faker import Faker
import random

from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory

fake = Faker()


class Command(BaseCommand):
    help = "Seed dummy data for categories, products, stores, and inventory"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        Category.objects.all().delete()
        Product.objects.all().delete()
        Store.objects.all().delete()
        Inventory.objects.all().delete()

        categories = [
            Category.objects.create(name=name)
            for name in ["Electronics", "Books", "Groceries", "Fashion", "Home"]
        ]

        products = []
        for _ in range(200):
            cat = random.choice(categories)
            products.append(
                Product.objects.create(
                    title=fake.sentence(nb_words=3),
                    description=fake.text(max_nb_chars=100),
                    price=round(random.uniform(50, 5000), 2),
                    category=cat,
                )
            )

        stores = []
        for _ in range(5):
            stores.append(
                Store.objects.create(
                    name=fake.company(),
                    location=fake.city(),
                )
            )

        for store in stores:
            sample_products = random.sample(products, 80)
            Inventory.objects.bulk_create(
                [
                    Inventory(
                        store=store,
                        product=p,
                        quantity=random.randint(0, 100),
                    )
                    for p in sample_products
                ]
            )

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
