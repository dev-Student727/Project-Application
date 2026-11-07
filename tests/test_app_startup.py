import unittest

from main import BarangayApp


class AppStartupTests(unittest.TestCase):
    def test_all_navigation_screens_are_registered(self):
        manager = BarangayApp().build()
        expected = {"StartUp", "login", "forgot_password", "sign_up", "resident_dashboard", "admin_dashboard"}
        self.assertEqual(set(manager.screen_names), expected)
        manager.current = "login"
        manager.current = "forgot_password"
        manager.get_screen("forgot_password").set_username("validation_user")
        self.assertEqual(manager.get_screen("forgot_password").username_input.text, "validation_user")


if __name__ == "__main__":
    unittest.main()
