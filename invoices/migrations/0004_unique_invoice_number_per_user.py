from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0003_item_invoiceitem_item"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                fields=["user", "invoice_number"],
                name="unique_invoice_number_per_user",
            ),
        ),
    ]
