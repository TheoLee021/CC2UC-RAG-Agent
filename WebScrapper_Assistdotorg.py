import requests
from bs4 import BeautifulSoup
import re

class AssistScraper:
    def __init__(self, target_ucs, target_major, output_filename):
        self.target_ucs = target_ucs
        self.target_major = target_major
        self.output_filename = output_filename
        self.normalized_data = {
            "uc_requirements": {},
            "articulations": {},
        }

    def get_uc_key(self, uc_name):
        """
        Key generation like 'UC Berkeley' -> 'ucb_computer_science'
        """
        uc_short_name = self.target_ucs.get(uc_name, "").lower()
        major_key = re.sub(r'\s+', '_', self.target_major.lower())
        return f"{uc_short_name}_{major_key}"

    def get_all_cc_institutions(self):
        """
        """
        print("Fetching list of all community colleges...")
        # Sample Data
        return {
            "De Anza College": "de-anza-college",
            "Diablo Valley College": "diablo-valley-college",
            "Santa Monica College": "santa-monica-college",
        }

    def parse_agreement_page(self, soup, cc_name, uc_name):
        """
        Update self.normalized_data
        """
        uc_key = self.get_uc_key(uc_name)

        if uc_key not in self.normalized_data["uc_requirements"]:
            self.normalized_data["uc_requirements"][uc_key] = []
        if cc_name not in self.normalized_data["articulations"]:
            self.normalized_data["articulations"][cc_name] = {}

        requirement_blocks = soup.find_all('div', class_='articRow')

        req_index = len(self.normalized_data["uc_requirements"].get(uc_key, []))

        for block in requirement_blocks:
            try:
                # 1. UC requirements (left 'sending' div)
                sending_div = block.find('div', class_='sending')
                if not sending_div or not sending_div.find('div', class_='prefixAndNumber'):
                    continue

                uc_course_code = sending_div.find('div', class_='prefixAndNumber').text.strip()
                uc_course_title = sending_div.find('div', class_='title').text.strip()
                uc_requirement_name = f"{uc_course_code}: {uc_course_title}"

                # 2. CC Courses (right 'receiving' div)
                receiving_div = block.find('div', class_='receiving')
                if not receiving_div:
                    continue

                or_choices = []
                and_group_builder = []

                for element in receiving_div.find_all(recursive=False):
                    if 'courseLine' in element.get('class', []):
                        course_data = self.parse_agreement_page(element)
                        if course_data:
                            and_group_builder.append(course_data)
                    elif 'logical-block-connector' in element.get('class', []):
                        logic_text = element.text.strip().upper()
                        if logic_text == 'OR' and and_group_builder:
                            or_choices.append(and_group_builder)
                            and_group_builder = []

                if and_group_builder:
                    or_choices.append(and_group_builder)

                if not or_choices:
                    continue

                final_logic_structure = {"type": "OR", "course_groups": or_choices}

                req_id = f"{uc_key}-req-{req_index:02d}"
                req_index += 1

            except (AttributeError, IndexError, TypeError) as e:
                print(f"    - Skipping a block for {cc_name} to {uc_name} due to parsing error: {e}")
                continue