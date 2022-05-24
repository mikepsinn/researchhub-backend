"""
Removes all unpaid distributions so they will not be eligible for withdrawal.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum

from user.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = User.objects.all()
        total_changed_records = 0
        for i, user in enumerate(users):
            print("{} / {}".format(i, users.count()))
            rep = user.reputation_records.exclude(distribution_type="REFERRAL")
            for record in rep:
                if record.giver and record.giver.reputation < 110:
                    total_changed_records += 1
                    print(record)
                    record.amount = 0
                    record.save()

            rep_sum = user.reputation_records.exclude(
                distribution_type="REFERRAL"
            ).aggregate(rep=Sum("amount"))
            print(rep_sum)
            rep = rep_sum.get("rep") or 0
            user.reputation = rep + 100
            try:
                user.save()
            except Exception as e:
                print(e)

            print(total_changed_records)
