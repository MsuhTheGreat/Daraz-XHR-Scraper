import requests
import json

# cookies = {
#     'aeu_cid': 'b5d286c1e1b045ae981f06d8bce940fa-1751543664917-07228-_on93nbE',
#     'af_ss_a': '1',
#     'xman_us_f': 'x_locale=en_US&x_l=1&x_c_chg=1&acs_rt=9d05d10103c7451cb3c3fa5de2864131',
#     'xman_t': 'RwEMp4CG6wkyVBimrvcxEgawV/wye5dnyRw7wQFguW9htFy0zqLTSWmAxrh9j4e9',
#     'lwrid': 'AgGX0CNly1G7vl29Y2uAX39uI%2BOq',
#     'ali_apache_id': '33.46.80.143.1751543667100.220675.9',
#     'lwrtk': 'AAIEaGbf9uIOL2P1kxKCDwmcx9Eew3pq4wXaiUkrbL+UiOn38E73NZA=',
#     'lwrtk': 'AAIEaGbf9uIOL2P1kxKCDwmcx9Eew3pq4wXaiUkrbL+UiOn38E73NZA=',
#     'e_id': 'pt60',
#     'cna': 'dF3tICBx3UcCASc8xuKOfPO9',
#     '_gcl_gs': '2.1.k1$i1751543668$u3375712',
#     '_gcl_au': '1.1.469377821.1751543672',
#     'xlly_s': '1',
#     '_fbp': 'fb.1.1751543672939.346472209528044163',
#     '_ga': 'GA1.1.1711681548.1751543673',
#     '_pin_unauth': 'dWlkPVlURmlPV1UzTTJZdFlUVmxPQzAwTkRFekxUbGhOV1l0T1Rnd1pEUTJNV0ZrWkdKaA',
#     '_gcl_aw': 'GCL.1751543915.Cj0KCQjw1JjDBhDjARIsABlM2Sv9G6YNOE6RTgtJzRKtsoc4L6pXTzE5fWJm1Co0HG0sLGcKsHoZF-EaAnySEALw_wcB',
#     '__rtbh.lid': '%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22qIjcqjhJsFSdBxCAQO4a%22%2C%22expiryDate%22%3A%222026-07-03T12%3A46%3A28.140Z%22%7D',
#     '_ga_VED1YSGNC7': 'GS2.1.s1751543673$o1$g1$t1751546788$j38$l0$h0',
#     'cto_bundle': 'WJWWxV9PZ1d5RVA2aFNhbFl3ZG5MZHhwY3VxcW9rZW9heDFVd2Y4UWFKNTRNcGtqSEpGMkw2dUZsMTYlMkJVUE5jYkloTGc2Q3R4SzhJJTJGaFRHaEdRcFllSzh6am1kWGRXU1diRE0zdWZwajVOazNsSElUVGhuSkJnTjN4OWRtWnF3TjdDYmxIaW1ZY1JQazN5Z1FsZW5qbEx3M01jZzhJbEtma0Fub1dxOTFnNkFxaEcwJTNE',
#     '_uetsid': '7c137460580411f085147bb94434ac6c',
#     '_uetvid': '7c139900580411f098f33f03211a22f6',
#     'aep_usuc_f': 'site=glo&c_tp=PKR&ups_d=0|0|0|0&ups_u_t=&region=PK&b_locale=en_US&ae_u_p_s=1',
#     'intl_locale': 'en_US',
#     'acs_usuc_t': 'x_csrf=16hvzv2xg0zi8&acs_rt=a5377b0cb8a142449db4c002110d37db',
#     '_m_h5_tk': '8e2b644e6e9ea104acc937864caec0fd_1751559752554',
#     '_m_h5_tk_enc': 'd148d9ab65c7263af9d97354a9221fb4',
#     'xman_f': 'L9+UJYWaFrjsyQTiCr9yMuGqxw/hFlGM2IQEXNzFPhemiD4UNTquMKp2D6j/u/oKysMtzOUp1D3aqgSS/NpKOLRitIgMZKKEHlnMV/QnD/7pBYZNEw20hQ==',
#     'intl_common_forever': 'CxivJdLMt8xB50g/uRN9Di2KAByKS2umZLU1Bb+4iRpBiJnh9QQYYw==',
#     'isg': 'BIGB9bJmjbYpxeGCPPFNg3g_kM2brvWgoWn3X-PSBghAyqOcK_4_cjyMrSaMMY3Y',
#     'tfstk': 'g-XIDCtfb20CzU9-VBqZCK2d_895Aly2w0tRmgHE2ppKy4Iv7kvPTkmR2g_jLvS8-a6WWiYK8TJUVYsRPL5FvaJ52ibMzQByzTZWKO5EUezHFgQ2Frz43-ShxKv8urzN9xm6hng8U3KLBpxPKeU8f-Shxcnvc-BL30G7lIYpyadp6cKWWHnKp3E66n-Jevd-pf39SFp-JUdLBfKycHKRyLE1XFxk2HQJ9l99S3h8kPtgOeIQYQ3pZk2xjMTseYB6fkYAAjkpmOxI7FIe5jAVIHgDkMLseYLfsi5lfMzInGJheZtV8RHClgIcwC6SWrTlCGBdwG0QXKs1_sRC1yHW79-WMLds2YI6F6d5QKex5hfOY_BhR0MJx9W2NEA_2YAyBtRAMwiumGpp2aAcUrDHJgIcnsJbdqxC6i9141H2lL_ENcOmFhT4flGoZrSAZAtymz6y9hxN3lZsRbApjhT4flGoZBKMbIr_f2Gl.',
#     'epssw': '9*mmCR2HF9C4EEFRmm3tIYZR33z3u70ILidYAp0m4X3hd_-cAz7tNdscvOdSvO3Sa44IHYfUSZcNBOQaDuVA6n-Gpzg1dR9f5fGSN13RHH7Lud0zm8utODl5rpanMe08fcjz4JMe34VL0UuBiw0uDe_uKe1uwR9LmR9LvETHJifEjemA3Z2131mb7u3zwaFQjc1YeeCCRZxITcex1haFIlN82P-bbAuYrf8AV7uCF3utBwmmTm7sJ2vJ-p0SCp3ALRHSWf4mHB7Q43661XK4mSFsVdY2dqH5yWnAKNyt6OwVpOhuJVplwkA1SH4QVeWRmqytg0Qbw9Iiy0xm..',
# }

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'bx-v': '2.5.31',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://www.aliexpress.com',
    'priority': 'u=1, i',
    'referer': 'https://www.aliexpress.com/w/wholesale-laptop.html?g=y&SearchText=laptop&attr=10083-4163640',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
}

json_data = {
    'pageVersion': '7ece9c0cc9cf2052db74f0d1b26b7033',
    'target': 'root',
    'data': {
        'SearchText': 'laptop',
    },
    'eventName': 'onChange',
    'dependency': [],
}

response = requests.post('https://www.aliexpress.com/fn/search-pc/index', headers=headers, json=json_data)
print(response.text)
with open("hoola_hooka.json", "w", encoding="utf-8") as file:
    json.dump(response.json(), file, indent=4)


# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"pageVersion":"7ece9c0cc9cf2052db74f0d1b26b7033","target":"root","data":{"g":"y","SearchText":"laptop","attr":"10083-4163640","origin":"y"},"eventName":"onChange","dependency":[]}'
#response = requests.post('https://www.aliexpress.com/fn/search-pc/index', cookies=cookies, headers=headers, data=data)
