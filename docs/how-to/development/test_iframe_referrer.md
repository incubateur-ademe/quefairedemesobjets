# Tester le referrer d'une iframe

Ce guide explique comment tester que le referrer (l'URL de la page parente) est correctement capturé et transmis lorsque notre site est intégré dans une iframe sur un autre site.

## Contexte

Lorsque notre application est intégrée via iframe sur un site tiers, nous capturons l'URL complète de la page parente (incluant les paramètres de requête) pour nos analyses. Cette URL est encodée en base64 et passée comme paramètre `ref` dans l'URL de l'iframe, puis décodée côté analytics pour être stockée dans le sessionStorage sous la clé `qf_ifr`.

## Prérequis

- [ngrok](https://ngrok.com/) installé sur votre machine
- Le serveur de développement local configuré

## Étapes de test

### 1. Installer ngrok

Si ce n'est pas déjà fait, installez ngrok depuis [https://ngrok.com/](https://ngrok.com/)

### 2. Démarrer le serveur local

Lancez votre serveur web local sur le port 8000 (ou un autre port de votre choix) :

```bash
python manage.py runserver 8000
```

### 3. Exposer le serveur local via ngrok

Dans un autre terminal, lancez ngrok en spécifiant le même port que votre serveur local :

```bash
ngrok http 8000
```

Ngrok vous donnera une URL publique temporaire, par exemple : `https://4a3a46f653a8.ngrok-free.app`

### 4. Récupérer l'URL de prévisualisation Lookbook

Allez sur la page de test Lookbook du referrer :

```
https://quefairedemesdechets.localhost/lookbook/inspect/tests/t_1_referrer/
```

En haut à droite de l'écran, copiez l'URL de prévisualisation. Elle ressemble à :

```
https://quefairedemesdechets.localhost/lookbook/preview/tests/t_1_referrer/?timestamp=1768857086931&display=%257B%2522theme%2522%253A%2522light%2522%257D
```

### 5. Remplacer le host par celui de ngrok

Remplacez `quefairedemesdechets.localhost` par votre URL ngrok dans l'URL de prévisualisation :

```
https://4a3a46f653a8.ngrok-free.app/lookbook/preview/tests/t_1_referrer/?timestamp=1768857086931&display=%257B%2522theme%2522%253A%2522light%2522%257D
```

Ouvrez cette URL dans votre navigateur.

### 6. Vérifier le sessionStorage

1. Ouvrez les outils de développement de votre navigateur (F12)
2. Allez dans l'onglet "Application" (Chrome) ou "Stockage" (Firefox)
3. Dans la section "Session Storage", sélectionnez le domaine local
4. Cherchez la clé `qf_ifr`

### 7. Vérifier le résultat attendu

La valeur de `qf_ifr` doit afficher le referrer complet avec tous les paramètres, par exemple :

```
https://4a3a46f653a8.ngrok-free.app/lookbook/preview/tests/t_1_referrer/?timestamp=1768855346452&display=%257B%2522theme%2522%253A%2522light%2522%257D
```

Si c'est le cas, le referrer est correctement capturé et transmis ! 🎉
