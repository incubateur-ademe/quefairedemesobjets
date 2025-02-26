COL_URL_DB = "url"
COL_URL_ORIGINAL = "url_original"
COL_URLS_TO_TRY = "urls_to_try"
COL_URL_SUCCESS = "url_success"
COL_URLS_RESULTS = "urls_results"
COL_DOMAINS_TO_TRY = "domains_to_try"
COL_DOMAINS_RESULTS = "domains_results"
COL_DOMAIN_SUCCESS = "domain_success"
COL_ACTEURS = "acteurs"
COL_SUGGEST_VALUE = "suggest_value"
COL_SCENARIO = "suggest_scenario"
COL_ID = "identifiant_unique"

SORT_COLS = [
    COL_URL_SUCCESS,
    COL_URL_SUCCESS,
    COL_URL_ORIGINAL,
    COL_URLS_TO_TRY,
]

SCENARIO_SYNTAX_FAIL = "🔴 Syntaxe invalide -> mise à vide"
SCENARIO_DNS_FAIL = "🔴 Domaine inaccessible -> mise à vide"
SCENARIO_URL_OK_DIFF = "🟡 URL OK mais différente -> nouvelle proposée"
SCENARIO_URL_FAIL = "🔴 URL inaccessible -> mise à vide"
SCENARIO_TOTAL = "🔢 Total Suggestions"

LABEL_SCENARIO = "Scénario"
LABEL_URL_ORIGINE = "URL d'origine"
LABEL_URL_PROPOSEE = "URL proposée"
