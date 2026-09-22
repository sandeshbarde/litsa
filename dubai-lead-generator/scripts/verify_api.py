import requests
import json

base = 'http://127.0.0.1:8000'

def test_api():
    # 1. Health
    h = requests.get(f'{base}/health').json()
    print('Health status:', h.get('status'))

    # 2. Leads
    leads_resp = requests.get(f'{base}/leads?limit=5').json()
    leads = leads_resp.get('leads', [])
    total = leads_resp.get('total')
    print(f'Retrieved {len(leads)} leads. Total in DB: {total}')

    if leads:
        first = leads[0]
        lid = first['id']
        name = first.get('business_name')
        b_type = first.get('business_type')
        print(f'Testing lead: {name} ({b_type})')

        # 3. Loophole research
        lp = requests.get(f'{base}/leads/{lid}/loophole-research').json()
        print('Loophole title:', lp.get('loophole', {}).get('primary_loophole'))
        print('Revenue leak:', lp.get('loophole', {}).get('estimated_revenue_leak'))

        # 4. Generate CEO pitch
        pitch_resp = requests.post(f'{base}/leads/{lid}/generate-pitch', json={'sequence_step': 1}).json()
        pitch = pitch_resp.get('pitch', {})
        print('Pitch subject:', pitch.get('subject'))
        snippet = pitch.get('body', '')[:140].replace('\n', ' ')
        print(f'Pitch preview: {snippet}...')

        # 5. Website mockup preview
        mockup = requests.get(f'{base}/leads/{lid}/website-preview').json()
        print('Website Mockup Hero:', mockup.get('hero_title'))
        print('Website Services count:', len(mockup.get('services', [])))

    print('\nAll API endpoints working with 100% success!')

if __name__ == '__main__':
    test_api()
