import pathlib
import tempfile
import unittest

from database.store import BarangayStore


class AccountPersistenceTests(unittest.TestCase):
    def test_account_fetch_and_password_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            store = BarangayStore(pathlib.Path(folder) / "barangay.db")
            account_id = store.create_account(
                "Validation User",
                "validation@example.com",
                "09171234567",
                "1 Main Street, Barangay, City, Province",
                "resident",
                "Government-issued resident ID",
                "manual-id:validation",
                "OldPassword1",
                "validation_user",
                profile={
                    "birth_date": "1990-01-01",
                    "sex": "Male",
                    "civil_status": "Single",
                    "house_number": "1",
                    "street": "Main Street",
                    "barangay": "Barangay",
                    "city": "City",
                    "province": "Province",
                    "id_number": "validation",
                    "id_full_name": "Validation User",
                    "id_birth_date": "1990-01-01",
                    "id_sex": "Male",
                    "id_address": "1 Main Street Barangay City Province",
                    "id_issued_by": "Barangay",
                    "id_expiry": "N/A",
                },
            )
            store.update_account_status(account_id, application_verified=True)
            account = store.get_account_by_username("validation_user")
            self.assertEqual(account["id"], account_id)
            self.assertTrue(store.authenticate_account("validation_user", "OldPassword1"))
            self.assertIsNotNone(store.get_account_by_username("validation_user"))

            store.update_account_password(account_id, "NewPassword2")
            self.assertIsNone(store.authenticate_account("validation_user", "OldPassword1"))
            self.assertTrue(store.authenticate_account("validation_user", "NewPassword2"))


if __name__ == "__main__":
    unittest.main()
