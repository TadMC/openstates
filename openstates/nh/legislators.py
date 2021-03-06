import re

from billy.scrape.legislators import LegislatorScraper, Legislator
from openstates.utils import LXMLMixin


class NHLegislatorScraper(LegislatorScraper, LXMLMixin):
    jurisdiction = 'nh'
    latest_only = True
    members_url = 'http://www.gencourt.state.nh.us/downloads/Members.txt'

    chamber_map = {'H': 'lower', 'S': 'upper'}
    party_map = {
        'D': 'Democratic',
        'R': 'Republican',
        'I': 'Independent',
        'L': 'Libertarian',
    }

    def _get_photo(self, url, chamber):
        """Attempts to find a portrait in the given legislator profile."""
        doc = self.lxmlize(url)

        if chamber == 'upper':
            src = doc.xpath('//div[@id="page_content"]//img[contains(@src, '
                '"images/senators") or contains(@src, "Senator")]/@src')
        elif chamber == 'lower':
            src = doc.xpath('//img[contains(@src, "images/memberpics")]/@src')

        if src and 'nophoto' not in src[0]:
            photo_url = src[0]
        else:
            photo_url = ''

        return photo_url

    def _parse_legislator(self, row, chamber, term):
        # Capture legislator vitals.
        first_name = row['FirstName']
        middle_name = row['MiddleName']
        last_name = row['lastname']
        full_name = '{} {} {}'.format(first_name, middle_name, last_name)
        full_name = re.sub(r'[\s]{2,}', ' ', full_name)

        district = '{} {}'.format(row['county'], int(row['District'])).strip()
        party = self.party_map[row['party']]
        email = row['EMailAddress1']

        legislator = Legislator(term, chamber, district, full_name,
                                first_name=first_name, last_name=last_name,
                                middle_name=middle_name, party=party,
                                email=email)

        # Capture legislator office contact information.
        district_address = '{}\n{}\n{}, {} {}'.format(row['street'],
            row['address2'], row['city'], row['state'], row['zipcode']).strip()

        legislator.add_office('district', 'Home Address',
                              address=district_address)

        # Retrieve legislator portrait.
        #profile_url = None
        #if chamber == 'upper':
        #    profile_url = 'http://www.gencourt.state.nh.us/Senate/members/webpages/district{:02d}.aspx'.format(row['District'])
        #elif chamber == 'lower':
        #    profile_url = 'http://www.gencourt.state.nh.us/house/members/member.aspx?member={}'.format(row['employee_no'])

        #if profile_url:
        #    legislator['photo_url'] = self._get_photo(profile_url, chamber)
        #    legislator.add_source(profile_url)

        return legislator

    def _parse_members_txt(self):
        lines = self.get(self.members_url).text.splitlines()

        header = lines[0].split('\t')

        for line in lines[1:]:
            yield dict(zip(header, line.split('\t')))

    def scrape(self, chamber, term):
        for row in self._parse_members_txt():
            if self.chamber_map[row['LegislativeBody']] == chamber:
                leg = self._parse_legislator(row, chamber, term)
                leg.add_source(self.members_url)
                self.save_legislator(leg)
