import csv

from playwright.sync_api import expect


def test_added_expense_persists_after_reload(page, live_server):
    page.goto(live_server)
    page.get_by_placeholder("Amount", exact=True).fill("12.50")
    page.get_by_placeholder("Description", exact=True).fill("E2E lunch")
    page.get_by_role("combobox").select_option(label="Food & Dining")
    page.locator('input[name="date"]').fill("2026-01-15")

    page.get_by_role("button", name="Add", exact=True).click()

    expense = page.get_by_role("row").filter(has_text="E2E lunch")
    expect(expense).to_be_visible()

    page.reload()
    expect(expense.get_by_role("cell").nth(0)).to_have_text("2026-01-15")
    expect(expense.get_by_role("cell").nth(1)).to_have_text("$12.50")
    expect(expense.get_by_role("cell").nth(3)).to_have_text("Food & Dining")


def test_deleted_expense_stays_deleted(page, live_server):

    response = page.request.post(
        f"{live_server}/api/expenses",
        data={"amount": 8.75, "description": "Delete this expense"},
    )
    assert response.status == 201

    kept = page.request.post(
        f"{live_server}/api/expenses",
        data={"amount": 15.00, "description": "Keep this expense"}
    )
    assert kept.status == 201

    page.goto(live_server)
    target = page.get_by_role("row").filter(has_text="Delete this expense")
    expect(target).to_be_visible()

    target.get_by_title("Delete", exact=True).click()

    expect(target).to_have_count(0)
    page.reload()
    expect(target).to_have_count(0)

    survivor = page.get_by_role("row").filter(has_text="Keep this expense")
    expect(survivor).to_be_visible()


def test_month_picker_changes_displayed_summary(page, live_server):

    january = page.request.post(
        f"{live_server}/api/expenses",
        data={"amount": 12.50, "category_id": 1, "date": "2026-01-15"},
    )
    assert january.status == 201

    february = page.request.post(
        f"{live_server}/api/expenses",
        data={"amount": 27.75, "category_id": 1, "date": "2026-02-15"},
    )
    assert february.status == 201

    page.goto(live_server)
    page.get_by_role("link", name="Summary", exact=True).click()
    page.locator('input[name="month"]').fill("2026-01")
    page.get_by_role("button", name="Go", exact=True).click()

    total = page.locator(".grand-total strong")
    expect(total).to_have_text("$12.50")

    page.locator('input[name="month"]').fill("2026-02")
    page.get_by_role("button", name="Go", exact=True).click()
    expect(total).to_have_text("$27.75")


def test_export_link_downloads_expenses_csv(page, live_server, tmp_path):

    response = page.request.post(
        f"{live_server}/api/expenses",
        data={"amount": 9.50, "description": "Lunch, with coffee"}
    )
    assert response.status == 201

    page.goto(live_server)

    with page.expect_download() as download_info:
        page.get_by_role("link", name="Export CSV", exact=True).click()
    download = download_info.value

    assert download.suggested_filename == "expenses.csv"
    csv_path = tmp_path / "expenses.csv"
    download.save_as(csv_path)

    with csv_path.open(encoding="utf-8", newline="") as exported:
        rows = list(csv.DictReader(exported))
        assert len(rows) == 1
        assert rows[0]["Description"] == "Lunch, with coffee"
        assert rows[0]["Amount"] == "9.5"
