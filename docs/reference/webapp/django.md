# Django

## Applications

- `core` : main access point, handle shared code
- `qfdmo` : handle map and acteur
- `qfdmd` : handle advise about circular economy
- `search` : search engine
- `data` : object used by the backoffice to handle data
- `infotri` : info tri widget
- `stats` : stats api
- `dsfr-hacks` : tooling to help about using DSFR

### Django Tips

- Use class-based views when appropriate
- Prefer `LoginRequiredMixin` for protected views
- use Mixin classes to handle shared behaviour
- Use `prefetch_related` and `select_related` to optimize queries
