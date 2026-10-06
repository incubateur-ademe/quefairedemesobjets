"""Converting the first row of cards into a consignes grid, by the rules of
the spec: deterministic, and the text moves untouched."""

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from wagtail.models import PageLogEntry, Site

from qfdmd.consignes_migration import (
    apply_plan,
    badge_texts,
    first_row_of_cards,
    generate_on_deploy,
    normalise,
    plan_conversion,
)
from qfdmd.models import LieuDeDepot
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db

REPAIR_HTML = "<p>Un <b>réparateur</b> près de chez vous, &amp; c'est tout.</p>"


def badges(*texts):
    """Badges as the CMS stores them: a `badges_list` stream of `badge`."""
    return [
        {
            "type": "badges_list",
            "value": [
                {"type": "badge", "value": {"text": t, "color": "new"}} for t in texts
            ],
        }
    ]


def card(title, description, *badge_texts, page_id=None, id=None):
    return {
        "type": "card",
        "id": id or f"card-{title}",
        "value": {
            "title": title,
            "description": description,
            "link": {"link_type": "page", "page": page_id} if page_id else {},
            "top_detail_badges_tags": badges(*badge_texts),
        },
    }


def tile(title):
    return {"type": "tile", "id": f"tile-{title}", "value": {"title": title}}


def objet_page(page_id=None, **kwargs):
    """An objet fiche as the live ones are laid out: an intro heading, the
    row of three cards, the map, then advice tiles and a card that is not a
    consigne ("Des emballages pensés pour être réemployés")."""
    body = [
        {
            "type": "paragraph",
            "id": "intro",
            "value": "<h2>Une chaise, ça se garde.</h2>",
        },
        {
            "type": "item_grid",
            "id": "grid",
            "value": {
                "column_width": "4",
                "items": [
                    card(
                        "Réparer",
                        REPAIR_HTML,
                        "Réparable",
                        "% Bonus Réparation",
                        page_id=page_id,
                    ),
                    card("Donner ou revendre", "<p>Donnez-la</p>", "Bon état"),
                    card("Déposer", "<p>En déchèterie</p>", "Mauvais état"),
                ],
            },
        },
        {"type": "html", "id": "html", "value": "<div></div>"},
        {"type": "carte", "id": "carte", "value": {"carte_config": None}},
        {
            "type": "item_grid",
            "id": "tiles",
            "value": {"column_width": "4", "items": [tile("Privilégier le vrac")]},
        },
        card(
            "Des emballages pensés pour être réemployés", "<p>Réemploi</p>", id="later"
        ),
        {"type": "paragraph", "id": "outro", "value": "<p>Et voilà.</p>"},
    ]
    return ProduitPageFactory(body=json.dumps(body), live=True, **kwargs)


def dechet_page(**kwargs):
    """Emballages en verre: four cards, lieux as badges, a réemploi one."""
    body = [
        {"type": "paragraph", "id": "intro", "value": "<h2>Les emballages</h2>"},
        {
            "type": "item_grid",
            "id": "grid",
            "value": {
                "column_width": "6",
                "items": [
                    card("✅ Déposer les contenants", "<p>…</p>", "Conteneur à verre"),
                    card("⚠️ Trier séparément", "<p>…</p>", "BAC DE TRI"),
                    card(
                        "🚫 Les autres objets",
                        "<p>…</p>",
                        "Ordures ménagères",
                        "Déchèterie",
                    ),
                    card(
                        "💡 Bouteilles réemployables",
                        "<p>Rapportez-les au magasin</p>",
                        "Réemploi",
                    ),
                ],
            },
        },
        {"type": "html", "id": "html", "value": ""},
    ]
    return ProduitPageFactory(
        body=json.dumps(body), live=True, usage_unique=True, **kwargs
    )


def draft_types(page):
    return [b.block_type for b in page.get_latest_revision_as_object().body]


def draft_consignes(page):
    return [
        c.value
        for b in page.get_latest_revision_as_object().body
        if b.block_type == "consignes"
        for c in b.value["consignes"].bound_blocks
    ]


class TestFirstRowOfCards:
    def test_the_row_is_the_cards_after_the_intro_and_before_the_map(self):
        cards = first_row_of_cards(objet_page())

        assert [(c["block_id"], c["item_index"]) for c in cards] == [
            ("grid", 0),
            ("grid", 1),
            ("grid", 2),
        ]
        assert cards[0]["card"]["title"] == "Réparer"

    def test_a_lone_card_then_a_grid_form_one_row(self):
        """Cosmétique: a card "Trier les emballages vides" then a grid,
        before the map."""
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {"type": "paragraph", "id": "intro", "value": "<h2>Où</h2>"},
                    card("Trier les emballages vides", "<p>…</p>", id="lone"),
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {"items": [card("Déposer", "<p>…</p>")]},
                    },
                    {"type": "html", "id": "html", "value": ""},
                    card("Des cosmétiques plus sains", "<p>…</p>", id="later"),
                ]
            )
        )

        assert [(c["block_id"], c["item_index"]) for c in first_row_of_cards(page)] == [
            ("lone", None),
            ("grid", 0),
        ]

    def test_tiles_and_later_cards_are_not_in_the_row(self):
        ids = {c["block_id"] for c in first_row_of_cards(objet_page())}

        assert "tiles" not in ids
        assert "later" not in ids

    def test_a_page_without_cards_has_no_row(self):
        page = ProduitPageFactory(
            body=json.dumps([{"type": "paragraph", "id": "p", "value": "<p>x</p>"}])
        )

        assert first_row_of_cards(page) == []


class TestNormalise:
    def test_badges_typed_by_hand_meet_the_rules(self):
        assert normalise("BAC DE TRI") == "bac de tri"
        assert normalise("✅ Déposer les contenants") == "deposer les contenants"
        assert normalise("% Bonus Réparation") == "bonus reparation"
        assert normalise("Réparable") == "reparable"

    def test_badge_texts_reads_badges_and_tags(self):
        value = {
            "top_detail_badges_tags": badges("Bon état")
            + [
                {
                    "type": "tags_list",
                    "value": [{"type": "tag", "value": {"label": "Neuf"}}],
                }
            ]
        }

        assert badge_texts(value) == ["Bon état", "Neuf"]


class TestPlanForObjets:
    def test_etat_gestes_and_bonus_follow_the_badges(self):
        plan = plan_conversion(objet_page())

        assert not plan.unresolved
        reparer, donner, deposer = (c.value for c in plan.consignes)
        assert (reparer["etat"], reparer["gestes"], reparer["bonus_reparation"]) == (
            "reparable",
            ["reparer"],
            True,
        )
        assert (donner["etat"], donner["gestes"], donner["bonus_reparation"]) == (
            "bon_etat",
            ["donner", "revendre", "preter", "louer"],
            False,
        )
        assert (deposer["etat"], deposer["gestes"]) == ("mauvais_etat", ["trier"])
        assert all(c.value["lieu_de_depot"] is None for c in plan.consignes)

    def test_the_title_gives_the_etat_when_there_is_no_badge_and_says_so(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {
                            "items": [
                                card("Réparer", "<p>…</p>"),
                                card("Donner ou revendre", "<p>…</p>"),
                                card("Déposer", "<p>…</p>"),
                            ]
                        },
                    }
                ]
            )
        )

        plan = plan_conversion(page)

        assert [c.value["etat"] for c in plan.consignes] == [
            "reparable",
            "bon_etat",
            "mauvais_etat",
        ]
        assert len(plan.notes) == 3
        assert "état déduit du titre" in plan.notes[0]

    def test_a_lieu_badge_on_an_objet_fiche_stops_the_card(self):
        """Piles, Ampoules… are flagged objet but talk like déchets: no
        guessed état, the editor is told to check « À usage unique »."""
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {
                            "items": [
                                card(
                                    "Les piles boutons", "<p>…</p>", "Point de collecte"
                                ),
                                card(
                                    "Déposer les ampoules",
                                    "<p>en point de collecte</p>",
                                ),
                            ]
                        },
                    }
                ]
            )
        )

        plan = plan_conversion(page)

        assert plan.consignes == []
        assert [u.titre for u in plan.unresolved] == [
            "Les piles boutons",
            "Déposer les ampoules",
        ]
        assert all("À usage unique" in u.reason for u in plan.unresolved)

    def test_a_card_without_etat_stays_and_is_reported(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {
                            "items": [
                                card(
                                    "Les piles boutons", "<p>…</p>", "Point de collecte"
                                ),
                                card("Réparer", "<p>…</p>", "Réparable"),
                            ]
                        },
                    }
                ]
            )
        )

        plan = plan_conversion(page)

        assert [c.value["titre"] for c in plan.consignes] == ["Réparer"]
        assert [(u.titre, u.reason) for u in plan.unresolved] == [
            (
                "Les piles boutons",
                "badge de lieu de dépôt sur une fiche objet : la fiche est-elle un"
                " déchet (« À usage unique ») ?",
            )
        ]


class TestPlanForDechets:
    def test_lieu_from_the_first_matching_badge_and_trier(self):
        plan = plan_conversion(dechet_page())

        lieux = [
            LieuDeDepot.objects.get(pk=c.value["lieu_de_depot"]).code
            for c in plan.consignes
        ]
        assert lieux == [
            "conteneur_a_verre",
            "bac_de_tri",
            "ordures_menageres",
            "reemploi",
        ]
        assert [c.value["gestes"] for c in plan.consignes][:3] == [["trier"]] * 3
        assert all(c.value["etat"] is None for c in plan.consignes)
        assert not plan.unresolved

    def test_rapporter_when_the_card_says_so(self):
        plan = plan_conversion(dechet_page())

        assert plan.consignes[3].value["gestes"] == ["rapporter"]

    def test_an_etat_badge_on_a_dechet_fiche_stops_the_card(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {"items": [card("Réparer", "<p>…</p>", "Réparable")]},
                    }
                ]
            ),
            usage_unique=True,
        )

        plan = plan_conversion(page)

        assert plan.consignes == []
        assert "décocher « À usage unique »" in plan.unresolved[0].reason

    def test_an_unknown_badge_is_noted_but_the_card_still_converts(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {"items": [card("Brûler", "<p>…</p>", "Cheminée")]},
                    }
                ]
            ),
            usage_unique=True,
        )

        plan = plan_conversion(page)

        assert plan.consignes[0].value["lieu_de_depot"] is None
        assert plan.consignes[0].value["gestes"] == ["trier"]
        assert "Cheminée" in plan.notes[0]


class TestApplyPlan:
    def test_cards_move_into_a_draft_grid_word_for_word(self):
        target = ProduitPageFactory(parent=None, title="Bonus réparation")
        page = objet_page(page_id=target.pk)

        count = apply_plan(page, plan_conversion(page))

        assert count == 3
        # The live page has not changed: the grid lives in the draft.
        page.refresh_from_db()
        assert [b.block_type for b in page.body][:3] == [
            "paragraph",
            "item_grid",
            "html",
        ]
        # The emptied grid is gone, the new one takes its place and width,
        # the rest of the page is untouched.
        assert draft_types(page) == [
            "paragraph",
            "consignes",
            "html",
            "carte",
            "item_grid",
            "card",
            "paragraph",
        ]
        grid = page.get_latest_revision_as_object().body[1].value
        assert grid["column_width"] == "4"
        reparer = draft_consignes(page)[0]
        assert reparer["titre"] == "Réparer"
        assert str(reparer["contenu"]) == REPAIR_HTML
        assert reparer["lien"].pk == target.pk
        assert PageLogEntry.objects.filter(
            page=page, action="qfdmd.generate_consignes"
        ).exists()

    def test_the_grid_keeps_the_width_of_the_original(self):
        page = dechet_page()

        apply_plan(page, plan_conversion(page))

        grid = page.get_latest_revision_as_object().body[1].value
        assert grid["column_width"] == "6"
        assert draft_consignes(page)[3]["lieu_de_depot"].code == "reemploi"

    def test_a_partly_converted_grid_keeps_its_other_cards(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {
                            "column_width": "6",
                            "items": [
                                card(
                                    "Les piles boutons", "<p>…</p>", "Point de collecte"
                                ),
                                card("Réparer", "<p>…</p>", "Réparable"),
                            ],
                        },
                    }
                ]
            )
        )

        apply_plan(page, plan_conversion(page))

        assert draft_types(page) == ["consignes", "item_grid"]
        left = page.get_latest_revision_as_object().body[1].value["items"]
        assert [item.value["title"] for item in left] == ["Les piles boutons"]

    def test_lone_cards_get_a_width_from_their_number(self):
        page = ProduitPageFactory(
            body=json.dumps(
                [
                    card("Trier", "<p>…</p>", "Bac de tri", id="a"),
                    card("Vider", "<p>…</p>", "Bac de tri", id="b"),
                    {"type": "html", "id": "html", "value": ""},
                ]
            ),
            usage_unique=True,
        )

        apply_plan(page, plan_conversion(page))

        grid = page.get_latest_revision_as_object().body[0].value
        assert grid["column_width"] == "6"

    def test_nothing_usable_writes_no_draft(self):
        page = ProduitPageFactory(
            body=json.dumps([{"type": "paragraph", "id": "p", "value": "<p>x</p>"}])
        )
        before = page.revisions.count()

        assert apply_plan(page, plan_conversion(page)) == 0
        assert page.revisions.count() == before

    def test_the_same_page_converts_the_same_way_twice(self):
        """Deterministic: two plans of one page are identical."""
        page = objet_page()

        first = plan_conversion(page)
        second = plan_conversion(page)

        assert [c.value for c in first.consignes] == [c.value for c in second.consignes]


class TestAdminAction:
    @pytest.fixture
    def page(self):
        root = Site.objects.get(is_default_site=True).root_page
        return objet_page(parent=root)

    def test_get_shows_a_confirmation(self, admin_client, page):
        response = admin_client.get(reverse("generate_consignes", args=[page.pk]))

        assert response.status_code == 200
        assert "brouillon" in response.content.decode()

    def test_post_converts_into_a_draft_and_returns_to_the_editor(
        self, admin_client, page
    ):
        response = admin_client.post(
            reverse("generate_consignes", args=[page.pk]), follow=True
        )

        assert response.redirect_chain[-1][0] == reverse(
            "wagtailadmin_pages:edit", args=[page.pk]
        )
        assert "3 consigne(s) générée(s)" in response.content.decode()
        page.refresh_from_db()
        assert len(page.get_latest_revision_as_object().consignes) == 3

    def test_post_reports_the_cards_left_behind(self, admin_client):
        root = Site.objects.get(is_default_site=True).root_page
        page = ProduitPageFactory(
            parent=root,
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {"items": [card("Les piles boutons", "<p>…</p>")]},
                    }
                ]
            ),
        )

        response = admin_client.post(
            reverse("generate_consignes", args=[page.pk]), follow=True
        )

        content = response.content.decode()
        assert "Aucune carte de la première rangée" in content
        assert "Les piles boutons" in content

    def test_the_action_is_in_the_page_menu(self, admin_client, page):
        content = admin_client.get(
            reverse("wagtailadmin_pages:edit", args=[page.pk])
        ).content.decode()

        assert reverse("generate_consignes", args=[page.pk]) in content


def live_types(page):
    page.refresh_from_db()
    return [b.block_type for b in page.body]


def generate():
    call_command("generate_consignes", stdout=StringIO())


class TestGenerateOnDeploy:
    """`manage.py generate_consignes`, run by every deploy: publishes the grid
    of the live fiches that convert cleanly, leaves a draft for the others,
    and does nothing on a fiche that already has one."""

    def test_a_clean_live_fiche_is_published_with_its_grid(self):
        page = objet_page()

        generate()

        assert live_types(page)[:2] == ["paragraph", "consignes"]
        assert not page.has_unpublished_changes

    def test_a_second_deploy_is_a_no_op(self):
        page = objet_page()
        generate()
        before = page.revisions.count()

        generate()

        assert page.revisions.count() == before

    def test_a_fiche_that_is_not_live_is_left_alone(self):
        page = objet_page()
        page.live = False
        page.save()

        generate()

        assert "consignes" not in live_types(page)
        assert page.revisions.count() == 0

    def test_a_fiche_with_an_unresolved_card_gets_a_draft_only(self):
        page = ProduitPageFactory(
            live=True,
            body=json.dumps(
                [
                    {
                        "type": "item_grid",
                        "id": "grid",
                        "value": {
                            "items": [
                                card("Les piles", "<p>…</p>", "Point de collecte"),
                                card("Réparer", "<p>…</p>", "Réparable"),
                            ]
                        },
                    }
                ]
            ),
        )

        generate()
        generate()

        assert "consignes" not in live_types(page)
        assert page.has_unpublished_changes
        assert "consignes" in draft_types(page)
        assert page.revisions.count() == 1

    def test_a_pending_editor_draft_is_kept_and_converted_too(self):
        page = objet_page(title="Chaise")
        page.title = "Chaise (relue)"
        page.save_revision()

        generate()

        page.refresh_from_db()
        assert page.title == "Chaise"
        assert "consignes" in live_types(page)
        draft = page.get_latest_revision_as_object()
        assert page.has_unpublished_changes
        assert draft.title == "Chaise (relue)"
        assert "consignes" in [b.block_type for b in draft.body]

    def test_a_pending_draft_already_holding_a_grid_is_a_no_op(self):
        page = objet_page()
        apply_plan(page, plan_conversion(page))  # the admin action's draft
        page.refresh_from_db()
        before = page.revisions.count()

        generate()

        assert "consignes" not in live_types(page)
        assert page.revisions.count() == before

    def test_a_failing_fiche_does_not_stop_the_others(self, mocker):
        broken, page = objet_page(), objet_page()
        real = generate_on_deploy

        def fail_on_broken(p):
            if p.pk == broken.pk:
                raise ValueError("boom")
            return real(p)

        mocker.patch(
            "qfdmd.management.commands.generate_consignes.generate_on_deploy",
            side_effect=fail_on_broken,
        )

        generate()

        assert "consignes" not in live_types(broken)
        assert "consignes" in live_types(page)
