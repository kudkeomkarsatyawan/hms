import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:5000"

class HospitalSystemTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _login(self, username, password):
        self.driver.get(f"{BASE_URL}/login")
        self.wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()

    def get_flash_message(self):
        try:
            return self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "flash"))).text
        except:
            return ""

    def test_01_login_valid(self):
        self._login("admin", "password")
        self.assertTrue(self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text == "Dashboard")

    def test_02_login_invalid(self):
        self._login("wronguser", "wrongpass")
        self.assertIn("Invalid username or password", self.get_flash_message())

    def test_03_register_patient_valid(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Register Patient"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "name"))).send_keys("John Doe")
        self.driver.find_element(By.ID, "age").send_keys("30")
        self.driver.find_element(By.ID, "gender").send_keys("Male")
        self.driver.find_element(By.ID, "contact").send_keys("1234567890")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "John Doe"))
        self.assertIn("John Doe", self.driver.page_source)

    def test_04_register_patient_missing_field(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Register Patient"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "age"))).send_keys("40")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.assertIn("Name is required", self.get_flash_message())

    def test_05_search_patient_existing(self):
        self._login("admin", "password")
        self.wait.until(EC.presence_of_element_located((By.NAME, "patient_id"))).send_keys("1")
        self.driver.find_element(By.XPATH, "//form/button[text()='Search']").click()
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "h2"), "Patient Details"))
        self.assertIn("Patient Details", self.driver.page_source)
        self.assertIn("John Doe", self.driver.page_source)

    def test_06_update_patient(self):
        self._login("admin", "password")
        self.driver.get(f"{BASE_URL}/patient/update/1")
        contact_field = self.wait.until(EC.presence_of_element_located((By.ID, "contact")))
        contact_field.clear()
        contact_field.send_keys("0987654321")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "0987654321"))
        self.assertIn("0987654321", self.driver.page_source)

    def test_07_book_appointment_available(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Book Appointment"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "time_slot"))).send_keys("10:00 AM")
        self.driver.find_element(By.ID, "patient_name").send_keys("Test Patient")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.assertIn("Appointment confirmed", self.get_flash_message())

    def test_08_book_appointment_taken(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Book Appointment"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "time_slot"))).send_keys("10:00 AM")
        self.driver.find_element(By.ID, "patient_name").send_keys("Another Patient")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.assertIn("Slot not available", self.get_flash_message())

    def test_09_generate_bill_correct(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Generate Bill"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "consultation"))).click()
        self.driver.find_element(By.ID, "lab_tests").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        self.assertIn("total amount: 2000", self.get_flash_message())

    def test_10_generate_bill_no_service(self):
        self._login("admin", "password")
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Generate Bill"))).click()
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn"))).click()
        self.assertIn("No service selected", self.get_flash_message())

    def test_11_delete_patient(self):
        self._login("admin", "password")
        # Create a patient to delete
        self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Register Patient"))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, "name"))).send_keys("PatientToDelete")
        self.driver.find_element(By.ID, "age").send_keys("50")
        self.driver.find_element(By.ID, "gender").send_keys("Female")
        self.driver.find_element(By.ID, "contact").send_keys("5555555555")
        self.driver.find_element(By.CSS_SELECTOR, ".btn").click()
        
        # Find and delete the patient
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'PatientToDelete'))
        delete_form = self.driver.find_element(By.XPATH, "//td[text()='PatientToDelete']/following-sibling::td/form")
        delete_form.find_element(By.CSS_SELECTOR, ".btn-danger").click()
        
        self.assertIn("deleted successfully", self.get_flash_message())
        self.wait.until(EC.invisibility_of_element_located((By.XPATH, "//td[text()='PatientToDelete']")))
        self.assertNotIn("PatientToDelete", self.driver.page_source)

if __name__ == "__main__":
    unittest.main(verbosity=2)
