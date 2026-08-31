"""Al Balı (@al.bali.az) — canlı Instagram DM piloru.

Sifariş kanalı yalnız Instagram DM-dir; qiymətlər postlarda yazılmır.
Meta Advanced Access olmadan mesajlar ManyChat relay ilə gəlir.

İstifadə:
    python manage.py seed_albali
    python manage.py seed_albali --manychat-token <öz-tokenin>

Qaytarılan `manychat_token`-i ManyChat External Request-də
X-Relay-Token header-i kimi yaz (bax: INSTAGRAM_PILOT.md).
"""

import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from businesses.models import Business, FAQItem, Service
from inbox.models import BusinessMembership


class Command(BaseCommand):
    help = "Al Balı Instagram DM piloru üçün tenant və ManyChat tokeni yaradır"

    def add_arguments(self, parser):
        parser.add_argument(
            "--manychat-token",
            default="",
            help="Boşdursa təsadüfi token generasiya olunur (yalnız yeni/yeniləmə üçün)",
        )
        parser.add_argument("--username", default="albali")
        parser.add_argument("--password", default="demopass123")

    def handle(self, *args, **opts):
        existing = Business.objects.filter(slug="al-bali").first()
        token = opts["manychat_token"].strip()
        if not token:
            token = (existing.manychat_token if existing and existing.manychat_token else "") or secrets.token_urlsafe(24)

        business, created = Business.objects.update_or_create(
            slug="al-bali",
            defaults={
                "name": "Al Balı",
                "address": "Laçın — Oğuldərə kəndi (Bakı metrolarına çatdırılma)",
                "phone": "",
                "working_hours_text": "Sifariş: Instagram DM, hər gün",
                "extra_info": (
                    "Laçın — Oğuldərə kəndində, dəniz səviyyəsindən 2441 metr "
                    "yüksəklikdə dağ çiçəklərindən hazırlanan təbii bal. "
                    "Heç bir əlavəsi yoxdur. Vaxt keçdikcə xarlanması (bərkiməsi) "
                    "təbiidir — bu, təbii balın əlamətidir. "
                    "Sifariş yalnız Instagram DM-də qəbul olunur. "
                    "Stok məhduddur — admin-dən aktual kq-ı yoxla."
                ),
                "staff_label": "Komanda",
                "guardrail_text": (
                    "Tibbi müalicə, diaqnoz və ya xəstəliyə şəfa vədi vermə. "
                    "Balın faydaları haqqında yalnız ümumi, ehtiyatlı danış; "
                    "konkret xəstəlik üçün 'müalicə edir' demə — operatora yönləndir. "
                    "Stokda olmayan miqdarı vəd etmə. Qiyməti uydurma — yalnız "
                    "aşağıdakı cədvəldəki rəqəmləri de."
                ),
                "manychat_token": token,
                "is_active": True,
            },
        )

        business.services.all().delete()
        Service.objects.bulk_create(
            [
                Service(
                    business=business,
                    name="Süzmə bal, 250 qr",
                    price_text="12.50 ₼",
                    description="Mumdan ayrılmış, çaya və yeməyə rahat.",
                ),
                Service(
                    business=business,
                    name="Süzmə bal, 500 qr",
                    price_text="25 ₼",
                ),
                Service(
                    business=business,
                    name="Süzmə bal, 1 kq",
                    price_text="50 ₼",
                ),
                Service(
                    business=business,
                    name="Şanı (pətək) bal, 250 qr",
                    price_text="17.50 ₼",
                    description="Pətəkdən çıxdığı kimi, mumu ilə; mumu da yeyilir.",
                ),
                Service(
                    business=business,
                    name="Şanı (pətək) bal, 500 qr",
                    price_text="35 ₼",
                ),
                Service(
                    business=business,
                    name="Şanı (pətək) bal, 1 kq",
                    price_text="70 ₼",
                ),
            ]
        )

        business.faq_items.all().delete()
        FAQItem.objects.bulk_create(
            [
                FAQItem(
                    business=business,
                    question="Şanı ilə süzmə fərqi nədir?",
                    answer=(
                        "İkisi də eyni pətəkdən, eyni arılardan gəlir — fərq yalnız "
                        "formadadır. Şanı bal pətəkdən çıxdığı kimi, mumu ilə birlikdə "
                        "olur. Süzmə bal isə mumdan ayrılmış haldadır. İlk dəfə "
                        "alırsınızsa, çox vaxt süzmədən başlamağı məsləhət görürük."
                    ),
                ),
                FAQItem(
                    business=business,
                    question="Çatdırılma necədir?",
                    answer=(
                        "Bakı metrolarına çatdırılma ödənişsizdir. Uyğun metro "
                        "stansiyasını deyin, orada görüşürük. Metrodan kənar ünvanlar "
                        "üçün variantı ayrıca danışırıq."
                    ),
                ),
                FAQItem(
                    business=business,
                    question="Bal təbiidirmi? Xarlanırsa xarabdır?",
                    answer=(
                        "Bal Laçın — Oğuldərə kəndində, öz arı təsərrüfatımızda "
                        "hazırlanır. Heç bir əlavəsi yoxdur. Xarlanması (bərkiməsi) "
                        "təbiidir — bu, təbii balın əlamətidir."
                    ),
                ),
                FAQItem(
                    business=business,
                    question="Necə sifariş edim?",
                    answer=(
                        "Adınızı, məhsulu (şanı və ya süzmə), qramı (250 qr / 500 qr / "
                        "1 kq) və çatdırılma üçün metro adını yazın — qeydiyyata salırıq."
                    ),
                ),
            ]
        )

        user, _ = User.objects.get_or_create(
            username=opts["username"],
            defaults={"is_staff": True, "is_superuser": False},
        )
        user.set_password(opts["password"])
        user.is_staff = True
        user.save()
        BusinessMembership.objects.get_or_create(user=user, business=business)

        action = "yaradıldı" if created else "yeniləndi"
        self.stdout.write(
            self.style.SUCCESS(
                f"OK: Al Balı {action}.\n"
                f"  slug: al-bali\n"
                f"  operator: {opts['username']} / {opts['password']}\n"
                f"  manychat_token: {business.manychat_token}\n"
                "ManyChat-də External Request URL: "
                "<tunnel>/webhook/manychat/\n"
                "Header: X-Relay-Token: yuxarıdakı token\n"
                "Addımlar: INSTAGRAM_PILOT.md"
            )
        )
