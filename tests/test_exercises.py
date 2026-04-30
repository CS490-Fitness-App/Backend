# GET /exercises — empty database should return an empty list, not an error.
def test_list_exercises_empty(client):
    resp = client.get("/exercises")
    assert resp.status_code == 200
    assert resp.json() == []


# GET /exercises/{id} — requesting a non-existent ID should return 404, not crash.
def test_get_exercise_not_found(client):
    resp = client.get("/exercises/9999")
    assert resp.status_code == 404


# GET /exercises/meta/options — with no lookup data seeded, all three lists should be empty.
def test_get_meta_empty(client):
    resp = client.get("/exercises/meta/options")
    assert resp.status_code == 200
    data = resp.json()
    assert data["categories"] == []
    assert data["experience_levels"] == []
    assert data["muscle_groups"] == []


# GET /exercises/meta/options — verifies that seeded categories, levels, and muscle groups
# are returned correctly so the frontend filter dropdowns have data to display.
def test_get_meta_seeded(client, seed_lookup):
    resp = client.get("/exercises/meta/options")
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["name"] == "Strength" for c in data["categories"])
    assert any(l["name"] == "Beginner" for l in data["experience_levels"])
    assert any(m["name"] == "Chest" for m in data["muscle_groups"])


# POST /exercises: checks the response contains the resolved names
# (category, experience level, muscle groups) not just the raw IDs.
def test_create_exercise(client, seed_lookup):
    resp = client.post("/exercises", json={
        "name": "Bench Press",
        "category_id": seed_lookup["category_id"],
        "experience_level_id": seed_lookup["level_id"],
        "muscle_group_ids": [seed_lookup["muscle_id"]],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Bench Press"
    assert data["category"] == "Strength"
    assert data["experience_level"] == "Beginner"
    assert "Chest" in data["muscle_groups"]


# POST /exercises twice with the same name. the second request must be rejected with 409
# because exercise names have a unique constraint.
def test_create_exercise_duplicate_name(client, seed_lookup):
    payload = {"name": "Squat", "category_id": seed_lookup["category_id"], "muscle_group_ids": []}
    client.post("/exercises", json=payload)
    resp = client.post("/exercises", json=payload)
    assert resp.status_code == 409


# POST /exercises with a category_id that doesn't exist: the route validates foreign keys
# manually and must return 404 rather than letting the DB throw an integrity error.
def test_create_exercise_invalid_category(client):
    resp = client.post("/exercises", json={
        "name": "Pull Up",
        "category_id": 9999,
        "muscle_group_ids": [],
    })
    assert resp.status_code == 404


# POST /exercises with a muscle_group_id that doesn't exist: same validation as category;
# each muscle group ID is checked individually and an invalid one returns 404.
def test_create_exercise_invalid_muscle_group(client, seed_lookup):
    resp = client.post("/exercises", json={
        "name": "Dumbbell Curl",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [9999],
    })
    assert resp.status_code == 404


# GET /exercises?name=dead: partial, case-insensitive name filter should return
# only exercises whose name contains the search term.
def test_list_exercises_filter_by_name(client, seed_lookup):
    client.post("/exercises", json={
        "name": "Deadlift",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    resp = client.get("/exercises?name=dead")
    assert resp.status_code == 200
    assert any(e["name"] == "Deadlift" for e in resp.json())


# GET /exercises?category_id=N: category filter should return at least the one exercise
# created for that category, confirming the filter is applied correctly.
def test_list_exercises_filter_by_category(client, seed_lookup):
    client.post("/exercises", json={
        "name": "Leg Press",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    resp = client.get(f"/exercises?category_id={seed_lookup['category_id']}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# PUT /exercises/{id}: checks that an existing exercise's name is updated and the new
# value is reflected in the response.
def test_update_exercise(client, seed_lookup):
    create_resp = client.post("/exercises", json={
        "name": "Overhead Press",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    ex_id = create_resp.json()["exercise_id"]

    update_resp = client.put(f"/exercises/{ex_id}", json={
        "name": "Standing Overhead Press",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Standing Overhead Press"


# PUT /exercises/{id} with a non-existent ID: update on a missing resource should
# return 404, not silently succeed or crash.
def test_update_exercise_not_found(client, seed_lookup):
    resp = client.put("/exercises/9999", json={
        "name": "Ghost Exercise",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    assert resp.status_code == 404


# DELETE /exercises/{id}: verifies the exercise is removed by checking that a subsequent
# GET on the same ID returns 404.
def test_delete_exercise(client, seed_lookup):
    create_resp = client.post("/exercises", json={
        "name": "Romanian Deadlift",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    ex_id = create_resp.json()["exercise_id"]

    assert client.delete(f"/exercises/{ex_id}").status_code == 204
    assert client.get(f"/exercises/{ex_id}").status_code == 404


# DELETE /exercises/{id} with a non-existent ID: should return 404, not 500.
def test_delete_exercise_not_found(client):
    assert client.delete("/exercises/9999").status_code == 404


# POST /exercises with a valid category but an experience_level_id that doesn't exist:
# the route checks each FK manually and must return 404 before touching the DB.
def test_create_exercise_invalid_experience_level(client, seed_lookup):
    resp = client.post("/exercises", json={
        "name": "Cable Row",
        "category_id": seed_lookup["category_id"],
        "experience_level_id": 9999,
        "muscle_group_ids": [],
    })
    assert resp.status_code == 404


# GET /exercises?experience_level_id=N: filter by experience level should return only
# exercises tagged with that level, excluding untagged ones.
def test_list_exercises_filter_by_experience_level(client, seed_lookup):
    client.post("/exercises", json={
        "name": "Barbell Row",
        "category_id": seed_lookup["category_id"],
        "experience_level_id": seed_lookup["level_id"],
        "muscle_group_ids": [],
    })
    client.post("/exercises", json={
        "name": "Machine Row",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    resp = client.get(f"/exercises?experience_level_id={seed_lookup['level_id']}")
    assert resp.status_code == 200
    results = resp.json()
    assert any(e["name"] == "Barbell Row" for e in results)
    assert all(e["experience_level_id"] == seed_lookup["level_id"] for e in results)


# DELETE /exercises/{id} when the exercise is referenced by a workout plan: should return
# 409 to protect data integrity rather than cascade-deleting the plan silently.
def test_delete_exercise_in_use(client, seed_lookup, db):
    from models.workout import WorkoutPlan

    create_resp = client.post("/exercises", json={
        "name": "Incline Press",
        "category_id": seed_lookup["category_id"],
        "muscle_group_ids": [],
    })
    ex_id = create_resp.json()["exercise_id"]

    # Insert a WorkoutPlan row directly — SQLite skips FK enforcement so stub IDs are fine.
    db.add(WorkoutPlan(workout_id=1, exercise_id=ex_id, unit_id=1))
    db.flush()

    resp = client.delete(f"/exercises/{ex_id}")
    assert resp.status_code == 409
