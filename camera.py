# camera.py
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

class Camera:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}/iAPI/apps.cgi"
        
        # Initialize count attributes to store entered and exited counts
        self.entered = 0
        self.exited = 0

    def send_request(self):
        """Send a GET request to the API to retrieve the person count data."""
        try:
            response = requests.get(
                f"{self.base_url}?action=read&path=personcount.default", 
                auth=HTTPBasicAuth(self.username, self.password)
            )
            response.raise_for_status()  # Ensure we catch any HTTP errors
            print(f"API call to {self.ip} succeeded.")
            return response.text
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred for {self.ip}: {req_err}")
        return ""

    def get_counts(self):
        """Retrieve and store the in and out counts from the API."""
        try:
            response_text = self.send_request()
            if response_text.startswith("Content-Type: text/xml"):
                # Remove Content-Type header if present
                response_text = response_text.split("\n", 1)[1].strip()

            root = ET.fromstring(response_text)
            in_count = root.find(".//parameter[@name='inCountTotal']").text if root.find(".//parameter[@name='inCountTotal']") is not None else "0"
            out_count = root.find(".//parameter[@name='outCountTotal']").text if root.find(".//parameter[@name='outCountTotal']") is not None else "0"
            
            # Update the instance attributes with retrieved counts
            self.entered = int(in_count)
            self.exited = int(out_count)
            currently_in = self.entered - self.exited  # Calculate currently in as entered - exited

            # Debugging: Confirm data is fetched and processed correctly
            print(f"Camera {self.ip} - Entered: {self.entered}, Exited: {self.exited}, Currently In: {currently_in}")
            return self.entered, self.exited, currently_in

        except ET.ParseError as parse_err:
            print(f"XML parse error for {self.ip}: {parse_err}")
            return 0, 0, 0

    def reset_counts(self):
        """Send a POST request to reset the camera counts."""
        reset_xml = '<app name="personcount"><instance name="default"><parameter name="manualReset">true</parameter></instance></app>'
        try:
            response = requests.post(
                f"{self.base_url}?action=Update", 
                auth=HTTPBasicAuth(self.username, self.password), 
                data=reset_xml, 
                headers={"Content-Type": "text/xml"}
            )
            response.raise_for_status()
            print(f"Successfully reset counts for camera at {self.ip}")
            # Reset local count attributes as well
            self.entered = 0
            self.exited = 0
        except requests.exceptions.RequestException as req_err:
            print(f"Failed to reset counts for camera at {self.ip}: {req_err}")