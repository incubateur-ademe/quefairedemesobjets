Le projet est actuellement déployé sur Scalingo.
Ils imposent une limite de 50 requêtes/seconde sur un worker.

Dans l'hypothèse d'un pic de charge, nous avons décidé d'ajouter Nginx en janvier 2025 afin d'agir comme serveur de cache et d'optimiser
- Le **cache** de certaines **vues Django**
- Le **cache** des **fichiers statiques**

Des images valant mille mots, ci-dessous un schéma résumant le parcours d'une requête lorsqu'elle atteint `lvao.ademe.fr` ou `quefairedemesdechets.ademe.fr

```mermaid
sequenceDiagram

participant Client
participant Nginx
participant Django



Client->>Nginx: Request lvao.ademe.fr

alt Cache Hit

Nginx-->>Client: Return cached response

else Cache Miss

Nginx->>Django: Forward request to Django

Django-->>Nginx: Generate response

alt Authenticated User

Django->>Nginx: Add 'logged_in' cookie

end

alt iframe query param present

Django->>Nginx: Add iframe cookie

end

Nginx-->>Client: Return Django response

end
```
# nginx
# whitenoise
# cache
