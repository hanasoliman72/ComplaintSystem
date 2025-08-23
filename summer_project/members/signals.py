from django.db.models.signals import post_migrate
from django.dispatch import receiver
from members.models import User

@receiver(post_migrate)
def create_default_superuser(sender, **kwargs):
    if not User.objects.filter(username="admin").exists():
        user = User(
            username="admin",
            email="hanasmsalah105@gmail.com",
            Name="Super Admin",
            Role="GeneralManager",
            is_superuser=True,
            is_staff=True,
        )
        user.set_password("Admin1234")
        user.save()
        print("Default superuser created: admin / Admin1234")
