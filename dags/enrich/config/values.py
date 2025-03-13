"""
-- https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/templates/api/documentation/download.jag?tenant=carbon.super&resourceUrl=/registry/resource/_system/governance/apimgt/applicationdata/provider/insee/Sirene/V3/documentation/files/INSEE%20Documentation%20API%20Sirene%20Variables.pdf
-- 'C' pour "Cessée"
unite."etatAdministratifUniteLegale" = 'C'
OR
-- 'F' pour "Fermé"
etab."etatAdministratifEtablissement" = 'F'"
"""

# To make data more explicit
AE_UNITE_STATUS_MAPPING_EXPLICIT = {
    "A": "🟢 A = Active",
    "C": "🔴 C = Cessée",
}
AE_ETAB_STATUS_MAPPING_EXPLICIT = {
    "A": "🟢 A = Actif",
    "F": "🟠 F = Fermé",
}
