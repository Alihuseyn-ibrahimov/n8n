"""Mövcud tenant üçün ManyChat Instagram relay tokenini aktivləşdirir.

İstifadə:
    python manage.py enable_instagram_relay --slug=al-bali
    python manage.py enable_instagram_relay --slug=master-nr-1 --rotate
"""

import secrets

from django.core.management.base import BaseCommand, CommandError

from businesses.models import Business


class Command(BaseCommand):
    help = "Business.manychat_token təyin edir və webhook quraşdırma mətnini çap edir"

    def add_arguments(self, parser):
        parser.add_argument("--slug", required=True, help="Business.slug")
        parser.add_argument(
            "--token",
            default="",
            help="Verilməsə mövcud token saxlanır, yoxdursa yenisi yaranır",
        )
        parser.add_argument(
            "--rotate",
            action="store_true",
            help="Mövcud tokeni yenisi ilə əvəz et",
        )

    def handle(self, *args, **opts):
        try:
            business = Business.objects.get(slug=opts["slug"])
        except Business.DoesNotExist as exc:
            raise CommandError(f"slug={opts['slug']} tapılmadı") from exc

        token = opts["token"].strip()
        if opts["rotate"] or not (token or business.manychat_token):
            token = token or secrets.token_urlsafe(24)
        else:
            token = token or business.manychat_token

        business.manychat_token = token
        business.is_active = True
        business.save(update_fields=["manychat_token", "is_active"])

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: '{business.name}' Instagram ManyChat relay aktivdir.\n"
                f"  slug: {business.slug}\n"
                f"  manychat_token: {token}\n\n"
                "ManyChat External Request:\n"
                "  URL: https://<cloudflared-host>/webhook/manychat/\n"
                "  Method: POST\n"
                "  Header: X-Relay-Token = yuxarıdakı token\n"
                "  Body JSON: "
                '{"subscriber_id": "{{user_id}}", "text": "{{last_input_text}}",'
                ' "first_name": "{{first_name}}"}\n'
                "  Cavab sahəsi: reply  (və ya Dynamic Content: content.messages)\n\n"
                "Lokal sınaq:\n"
                f'  curl -s -X POST http://127.0.0.1:8055/webhook/manychat/ \\\n'
                f'    -H "Content-Type: application/json" \\\n'
                f'    -H "X-Relay-Token: {token}" \\\n'
                '    -d \'{"subscriber_id":"test-1","text":"salam"}\'\n'
            )
        )
