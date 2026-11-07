import pathlib
import tempfile
import unittest

from database.store import BarangayStore


class RequestSharingTests(unittest.TestCase):
    def test_resident_request_is_visible_to_admin_and_status_returns(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = pathlib.Path(folder) / "barangay.db"
            resident_store = BarangayStore(db_path)
            account_id = resident_store.create_account(
                "Request User", "request@example.com", "09171234567",
                "1 Main Street, Barangay, City, Province", "resident",
                "Government-issued resident ID", "manual-id:request",
                "Password1", "request_user",
                profile={"birth_date": "1990-01-01", "sex": "Male", "civil_status": "Single"},
            )
            request_no = resident_store.create_request(
                "Request User", "Barangay Clearance", "Employment", email="request@example.com",
                bypass_capacity=True, account_id=account_id,
            )

            admin_store = BarangayStore(db_path)
            admin_view = admin_store.list_requests()
            self.assertEqual(len(admin_view), 1)
            self.assertEqual(admin_view[0]["request_no"], request_no)
            admin_store.update_request(admin_view[0]["id"], status="Processing", note="Admin started processing")

            resident_view = resident_store.list_requests(account_id=account_id)
            self.assertEqual(resident_view[0]["status"], "Processing")
            self.assertEqual(resident_store.get_request_history(resident_view[0]["id"])[-1]["status"], "Processing")


if __name__ == "__main__":
    unittest.main()
