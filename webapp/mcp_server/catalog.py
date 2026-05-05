"""Static reference data exposed by the MCP tools.

Action and sub-category codes are stable identifiers used by the ADEME
data-fair `/lines` filter (`qs=<action>:"<sous_categorie>"`). Keeping them
inline avoids a roundtrip on every `list_actions` / `list_sous_categories`
call and keeps the tool deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    code: str
    libelle: str
    description: str


@dataclass(frozen=True)
class SousCategorie:
    code: str
    libelle: str
    groupe: str


ACTIONS: tuple[Action, ...] = (
    Action(
        "preter",
        "Prêter",
        "L'utilisateur veut prêter un objet à un tiers (bibliothèque d'objets, "
        "prêt entre particuliers).",
    ),
    Action(
        "emprunter",
        "Emprunter",
        "L'utilisateur veut emprunter gratuitement un objet (bibliothèque "
        "d'objets, prêt entre particuliers).",
    ),
    Action("louer", "Louer", "L'utilisateur veut louer un objet (location payante)."),
    Action(
        "mettreenlocation",
        "Mettre en location",
        "L'utilisateur veut proposer son objet à la location.",
    ),
    Action(
        "reparer",
        "Réparer",
        "L'utilisateur veut faire réparer un objet (atelier, repair café, "
        "réparateur professionnel).",
    ),
    Action(
        "rapporter",
        "Rapporter",
        "L'utilisateur veut rapporter un objet en fin de vie pour qu'il soit "
        "valorisé (point de collecte, déchèterie, magasin reprenant l'objet).",
    ),
    Action(
        "donner",
        "Donner",
        "L'utilisateur veut donner un objet (ressourcerie, association).",
    ),
    Action(
        "echanger",
        "Échanger",
        "L'utilisateur veut échanger un objet (boîte à livres, gratiferia, troc).",
    ),
    Action(
        "acheter",
        "Acheter",
        "L'utilisateur veut acheter d'occasion (boutique de seconde main, "
        "ressourcerie, friperie).",
    ),
    Action(
        "revendre",
        "Revendre",
        "L'utilisateur veut revendre un objet (dépôt-vente, plateforme).",
    ),
    Action(
        "trier",
        "Trier",
        "L'utilisateur veut savoir comment trier un déchet (centre de tri, "
        "conseils par filière).",
    ),
)

ACTIONS_BY_CODE: dict[str, Action] = {a.code: a for a in ACTIONS}


SOUS_CATEGORIES: tuple[SousCategorie, ...] = (
    # Électroménager, hifi, image, son, photo
    SousCategorie(
        "gros_electromenager_refrigerant",
        "Gros électroménager (réfrigérant)",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "gros_electromenager_hors_refrigerant",
        "Gros électroménager (hors réfrigérant)",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "petit_electromenager",
        "Petit électroménager",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "materiel_hifi_et_video",
        "Matériel hifi et vidéo",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "materiel_photo_et_cinema",
        "Matériel photo et cinéma",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie("ecran", "Écran", "Électroménager, hifi, image, son, photo"),
    SousCategorie(
        "cd_dvd_et_jeu_video",
        "CD, DVD et jeu vidéo",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "instrument_de_musique",
        "Instrument de musique",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "instrument_musique_electrique",
        "Instrument de musique électrique",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie("ampoule", "Ampoule", "Électroménager, hifi, image, son, photo"),
    SousCategorie("luminaire", "Luminaire", "Électroménager, hifi, image, son, photo"),
    SousCategorie(
        "autre_equipement_electronique",
        "Autre équipement électronique",
        "Électroménager, hifi, image, son, photo",
    ),
    SousCategorie(
        "cartouches", "Cartouches d'encre", "Électroménager, hifi, image, son, photo"
    ),
    # Téléphonie, informatique
    SousCategorie(
        "smartphone_tablette_et_console",
        "Smartphone, tablette et console",
        "Téléphonie, informatique",
    ),
    SousCategorie(
        "materiel_informatique", "Matériel informatique", "Téléphonie, informatique"
    ),
    # Mobilité, véhicules
    SousCategorie("vehicule", "Véhicule", "Mobilité, véhicules"),
    SousCategorie("bateau", "Bateau", "Mobilité, véhicules"),
    SousCategorie("velo", "Vélo", "Mobilité, véhicules"),
    SousCategorie("pneu", "Pneu", "Mobilité, véhicules"),
    SousCategorie(
        "batterie_de_voitures_pour_demarrage",
        "Batteries de voitures (SLI)",
        "Mobilité, véhicules",
    ),
    SousCategorie(
        "batteries_de_mtl",
        "Batteries de moyens de transport légers",
        "Mobilité, véhicules",
    ),
    SousCategorie(
        "jels_mobilite_electrique", "JELS – Mobilité électrique", "Mobilité, véhicules"
    ),
    # Vêtement, textile, mode
    SousCategorie("vetement", "Vêtement", "Vêtement, textile, mode"),
    SousCategorie("chaussures", "Chaussures", "Vêtement, textile, mode"),
    SousCategorie("linge_de_maison", "Linge de maison", "Vêtement, textile, mode"),
    SousCategorie(
        "decorations_textiles_elements_d_ameublement",
        "Décoration textile (ameublement)",
        "Vêtement, textile, mode",
    ),
    SousCategorie("maroquinerie", "Maroquinerie", "Vêtement, textile, mode"),
    SousCategorie("bijou_et_montre", "Bijou et montre", "Vêtement, textile, mode"),
    SousCategorie(
        "lunettes_de_vue_aides_techniques", "Lunettes de vue", "Vêtement, textile, mode"
    ),
    # Mobilier, ameublement, décoration
    SousCategorie("meuble", "Meuble", "Mobilier, ameublement, décoration"),
    SousCategorie(
        "sieges_elements_d_ameublement",
        "Sièges (ameublement)",
        "Mobilier, ameublement, décoration",
    ),
    SousCategorie(
        "literie_elements_d_ameublement",
        "Literie (ameublement)",
        "Mobilier, ameublement, décoration",
    ),
    SousCategorie(
        "rembourres_d_assise_ou_de_couchage_elements_d_ameublement",
        "Rembourrés assise/couchage",
        "Mobilier, ameublement, décoration",
    ),
    SousCategorie("decoration", "Décoration", "Mobilier, ameublement, décoration"),
    SousCategorie(
        "accessoire_et_meuble_de_jardin",
        "Accessoire et meuble de jardin",
        "Mobilier, ameublement, décoration",
    ),
    # Loisirs, jeux, sport, livres
    SousCategorie("jouet", "Jouets et jeux", "Loisirs, jeux, sport, livres"),
    SousCategorie(
        "materiel_de_sport_hors_velo",
        "Matériel de sport (hors vélo)",
        "Loisirs, jeux, sport, livres",
    ),
    SousCategorie("livre", "Livre", "Loisirs, jeux, sport, livres"),
    SousCategorie(
        "papiers_graphiques", "Papier graphique", "Loisirs, jeux, sport, livres"
    ),
    SousCategorie("papeterie", "Papèterie", "Loisirs, jeux, sport, livres"),
    # Bricolage, outillage, jardinage
    SousCategorie(
        "outil_de_bricolage_et_jardinage",
        "Outil de bricolage et jardinage",
        "Bricolage, outillage, jardinage",
    ),
    SousCategorie(
        "abj_electrique",
        "Outil de bricolage et jardinage électrique",
        "Bricolage, outillage, jardinage",
    ),
    SousCategorie(
        "abj_outillage_du_peintre_usage",
        "Outillage du peintre usagé",
        "Bricolage, outillage, jardinage",
    ),
    SousCategorie(
        "machines_et_appareils_motorises_thermiques",
        "Machines et appareils motorisés thermiques",
        "Bricolage, outillage, jardinage",
    ),
    # Cuisine, vaisselle
    SousCategorie("poele_casserole", "Poêle et casserole", "Cuisine, vaisselle"),
    SousCategorie("vaisselle", "Vaisselle", "Cuisine, vaisselle"),
    # Bébé, santé
    SousCategorie("puericulture", "Puériculture", "Bébé, santé"),
    SousCategorie("materiel_medical", "Matériel médical", "Bébé, santé"),
    SousCategorie("medicaments", "Médicaments non utilisés", "Bébé, santé"),
    SousCategorie(
        "dasri", "DASRI – Déchets de soins à risque infectieux", "Bébé, santé"
    ),
    # Énergie, batteries
    SousCategorie(
        "batteries_et_piles_portables",
        "Batteries & piles portables",
        "Énergie, batteries",
    ),
    SousCategorie(
        "panneaux_photovoltaiques", "Panneaux photovoltaïques", "Énergie, batteries"
    ),
    # Bâtiment, matériaux de construction (PMCB)
    SousCategorie(
        "bois_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Bois (bâtiment)",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "huisseries_produits_et_materiaux_de_construction_du_batiment",
        "Huisseries",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "laine_de_roche_produits_et_materiaux_de_construction_du_batiment",
        "Laine de roche",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "laine_de_verre_produits_et_materiaux_de_construction_du_batiment",
        "Laine de verre",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "metal_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Métal (bâtiment)",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "platre_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Plâtre",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "beton_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Béton",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "plastiques_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Plastiques (bâtiment)",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "melange_d_inertes_produits_et_materiaux_de_construction_du_batiment",
        "Mélange d'inertes",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "membranes_bitumineuses_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Membranes bitumineuses",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "dechets_dangereux_de_pmcb_produits_et_materiaux_de_construction_du_batiment",
        "Déchets dangereux du bâtiment",
        "Bâtiment, PMCB",
    ),
    SousCategorie(
        "materiau_du_batiment_reemployable",
        "Matériau du bâtiment réemployable",
        "Bâtiment, PMCB",
    ),
    SousCategorie("autres_pmcb", "Autres PMCB", "Bâtiment, PMCB"),
    # Produits chimiques, dangereux
    SousCategorie(
        "dechets_de_produits_chimiques",
        "Déchets de produits chimiques",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "dechets_de_produits_chimiques_basiques",
        "Produits chimiques – basiques",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "dechets_de_produits_chimiques_acides",
        "Produits chimiques – acides",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "produits_chimiques_solvants",
        "Produits chimiques – solvants",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "dechets_de_peintures_vernis_encres_et_colles_produits_chimiques",
        "Peintures, vernis, encres, colles",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "dechets_phytosanitaires_menagers_produits_chimiques",
        "Déchets phytosanitaires ménagers",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "huile_alimentaire", "Huile alimentaire", "Produits chimiques, dangereux"
    ),
    SousCategorie(
        "huiles_lubrifiantes", "Huiles lubrifiantes", "Produits chimiques, dangereux"
    ),
    SousCategorie(
        "petits_appareils_extincteurs",
        "Petits appareils extincteurs",
        "Produits chimiques, dangereux",
    ),
    SousCategorie(
        "produits_pyrotechniques",
        "Produits pyrotechniques",
        "Produits chimiques, dangereux",
    ),
    # Emballages
    SousCategorie("emballage_carton", "Emballage en carton", "Emballages"),
    SousCategorie("emballage_verre", "Emballage en verre", "Emballages"),
    SousCategorie("emballage_metal", "Emballage en métal", "Emballages"),
    SousCategorie("emballage_plastique", "Emballage en plastique", "Emballages"),
    SousCategorie("bouteilles_plastique", "Bouteille plastique", "Emballages"),
    SousCategorie(
        "autres_emballages_menagers", "Emballages ménagers multimatériaux", "Emballages"
    ),
    SousCategorie("emballage_reemployable", "Emballage réemployable", "Emballages"),
    SousCategorie("bouchons_en_liege", "Bouchons en liège", "Emballages"),
    # Biodéchets, déchets verts, divers
    SousCategorie(
        "biodechets", "Déchets alimentaires", "Biodéchets, déchets verts, divers"
    ),
    SousCategorie(
        "dechets_verts", "Déchets verts", "Biodéchets, déchets verts, divers"
    ),
    SousCategorie("palette", "Palette", "Biodéchets, déchets verts, divers"),
    SousCategorie(
        "encombrants_menagers_divers",
        "Encombrants ménagers divers",
        "Biodéchets, déchets verts, divers",
    ),
)

SOUS_CATEGORIES_BY_CODE: dict[str, SousCategorie] = {
    sc.code: sc for sc in SOUS_CATEGORIES
}


# TODO : load actions from database
def filter_actions(query: str | None) -> list[Action]:
    if not query:
        return list(ACTIONS)
    needle = query.lower()
    return [
        a
        for a in ACTIONS
        if needle in a.code.lower()
        or needle in a.libelle.lower()
        or needle in a.description.lower()
    ]


# TODO : load sous-categories from database
def filter_sous_categories(query: str | None) -> list[SousCategorie]:
    if not query:
        return list(SOUS_CATEGORIES)
    needle = query.lower()
    return [
        sc
        for sc in SOUS_CATEGORIES
        if needle in sc.code.lower()
        or needle in sc.libelle.lower()
        or needle in sc.groupe.lower()
    ]
