# Nigerian Cities and Local Government Areas (LGAs)
# Organized by state for multi-city scraping strategy

NIGERIAN_LOCATIONS = {
    "Lagos": {
        "state_code": "LA",
        "lgas": [
            "Alimosho", "Ajeromi-Ifelodun", "Apapa", "Badagry", "Epe",
            "Eti-Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja", "Ikorodu",
            "Kosofe", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo",
            "Oshodi-Isolo", "Shomolu", "Somolu", "Surulere", "Lekki"
        ]
    },
    "Abuja": {
        "state_code": "AB",
        "lgas": [
            "Abuja Municipal Area Council", "Bwari", "Gwagwalada", "Kuje",
            "Kwali", "Municipal Area Council", "Kubwa", "Wuse", "Garki",
            "Gwarinpa", "Maitama", "Asokoro"
        ]
    },
    "Rivers": {
        "state_code": "RV",
        "lgas": [
            "Port Harcourt", "Obio-Akpor", "Oyigbo", "Eleme", "Ogu-Bolo",
            "Goki", "Bonny", "Tai", "Degema", "Asari-Toru", "Akuku-Toru",
            "Abua-Odual", "Ahoada East", "Ahoada West", "Ikwerre", "Khana",
            "Gokana", "Ogoni", "Okrika", "Okirika"
        ]
    },
    "Kano": {
        "state_code": "KA",
        "lgas": [
            "Kano Municipal", "Dala", "Gwale", "Kumbotso", "Nassarawa",
            "Tarauni", "Fagge", "Kano", "Warawa", "Kura", "Garun Mallam",
            "Ungogo", "Bunkure", "Dawakin Kudu", "Gaya", "Bebeji",
            "Kibiya", "Rano", "Madobi", "Karaye"
        ]
    },
    "Kaduna": {
        "state_code": "KD",
        "lgas": [
            "Kaduna Municipal", "Igabi", "Kaduna South", "Jikara", "Kajuru",
            "Kachia", "Birnin Gwari", "Zangon Kataf", "Sabon Gida", "Giwa",
            "Soba", "Chikun", "Kudan", "Kubau", "Makarfi"
        ]
    },
    "Oyo": {
        "state_code": "OY",
        "lgas": [
            "Ibadan North", "Ibadan South East", "Ibadan South West", "Ibadan North West",
            "Ibadan North East", "Ido", "Afiijo", "Iseyin", "Ibarapa Central",
            "Ibarapa East", "Ibarapa North", "Ibarapa North West", "Atisbo",
            "Oyo West", "Oyo East", "Surulere", "Irepo", "Orelope"
        ]
    },
    "Delta": {
        "state_code": "DT",
        "lgas": [
            "Warri", "Effurun", "Sapele", "Asaba", "Ughelli", "Agbor",
            "Abraka", "Aniocha", "Isoko", "Okpe", "Oshimili",
            "Uvwie", "Udu", "Ika", "Oshimili South"
        ]
    },
    "Enugu": {
        "state_code": "EN",
        "lgas": [
            "Enugu East", "Enugu North", "Enugu South", "Nkanu East",
            "Nkanu West", "Udi", "Oji River", "Igbo Etiti", "Nsukka",
            "Udenu", "Ezeagu", "Uzo-Uwani", "Awgu", "Aninri"
        ]
    },
    "Imo": {
        "state_code": "IM",
        "lgas": [
            "Owerri", "Owerri North", "Owerri West", "Imo", "Enugu",
            "Orlu", "Onuimo", "Isiala Mbano", "Mbaitoli", "Nkwerre",
            "Ehime Mbano", "Okigwe", "Oguta", "Ohaji-Egbema"
        ]
    },
    "Bauchi": {
        "state_code": "BC",
        "lgas": [
            "Bauchi", "Alia", "Ningilari", "South Bauchi", "North Bauchi",
            "Toro", "Dindim", "Dass", "Gadaka", "Zaki", "Yuli",
            "Tafawa Balewa", "Jemma"
        ]
    },
    "Osun": {
        "state_code": "OS",
        "lgas": [
            "Osogbo", "Ife", "Iwo", "Ijebu", "Ilesha", "Oka", "Irepodun",
            "Irewole", "Isedo", "Atakumosa", "Ose", "Olorunda", "Oriade",
            "Odo-Otin", "Oyil"
        ]
    }
}

# Priority cities for initial rollout
PRIORITY_CITIES = ["Lagos", "Abuja", "Kano", "Port Harcourt", "Enugu"]

# Additional search modifiers for Nigerian context
SEARCH_MODIFIERS = {
    "location_specificity": ["in {lga}, {state}", "near {city}", "{lga} {state}"],
    "service_keywords": ["{finder}", "{finder} service", "{finder} near me"],
    "contact_keywords": ["WhatsApp", "phone", "contact", "call", "mobile"]
}
