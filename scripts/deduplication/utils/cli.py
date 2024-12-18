from rich import print


def banner(text: str) -> None:
    """
    Affiche une banière pour aider à relire les logs CLI

    Args:
        text: texte à afficher
    """
    print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    print(f"[bold cyan]{text}[/bold cyan]")
    print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")
