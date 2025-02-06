from scripts.deduplication.tasks.db_manage_parent import parent_id_generate


def test_parent_id_generate():
    uuid1 = parent_id_generate(["a", "b", "c"])
    uuid2 = parent_id_generate(["a", "c", "b"])
    uuid3 = parent_id_generate(["b", "a", "c"])

    assert uuid1 == uuid2 == uuid3, "UUID générés déterministes et ordre-insensibles"
