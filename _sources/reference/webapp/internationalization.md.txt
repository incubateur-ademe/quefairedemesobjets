# Internationalisation

The website is only in french
Then the locale is set to `FR` only
We need internationalisation to translate default plugin to french (mainly wagtail)

## Update messages

To translate messages, add the message to `webapp/locale/fr/LC_MESSAGES/django.po`

```txt
msgid "Submit form"
msgstr "Valider"
```

Compile it `make -C webapp compilemessages`

And restart the Django server :

- `cd webapp`
- `make runserver`
