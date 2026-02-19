# Tests de Régression E2E

Ce document explique comment créer et maintenir les tests de régression end-to-end (E2E) en utilisant Django Lookbook et Playwright.

## Vue d'ensemble

Le projet utilise deux outils complémentaires pour les tests de régression :

- **Django Lookbook** : Un outil de prévisualisation de composants Django qui permet de créer des pages de test isolées
- **Playwright** : Un framework de test E2E qui automatise l'interaction avec le navigateur

## Architecture des tests

Les tests E2E sont organisés en trois parties :

1. **Templates de test** (`webapp/templates/ui/tests/`) : Pages HTML dédiées aux tests
2. **Previews Lookbook** (`webapp/previews/template_preview.py`) : Méthodes Python qui rendent les templates
3. **Tests Playwright** (`webapp/e2e_tests/`) : Scripts de test qui interagissent avec les previews

## Ajouter un nouveau test E2E

### Étape 1 : Créer un template de test

Créez un fichier HTML dans `webapp/templates/ui/tests/` qui contient le scénario de test.

**Exemple** : `webapp/templates/ui/tests/mon_nouveau_test.html`

```html
{% load dsfr_tags %} {% dsfr_callout title="Test de mon fonctionnalité"
text="Cette page teste [décrire ce qui est testé]."
icon_class="fr-icon-alert-line" %}

<!-- Contenu du test : iframe, formulaire, carte, etc. -->
<iframe src="..." width="100%" height="800"></iframe>
```

### Étape 2 : Ajouter une méthode preview

Dans `previews/template_preview.py`, ajoutez une méthode dans la classe `TestsPreview`.

**Convention de nommage** :

- Préfixer avec `t_{number}_` où `{number}` est incrémental (t_1, t_2, t_3, etc.)
- Le numéro représente l'ordre chronologique de création
- Les tests plus anciens ont des numéros plus bas et apparaissent en premier
- Ajouter les nouveaux tests à la fin de la classe

**Exemple** :

```python
class TestsPreview(LookbookPreview):
    # ... autres tests ...

    def t_4_mon_nouveau_test(self, **kwargs):
        """Description du test"""
        return render_to_string(
            "ui/tests/mon_nouveau_test.html",
            {"base_url": base_url},  # Optionnel : passer des variables de contexte
        )
```

### Étape 3 : Créer le test Playwright

Ajoutez un test dans `webapp/e2e_tests/` (généralement `carte.spec.ts` ou un fichier dédié).

**Exemple** :

```typescript
test.describe("🎯 Ma Fonctionnalité", () => {
  test("Le test vérifie que [comportement attendu]", async ({ page }) => {
    // Naviguer vers la preview Lookbook
    await page.goto("/lookbook/preview/tests/t_4_mon_nouveau_test", {
      waitUntil: "domcontentloaded",
    });

    // Si le test utilise une iframe
    const iframe = page.frameLocator("iframe").first();
    await expect(iframe.locator("body")).toBeAttached({ timeout: 10000 });

    // Interagir avec les éléments (utiliser data-testid autant que possible)
    await iframe.locator('[data-testid="mon-element"]').click();

    // Vérifier le comportement attendu
    await expect(iframe.locator('[data-testid="resultat"]')).toBeVisible();
    await expect(iframe.locator('[data-testid="resultat"]')).toContainText(
      "Texte attendu",
    );
  });
});
```

### Étape 4 : Utiliser les data-testid

Pour des tests robustes, utilisez des attributs `data-testid` dans vos templates :

```html
<div data-testid="mon-composant">
  <button data-testid="mon-bouton">Cliquer</button>
</div>
```

Puis dans le test :

```typescript
await page.locator('[data-testid="mon-bouton"]').click();
```

## Bonnes pratiques

### Nommage des tests

- **Groupes de tests** : Utilisez des emojis et des noms descriptifs en français

```typescript
test.describe("🗺️ Affichage de la Carte", () => { ... })
```

- **Noms de tests individuels** : Décrivez clairement le comportement vérifié

```typescript
test("La carte affiche la légende après une recherche", async ({ page }) => { ... })
```

### Utilisation des iframes

Si votre test utilise une iframe (par exemple pour tester `carte.js` ou `formulaire`) :

```typescript
// Attendre que l'iframe soit chargée
const iframe = page.frameLocator("iframe").first();
await expect(iframe.locator("body")).toBeAttached({ timeout: 10000 });

// Interagir avec les éléments dans l'iframe
await iframe.locator('[data-testid="element"]').click();
```

## Exécuter les tests

### Tous les tests

```bash
npm run test:e2e
```

### Un fichier spécifique

```bash
npx playwright test webapp/e2e_tests/carte.spec.ts
```

### Un test spécifique

```bash
npx playwright test -g "Le label ESS est affiché"
```

### Mode interactif (debug)

```bash
npx playwright test --ui
```

### Avec interface graphique

```bash
npx playwright test --headed
```

## Dépannage

### L'iframe ne se charge pas

- Vérifiez que le `base_url` est correctement passé au template
- Vérifiez que le script (carte.js, formulaire, etc.) est correctement chargé

### Les sélecteurs ne fonctionnent pas

- Privilégiez les `data-testid` aux sélecteurs CSS complexes
- Utilisez `.first()` ou `.nth(index)` pour les éléments multiples
- Vérifiez que l'élément est dans l'iframe avec `iframe.locator()`

### Les tests sont instables (flaky)

Playwright dispose de mécanismes d'auto-waiting intégrés. Consultez les bonnes pratiques :

- [Best Practices - Playwright](https://playwright.dev/docs/best-practices)
- [Auto-waiting - Playwright](https://playwright.dev/docs/actionability)

Évitez d'ajouter des `timeout` ou `force: true` sauf si absolument nécessaire, car cela masque souvent des problèmes sous-jacents.

## Ressources

- [Documentation Playwright](https://playwright.dev/)
- [Best Practices Playwright](https://playwright.dev/docs/best-practices)
- [Documentation Django Lookbook](https://django-lookbook.readthedocs.io/en/latest/)
- [Tests existants](../../../webapp/e2e_tests/)
- [Previews de test](../../../webapp/previews/template_preview.py)
