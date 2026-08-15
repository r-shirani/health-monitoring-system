import secrets
import string
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from monitoring.models import Device

User = get_user_model()


def generate_random_password(length=8):
  alphabet = string.ascii_letters + string.digits
  return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
  help = (
      "Provision users with random passwords and save details to a log file."
  )

  def add_arguments(self, parser):
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of users/devices to create",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="provisioned_users.txt",
        help="Output text file path",
    )

  def handle(self, *args, **options):
    count = options["count"]
    output_file = options["output"]

    last_user = (
        User.objects.filter(username__startswith="user-")
        .order_by("-id")
        .first()
    )

    if last_user and last_user.username.replace("user-", "").isdigit():
      start_code = int(last_user.username.replace("user-", "")) + 1
    else:
      start_code = 1001

    log_entries = []

    for i in range(count):
      current_code = start_code + i
      username = f"user-{current_code}"
      device_id = f"ESP32-{current_code}"
      name = f"ESP32-{current_code}"
      random_password = generate_random_password(8)

      user, _ = User.objects.get_or_create(username=username)
      user.set_password(random_password)
      user.save()

      token, _ = Token.objects.get_or_create(user=user)

      device, _ = Device.objects.get_or_create(
          device_id=device_id,
          defaults={
            "user": user,
            "name": name,
            "is_active": True,
            },
      )
      device.user = user
      device.name = name
      device.is_active = True
      device.save()

      login_url = f"http://localhost:8000/login?username={username}&password={random_password}"

      entry = (
          f"Username: {username} | Password: {random_password} | Device:"
          f" {device_id} | Token: {token.key} | URL: {login_url}"
      )
      log_entries.append(entry)

      self.stdout.write(
          self.style.SUCCESS(
              f"[{i+1}/{count}] CREATED: {username} | Pass: {random_password}"
          )
      )

    with open(output_file, "a", encoding="utf-8") as f:
      for line in log_entries:
        f.write(line + "\n")

    self.stdout.write(
        self.style.SUCCESS(f"\nAll login details saved to '{output_file}'.")
    )