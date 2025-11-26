"""
Django management command to test LLM-powered search.
Usage: python manage.py test_llm_search "your query here"
"""

from django.core.management.base import BaseCommand

from data.admin import LLMQueryBuilder
from data.models.suggestion import SuggestionCohorte


class Command(BaseCommand):
    help = "Test LLM-powered search with a query"

    def add_arguments(self, parser):
        parser.add_argument("query", type=str, help="Search query to test")

    def handle(self, *args, **options):
        query = options["query"]

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(f"Testing query: '{query}'"))
        self.stdout.write("=" * 80)

        builder = LLMQueryBuilder(SuggestionCohorte)

        # Check API key
        if not builder.api_key:
            self.stdout.write(self.style.ERROR("❌ ANTHROPIC_API_KEY not configured!"))
            self.stdout.write(
                "Please set ANTHROPIC_API_KEY or ANTHROPIC_KEY in your .env file"
            )
            return

        self.stdout.write(self.style.SUCCESS(f"✓ API key configured"))

        # Show model schema
        self.stdout.write("\n" + self.style.WARNING("Model schema being sent to LLM:"))
        self.stdout.write("-" * 80)
        schema = builder._get_model_schema()
        self.stdout.write(schema[:500] + "..." if len(schema) > 500 else schema)
        self.stdout.write("-" * 80)

        # Get the queryset
        queryset = SuggestionCohorte.objects.all()
        initial_count = queryset.count()
        self.stdout.write(f"\nInitial queryset count: {initial_count}")

        # Apply LLM search
        self.stdout.write(self.style.WARNING("\nCalling LLM..."))
        filtered_queryset = builder.build_queryset(queryset, query)

        final_count = filtered_queryset.count()
        self.stdout.write(f"Filtered queryset count: {final_count}")

        if filtered_queryset.query.where:
            self.stdout.write(self.style.SUCCESS("\n✓ Query was modified by LLM"))
            self.stdout.write(f"SQL WHERE clause: {filtered_queryset.query.where}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠ Query was NOT modified"))

        # Show some results
        if final_count > 0:
            self.stdout.write(self.style.SUCCESS(f"\nFirst 3 results:"))
            for i, cohorte in enumerate(filtered_queryset[:3], 1):
                self.stdout.write(f"\n{i}. ID: {cohorte.id}")
                self.stdout.write(f"   Action: {cohorte.identifiant_action}")
                self.stdout.write(f"   Type: {cohorte.type_action}")
                self.stdout.write(f"   Statut: {cohorte.statut}")
                if cohorte.metadata:
                    keys = list(cohorte.metadata.keys())[:3]
                    self.stdout.write(f"   Metadata keys: {keys}")
                    if "1) 📦 Nombre Clusters Proposés" in cohorte.metadata:
                        clusters = cohorte.metadata["1) 📦 Nombre Clusters Proposés"]
                        self.stdout.write(f"   Clusters proposés: {clusters}")

        self.stdout.write("\n" + "=" * 80)
